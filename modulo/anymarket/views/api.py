import logging
from zoneinfo import ZoneInfo

from django.conf import settings
from django.core.paginator import Paginator
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_POST

from modulo.anymarket.views import consulta_pedidos, exportar_pedidos, solicitar_sincronizacion
from modulo.anymarket.models import IntentoInet, Pedido, Sincronizacion
from modulo.anymarket.services.inet import crear_pedido
from modulo.anymarket.services.tipo_documento import tipo_documento_solicitado
from modulo.anymarket.services.auditoria_inet import AuditoriaInetError, descifrar_mensaje

logger = logging.getLogger(__name__)


@require_POST
@never_cache
def sincronizar(request: HttpRequest) -> JsonResponse:
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Inicia sesión.'}, status=401)
    if not request.user.has_perm('anymarket.change_pedido'):
        return JsonResponse({'error': 'No tienes permiso para ejecutar la sincronización.'}, status=403)
    nivel, mensaje = solicitar_sincronizacion()
    return JsonResponse({'mensaje': mensaje} if nivel == 'success' else {'error': mensaje},
                        status={'success': 200, 'warning': 429, 'error': 503}[nivel])


@require_POST
@never_cache
def crear_pedido_inet(request: HttpRequest, uuid_pedido: object) -> JsonResponse:
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Inicia sesión.'}, status=401)
    if not request.user.has_perm('anymarket.change_pedido'):
        return JsonResponse({'error': 'No tienes permiso para crear pedidos en I-NET.'}, status=403)
    try:
        crear_pedido(uuid_pedido, venta=True)
    except Pedido.DoesNotExist:
        return JsonResponse({'error': 'Pedido no encontrado.'}, status=404)
    except ValueError as exc:
        return JsonResponse({'error': str(exc)}, status=409)
    pedido = Pedido.objects.get(uuid=uuid_pedido)
    if pedido.inet_estado != 'creado':
        return JsonResponse({'error': pedido.inet_error}, status=409)
    return JsonResponse({'mensaje': 'Documento creado en I-NET.', 'numero': pedido.inet_numero,
                         'tipo_documento': pedido.inet_tipo_documento})


@require_GET
@never_cache
def errores_pedido_inet(request: HttpRequest, uuid_pedido: object) -> JsonResponse:
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Inicia sesión.'}, status=401)
    if not request.user.has_perm('anymarket.change_pedido'):
        return JsonResponse({'error': 'No tienes permiso para consultar errores.'}, status=403)
    pedido = Pedido.objects.filter(uuid=uuid_pedido).first()
    if pedido is None:
        return JsonResponse({'error': 'Pedido no encontrado.'}, status=404)
    intentos = pedido.intentos_inet.order_by('-fecha').values('uuid', 'fecha', 'resultado', 'detalle')[:100]
    return JsonResponse({'intentos': list(intentos)})


@require_GET
@never_cache
def detalle_intento_inet(request: HttpRequest, uuid_pedido: object, uuid_intento: object) -> JsonResponse:
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Inicia sesión.'}, status=401)
    if not request.user.has_perm('anymarket.change_pedido'):
        return JsonResponse({'error': 'No tienes permiso para consultar el detalle.'}, status=403)
    intento = IntentoInet.objects.filter(uuid=uuid_intento, pedido__uuid=uuid_pedido).first()
    if intento is None:
        return JsonResponse({'error': 'Intento no encontrado.'}, status=404)
    try:
        solicitud = descifrar_mensaje(intento.solicitud_cifrada)
        respuesta = descifrar_mensaje(intento.respuesta_cifrada)
    except AuditoriaInetError:
        logger.warning('No se pudieron descifrar los detalles de un intento I-NET.')
        return JsonResponse({'error': 'No fue posible leer el detalle guardado.'}, status=503)
    logger.info('Consulta del detalle de un intento I-NET por usuario interno %s.', request.user.pk)
    return JsonResponse({'solicitud': solicitud, 'respuesta': respuesta})


@require_GET
@never_cache
def exportar(request: HttpRequest) -> HttpResponse:
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Inicia sesión.'}, status=401)
    if not request.user.has_perm('anymarket.view_pedido'):
        return JsonResponse({'error': 'No tienes permiso para exportar pedidos.'}, status=403)
    response = exportar_pedidos(request)
    if response.status_code == 400:
        return JsonResponse({'error': response.content.decode('utf-8')}, status=400)
    return response


@require_GET
@never_cache
def pedidos(request: HttpRequest) -> JsonResponse:
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Inicia sesión.'}, status=401)
    if not request.user.has_perm('anymarket.view_pedido'):
        return JsonResponse({'error': 'No tienes permiso para ver pedidos.'}, status=403)
    queryset, filtros, _, _ = consulta_pedidos(request)
    if not filtros.is_valid():
        return JsonResponse({'error': 'Los filtros no son válidos.'}, status=400)
    pagina = Paginator(queryset, 20).get_page(request.GET.get('page'))
    results = []
    for pedido in pagina:
        datos = pedido.datos
        buyer = datos.get('buyer') or {}
        results.append({'uuid': str(pedido.uuid), 'numero': pedido.numero_mercado,
                        'canal': datos.get('marketPlace'), 'cliente': buyer.get('name') if isinstance(buyer, dict) else None,
                        'fecha': pedido.creado_en.isoformat(),
                        'fecha_local': timezone.localtime(pedido.creado_en, ZoneInfo(settings.ANYMARKET_TIME_ZONE)).strftime('%d/%m/%Y %H:%M:%S'),
                        'items': pedido.cantidad_items,
                         'total': datos.get('total'), 'estado': datos.get('marketPlaceStatus'),
                         'inet_estado': pedido.inet_estado, 'inet_numero': pedido.inet_numero,
                         'inet_tipo_documento': pedido.inet_tipo_documento,
                         'documento_solicitado': tipo_documento_solicitado(datos),
                         'fulfillment': datos.get('fulfillment') is True})
    canales = list(Pedido.objects.exclude(datos__marketPlace__isnull=True)
                   .values_list('datos__marketPlace', flat=True).distinct().order_by('datos__marketPlace')[:200])
    estados = list(Pedido.objects.exclude(datos__marketPlaceStatus__isnull=True)
                   .values_list('datos__marketPlaceStatus', flat=True).distinct()
                   .order_by('datos__marketPlaceStatus')[:100])
    sincronizaciones = {
        registro.clave: {
            'ultimo_exito': registro.ultimo_exito.isoformat() if registro.ultimo_exito else None,
            'ultimo_error_en': registro.ultimo_error_en.isoformat() if registro.ultimo_error_en else None,
            'ultimo_error': registro.ultimo_error,
        }
        for registro in Sincronizacion.objects.filter(clave__in=['pedidos', 'reconciliacion'])
    }
    return JsonResponse({'resultados': results, 'pagina': pagina.number,
                         'paginas': pagina.paginator.num_pages, 'total': pagina.paginator.count,
                         'canales': canales, 'estados': estados, 'sincronizaciones': sincronizaciones,
                         'zona_horaria': settings.ANYMARKET_TIME_ZONE})
