import json
import logging
import secrets
from functools import wraps
from uuid import UUID
from json import JSONDecodeError

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.base_user import AbstractBaseUser
from django.core.cache import caches
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.http import HttpRequest, JsonResponse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt

from modulo.informat.services.bodegas import BodegasNoDisponibles, buscar_bodega
from modulo.inventario.forms.inventario import (
    AsignacionForm, BodegaForm, ConteoForm, InventarioForm, PaginaForm, TurnoForm, ZonaForm,
)
from modulo.inventario.models import (
    Asignacion, Bodega, Conteo, Inventario, ProductoSnapshot, TokenMovil, Ubicacion, Zona,
)
from modulo.inventario.services.analisis import analizar
from modulo.inventario.services.capturadores import (crear_capturador, generar_vinculacion,
                                                      identificar_capturador, vincular_capturador)
from modulo.inventario.services.catalogo import CatalogoNoDisponible, importar_pagina
from modulo.inventario.services.turnos import ErrorTurno, actualizar_turno, asignar_turno, turnos_de_capturador

logger = logging.getLogger(__name__)


def _acceso(request: HttpRequest, permiso: str) -> JsonResponse | None:
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Inicia sesión.'}, status=401)
    if not request.user.is_active or not request.user.has_perm(f'inventario.{permiso}'):
        return JsonResponse({'error': 'Acceso denegado.'}, status=403)
    return None


def _datos(request: HttpRequest) -> dict[str, object] | None:
    if request.content_type != 'application/json' or len(request.body) > 128_000:
        return None
    try:
        datos = json.loads(request.body)
    except (JSONDecodeError, UnicodeDecodeError):
        return None
    return datos if isinstance(datos, dict) else None


def _invalidos(formulario: forms.Form) -> JsonResponse:
    return JsonResponse({'error': 'Datos inválidos.', 'detalles': formulario.errors}, status=400)


def _nombre_contador(usuario: AbstractBaseUser) -> str:
    capturador = getattr(usuario, 'capturador_inventario', None)
    return capturador.nombre if capturador else usuario.get_username()


def _configuracion_turno(turno: Asignacion, operador: str) -> dict[str, str]:
    """Configuración que recibe el capturador: operador, bodega, zona y tipo.

    El QR solo transporta el código temporal; esta estructura la decide el
    servidor a partir del turno asignado.
    """
    return {
        'inventario': str(turno.inventario.public_id),
        'inventario_nombre': turno.inventario.nombre,
        'bodega': turno.inventario.bodega.codigo,
        'bodega_nombre': turno.inventario.bodega.nombre,
        'zona': turno.zona.codigo if turno.zona_id else '',
        'zona_nombre': turno.zona.nombre if turno.zona_id else '',
        'operador': operador,
        'usuario': operador,
        'tipo': turno.tipo,
        'tipo_nombre': Asignacion.Tipo(turno.tipo).label,
        'turno': str(turno.public_id),
    }


def _token_movil(request: HttpRequest) -> bool:
    header = request.headers.get('Authorization', '')
    token = settings.INVENTARIO_APP_TOKEN
    return bool(token and len(token) >= 40 and header.startswith('Bearer ') and len(header) <= 200
                and secrets.compare_digest(header[7:], token))


def _movil(view: object, *, usuario: bool = False) -> object:
    @wraps(view)
    @csrf_exempt  # Exclusively bearer-token auth; no cookie/session path is accepted here.
    def wrapper(request: HttpRequest, *args: object, **kwargs: object) -> JsonResponse:
        header = request.headers.get('Authorization', '')
        dispositivo = identificar_capturador(header[7:]) if header.startswith('Bearer ') else None
        if dispositivo is None and not _token_movil(request):
            return JsonResponse({'error': 'Token de aplicación inválido.'}, status=401)
        if dispositivo is not None:
            request.user = dispositivo.usuario
            request.capturador = dispositivo
        elif usuario:
            nombre = request.headers.get('X-Contador', '').strip()
            if not nombre or len(nombre) > 150:
                return JsonResponse({'error': 'Configura el nombre del contador.'}, status=400)
            contador = get_user_model().objects.filter(username=nombre, is_active=True).first()
            if (contador is None or not contador.has_perm('inventario.contar_inventario')
                    or TokenMovil.objects.filter(usuario=contador).exists()):
                return JsonResponse({'error': 'Contador no autorizado.'}, status=403)
            request.user = contador
        return view(request, *args, **kwargs)
    return wrapper


class CapturadorForm(forms.Form):
    nombre = forms.CharField(max_length=80, strip=True)
    inventario = forms.UUIDField(required=False)
    zona = forms.CharField(max_length=30, strip=True, required=False)
    tipo = forms.ChoiceField(choices=Asignacion.Tipo.choices, required=False)


