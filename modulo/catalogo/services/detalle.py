import logging
from datetime import timedelta
from typing import Any

from django.db import transaction
from django.utils import timezone

from modulo.informat.services.stock import ServicioInformatError, consultar_producto_venta

from ..models import AtributoProducto, Producto

logger = logging.getLogger(__name__)
DETALLE_VIGENTE_POR = timedelta(hours=24)
REINTENTO_DETALLE_CADA = timedelta(minutes=15)
ATRIBUTOS_WS = ('ATTUNO', 'ATTDOS', 'ATTTRE', 'ATTCUA', 'ATTCIN')


def _es_diccionario(valor: Any) -> dict[str, Any]:
    return valor if isinstance(valor, dict) else {}


def normalizar_detalle_ws(respuesta: dict[str, Any] | None) -> dict[str, Any]:
    """Expone solo campos descriptivos; omite cuentas, precios y stock."""
    respuesta = _es_diccionario(respuesta)
    venta = _es_diccionario(respuesta.get('VENTA'))
    existencias = _es_diccionario(respuesta.get('EXISTENCIAS'))
    atributos_ws = _es_diccionario(respuesta.get('ATRIBUTOS'))
    metricas = _es_diccionario(respuesta.get('METRICAS'))
    codigos = venta.get('CODIGO_BARRA')
    if not isinstance(codigos, list):
        codigos = [codigos] if isinstance(codigos, (str, int)) else []
    atributos = []
    for prefijo in ATRIBUTOS_WS:
        nombre = atributos_ws.get(f'{prefijo}_DSC')
        codigo = atributos_ws.get(f'{prefijo}_COD')
        if nombre:
            atributos.append({'clave': prefijo, 'codigo': str(codigo or ''), 'nombre': str(nombre)})
    return {
        'venta': {
            'descripcion_corta': str(venta.get('DESC_CORTA') or ''),
            'descripcion_larga': str(venta.get('DESC_LARGA') or ''),
            'especificaciones': str(venta.get('ESPEC_TECNICAS') or ''),
            'codigos_barra': [str(codigo) for codigo in codigos if isinstance(codigo, (str, int))],
        },
        'existencias': {
            'estado': existencias.get('ESTADO'),
            'unidad': str(existencias.get('UNIDADNOM_EXI') or ''),
            'unidad_abreviada': str(existencias.get('UNIDADABR_EXI') or ''),
            'clasificacion': str(existencias.get('CLASIFICACION_DES') or ''),
        },
        'atributos': atributos,
        'metricas': {
            'unidad': str(metricas.get('UNIMED_ABR') or metricas.get('UNIMED_DSC') or ''),
            'factor_conversion': str(metricas.get('FACTOR_CONV') or ''),
            'peso': str(metricas.get('PESO') or ''),
            'volumen': str(metricas.get('VOLUMEN') or ''),
            'alto': str(metricas.get('ALTO') or ''),
            'largo': str(metricas.get('LARGO') or ''),
            'ancho': str(metricas.get('ANCHO') or ''),
        },
    }


def _atributos_cache_validos(detalle: dict[str, Any]) -> bool:
    atributos = detalle.get('atributos', [])
    return isinstance(atributos, list) and all(
        isinstance(atributo, dict) and atributo.get('clave') in ATRIBUTOS_WS
        for atributo in atributos
    )


def _guardar_atributos(producto: Producto, detalle: dict[str, Any]) -> None:
    atributos = [
        AtributoProducto(
            producto=producto,
            clave=atributo['clave'],
            codigo=atributo['codigo'],
            nombre=atributo['nombre'],
        )
        for atributo in detalle.get('atributos', [])
        if isinstance(atributo, dict) and atributo.get('clave') in ATRIBUTOS_WS and atributo.get('nombre')
    ]
    claves = [atributo.clave for atributo in atributos]
    if atributos:
        AtributoProducto.objects.bulk_create(
            atributos,
            update_conflicts=True,
            unique_fields=['producto', 'clave'],
            update_fields=['codigo', 'nombre'],
        )
        producto.atributos_catalogo.exclude(clave__in=claves).delete()
    else:
        producto.atributos_catalogo.all().delete()


def obtener_detalle_ws(producto: Producto) -> dict[str, Any]:
    """Usa el último detalle guardado y lo renueva bajo demanda cada 24 horas."""
    ahora = timezone.now()
    vencido = (producto.detalle_ws_actualizado_en is None
               or producto.detalle_ws_actualizado_en <= ahora - DETALLE_VIGENTE_POR)
    reintentar = (producto.detalle_ws_intento_en is None
                  or producto.detalle_ws_intento_en <= ahora - REINTENTO_DETALLE_CADA)
    if not _atributos_cache_validos(producto.detalle_ws):
        vencido = True
    if not vencido or not reintentar:
        atributos_cacheados = producto.detalle_ws.get('atributos', [])
        if atributos_cacheados and not producto.atributos_catalogo.exists():
            with transaction.atomic():
                _guardar_atributos(producto, producto.detalle_ws)
        return producto.detalle_ws

    producto.detalle_ws_intento_en = ahora
    producto.save(update_fields=['detalle_ws_intento_en'])
    try:
        respuesta = consultar_producto_venta(producto.sku)
    except ServicioInformatError as exc:
        logger.warning('No se pudo actualizar detalle I-NET (%s).', type(exc).__name__)
        return producto.detalle_ws

    detalle = normalizar_detalle_ws(respuesta)
    with transaction.atomic():
        producto.detalle_ws = detalle
        producto.detalle_ws_actualizado_en = ahora
        producto.save(update_fields=['detalle_ws', 'detalle_ws_actualizado_en'])
        _guardar_atributos(producto, detalle)
    return producto.detalle_ws
