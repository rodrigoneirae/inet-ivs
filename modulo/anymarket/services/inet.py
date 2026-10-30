"""Creación manual de pedidos AnyMarket en el servicio comercial I-NET."""

import re
from decimal import Decimal, ROUND_HALF_UP
from typing import Any
from uuid import UUID
from zoneinfo import ZoneInfo

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from modulo.informat.services.comercial import crear_documento, validar_cliente_documento
from modulo.informat.services.clientes import ConsultaClienteError

from .importes_inet import ImportePedidoError, calcular_importes
from .auditoria_inet import cifrar_mensaje
from ..models import IntentoInet, Pedido
from .reglas_documento import buscar_regla
from .tipo_documento import tipo_documento_solicitado

def preparar_venta(pedido: Pedido) -> dict[str, Any]:
    """Prepara un documento comercial bruto pendiente con su recaudación."""
    datos = pedido.datos
    tipo = tipo_documento_solicitado(datos)
    if not tipo:
        raise ImportePedidoError('No se puede determinar si la venta requiere boleta o factura.')
    canal = datos.get('marketPlace')
    regla = buscar_regla(tipo, canal if isinstance(canal, str) else '')
    if regla is None:
        raise ImportePedidoError('No hay una regla activa de documento para el tipo y canal de la venta.')
    importes = calcular_importes(datos)
    try:
        equipo = int(settings.INET_RECAUDACION_EQUIPO)
        cajero = int(settings.INET_RECAUDACION_CAJERO)
        forma_pago = int(settings.INET_RECAUDACION_FORMA_PAGO)
    except (TypeError, ValueError) as exc:
        raise ImportePedidoError('La configuración de recaudación debe contener códigos numéricos.') from exc
    if not (0 <= equipo <= 99999 and 0 <= cajero <= 999999999999 and 0 <= forma_pago <= 9999):
        raise ImportePedidoError('La configuración de recaudación contiene códigos fuera de rango.')
    fecha = timezone.localtime(timezone.now(), ZoneInfo(settings.ANYMARKET_TIME_ZONE)).date().isoformat()
    cliente: dict[str, Any] = {'ClienteCodigo': settings.INET_PEDIDO_CLIENTE, 'ClienteSecuencia': 0}
    if tipo == 'factura':
        metadata = datos.get('metadata') if isinstance(datos.get('metadata'), dict) else {}
        buyer = datos.get('buyer') if isinstance(datos.get('buyer'), dict) else {}
        direccion = datos.get('billingAddress') if isinstance(datos.get('billingAddress'), dict) else {}
        rut = metadata.get('buyerDNI') or buyer.get('document') or direccion.get('shipmentUserDocument')
        if not isinstance(rut, str):
            raise ImportePedidoError('La factura no tiene RUT del cliente.')
        rut = re.sub(r'[.\s-]', '', rut).upper()
        if not re.fullmatch(r'[0-9]{6,8}[0-9K]', rut):
            raise ImportePedidoError('El RUT del cliente de la factura no tiene un formato válido.')
        razon = metadata.get('razon') or buyer.get('name')
        giro = metadata.get('giro') or metadata.get('economicActivity') or buyer.get('economicActivity')
        campos = {'ClienteNombre': (razon, 100), 'ClienteGiro': (giro, 80),
                  'ClienteDireccion': (direccion.get('address') or direccion.get('street'), 70),
                  'ClienteComuna': (direccion.get('neighborhood') or direccion.get('city'), 15),
                  'ClienteCiudad': (direccion.get('city'), 40)}
        for nombre, (valor, limite) in campos.items():
            if not isinstance(valor, str) or not valor.strip() or len(valor.strip()) > limite:
                raise ImportePedidoError(f'La factura requiere {nombre} válido (máximo {limite} caracteres).')
            cliente[nombre] = valor.strip()
        cliente['ClienteCodigo'] = rut[:-1]
        email = buyer.get('email')
        if isinstance(email, str) and email and len(email) <= 40:
            cliente['ClienteEmail'] = email
    lineas: list[dict[str, Any]] = []
    neto_total = Decimal('0')
    for numero, item in enumerate(importes['lineas'], 1):
        bruto = item['total_con_iva']
        precio = (bruto / item['cantidad']).quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)
        if (precio * item['cantidad']).quantize(Decimal('1'), rounding=ROUND_HALF_UP) != bruto:
            raise ImportePedidoError('No se puede representar el precio bruto de una línea.')
        precio_neto = (precio / Decimal('1.19')).quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)
        neto_linea = (precio_neto * item['cantidad']).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        iva_linea = (bruto - neto_linea).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        # I-NET redondea el neto de cada línea a pesos para los conceptos
        # del documento, conservando centavos para el IVA de la línea.
        neto_total += neto_linea.quantize(Decimal('1'), rounding=ROUND_HALF_UP)
        lineas.append({'NroLinea': numero, 'ProductoVentas': item['producto'],
                       'Cantidad': float(item['cantidad']), 'PrecioLista': float(precio),
                       'PrecioBruto': float(precio), 'PrecioNeto': float(precio_neto),
                       'Iva': float(iva_linea), 'TotalLinea': float(bruto)})
    conceptos = [{'ConceptoCodigo': codigo, 'ConceptoValor': float(valor)} for codigo, valor in (
        (100, neto_total), (110, 0), (120, 0), (130, 0), (140, 0), (160, neto_total),
        (170, importes['total'] - neto_total), (200, importes['total']))]
    return {'Encabezado': {
        'Referencias': {'ClienteReferencia': f'ANYMARKET-{pedido.anymarket_id}', 'Modulo': 'W16'},
        'Cliente': cliente,
        'Facturacion': {'DocumentoOrigen': 0, 'DocumentoaGenerar': regla.codigo,
                        'DocumentoNro': 0, 'Estado': 0, 'FechaEmision': fecha, 'FechaAtencion': fecha,
                        'Moneda': 1, 'MonedaParidad': 1, 'CondicionVenta': settings.INET_PEDIDO_CONDICION,
                        'Equipo': equipo,
                        'BodegaSalida': settings.INET_PEDIDO_BODEGA, 'Vendedor': settings.INET_PEDIDO_VENDEDOR,
                        'VendedorSec': 0, 'Sucursal': int(settings.INET_PEDIDO_SUCURSAL),
                        'ListaPrecio': int(settings.INET_PEDIDO_LISTA), 'ListaPrecioMoneda': 1},
    }, 'Detalle': {'LineasDetalle': lineas}, 'Totales': {'ConceptosTotales': conceptos},
        'Recaudacion': {
            'Encabezado': {'RECajero': cajero, 'RECajeroSecuencia': 0,
                           'REClienteCodigo': cliente['ClienteCodigo'], 'REClienteSecuencia': 0,
                           'RETipoVuelto': 0, 'RETotalRecaudacion': format(importes['total'], '.2f'),
                           'RecaudacionEnc_extension': []},
            'Detalle': [{'RDCodigo': forma_pago, 'RDReferencia': '', 'RDMoneda': 1, 'RDMonedaTasa': 1,
                         'RDMonto': format(importes['total'], '.2f'), 'RecaudacionDet_extension': []}],
        }}


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
                       tipo_documento: str = '', intento_id: int | None = None,
                       respuesta: dict[str, Any] | None = None) -> None:
    with transaction.atomic():
        pedido = Pedido.objects.select_for_update().get(pk=pedido_id)
        pedido.inet_estado, pedido.inet_error, pedido.inet_numero = estado, detalle[:500], numero[:64]
        pedido.inet_tipo_documento = tipo_documento[:64]
        pedido.save(update_fields=['inet_estado', 'inet_error', 'inet_numero', 'inet_tipo_documento'])
        if intento_id is None:
            IntentoInet.objects.create(pedido=pedido, resultado=estado, detalle=detalle[:500])
        else:
            intento = IntentoInet.objects.select_for_update().get(pk=intento_id, pedido=pedido)
            intento.resultado, intento.detalle = estado, detalle[:500]
            intento.respuesta_cifrada = cifrar_mensaje(respuesta) if respuesta is not None else ''
            intento.save(update_fields=['resultado', 'detalle', 'respuesta_cifrada'])