@require_GET
def capturadores(request: HttpRequest) -> JsonResponse:
    denegado = _acceso(request, 'supervisar_inventario')
    if denegado:
        return denegado
    dispositivos = list(TokenMovil.objects.filter(usuario__isnull=False).select_related('usuario')
                        .order_by('nombre')[:500])
    turnos_por_usuario: dict[int, list[Asignacion]] = {}
    for dispositivo in dispositivos:
        if dispositivo.usuario_id is None:
            continue
        turnos_por_usuario[dispositivo.usuario_id] = list(turnos_de_capturador(dispositivo.usuario_id)[:50])
    return JsonResponse({'capturadores': [{
        'id': str(item.public_id), 'nombre': item.nombre, 'activo': item.activo,
        'vinculado': item.vinculado_en is not None,
        'turnos': [{**_configuracion_turno(turno, item.nombre),
                    'finalizado': turno.finalizada_en is not None,
                    'inventario_estado': turno.inventario.estado}
                   for turno in turnos_por_usuario.get(item.usuario_id, [])],
    } for item in dispositivos]})


@require_POST
@never_cache
def crear_dispositivo(request: HttpRequest) -> JsonResponse:
    """Registra el capturador y, si se indica el inventario, crea su turno.

    El supervisor define zona y tipo en el mismo paso: el capturador recibe esa
    configuración y no la escribe. Todo ocurre en una transacción: si el turno
    choca con las reglas del inventario, el equipo tampoco se crea.
    """
    denegado = _acceso(request, 'supervisar_inventario')
    if denegado:
        return denegado
    form = CapturadorForm(_datos(request))
    if not form.is_valid():
        return _invalidos(form)
    inventario = None
    if form.cleaned_data['inventario'] is not None:
        inventario = Inventario.objects.filter(public_id=form.cleaned_data['inventario']).first()
        if inventario is None:
            return JsonResponse({'error': 'Inventario no encontrado.'}, status=404)
        if inventario.estado != Inventario.Estado.ABIERTO:
            return JsonResponse({'error': 'Inventario cerrado.'}, status=409)
        if not form.cleaned_data['zona']:
            return JsonResponse({'error': 'Indica la zona de conteo del capturador.'}, status=400)
        if not form.cleaned_data['tipo']:
            return JsonResponse({'error': 'Indica el tipo de conteo del capturador.'}, status=400)
    try:
        with transaction.atomic():
            dispositivo = crear_capturador(form.cleaned_data['nombre'])
            turno = None
            if inventario is not None:
                turno = asignar_turno(inventario, dispositivo.usuario, form.cleaned_data['tipo'],
                                      form.cleaned_data['zona'])
    except ErrorTurno as error:
        return JsonResponse({'error': error.mensaje}, status=error.estado)
    respuesta = {'id': str(dispositivo.public_id), 'nombre': dispositivo.nombre}
    if turno is not None:
        respuesta['turno'] = {'id': str(turno.public_id), **_configuracion_turno(turno, dispositivo.nombre)}
    return JsonResponse(respuesta, status=201)


@require_POST
def revocar_dispositivo(request: HttpRequest, capturador_id: UUID) -> JsonResponse:
    denegado = _acceso(request, 'supervisar_inventario')
    if denegado:
        return denegado
    dispositivo = TokenMovil.objects.filter(public_id=capturador_id, usuario__isnull=False).first()
    if dispositivo is None:
        return JsonResponse({'error': 'Capturador no encontrado.'}, status=404)
    dispositivo.activo = False
    dispositivo.save(update_fields=['activo'])
    return JsonResponse({'revocado': True})


@require_POST
@never_cache
def eliminar_dispositivo(request: HttpRequest, capturador_id: UUID) -> JsonResponse:
    """Elimina un capturador sin turnos ni conteos registrados.

    Un equipo con conteos conserva su historial: se revoca, no se elimina.
    """
    denegado = _acceso(request, 'supervisar_inventario')
    if denegado:
        return denegado
    with transaction.atomic():
        dispositivo = TokenMovil.objects.select_for_update().filter(
            public_id=capturador_id, usuario__isnull=False).select_related('usuario').first()
        if dispositivo is None:
            return JsonResponse({'error': 'Capturador no encontrado.'}, status=404)
        turnos = list(Asignacion.objects.select_for_update().filter(usuario=dispositivo.usuario))
        if any(turno.conteos.exists() for turno in turnos):
            return JsonResponse({'error': 'El capturador tiene conteos registrados; revócalo en lugar de eliminarlo.'}, status=409)
        try:
            # El token apunta al turno con FK PROTECT: se borra primero el equipo y
            # después el turno, o el historial de vinculación bloquea la eliminación.
            usuario = dispositivo.usuario
            dispositivo.vinculacion_asignacion = None
            dispositivo.save(update_fields=['vinculacion_asignacion'])
            dispositivo.delete()
            Asignacion.objects.filter(usuario=usuario).delete()
            usuario.delete()
        except ProtectedError as error:
            return JsonResponse({'error': 'El capturador tiene historial asociado; revócalo en lugar de eliminarlo.'}, status=409)
    logger.info('Capturador eliminado: %s', capturador_id)
    return JsonResponse({'eliminado': True})


