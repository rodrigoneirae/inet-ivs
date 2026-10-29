import logging
from datetime import datetime, time, timedelta
from tempfile import TemporaryFile
from zoneinfo import ZoneInfo

from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.core.cache import cache
from django.core.paginator import Paginator
from django.db.models import Case, DateTimeField, F, Func, IntegerField, Q, TextField, Value, When
from django.db.models.fields.json import KeyTextTransform
from django.db.models.functions import Cast, Coalesce, NullIf
from django.db.models.query import QuerySet
from django.http import FileResponse, HttpRequest, HttpResponse, HttpResponseBadRequest
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_POST
from openpyxl import Workbook
from openpyxl.cell import WriteOnlyCell
from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE

from .models import Pedido, Sincronizacion
from .forms import FiltrosPedidosForm
from .tasks import sincronizar_pedidos

logger = logging.getLogger(__name__)


def consulta_pedidos(request: HttpRequest) -> tuple[QuerySet, FiltrosPedidosForm, str, str]:
    columnas = {
        'pedido': 'numero_mercado',
        'canal': 'datos__marketPlace',
        'fecha': 'creado_en',
        'estado': 'datos__marketPlaceStatus',
        'total': 'datos__total',
        'cliente': 'datos__buyer__name',
        'items': 'cantidad_items',
        'fulfillment': 'datos__fulfillment',
    }
    orden = request.GET.get('orden', 'fecha')
    if orden not in columnas:
        orden = 'fecha'
    direccion = request.GET.get('direccion', 'desc')
    if direccion not in ('asc', 'desc'):
        direccion = 'desc'
    queryset = Pedido.objects.annotate(
        numero_mercado=Coalesce(
            NullIf(KeyTextTransform('marketPlaceNumber', 'datos'), Value('', output_field=TextField())),
            KeyTextTransform('marketPlaceId', 'datos'),
        ),
        tipo_items=Func(F('datos__items'), function='jsonb_typeof', output_field=TextField()),
    ).annotate(
        cantidad_items=Case(
            When(tipo_items='array', then=Func(F('datos__items'), function='jsonb_array_length', output_field=IntegerField())),
            default=Value(0), output_field=IntegerField(),
        ),
    )
    filtros = FiltrosPedidosForm(request.GET)
    if filtros.is_valid():
        datos = filtros.cleaned_data
        zona = ZoneInfo(settings.ANYMARKET_TIME_ZONE)
        if datos['desde']:
            inicio = timezone.make_aware(datetime.combine(datos['desde'], time.min), zona)
            queryset = queryset.filter(creado_en__gte=inicio)
        if datos['hasta']:
            fin = timezone.make_aware(datetime.combine(datos['hasta'] + timedelta(days=1), time.min), zona)
            queryset = queryset.filter(creado_en__lt=fin)
        if datos['busqueda']:
            busqueda = datos['busqueda']
            queryset = queryset.annotate(
                texto_canal=Case(
                    When(datos__marketPlace__iexact='mercado_livre', then=Value('MERCADO LIBRE')),
                    When(datos__marketPlace__iexact='shopify', then=Value('PORTOMENAJE')),
                    When(datos__marketPlace__iexact='C52434-09', then=Value('YAKU')),
                    default=KeyTextTransform('marketPlace', 'datos'), output_field=TextField(),
                ),
                texto_estado=KeyTextTransform('marketPlaceStatus', 'datos'),
                texto_total=KeyTextTransform('total', 'datos'),
                texto_items=Cast('cantidad_items', output_field=TextField()),
                texto_fecha=Func(
                    Func(Value(settings.ANYMARKET_TIME_ZONE), F('creado_en'),
                         function='timezone', output_field=DateTimeField()),
                    Value('DD/MM/YYYY HH24:MI:SS'), function='TO_CHAR', output_field=TextField(),
                ),
            ).filter(
                Q(numero_mercado__icontains=busqueda) | Q(datos__buyer__name__icontains=busqueda) |
                Q(texto_canal__icontains=busqueda) | Q(datos__marketPlace__icontains=busqueda) |
                Q(texto_estado__icontains=busqueda) |
                Q(texto_total__icontains=busqueda) | Q(texto_items__icontains=busqueda) |
                Q(texto_fecha__icontains=busqueda)
            )
        if datos['canal']:
            queryset = queryset.filter(datos__marketPlace=datos['canal'])
        if datos['estado']:
            queryset = queryset.filter(datos__marketPlaceStatus=datos['estado'])
    else:
        queryset = queryset.none()
    campo = F(columnas[orden])
    criterio = campo.asc(nulls_last=True) if direccion == 'asc' else campo.desc(nulls_last=True)
    queryset = queryset.order_by(criterio, '-pk')
    return queryset, filtros, orden, direccion