def crear_pedido(uuid_pedido: UUID, *, venta: bool = False) -> None:
    with transaction.atomic():
        pedido = Pedido.objects.select_for_update().get(uuid=uuid_pedido)
        if pedido.inet_estado not in ('pendiente', 'error'):
            raise ValueError('El pedido ya fue enviado o requiere revisión antes de otro intento.')
        if pedido.estado != 'PAID_WAITING_SHIP':
            raise ValueError('Solo se pueden crear pedidos pagados pendientes de despacho.')
        if pedido.datos.get('fulfillment') is True:
            raise ValueError('Los pedidos fulfillment no generan documentos en I-NET.')
        try:
            documento = preparar_venta(pedido) if venta else preparar_documento(pedido)
            if venta:
                validar_cliente_documento(documento)
        except ConsultaClienteError as exc:
            mensaje = str(exc)
            pedido.inet_estado, pedido.inet_error = 'pendiente', mensaje
            pedido.save(update_fields=['inet_estado', 'inet_error'])
            IntentoInet.objects.create(pedido=pedido, resultado='pendiente', detalle=mensaje)
            return
        except (ImportePedidoError, ValueError, TypeError) as exc:
            mensaje = str(exc) if isinstance(exc, ImportePedidoError) else 'Configuración comercial inválida.'
            pedido.inet_estado, pedido.inet_error = 'error', mensaje
            pedido.save(update_fields=['inet_estado', 'inet_error'])
            IntentoInet.objects.create(pedido=pedido, resultado='error', detalle=mensaje)
            return
        pedido.inet_estado, pedido.inet_error = 'enviando', ''
        pedido.save(update_fields=['inet_estado', 'inet_error'])
        intento = IntentoInet.objects.create(
            pedido=pedido, resultado='enviando',
            solicitud_cifrada=cifrar_mensaje({'DocumentoComercial': documento}),
        )
        pedido_id = pedido.pk
        intento_id = intento.pk
    resultado = crear_documento(documento)
    _guardar_resultado(pedido_id, resultado.estado, resultado.detalle, numero=resultado.numero,
                       tipo_documento=resultado.tipo_documento, intento_id=intento_id, respuesta=resultado.respuesta)