@require_POST
@never_cache
def generar_qr_dispositivo(request: HttpRequest, capturador_id: UUID) -> JsonResponse:
    denegado = _acceso(request, 'supervisar_inventario')
    if denegado:
        return denegado
    datos = _datos(request)
    try:
        inventario_id = UUID(str(datos['inventario'])) if datos else None
    except (ValueError, KeyError, TypeError):
        inventario_id = None
    if inventario_id is None:
        return JsonResponse({'error': 'Inventario inválido.'}, status=400)
    asignacion_id = None
    if datos and datos.get('asignacion'):
        try:
            asignacion_id = UUID(str(datos['asignacion']))
        except (ValueError, TypeError):
            return JsonResponse({'error': 'Turno inválido.'}, status=400)
    resultado = generar_vinculacion(capturador_id, inventario_id, asignacion_id)
    if resultado is None:
        return JsonResponse({'error': 'Asigna primero el capturador y su zona en un inventario abierto.'}, status=409)
    dispositivo, turno, codigo = resultado
    configuracion = _configuracion_turno(turno, dispositivo.nombre)
    contenido = {'v': 1, 'codigo': codigo, **configuracion}
    return JsonResponse({'contenido_qr': json.dumps(contenido, separators=(',', ':'), ensure_ascii=False),
                         'vence_en': dispositivo.vinculacion_vence.isoformat(),
                         'configuracion': configuracion})


@require_POST
@never_cache
@csrf_exempt  # Solo se acepta el token de aplicación; no cookies ni sesiones.
def vincular_dispositivo(request: HttpRequest) -> JsonResponse:
    if not _token_movil(request):
        return JsonResponse({'error': 'Token de aplicación inválido.'}, status=401)
    ip = request.META.get('REMOTE_ADDR', '')
    clave = f'inventario:vincular:{ip}'
    try:
        cache = caches['api_rate_limit']
        if cache.add(clave, 1, timeout=60):
            intentos = 1
        else:
            intentos = cache.incr(clave)
    except Exception:
        logger.warning('No se pudo aplicar el límite de vinculación móvil.')
        return JsonResponse({'error': 'Vinculación temporalmente no disponible.'}, status=503)
    if intentos > 10:
        return JsonResponse({'error': 'Demasiados intentos. Espera un minuto.'}, status=429)
    datos = _datos(request)
    codigo = datos.get('codigo') if datos else None
    if not isinstance(codigo, str):
        return JsonResponse({'error': 'Código inválido.'}, status=400)
    resultado = vincular_capturador(codigo.strip())
    if resultado is None:
        return JsonResponse({'error': 'Código vencido o inválido.'}, status=400)
    dispositivo, token = resultado
    turno = Asignacion.objects.filter(pk=dispositivo.vinculacion_asignacion_id,
                                      usuario=dispositivo.usuario).select_related(
        'zona', 'inventario', 'inventario__bodega').first()
    if turno is None:
        return JsonResponse({'error': 'El turno asignado no está disponible.'}, status=409)
    return JsonResponse({'id': str(dispositivo.public_id), 'nombre': dispositivo.nombre, 'token': token,
                         'configuracion': _configuracion_turno(turno, dispositivo.nombre)})


@require_GET
@never_cache
def configuracion_equipo_movil(request: HttpRequest) -> JsonResponse:
    """Recupera la configuración vinculada sin confiar en datos locales o del QR."""
    dispositivo: TokenMovil | None = getattr(request, 'capturador', None)
    if dispositivo is None:
        return JsonResponse({'error': 'Token de equipo requerido.'}, status=401)
    denegado = _acceso(request, 'contar_inventario')
    if denegado:
        return denegado
    turno = Asignacion.objects.filter(pk=dispositivo.vinculacion_asignacion_id,
                                      usuario=request.user).select_related(
        'inventario__bodega', 'zona').first()
    if turno is None:
        return JsonResponse({'error': 'Configuración no disponible.'}, status=404)
    return JsonResponse({'nombre': dispositivo.nombre,
                         'configuracion': _configuracion_turno(turno, dispositivo.nombre)})


