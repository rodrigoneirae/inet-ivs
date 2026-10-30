"""Creación manual de pedidos AnyMarket en el servicio comercial I-NET."""

import logging
import re
from decimal import Decimal, ROUND_HALF_UP
from typing import Any
from uuid import UUID
from zoneinfo import ZoneInfo

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from modulo.informat.comercial import AutenticacionComercialError, insertar_documento
from modulo.informat.services import ServicioInformatError

from .importes_inet import ImportePedidoError, calcular_importes
from .models import IntentoInet, Pedido

logger = logging.getLogger(__name__)


def preparar_documento(pedido: Pedido) -> dict[str, Any]:
    importes = calcular_importes(pedido.datos)
    fecha = timezone.localtime(pedido.creado_en, ZoneInfo(settings.ANYMARKET_TIME_ZONE)).date().isoformat()
    lineas = []
    neto_lineas = Decimal('0')
    for numero, item in enumerate(importes['lineas'], 1):
        # Los importes del documento en pesos se redondean por línea, antes
        # de calcular el precio unitario y los conceptos totales.
        neto = (item['total_con_iva'] / Decimal('1.19')).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
        neto_lineas += neto
        precio = (neto / item['cantidad']).quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)
        if (precio * item['cantidad']).quantize(Decimal('1'), rounding=ROUND_HALF_UP) != neto:
            raise ImportePedidoError('No se puede representar el precio de una línea con cuatro decimales.')
        lineas.append({'NroLinea': numero, 'ProductoVentas': item['producto'],
                       'Cantidad': float(item['cantidad']), 'PrecioLista': float(precio),
                       'PrecioNeto': float(precio), 'TotalLinea': float(neto), 'FechaEntrega': fecha})
    # El servicio exige conceptos de acuerdo con la definición del documento.
    neto = neto_lineas.quantize(Decimal('1'), rounding=ROUND_HALF_UP)
    iva = importes['total'] - neto
    conceptos = [{'ConceptoCodigo': codigo, 'ConceptoValor': float(valor)} for codigo, valor in (
        (100, neto), (110, 0), (120, 0), (130, 0), (140, 0), (160, neto),
        (170, iva), (200, importes['total']), (180, 0))]
    return {'Encabezado': {
        'Referencias': {'ClienteReferencia': f'ANYMARKET-{pedido.anymarket_id}', 'Modulo': 'W16'},
        'Cliente': {'ClienteCodigo': settings.INET_PEDIDO_CLIENTE, 'ClienteSecuencia': 0},
        'Facturacion': {'DocumentoOrigen': 2, 'DocumentoaGenerar': int(settings.INET_PEDIDO_DOCUMENTO),
                        'DocumentoNro': '0', 'Estado': 0, 'Moneda': 1, 'MonedaParidad': 1,
                        'CondicionVenta': settings.INET_PEDIDO_CONDICION, 'Equipo': 1,
                        'BodegaSalida': settings.INET_PEDIDO_BODEGA, 'Vendedor': settings.INET_PEDIDO_VENDEDOR,
                        'VendedorSec': 0, 'Sucursal': int(settings.INET_PEDIDO_SUCURSAL),
                        'ListaPrecio': int(settings.INET_PEDIDO_LISTA), 'ListaPrecioMoneda': 1,
                        'FechaAtencion': fecha},
        'Pedido': {'PedidoClasificacion': 1, 'PedidoSector': 0, 'PedidoReservaProducto': 0,
                   'PedidoTipoCalculoTC': 1},
    }, 'Detalle': {'LineasDetalle': lineas}, 'Totales': {'ConceptosTotales': conceptos}}


def _guardar_resultado(pedido_id: int, estado: str, detalle: str = '', numero: str = '',
                       tipo_documento: str = '') -> None:
    with transaction.atomic():
        pedido = Pedido.objects.select_for_update().get(pk=pedido_id)
        pedido.inet_estado, pedido.inet_error, pedido.inet_numero = estado, detalle[:500], numero[:64]
        pedido.inet_tipo_documento = tipo_documento[:64]
        pedido.save(update_fields=['inet_estado', 'inet_error', 'inet_numero', 'inet_tipo_documento'])
        IntentoInet.objects.create(pedido=pedido, resultado=estado, detalle=detalle[:500])


def crear_pedido(uuid_pedido: UUID) -> None:
    with transaction.atomic():
        pedido = Pedido.objects.select_for_update().get(uuid=uuid_pedido)
        if pedido.inet_estado not in ('pendiente', 'error'):
            raise ValueError('El pedido ya fue enviado o requiere revisión antes de otro intento.')
        if pedido.estado != 'PAID_WAITING_SHIP':
            raise ValueError('Solo se pueden crear pedidos pagados pendientes de despacho.')
        try:
            documento = preparar_documento(pedido)
        except (ImportePedidoError, ValueError, TypeError) as exc:
            mensaje = str(exc) if isinstance(exc, ImportePedidoError) else 'Configuración comercial inválida.'
            pedido.inet_estado, pedido.inet_error = 'error', mensaje
            pedido.save(update_fields=['inet_estado', 'inet_error'])
            IntentoInet.objects.create(pedido=pedido, resultado='error', detalle=mensaje)
            return
        pedido.inet_estado, pedido.inet_error = 'enviando', ''
        pedido.save(update_fields=['inet_estado', 'inet_error'])
        pedido_id = pedido.pk
    try:
        respuesta = insertar_documento(documento)
    except AutenticacionComercialError as exc:
        _guardar_resultado(pedido_id, 'error', str(exc))
        return
    except ServicioInformatError:
        logger.warning('Resultado incierto al enviar un pedido a I-NET.')
        _guardar_resultado(pedido_id, 'revision', 'No se recibió una respuesta confirmada. Verifica la referencia en I-NET antes de volver a enviar.')
        return
    resultado = respuesta.get('RespuestaProceso')
    if isinstance(resultado, dict) and resultado.get('Tipo') == 1:
        errores = resultado.get('Errores')
        mensajes = [str(e.get('ErrorDescripcion', 'Error de I-NET')) for e in errores
                    if isinstance(e, dict)] if isinstance(errores, list) else []
        texto = '; '.join(mensajes) or 'I-NET rechazó el documento.'
        texto = re.sub(r'\b[0-9a-fA-F]{32,}\b', '[dato reservado]', texto)
        _guardar_resultado(pedido_id, 'error', texto)
        return
    datos = resultado.get('Datos') if isinstance(resultado, dict) and resultado.get('Tipo') == 0 else None
    numero = next((str(d.get('DATO')) for d in datos if isinstance(d, dict)
                   and d.get('NOMBRE') == 'DOCUMENTO_NUMERO' and d.get('DATO') is not None), '') if isinstance(datos, list) else ''
    if not numero:
        _guardar_resultado(pedido_id, 'revision', 'I-NET no devolvió un número de documento válido; verifica la referencia.')
        return
    tipo_documento = next((str(d.get('DATO')) for d in datos if isinstance(d, dict)
                           and d.get('NOMBRE') == 'DOCUMENTO_CODIGO' and d.get('DATO') is not None), '')
    _guardar_resultado(pedido_id, 'creado', numero=numero, tipo_documento=tipo_documento)
