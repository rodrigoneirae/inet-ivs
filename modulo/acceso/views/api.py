import hashlib
import logging

from django import forms
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.models import Group, Permission
from django.core.cache import caches
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.http import HttpRequest, JsonResponse
from django.middleware.csrf import get_token
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_POST

logger = logging.getLogger(__name__)
GRUPO_ADMINISTRADOR = 'Administrador'
PREFIJO_GRUPO_PERFIL = 'Perfil: '
PERMISOS_PERFIL = (
    ('anymarket.view_pedido', 'Consultar pedidos'),
    ('anymarket.change_pedido', 'Ejecutar acciones de pedidos y sincronización'),
    ('informat.consultar_stock', 'Consultar stock'),
    ('informat.consultar_productos_inet', 'Consultar productos I-NET'),
    ('informat.administrar_token', 'Administrar token de I-NET'),
    ('catalogo.ver_catalogo', 'Consultar catálogo web e imágenes'),
    ('catalogo.descargar_catalogo', 'Descargar imágenes del catálogo'),
)


class BuscarUsuariosForm(forms.Form):
    busqueda = forms.CharField(required=False, max_length=100)
    pagina = forms.IntegerField(required=False, min_value=1, max_value=10000)


class CambiarPerfilForm(forms.Form):
    username = forms.CharField(max_length=150)
    perfiles = forms.MultipleChoiceField(required=False)

    def __init__(self, *args: object, grupos: list[Group], **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        self.fields['perfiles'].choices = [(grupo.name, grupo.name) for grupo in grupos]


class GuardarPerfilForm(forms.Form):
    nombre = forms.CharField(max_length=80)
    nombre_original = forms.CharField(required=False, max_length=80)
    permisos = forms.MultipleChoiceField(
        required=False,
        choices=[(clave, etiqueta) for clave, etiqueta in PERMISOS_PERFIL],
    )

    def clean_nombre(self) -> str:
        nombre = self.cleaned_data['nombre'].strip()
        if not nombre or nombre.casefold() == GRUPO_ADMINISTRADOR.casefold():
            raise forms.ValidationError('Ese nombre está reservado.')
        if nombre.startswith(PREFIJO_GRUPO_PERFIL):
            raise forms.ValidationError('No incluyas el prefijo interno del perfil.')
        return nombre

    def clean_permisos(self) -> list[str]:
        permisos = self.cleaned_data['permisos']
        if 'catalogo.descargar_catalogo' in permisos and 'catalogo.ver_catalogo' not in permisos:
            raise forms.ValidationError('Descargar imágenes requiere también consultar el catálogo.')
        return permisos


def _grupos_perfiles() -> list[Group]:
    return list(Group.objects.filter(
        Q(name=GRUPO_ADMINISTRADOR) | Q(name__startswith=PREFIJO_GRUPO_PERFIL),
    ).order_by('name'))


def _nombre_perfil(grupo: Group) -> str:
    return grupo.name.removeprefix(PREFIJO_GRUPO_PERFIL)


def _serializar_perfil(grupo: Group) -> dict[str, object]:
    return {
        'nombre': _nombre_perfil(grupo),
        'clave': grupo.name,
        'administrador': grupo.name == GRUPO_ADMINISTRADOR,
        'permisos': sorted(
            f'{permiso.content_type.app_label}.{permiso.codename}'
            for permiso in grupo.permissions.select_related('content_type').all()
            if f'{permiso.content_type.app_label}.{permiso.codename}' in dict(PERMISOS_PERFIL)
        ),
        'usuarios_asignados': grupo.user_set.count(),
    }


def _permisos_sesion(user: object) -> dict[str, bool]:
    return {
        'puede_ver_stock': user.has_perm('informat.consultar_stock'),
        'puede_ver_catalogo': user.has_perm('informat.consultar_productos_inet'),
        'puede_ver_catalogo_web': user.has_perm('catalogo.ver_catalogo'),
        'puede_descargar_catalogo': user.has_perm('catalogo.ver_catalogo') and user.has_perm('catalogo.descargar_catalogo'),
        'puede_administrar_token': user.has_perm('informat.administrar_token'),
        'puede_ver_pedidos': user.has_perm('anymarket.view_pedido'),
        'puede_sincronizar': user.has_perm('anymarket.change_pedido'),
        'puede_configurar_usuarios': user.is_superuser,
    }


def _acceso_solo_superusuario(request: HttpRequest) -> JsonResponse | None:
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Debes iniciar sesión.'}, status=401)
    if not request.user.is_superuser:
        return JsonResponse({'error': 'No tienes permiso para configurar perfiles.'}, status=403)
    return None

class LoginForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(max_length=256, strip=False)


@require_GET
@never_cache
def sesion(request: HttpRequest) -> JsonResponse:
    datos = {
        'csrf': get_token(request),
        'usuario': request.user.get_username() if request.user.is_authenticated else None,
        **_permisos_sesion(request.user),
    }
    return JsonResponse(datos)


@require_POST
@never_cache
def ingresar(request: HttpRequest) -> JsonResponse:
    # A shared Redis counter limits attempts even when several web workers run.
    cache = caches['api_rate_limit']
    ip = request.META.get('REMOTE_ADDR', '')
    key = 'api-login:' + hashlib.sha256(ip.encode()).hexdigest()
    if cache.add(key, 1, timeout=60):
        count = 1
    else:
        try:
            count = cache.incr(key)
        except ValueError:
            cache.add(key, 1, timeout=60)
            count = 1
    if count > 10:
        return JsonResponse({'error': 'Demasiados intentos. Inténtalo en un minuto.'}, status=429)
    form = LoginForm(request.POST)
    if not form.is_valid():
        return JsonResponse({'error': 'Credenciales inválidas.'}, status=400)
    user = authenticate(request, **form.cleaned_data)
    if user is None:
        return JsonResponse({'error': 'Credenciales inválidas.'}, status=401)
    login(request, user)
    return JsonResponse({
        'csrf': get_token(request),
        'usuario': user.get_username(),
        **_permisos_sesion(user),
    })


@require_GET
@never_cache
def usuarios_perfiles(request: HttpRequest) -> JsonResponse:
    denegado = _acceso_solo_superusuario(request)
    if denegado:
        return denegado
    formulario = BuscarUsuariosForm(request.GET)
    if not formulario.is_valid():
        return JsonResponse({'error': 'Parámetros de búsqueda inválidos.'}, status=400)
    usuarios = get_user_model().objects.all().order_by('username')
    busqueda = formulario.cleaned_data['busqueda'].strip()
    if busqueda:
        usuarios = usuarios.filter(username__icontains=busqueda)
    pagina = Paginator(usuarios, 50).get_page(formulario.cleaned_data['pagina'])
    grupos = _grupos_perfiles()
    grupos_usuario: dict[int, list[str]] = {usuario.pk: [] for usuario in pagina.object_list}
    for grupo in grupos:
        miembros = grupo.user_set.filter(pk__in=grupos_usuario).values_list('pk', flat=True)
        for user_id in miembros:
            grupos_usuario[user_id].append(grupo.name)
    return JsonResponse({
        'usuarios': [{
            'username': usuario.get_username(),
            'activo': usuario.is_active,
            'superusuario': usuario.is_superuser,
            'perfiles': grupos_usuario[usuario.pk],
        } for usuario in pagina.object_list],
        'pagina': pagina.number,
        'paginas': pagina.paginator.num_pages,
        'total': pagina.paginator.count,
        'hay_anterior': pagina.has_previous(),
        'hay_siguiente': pagina.has_next(),
        'grupo_configurado': any(grupo.name == GRUPO_ADMINISTRADOR for grupo in grupos),
        'perfiles': [_serializar_perfil(grupo) for grupo in grupos],
        'permisos_disponibles': [{'clave': clave, 'nombre': nombre} for clave, nombre in PERMISOS_PERFIL],
    })


@require_POST
@never_cache
def cambiar_perfil_usuario(request: HttpRequest) -> JsonResponse:
    denegado = _acceso_solo_superusuario(request)
    if denegado:
        return denegado
    grupos = _grupos_perfiles()
    formulario = CambiarPerfilForm(request.POST, grupos=grupos)
    if not formulario.is_valid():
        return JsonResponse({'error': 'Datos de usuario inválidos.'}, status=400)
    try:
        with transaction.atomic():
            usuario = get_user_model().objects.select_for_update().get(
                username=formulario.cleaned_data['username'],
            )
            if usuario.is_superuser:
                return JsonResponse({'error': 'Los superusuarios ya tienen acceso total; su perfil no se modifica aquí.'}, status=400)
            grupos_perfil = _grupos_perfiles()
            usuario.groups.remove(*grupos_perfil)
            grupos_elegidos = [
                grupo for grupo in grupos_perfil
                if grupo.name in formulario.cleaned_data['perfiles']
            ]
            usuario.groups.add(*grupos_elegidos)
    except get_user_model().DoesNotExist:
        return JsonResponse({'error': 'No se encontró el usuario.'}, status=404)
    logger.info(
        'Perfiles de acceso actualizados para usuario interno %s por usuario interno %s.',
        usuario.pk,
        request.user.pk,
    )
    return JsonResponse({
        'mensaje': 'Perfil actualizado.',
        'username': usuario.get_username(),
        'perfiles': formulario.cleaned_data['perfiles'],
    })


@require_POST
@never_cache
def guardar_perfil(request: HttpRequest) -> JsonResponse:
    denegado = _acceso_solo_superusuario(request)
    if denegado:
        return denegado
    formulario = GuardarPerfilForm(request.POST)
    if not formulario.is_valid():
        return JsonResponse({'error': 'Datos del perfil inválidos.', 'detalles': formulario.errors}, status=400)
    nombre = formulario.cleaned_data['nombre']
    nombre_original = formulario.cleaned_data['nombre_original'].strip()
    nombre_grupo_original = (PREFIJO_GRUPO_PERFIL + nombre_original) if nombre_original else ''
    nombre_grupo = PREFIJO_GRUPO_PERFIL + nombre
    permisos_ids = [valor.split('.', 1) for valor in formulario.cleaned_data['permisos']]
    permisos = []
    for app_label, codename in permisos_ids:
        try:
            permisos.append(Permission.objects.get(content_type__app_label=app_label, codename=codename))
        except Permission.DoesNotExist:
            return JsonResponse({'error': 'Uno de los permisos seleccionados ya no está disponible.'}, status=400)

    try:
        with transaction.atomic():
            if nombre_grupo_original:
                grupo = Group.objects.select_for_update().get(name=nombre_grupo_original)
                if Group.objects.filter(name=nombre_grupo).exclude(pk=grupo.pk).exists():
                    return JsonResponse({'error': 'Ya existe un perfil con ese nombre.'}, status=409)
                grupo.name = nombre_grupo
                grupo.save(update_fields=['name'])
            else:
                if Group.objects.filter(name=nombre_grupo).exists():
                    return JsonResponse({'error': 'Ya existe un perfil con ese nombre.'}, status=409)
                grupo = Group.objects.create(name=nombre_grupo)
            grupo.permissions.set(permisos)
    except Group.DoesNotExist:
        return JsonResponse({'error': 'No se encontró el perfil que deseas editar.'}, status=404)
    except IntegrityError:
        return JsonResponse({'error': 'Ya existe un perfil con ese nombre.'}, status=409)

    logger.info('Perfil de acceso guardado por superusuario interno %s.', request.user.pk)
    return JsonResponse({'mensaje': 'Perfil guardado.', 'nombre': nombre})


@require_POST
@never_cache
def eliminar_perfil(request: HttpRequest) -> JsonResponse:
    denegado = _acceso_solo_superusuario(request)
    if denegado:
        return denegado
    clave = request.POST.get('clave', '').strip()
    if not clave.startswith(PREFIJO_GRUPO_PERFIL):
        return JsonResponse({'error': 'Solo se pueden eliminar perfiles personalizados.'}, status=400)
    try:
        with transaction.atomic():
            grupo = Group.objects.select_for_update().get(name=clave)
            if grupo.user_set.exists():
                return JsonResponse({'error': 'Retira el perfil de los usuarios antes de eliminarlo.'}, status=409)
            nombre = _nombre_perfil(grupo)
            grupo.delete()
    except Group.DoesNotExist:
        return JsonResponse({'error': 'No se encontró el perfil.'}, status=404)
    logger.info('Perfil personalizado eliminado por superusuario interno %s.', request.user.pk)
    return JsonResponse({'mensaje': f'Perfil {nombre} eliminado.'})


@require_POST
@never_cache
def salir(request: HttpRequest) -> JsonResponse:
    logout(request)
    return JsonResponse({'csrf': get_token(request)})