@require_GET
@never_cache
def lista_movil(request: HttpRequest) -> JsonResponse:
    form = PaginaForm(request.GET)
    if not form.is_valid():
        return _invalidos(form)
    pagina = form.cleaned_data['pagina'] or 1
    inicio = (pagina - 1) * 100
    inventarios = Inventario.objects.filter(estado=Inventario.Estado.ABIERTO)
    if getattr(request, 'capturador', None) is not None:
        inventarios = inventarios.filter(asignaciones__usuario=request.user).distinct()
    filas = list(inventarios.select_related('bodega')
                 .order_by('-creado_en', '-pk')[inicio:inicio + 101])
    return JsonResponse({'inventarios': [{'id': str(item.public_id), 'nombre': item.nombre,
                                          'bodega': item.bodega.codigo} for item in filas[:100]],
                         'hay_mas': len(filas) > 100})


@require_GET
@never_cache
def configuracion_movil(request: HttpRequest, inventario_id: UUID) -> JsonResponse:
    disponibles = Inventario.objects.filter(public_id=inventario_id, estado=Inventario.Estado.ABIERTO)
    if getattr(request, 'capturador', None) is not None:
        disponibles = disponibles.filter(asignaciones__usuario=request.user)
    inventario = disponibles.select_related('bodega').first()
    if inventario is None:
        return JsonResponse({'error': 'Inventario no disponible.'}, status=404)
    turnos = Asignacion.objects.filter(inventario=inventario, usuario=request.user).select_related('zona')
    operador = (request.capturador.nombre if getattr(request, 'capturador', None)
                else request.user.get_username())
    return JsonResponse({'inventario': str(inventario.public_id), 'inventario_nombre': inventario.nombre,
                          'bodega': inventario.bodega.codigo, 'bodega_nombre': inventario.bodega.nombre,
                          'contador': operador,
                          'turnos': [{'id': str(t.public_id), 'zona': t.zona.codigo if t.zona_id else None,
                                      'zona_nombre': t.zona.nombre if t.zona_id else None,
                                      'tipo': t.tipo, 'tipo_nombre': Asignacion.Tipo(t.tipo).label,
                                      'finalizado': t.finalizada_en is not None} for t in turnos]})


@require_GET
@never_cache
def catalogo(request: HttpRequest) -> JsonResponse:
    denegado = _acceso(request, 'contar_inventario')
    if denegado:
        return denegado
    formulario = PaginaForm(request.GET)
    if not formulario.is_valid():
        return _invalidos(formulario)
    pagina = formulario.cleaned_data['pagina'] or 1
    tamano = formulario.cleaned_data['tamano'] or 200
    inicio = (pagina - 1) * tamano
    filas = list(ProductoSnapshot.objects.order_by('codigo').values(
        'codigo', 'descripcion', 'codigo_barra',
    )[inicio:inicio + tamano + 1])
    return JsonResponse({'productos': filas[:tamano], 'pagina': pagina, 'hay_mas': len(filas) > tamano})


@require_POST
@never_cache
def importar_productos(request: HttpRequest) -> JsonResponse:
    denegado = _acceso(request, 'supervisar_inventario')
    if denegado:
        return denegado
    formulario = PaginaForm(_datos(request))
    if not formulario.is_valid():
        return _invalidos(formulario)
    pagina = formulario.cleaned_data['pagina'] or 1
    tamano = formulario.cleaned_data['tamano'] or 500
    try:
        importados, hay_mas = importar_pagina(pagina, tamano)
    except CatalogoNoDisponible as error:
        logger.warning('No se pudo importar el catálogo para inventario.')
        return JsonResponse({'error': str(error)}, status=503)
    return JsonResponse({'importados': importados, 'pagina': pagina, 'hay_mas': hay_mas})


def importar_catalogo_movil(request: HttpRequest) -> JsonResponse:
    """Importa una página del catálogo desde I-NET para el equipo vinculado.

    La app del capturador recorre las páginas y luego descarga la copia local
    (`movil/catalogo/`). Requiere token del equipo: la importación no se expone
    a sesiones web ni al token de aplicación.
    """
    if getattr(request, 'capturador', None) is None:
        return JsonResponse({'error': 'Token de equipo requerido.'}, status=401)
    denegado = _acceso(request, 'contar_inventario')
    if denegado:
        return denegado
    formulario = PaginaForm(_datos(request))
    if not formulario.is_valid():
        return _invalidos(formulario)
    pagina = formulario.cleaned_data['pagina'] or 1
    tamano = formulario.cleaned_data['tamano'] or 500
    try:
        importados, hay_mas = importar_pagina(pagina, tamano)
    except CatalogoNoDisponible as error:
        logger.warning('No se pudo importar el catálogo desde el equipo móvil.')
        return JsonResponse({'error': str(error)}, status=503)
    return JsonResponse({'importados': importados, 'pagina': pagina, 'hay_mas': hay_mas})