@login_required
@permission_required('anymarket.view_pedido', raise_exception=True)
@require_GET
@never_cache
def pedidos(request: HttpRequest) -> HttpResponse:
    queryset, filtros, orden, direccion = consulta_pedidos(request)
    tamano = request.GET.get('tamano', '10')
    if tamano not in ('5', '10', '15', '20', '25'):
        tamano = '10'
    pagina = Paginator(queryset, int(tamano)).get_page(request.GET.get('page'))
    params = request.GET.copy()
    params.pop('page', None)
    params['orden'] = orden
    params['direccion'] = direccion
    params['tamano'] = tamano
    return render(request, 'anymarket/pedidos.html', {
        'pagina': pagina,
        'zona_horaria': settings.ANYMARKET_TIME_ZONE,
        'orden': orden,
        'direccion': direccion,
        'filtros': filtros,
        'parametros': params.urlencode(),
        'tamano': tamano,
        'estado_sincronizacion': Sincronizacion.objects.filter(clave='pedidos').first(),
        'estado_reconciliacion': Sincronizacion.objects.filter(clave='reconciliacion').first(),
        'canales': list(Pedido.objects.exclude(datos__marketPlace__isnull=True)
                        .values_list('datos__marketPlace', flat=True).distinct().order_by('datos__marketPlace')[:200]),
        'estados': list(Pedido.objects.exclude(datos__marketPlaceStatus__isnull=True)
                        .values_list('datos__marketPlaceStatus', flat=True).distinct()
                        .order_by('datos__marketPlaceStatus')[:100]),
    })


def solicitar_sincronizacion() -> tuple[str, str]:
    clave = 'anymarket:solicitud-sincronizacion'
    if not cache.add(clave, True, timeout=60):
        return 'warning', 'Ya se solicitó una sincronización recientemente. Inténtalo en un minuto.'
    else:
        try:
            sincronizar_pedidos.apply_async(retry=False)
        except Exception:
            cache.delete(clave)
            logger.error('No se pudo encolar la sincronización de pedidos AnyMarket.')
            return 'error', 'No se pudo iniciar la sincronización. Inténtalo nuevamente.'
        else:
            return 'success', 'Sincronización enviada. Los pedidos se actualizarán en segundo plano.'


@login_required
@permission_required('anymarket.change_pedido', raise_exception=True)
@require_POST
def ejecutar_sincronizacion(request: HttpRequest) -> HttpResponse:
    nivel, mensaje = solicitar_sincronizacion()
    getattr(messages, nivel)(request, mensaje)
    return redirect('anymarket:pedidos')


@login_required
@permission_required('anymarket.view_pedido', raise_exception=True)
@require_GET
@never_cache
def exportar_pedidos(request: HttpRequest) -> HttpResponse:
    queryset, filtros, _, _ = consulta_pedidos(request)
    if not filtros.is_valid():
        return HttpResponseBadRequest('Los filtros de exportación no son válidos.')
    limite = 50000
    if queryset.count() > limite:
        return HttpResponseBadRequest('La exportación supera 50000 pedidos; acota los filtros.')
    libro = Workbook(write_only=True)
    hoja = libro.create_sheet('Órdenes')
    hoja.append(['Canal', 'OC', 'Cliente', 'Fecha', 'Ítems', 'Venta', 'Status', 'Estado'])
    zona = ZoneInfo(settings.ANYMARKET_TIME_ZONE)
    for pedido in queryset.iterator(chunk_size=500):
        datos = pedido.datos
        cliente = datos.get('buyer') or {}
        canal = datos.get('marketPlace')
        if isinstance(canal, str):
            canal = {'mercado_livre': 'MERCADO LIBRE', 'shopify': 'PORTOMENAJE',
                     'c52434-09': 'YAKU'}.get(canal.lower(), canal)
        valores = [canal, pedido.numero_mercado, cliente.get('name'),
                   timezone.localtime(pedido.creado_en, zona).strftime('%d-%m-%Y %H:%M:%S'),
                   pedido.cantidad_items, datos.get('total'), datos.get('marketPlaceStatus'),
                   'FullFillment' if datos.get('fulfillment') is True else '']
        fila = []
        for valor in valores:
            if isinstance(valor, str):
                celda = WriteOnlyCell(hoja, value=ILLEGAL_CHARACTERS_RE.sub('', valor)[:32767])
                celda.data_type = 's'
                fila.append(celda)
            else:
                fila.append(valor if isinstance(valor, (int, float)) else None)
        hoja.append(fila)
    archivo = TemporaryFile()
    try:
        libro.save(archivo)
        archivo.seek(0)
        return FileResponse(archivo, as_attachment=True, filename='pedidos.xlsx',
                            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    except Exception:
        archivo.close()
        raise
