"""Traducción explícita del contrato histórico al documento comercial I-NET."""

import math
from datetime import date
from decimal import Decimal
from typing import Any

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from ..models import DetPedidoApi, EncPedidoApi


def _seccion(objeto: models.Model, campos: str) -> dict[str, Any]:
    resultado: dict[str, Any] = {}
    for par in campos.split():
        destino, origen = par.split(':')
        valor = getattr(objeto, origen)
        if valor is None:
            campo = objeto._meta.get_field(origen)
            if campo.has_default():
                valor = campo.get_default()
            elif isinstance(campo, (models.IntegerField, models.FloatField)):
                valor = 0
            else:
                valor = None if isinstance(campo, models.DateField) else ''
        resultado[destino] = valor.isoformat() if isinstance(valor, date) else valor
    return resultado


def preparar_documento(pedido: EncPedidoApi, detalles: list[DetPedidoApi]) -> dict[str, Any]:
    permitidos = settings.PEDIDOS_INET_DOCUMENTOS_PERMITIDOS
    if str(pedido.documento_a_generar) not in permitidos:
        raise ValidationError('Tipo de documento no habilitado para la cola I-NET.')
    if not pedido.cliente_codigo or not pedido.cliente_codigo.strip():
        raise ValidationError('Falta el código del cliente.')
    if not detalles or len(detalles) > 1000:
        raise ValidationError('El pedido debe contener entre 1 y 1000 líneas completas.')
    for objeto in [pedido, *detalles]:
        for campo in objeto._meta.fields:
            valor = getattr(objeto, campo.name)
            if isinstance(valor, float) and not math.isfinite(valor):
                raise ValidationError('El documento contiene un importe no finito.')
            if isinstance(campo, models.CharField) and valor and len(valor) > campo.max_length:
                raise ValidationError('El documento contiene un texto fuera de rango.')
    numeros: set[int] = set()
    for linea in detalles:
        if (linea.nro_linea < 1 or linea.nro_linea in numeros or not linea.producto_ventas
                or not linea.producto_ventas.strip() or not linea.cantidad or linea.cantidad <= 0
                or linea.precio_neto is None or linea.precio_neto < 0
                or linea.total_linea is None or linea.total_linea < 0):
            raise ValidationError('El detalle contiene cantidades, precios, productos o números de línea inválidos.')
        numeros.add(linea.nro_linea)
    # El productor conserva sus reglas de IVA/descuento, pero sus totales deben cuadrar.
    suma = sum((Decimal(str(linea.total_linea)) for linea in detalles), Decimal('0'))
    subtotal = Decimal(str(pedido.concepto_codigo_100 or 0))
    neto = Decimal(str(pedido.concepto_codigo_160 or 0))
    iva = Decimal(str(pedido.concepto_codigo_170 or 0))
    total = Decimal(str(pedido.concepto_codigo_200 or 0))
    if min(subtotal, neto, iva, total) < 0 or abs(suma - subtotal) > 1 or abs(neto + iva - total) > 1:
        raise ValidationError('Los totales no concilian con el detalle neto y el IVA.')

    referencias = _seccion(pedido, '''
        ClienteReferencia:cliente_referencia Modulo:modulo Glosa:glosa ObservacionUno:observacion_uno
        ObservacionDos:observacion_dos NroOrdenCompra:nro_orden_compra NroOrdenTrabajo:nro_orden_trabajo
        TipoTransaccionVenta:tipo_transaccion_venta TipoTransaccionCompra:tipo_transaccion_compra
    ''')
    referencias['ClienteReferencia'] = pedido.cliente_referencia or f'COLA-{pedido.uuid}'
    referencias['Referencias_extension'] = []
    cliente = _seccion(pedido, '''
        ClienteCodigo:cliente_codigo ClienteSecuencia:cliente_secuencia ClienteNombre:cliente_nombre
        ClienteDireccion:cliente_direccion ClienteComuna:cliente_comuna ClienteCiudad:cliente_ciudad
        ClienteRegion:cliente_region ClienteTelefono:cliente_telefono ClienteEmail:cliente_email
        ClienteGiro:cliente_giro ClienteExtranjero:cliente_extranjero
    ''')
    cliente['ClienteContribuyente'] = {
        'ClienteEnviaXML': 0, 'ClienteEnviaPDF': 0, 'ClienteEmailIntercambio': '',
        'ClienteReceptorNombre': '', 'ClienteReceptorCodInt': '', 'ClienteReceptorEmail': '',
    }
    cliente['Cliente_Extension'] = []
    facturacion = _seccion(pedido, '''
        DocumentoOrigen:documento_origen DocumentoaGenerar:documento_a_generar DocumentoNro:documento_nro
        DocumentoNroHasta:documento_nro_hasta DoctoReferenciaCodigo:docto_referencia_codigo
        DoctoReferenciaNro:docto_referencia_nro FechaEmision:fecha_emision Estado:estado Moneda:moneda
        MonedaParidad:moneda_paridad CondicionVenta:condicion_venta Equipo:equipo BodegaSalida:bodega_salida
        BodegaEntrada:bodega_entrada Vendedor:vendedor VendedorSec:vendedor_sec Vendedor2:vendedor2
        Vendedor2Sec:vendedor2_sec Sucursal:sucursal ListaPrecio:lista_precio ListaPrecioMoneda:lista_precio_moneda
        FechaAtencion:fecha_atencion Pasaporte:pasaporte Facturador:facturador
    ''')
    facturacion['Facturacion_Extension'] = []
    descuentos = _seccion(pedido, '''
        DYRDesctoUnoCodigo:dyr_descto_uno_codigo DYRDesctoUnoPorcentaje:dyr_descto_uno_porcentaje
        DYRDesctoUnoMonto:dyr_descto_uno_monto DYRDesctoDosCodigo:dyr_descto_dos_codigo
        DYRDesctoDosPorcentaje:dyr_descto_dos_porcentaje DYRDesctoDosMonto:dyr_descto_dos_monto
        DYRDesctoTresCodigo:dyr_descto_tres_codigo DYRDesctoTresPorcentaje:dyr_descto_tres_porcentaje
        DYRDesctoTresMonto:dyr_descto_tres_monto DYRDesctoCuatroCodigo:dyr_descto_cuatro_codigo
        DYRDesctoCuatroPorcentaje:dyr_descto_cuatro_porcentaje DYRDesctoCuatroMonto:dyr_descto_cuatro_monto
        DYRRecgoCodigo:dyr_recgo_codigo DYRRecgoPorcentaje:dyr_recgo_porcentaje DYRRecgoMonto:dyr_recgo_monto
    ''')
    encabezado = {
        'Referencias': referencias, 'Cliente': cliente, 'Facturacion': facturacion,
        'DescuentosyRecargos': descuentos,
        'ClienteAdicional': _seccion(pedido, '''
            ClienteAdicionalCodigo:cliente_adicional_codigo ClienteAdicionalSecuencia:cliente_adicional_secuencia
        '''),
        'Pedido': _seccion(pedido, '''
            PedidoClasificacion:pedido_clasificacion PedidoSector:pedido_sector
            PedidoObservacionUno:pedido_observacion_uno PedidoGlosa:pedido_glosa
            PedidoReservaProducto:pedido_reserva_producto PedidoReservaFechaVencto:pedido_reserva_fecha_vencto
            PedidoTipoCalculoTC:pedido_tipo_calculo_tc
        '''),
        'Despacho': _seccion(pedido, '''
            DespachoVia:despacho_via DespachoDireccion:despacho_direccion DespachoComuna:despacho_comuna
            DespachoCiudad:despacho_ciudad DespachoSector:despacho_sector DespachoTransportista:despacho_transportista
            DespachoChofer:despacho_chofer DespachoPatente:despacho_patente
            DespachoTarifaTransporte:despacho_tarifa_transporte
        '''),
    }
    lineas: list[dict[str, Any]] = []
    for linea in detalles:
        datos = _seccion(linea, '''
            NroLinea:nro_linea ProductoVentas:producto_ventas ProductoCliente:producto_cliente Cantidad:cantidad
            PrecioLista:precio_lista PrecioBruto:precio_bruto PrecioNeto:precio_neto Iva:iva
            DescUno_Cod:desc_uno_cod DescUno_Porc:desc_uno_porc DescUno_Monto:desc_uno_monto
            DescDos_Cod:desc_dos_cod DescDos_Porc:desc_dos_porc DescDos_Monto:desc_dos_monto
            DescTre_Cod:desc_tre_cod DescTre_Porc:desc_tre_porc DescTre_Monto:desc_tre_monto
            DescCua_Cod:desc_cua_cod DescCua_Porc:desc_cua_porc DescCua_Monto:desc_cua_monto
            Recargo_Cod:recargo_cod Recargo_Porc:recargo_porc Recargo_Monto:recargo_monto
            ImpUno_Codigo:imp_uno_codigo ImpUno_Monto:imp_uno_monto ImpUno_Porc:imp_uno_porc
            ImpDos_Codigo:imp_dos_codigo ImpDos_Monto:imp_dos_monto ImpDos_Porc:imp_dos_porc
            FechaEntrega:fecha_entrega TotalLinea:total_linea
        ''')
        datos['Item_extension'] = []
        lineas.append(datos)
    codigos = [100, 110, 120, 130, 140, 160, 170, 200]
    if pedido.documento_a_generar != 759:
        codigos.append(180)
    conceptos = [{'ConceptoCodigo': codigo, 'ConceptoValor': getattr(pedido, f'concepto_codigo_{codigo}') or 0}
                 for codigo in codigos]
    return {'Encabezado': encabezado, 'Detalle': {'LineasDetalle': lineas}, 'Totales': {'ConceptosTotales': conceptos}}