@require_GET
@never_cache
def asignaciones(request: HttpRequest) -> JsonResponse:
    denegado = _acceso(request, 'contar_inventario')
    if denegado:
        return denegado
    turnos = Asignacion.objects.filter(usuario=request.user).select_related(
        'inventario', 'inventario__bodega', 'ubicacion', 'ubicacion__zona', 'zona',
    ).order_by('-inventario__creado_en')[:200]
    return JsonResponse({'asignaciones': [{
        'id': str(turno.public_id), 'inventario': str(turno.inventario.public_id),
        'nombre': turno.inventario.nombre, 'bodega': turno.inventario.bodega.codigo,
        'zona': turno.zona.codigo if turno.zona_id else (turno.ubicacion.zona.codigo if turno.ubicacion_id else None),
        'ubicacion': turno.ubicacion.codigo if turno.ubicacion_id else None,
        'tipo': turno.tipo, 'abierto': turno.inventario.estado == Inventario.Estado.ABIERTO,
        'finalizado': turno.finalizada_en is not None,
    } for turno in turnos]})


@require_POST
@never_cache
def sincronizar(request: HttpRequest, asignacion_id: UUID) -> JsonResponse:
    denegado = _acceso(request, 'contar_inventario')
    if denegado:
        return denegado
    datos = _datos(request)
    eventos = datos.get('eventos') if datos else None
    if not isinstance(eventos, list) or not 1 <= len(eventos) <= 100:
        return JsonResponse({'error': 'Envía entre 1 y 100 eventos.'}, status=400)
    formularios = [ConteoForm(evento) if isinstance(evento, dict) else ConteoForm({}) for evento in eventos]
    if not all(form.is_valid() for form in formularios):
        return JsonResponse({'error': 'Eventos inválidos.'}, status=400)
    claves = [form.cleaned_data['evento'] for form in formularios]
    if len(set(claves)) != len(claves):
        return JsonResponse({'error': 'Eventos repetidos en el lote.'}, status=400)
    with transaction.atomic():
        inventario = Inventario.objects.select_for_update().filter(
            asignaciones__public_id=asignacion_id, asignaciones__usuario=request.user,
        ).first()
        if inventario is None:
            return JsonResponse({'error': 'Asignación no encontrada.'}, status=404)
        turno = Asignacion.objects.select_related('inventario').select_for_update().filter(
            public_id=asignacion_id, usuario=request.user, inventario=inventario,
        ).first()
        if turno is None:
            return JsonResponse({'error': 'Asignación no encontrada.'}, status=404)
        if turno.zona_id or turno.ubicacion_id is None:
            codigos = [form.cleaned_data['ubicacion'].strip() for form in formularios]
            if not all(codigos):
                return JsonResponse({'error': 'Escanea una ubicación antes de cada conteo.'}, status=400)
            zonas: dict[str, Zona] = {}
            for form in formularios:
                codigo_zona = form.cleaned_data['zona'].strip()
                if turno.zona_id:
                    if codigo_zona and codigo_zona != turno.zona.codigo:
                        return JsonResponse({'error': 'La zona no corresponde al turno.'}, status=400)
                    zona = turno.zona
                else:
                    if not codigo_zona:
                        return JsonResponse({'error': 'Indica la zona antes de contar.'}, status=400)
                    zona, _ = Zona.objects.get_or_create(bodega=inventario.bodega, codigo=codigo_zona,
                                                         defaults={'nombre': codigo_zona})
                    if not zona.activa:
                        transaction.set_rollback(True)
                        return JsonResponse({'error': 'Zona desactivada.'}, status=409)
                zonas[codigo_zona] = zona
            ubicaciones: dict[tuple[str, str], Ubicacion] = {}
            for form in formularios:
                codigo = form.cleaned_data['ubicacion'].strip()
                codigo_zona = form.cleaned_data['zona'].strip()
                zona = zonas[codigo_zona]
                ubicacion, _ = Ubicacion.objects.get_or_create(zona=zona, codigo=codigo)
                if not ubicacion.activa:
                    transaction.set_rollback(True)
                    return JsonResponse({'error': 'Ubicación desactivada.'}, status=409)
                ubicaciones[(codigo_zona, codigo)] = ubicacion
        else:
            ubicaciones = {}
        anteriores = {c.public_id: c for c in Conteo.objects.filter(public_id__in=claves)}
        for form in formularios:
            valor = form.cleaned_data
            codigo = valor['producto'].strip()
            producto = ProductoSnapshot.objects.filter(codigo=codigo).first()
            if producto is None:
                candidatos = list(ProductoSnapshot.objects.filter(codigo_barra=codigo).order_by('codigo')[:2])
                if len(candidatos) > 1:
                    transaction.set_rollback(True)
                    return JsonResponse({'error': 'El código de barras corresponde a más de un producto.'}, status=409)
                producto = candidatos[0] if candidatos else None
            if producto is None:
                transaction.set_rollback(True)
                return JsonResponse({'error': 'Producto no disponible en el catálogo importado.'}, status=400)
            valor['codigo_resuelto'] = producto.codigo
            valor['ubicacion_resuelta'] = (ubicaciones[(valor['zona'].strip(), valor['ubicacion'].strip())]
                                           if turno.zona_id or turno.ubicacion_id is None else turno.ubicacion)
            anterior = anteriores.get(valor['evento'])
            if anterior and (anterior.asignacion_id != turno.pk or anterior.producto_codigo != producto.codigo
                             or anterior.cantidad != valor['cantidad'] or
                             (anterior.ubicacion_id or turno.ubicacion_id) != valor['ubicacion_resuelta'].pk):
                transaction.set_rollback(True)
                return JsonResponse({'error': 'Conflicto de identificador de evento.'}, status=409)
        if turno.inventario.estado != Inventario.Estado.ABIERTO or turno.finalizada_en:
            if len(anteriores) == len(formularios):
                return JsonResponse({'confirmados': [str(clave) for clave in claves]})
            transaction.set_rollback(True)
            return JsonResponse({'error': 'El conteo ya está cerrado.'}, status=409)
        for form in formularios:
            valor = form.cleaned_data
            if valor['evento'] not in anteriores:
                Conteo.objects.create(public_id=valor['evento'], asignacion=turno,
                                      ubicacion=valor['ubicacion_resuelta'],
                                      producto_codigo=valor['codigo_resuelto'], cantidad=valor['cantidad'])
    return JsonResponse({'confirmados': [str(clave) for clave in claves]})


