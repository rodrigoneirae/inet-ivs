import hashlib
import logging

from django import forms
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.models import Group
from django.core.cache import caches
from django.core.paginator import Paginator
from django.db import transaction
from django.http import HttpRequest, JsonResponse
from django.middleware.csrf import get_token
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_POST

logger = logging.getLogger(__name__)
GRUPO_ADMINISTRADOR = 'Administrador'


class BuscarUsuariosForm(forms.Form):
    busqueda = forms.CharField(required=False, max_length=100)
    pagina = forms.IntegerField(required=False, min_value=1, max_value=10000)


class CambiarPerfilForm(forms.Form):
    username = forms.CharField(max_length=150)
    administrador = forms.BooleanField(required=False)


def _permisos_sesion(user: object) -> dict[str, bool]:
    return {
        'puede_ver_stock': user.has_perm('informat.consultar_stock'),
        'puede_ver_catalogo': user.has_perm('informat.consultar_productos_inet'),
        'puede_ver_catalogo_web': user.has_perm('catalogo.ver_catalogo'),
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
    grupo = Group.objects.filter(name=GRUPO_ADMINISTRADOR).first()
    miembros = set(grupo.user_set.filter(pk__in=[usuario.pk for usuario in pagina.object_list]).values_list('pk', flat=True)) if grupo else set()
    return JsonResponse({
        'usuarios': [{
            'username': usuario.get_username(),
            'activo': usuario.is_active,
            'superusuario': usuario.is_superuser,
            'administrador': usuario.pk in miembros,
        } for usuario in pagina.object_list],
        'pagina': pagina.number,
        'paginas': pagina.paginator.num_pages,
        'total': pagina.paginator.count,
        'hay_anterior': pagina.has_previous(),
        'hay_siguiente': pagina.has_next(),
        'grupo_configurado': grupo is not None,
    })


@require_POST
@never_cache
def cambiar_perfil_usuario(request: HttpRequest) -> JsonResponse:
    denegado = _acceso_solo_superusuario(request)
    if denegado:
        return denegado
    formulario = CambiarPerfilForm(request.POST)
    if not formulario.is_valid():
        return JsonResponse({'error': 'Datos de usuario inválidos.'}, status=400)
    try:
        grupo = Group.objects.get(name=GRUPO_ADMINISTRADOR)
    except Group.DoesNotExist:
        return JsonResponse({'error': 'El perfil Administrador no está configurado.'}, status=409)
    try:
        with transaction.atomic():
            usuario = get_user_model().objects.select_for_update().get(
                username=formulario.cleaned_data['username'],
            )
            if usuario.is_superuser:
                return JsonResponse({'error': 'Los superusuarios ya tienen acceso total; su perfil no se modifica aquí.'}, status=400)
            if formulario.cleaned_data['administrador']:
                usuario.groups.add(grupo)
            else:
                usuario.groups.remove(grupo)
    except get_user_model().DoesNotExist:
        return JsonResponse({'error': 'No se encontró el usuario.'}, status=404)
    logger.info(
        'Perfil Administrador %s para usuario interno %s por usuario interno %s.',
        'asignado' if formulario.cleaned_data['administrador'] else 'retirado',
        usuario.pk,
        request.user.pk,
    )
    return JsonResponse({
        'mensaje': 'Perfil actualizado.',
        'username': usuario.get_username(),
        'administrador': formulario.cleaned_data['administrador'],
    })


@require_POST
@never_cache
def salir(request: HttpRequest) -> JsonResponse:
    logout(request)
    return JsonResponse({'csrf': get_token(request)})