@require_POST
@never_cache
def finalizar(request: HttpRequest, asignacion_id: UUID) -> JsonResponse:
    denegado = _acceso(request, 'contar_inventario')
    if denegado:
        return denegado
    with transaction.atomic():
        inventario = Inventario.objects.select_for_update().filter(
            asignaciones__public_id=asignacion_id, asignaciones__usuario=request.user,
        ).first()
        if inventario is None:
            return JsonResponse({'error': 'Asignación no encontrada.'}, status=404)
        turno = Asignacion.objects.select_related('inventario').select_for_update().filter(
            public_id=asignacion_id, usuario=request.user, inventario=inventario,
        ).first()
        if turno is None:
            return JsonResponse({'error': 'Asignación no encontrada.'}, status=404)
        if turno.inventario.estado != Inventario.Estado.ABIERTO:
            return JsonResponse({'error': 'Inventario cerrado.'}, status=409)
        if turno.finalizada_en is None:
            turno.finalizada_en = timezone.now()
            turno.save(update_fields=['finalizada_en'])
    return JsonResponse({'finalizado': True})


@require_GET
@never_cache
def maestros(request: HttpRequest) -> JsonResponse:
    denegado = _acceso(request, 'supervisar_inventario')
    if denegado:
        return denegado
    return JsonResponse({
        'bodegas': [{'id': str(b.public_id), 'codigo': b.codigo, 'nombre': b.nombre}
                    for b in Bodega.objects.filter(activa=True).order_by('codigo')],
        'zonas': [{'id': str(z.public_id), 'bodega': str(z.bodega.public_id), 'codigo': z.codigo}
                  for z in Zona.objects.filter(activa=True).select_related('bodega').order_by('codigo')],
        'ubicaciones': [{'id': str(u.public_id), 'zona': str(u.zona.public_id), 'codigo': u.codigo}
                        for u in Ubicacion.objects.filter(activa=True).select_related('zona').order_by('codigo')],
    })


@require_POST
@never_cache
def crear_maestro(request: HttpRequest, tipo: str) -> JsonResponse:
    denegado = _acceso(request, 'supervisar_inventario')
    if denegado:
        return denegado
    opciones = {'bodegas': BodegaForm, 'zonas': ZonaForm, 'ubicaciones': UbicacionForm}
    if tipo not in opciones:
        return JsonResponse({'error': 'Tipo desconocido.'}, status=404)
    form = opciones[tipo](_datos(request))
    if not form.is_valid():
        return _invalidos(form)
    valores = form.cleaned_data.copy()
    if tipo == 'zonas':
        valores['bodega'] = Bodega.objects.filter(public_id=valores['bodega'], activa=True).first()
    if tipo == 'ubicaciones':
        valores['zona'] = Zona.objects.filter(public_id=valores['zona'], activa=True, bodega__activa=True).first()
    if (tipo == 'zonas' and valores['bodega'] is None) or (tipo == 'ubicaciones' and valores['zona'] is None):
        return JsonResponse({'error': 'Maestro relacionado no encontrado.'}, status=400)
    try:
        objeto = {'bodegas': Bodega, 'zonas': Zona, 'ubicaciones': Ubicacion}[tipo].objects.create(**valores)
    except IntegrityError:
        return JsonResponse({'error': 'El código ya existe.'}, status=409)
    return JsonResponse({'id': str(objeto.public_id)}, status=201)


@require_GET
@never_cache
def inventarios(request: HttpRequest) -> JsonResponse:
    denegado = _acceso(request, 'supervisar_inventario')
    if denegado:
        return denegado
    form = PaginaForm(request.GET)
    if not form.is_valid():
        return _invalidos(form)
    pagina, tamano = form.cleaned_data['pagina'] or 1, min(form.cleaned_data['tamano'] or 25, 100)
    inicio = (pagina - 1) * tamano
    filas = list(Inventario.objects.select_related('bodega').order_by('-creado_en', '-pk')[inicio:inicio + tamano + 1])
    return JsonResponse({'inventarios': [{
        'id': str(i.public_id), 'nombre': i.nombre, 'bodega': i.bodega.codigo,
        'bodega_nombre': i.bodega.nombre,
        'estado': i.estado, 'creado_en': i.creado_en.isoformat(),
    } for i in filas[:tamano]], 'pagina': pagina, 'hay_mas': len(filas) > tamano})


@require_POST
@never_cache
def crear_inventario(request: HttpRequest) -> JsonResponse:
    denegado = _acceso(request, 'supervisar_inventario')
    if denegado:
        return denegado
    form = InventarioForm(_datos(request))
    if not form.is_valid():
        return _invalidos(form)
    codigo = form.cleaned_data['bodega'].strip()
    try:
        bodega_inet = buscar_bodega(codigo)
    except BodegasNoDisponibles:
        return JsonResponse({'error': 'No fue posible validar la bodega en I-NET.'}, status=503)
    if bodega_inet is None:
        return JsonResponse({'error': 'La bodega no existe en I-NET.'}, status=400)
    with transaction.atomic():
        bodega, _ = Bodega.objects.get_or_create(codigo=bodega_inet['codigo'],
                                                  defaults={'nombre': bodega_inet['nombre']})
        if not bodega.activa:
            return JsonResponse({'error': 'Bodega desactivada.'}, status=409)
        if bodega.nombre != bodega_inet['nombre']:
            bodega.nombre = bodega_inet['nombre']
            bodega.save(update_fields=['nombre'])
        objeto = Inventario.objects.create(nombre=form.cleaned_data['nombre'], bodega=bodega, creado_por=request.user)
    return JsonResponse({'id': str(objeto.public_id)}, status=201)


@require_POST
@never_cache
def asignar(request: HttpRequest, inventario_id: UUID) -> JsonResponse:
    denegado = _acceso(request, 'supervisar_inventario')
    if denegado:
        return denegado
    form = AsignacionForm(_datos(request))
    if not form.is_valid():
        return _invalidos(form)
    with transaction.atomic():
        inventario = Inventario.objects.select_for_update().filter(public_id=inventario_id).first()
        if inventario is None:
            return JsonResponse({'error': 'Inventario no encontrado.'}, status=404)
        if inventario.estado != Inventario.Estado.ABIERTO:
            return JsonResponse({'error': 'Inventario cerrado.'}, status=409)
        if form.cleaned_data['dispositivo']:
            dispositivo = TokenMovil.objects.filter(public_id=form.cleaned_data['dispositivo'], activo=True,
                                                     usuario__is_active=True).select_related('usuario').first()
            usuario = dispositivo.usuario if dispositivo else None
        else:
            usuario = get_user_model().objects.filter(username=form.cleaned_data['usuario'], is_active=True).first()
        if usuario is None or not usuario.has_perm('inventario.contar_inventario'):
            return JsonResponse({'error': 'Contador no disponible.'}, status=400)
        codigo_zona = form.cleaned_data['zona'].strip()
        if form.cleaned_data['dispositivo'] and not codigo_zona:
            return JsonResponse({'error': 'Asigna una zona desde el backend antes de vincular.'}, status=400)
        try:
            turno = asignar_turno(inventario, usuario, form.cleaned_data['tipo'], codigo_zona)
        except ErrorTurno as error:
            return JsonResponse({'error': error.mensaje}, status=error.estado)
    return JsonResponse({'id': str(turno.public_id)}, status=201)


@require_POST
@never_cache
def reconfigurar_turno(request: HttpRequest, asignacion_id: UUID) -> JsonResponse:
    """Reconfigura la zona y el tipo de conteo de un turno ya asignado."""
    denegado = _acceso(request, 'supervisar_inventario')
    if denegado:
        return denegado
    form = TurnoForm(_datos(request))
    if not form.is_valid():
        return _invalidos(form)
    with transaction.atomic():
        turno = Asignacion.objects.select_for_update().filter(public_id=asignacion_id).first()
        if turno is None:
            return JsonResponse({'error': 'Turno no encontrado.'}, status=404)
        try:
            actualizado, movidos = actualizar_turno(turno, form.cleaned_data['zona'],
                                                    form.cleaned_data['tipo'] or None)
        except ErrorTurno as error:
            return JsonResponse({'error': error.mensaje}, status=error.estado)
    return JsonResponse({'id': str(actualizado.public_id), 'zona': actualizado.zona.codigo,
                         'tipo': actualizado.tipo, 'turnos_movidos': movidos})


@require_GET
@never_cache
def detalle(request: HttpRequest, inventario_id: UUID) -> JsonResponse:
    denegado = _acceso(request, 'supervisar_inventario')
    if denegado:
        return denegado
    inventario = Inventario.objects.filter(public_id=inventario_id).first()
    if inventario is None:
        return JsonResponse({'error': 'Inventario no encontrado.'}, status=404)
    turnos = inventario.asignaciones.select_related('ubicacion', 'zona', 'usuario',
                                                     'usuario__capturador_inventario').order_by('tipo')
    return JsonResponse({'id': str(inventario.public_id), 'nombre': inventario.nombre, 'estado': inventario.estado,
                         'bodega': inventario.bodega.codigo, 'bodega_nombre': inventario.bodega.nombre,
                         'creado_en': inventario.creado_en.isoformat(),
                         'asignaciones': [{'id': str(t.public_id), 'zona': t.zona.codigo if t.zona_id else (t.ubicacion.zona.codigo if t.ubicacion_id else 'Todas'),
                                           'tipo': t.tipo, 'usuario': _nombre_contador(t.usuario),
                                           'capturador': str(t.usuario.capturador_inventario.public_id)
                                           if getattr(t.usuario, 'capturador_inventario', None) else None,
                                          'finalizado': t.finalizada_en is not None} for t in turnos],
                         'resultados': analizar(inventario)})


@require_POST
@never_cache
def cerrar(request: HttpRequest, inventario_id: UUID) -> JsonResponse:
    denegado = _acceso(request, 'supervisar_inventario')
    if denegado:
        return denegado
    with transaction.atomic():
        inventario = Inventario.objects.select_for_update().filter(public_id=inventario_id).first()
        if inventario is None:
            return JsonResponse({'error': 'Inventario no encontrado.'}, status=404)
        if inventario.estado != Inventario.Estado.ABIERTO:
            return JsonResponse({'error': 'Inventario ya cerrado.'}, status=409)
        turnos = list(inventario.asignaciones.values('ubicacion_id', 'zona_id', 'tipo', 'finalizada_en'))
        por_ubicacion: dict[tuple[str, int], set[str]] = {}
        for turno in turnos:
            if turno['finalizada_en'] is None:
                return JsonResponse({'error': 'Hay conteos sin finalizar.'}, status=409)
            clave = (('zona', turno['zona_id']) if turno['zona_id'] else
                     ('ubicacion', turno['ubicacion_id']) if turno['ubicacion_id'] else ('global', inventario.pk))
            por_ubicacion.setdefault(clave, set()).add(turno['tipo'])
        if not turnos or any(tipos not in ({'unico'}, {'a', 'b'}) for tipos in por_ubicacion.values()):
            return JsonResponse({'error': 'El inventario necesita A/B o conteo único por turno.'}, status=409)
        inventario.estado = Inventario.Estado.CERRADO
        inventario.cerrado_en = timezone.now()
        inventario.cerrado_por = request.user
        inventario.save(update_fields=['estado', 'cerrado_en', 'cerrado_por'])
    logger.info('Inventario cerrado: %s', inventario.public_id)
    return JsonResponse({'cerrado': True})


lista_movil_autorizada = _movil(lista_movil)
configuracion_movil_autorizada = _movil(configuracion_movil, usuario=True)
configuracion_equipo_movil_autorizada = _movil(configuracion_equipo_movil)
catalogo_movil = _movil(catalogo, usuario=True)
importar_catalogo_movil_autorizado = _movil(importar_catalogo_movil)
sincronizar_movil = _movil(sincronizar, usuario=True)
finalizar_movil = _movil(finalizar, usuario=True)
