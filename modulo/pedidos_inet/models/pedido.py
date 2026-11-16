"""Contrato de intercambio compatible con las tablas de apps_satventas."""

import uuid

from django.contrib.postgres.functions import RandomUUID
from django.db import models


class EncPedidoApi(models.Model):
    class EstadoEnvioChoices(models.TextChoices):
        PENDIENTE = 'P', 'Pendiente'
        ENVIADO = 'E', 'Enviado'
        RETENIDO_STOCK = 'RS', 'Retenido stock'
        RETENIDO = 'R', 'Retenido'
        PROCESANDO = 'PR', 'Procesando'
        ERROR = 'ER', 'Error'
        REVISION = 'RV', 'Requiere revisión'

    uuid = models.UUIDField(default=uuid.uuid4, db_default=RandomUUID(), unique=True, editable=False)
    estado_envio = models.CharField(
        max_length=2, choices=EstadoEnvioChoices.choices, default='P', db_default='P', db_index=True,
    )
    documento_origen = models.IntegerField(default=2, blank=True, null=True)
    documento_a_generar = models.IntegerField(blank=True, null=True)
    documento_nro = models.CharField(max_length=50, default='0', blank=True, null=True)
    documento_nro_hasta = models.CharField(max_length=50, default='', blank=True, null=True)
    cliente_referencia = models.CharField(max_length=255, blank=True, null=True)
    docto_referencia_codigo = models.IntegerField(default=0, blank=True, null=True)
    docto_referencia_nro = models.CharField(max_length=50, default='', blank=True, null=True)
    fecha_emision = models.DateField(blank=True, null=True)
    estado = models.IntegerField(default=0, blank=True, null=True)
    moneda = models.IntegerField(default=1, blank=True, null=True)
    moneda_paridad = models.FloatField(default=1, blank=True, null=True)
    condicion_venta = models.CharField(max_length=50, blank=True, null=True)
    equipo = models.IntegerField(default=1, blank=True, null=True)
    bodega_salida = models.TextField(max_length=50, blank=True, null=True)
    bodega_entrada = models.IntegerField(default=0, blank=True, null=True)
    vendedor = models.CharField(max_length=50, blank=True, null=True)
    vendedor_sec = models.IntegerField(default=0, blank=True, null=True)
    vendedor2 = models.CharField(max_length=50, blank=True, null=True)
    vendedor2_sec = models.IntegerField(default=0, blank=True, null=True)
    sucursal = models.IntegerField(default=1, blank=True, null=True)
    lista_precio = models.IntegerField(default=0, blank=True, null=True)
    lista_precio_moneda = models.IntegerField(default=1, blank=True, null=True)
    fecha_atencion = models.DateField(blank=True, null=True)
    pasaporte = models.CharField(max_length=50, default='', blank=True, null=True)
    facturador = models.IntegerField(default=0, blank=True, null=True)
    modulo = models.CharField(max_length=10, default='W16', blank=True, null=True)
    glosa = models.TextField(blank=True, null=True)
    observacion_uno = models.TextField(default='', blank=True, null=True)
    observacion_dos = models.TextField(default='', blank=True, null=True)
    nro_orden_compra = models.CharField(max_length=100, default='', blank=True, null=True)
    nro_orden_trabajo = models.CharField(max_length=100, default='', blank=True, null=True)
    tipo_transaccion_venta = models.IntegerField(default=0, blank=True, null=True)
    tipo_transaccion_compra = models.IntegerField(default=0, blank=True, null=True)
    cliente_codigo = models.CharField(max_length=100, blank=True, null=True)
    cliente_secuencia = models.IntegerField(default=0, blank=True, null=True)
    cliente_nombre = models.CharField(max_length=255, blank=True, null=True)
    cliente_direccion = models.CharField(max_length=255, blank=True, null=True)
    cliente_comuna = models.CharField(max_length=100, blank=True, null=True)
    cliente_ciudad = models.CharField(max_length=100, blank=True, null=True)
    cliente_region = models.CharField(max_length=100, blank=True, null=True)
    cliente_telefono = models.CharField(max_length=20, default='', blank=True, null=True)
    cliente_email = models.EmailField(default='', blank=True, null=True)
    cliente_giro = models.CharField(max_length=100, blank=True, null=True)
    cliente_extranjero = models.IntegerField(default=0, blank=True, null=True)
    cliente_adicional_codigo = models.CharField(max_length=100, default='0', blank=True, null=True)
    cliente_adicional_secuencia = models.IntegerField(default=0, blank=True, null=True)
    dyr_descto_uno_codigo = models.IntegerField(default=0, blank=True, null=True)
    dyr_descto_uno_porcentaje = models.FloatField(default=0, blank=True, null=True)
    dyr_descto_uno_monto = models.FloatField(default=0, blank=True, null=True)
    dyr_descto_dos_codigo = models.IntegerField(default=0, blank=True, null=True)
    dyr_descto_dos_porcentaje = models.FloatField(default=0, blank=True, null=True)
    dyr_descto_dos_monto = models.FloatField(default=0, blank=True, null=True)
    dyr_descto_tres_codigo = models.IntegerField(default=0, blank=True, null=True)
    dyr_descto_tres_porcentaje = models.FloatField(default=0, blank=True, null=True)
    dyr_descto_tres_monto = models.FloatField(default=0, blank=True, null=True)
    dyr_descto_cuatro_codigo = models.IntegerField(default=0, blank=True, null=True)
    dyr_descto_cuatro_porcentaje = models.FloatField(default=0, blank=True, null=True)
    dyr_descto_cuatro_monto = models.FloatField(default=0, blank=True, null=True)
    dyr_recgo_codigo = models.IntegerField(default=0, blank=True, null=True)
    dyr_recgo_porcentaje = models.FloatField(default=0, blank=True, null=True)
    dyr_recgo_monto = models.FloatField(default=0, blank=True, null=True)
    pedido_clasificacion = models.IntegerField(default=1, blank=True, null=True)
    pedido_sector = models.IntegerField(default=0, blank=True, null=True)
    pedido_observacion_uno = models.CharField(max_length=255, default='', blank=True, null=True)
    pedido_glosa = models.CharField(max_length=255, default='', blank=True, null=True)
    pedido_reserva_producto = models.IntegerField(default=1, blank=True, null=True)
    pedido_reserva_fecha_vencto = models.DateField(blank=True, null=True)
    pedido_tipo_calculo_tc = models.IntegerField(default=1, blank=True, null=True)
    despacho_via = models.CharField(max_length=50, blank=True, null=True)
    despacho_direccion = models.CharField(max_length=255, blank=True, null=True)
    despacho_comuna = models.CharField(max_length=100, blank=True, null=True)
    despacho_ciudad = models.CharField(max_length=100, blank=True, null=True)
    despacho_sector = models.CharField(max_length=100, blank=True, null=True)
    despacho_transportista = models.CharField(max_length=50, default='0', blank=True, null=True)
    despacho_chofer = models.CharField(max_length=50, default='0', blank=True, null=True)
    despacho_patente = models.CharField(max_length=20, blank=True, null=True)
    despacho_tarifa_transporte = models.IntegerField(default=0, blank=True, null=True)
    concepto_codigo_100 = models.FloatField(default=0, blank=True, null=True)
    concepto_codigo_110 = models.FloatField(default=0, blank=True, null=True)
    concepto_codigo_120 = models.FloatField(default=0, blank=True, null=True)
    concepto_codigo_130 = models.FloatField(default=0, blank=True, null=True)
    concepto_codigo_140 = models.FloatField(default=0, blank=True, null=True)
    concepto_codigo_160 = models.FloatField(default=0, blank=True, null=True)
    concepto_codigo_170 = models.FloatField(default=0, blank=True, null=True)
    concepto_codigo_180 = models.FloatField(default=0, blank=True, null=True)
    concepto_codigo_200 = models.FloatField(default=0, blank=True, null=True)
    usuario = models.CharField(max_length=50, blank=True, null=True)
    api_documento_codigo = models.CharField(max_length=255, blank=True, null=True)
    api_documento_atencion = models.CharField(max_length=255, blank=True, null=True)
    api_documento_numero = models.CharField(max_length=255, blank=True, null=True)
    api_documento_estado = models.CharField(max_length=255, blank=True, null=True)
    api_documento_motivo = models.CharField(max_length=255, blank=True, null=True)
    api_documento_error = models.CharField(max_length=255, blank=True, null=True)
    # Se conservan las columnas antiguas, pero el worker no guarda PII/tokens en ellas.
    api_json = models.JSONField(blank=True, null=True)
    api_json_response = models.JSONField(blank=True, null=True)
    notificacion = models.BooleanField(default=False, blank=True, null=True)
    estado_notificacion = models.TextField(default='', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    solicitud_cifrada = models.TextField(default='', db_default='', editable=False)
    respuesta_cifrada = models.TextField(default='', db_default='', editable=False)
    procesando_desde = models.DateTimeField(null=True, blank=True, editable=False)

    class Meta:
        db_table = 'inet_encpedidoapi'
        verbose_name = 'pedido I-NET'
        verbose_name_plural = 'pedidos I-NET'
        ordering = ['id']

    def __str__(self) -> str:
        return f'{self.uuid} — {self.get_estado_envio_display()}'


class DetPedidoApi(models.Model):
    estado_envio = models.CharField(
        max_length=2, default='P', db_default='P', choices=EncPedidoApi.EstadoEnvioChoices.choices,
    )
    enc_pedido = models.ForeignKey(EncPedidoApi, related_name='detalles', on_delete=models.CASCADE)
    nro_linea = models.IntegerField()
    producto_ventas = models.CharField(max_length=50, blank=True, null=True)
    producto_cliente = models.CharField(max_length=50, blank=True, null=True)
    cantidad = models.IntegerField(blank=True, null=True)
    precio_lista = models.FloatField(blank=True, null=True)
    precio_bruto = models.FloatField(default=0, blank=True, null=True)
    precio_neto = models.FloatField(blank=True, null=True)
    iva = models.FloatField(blank=True, null=True)
    desc_uno_cod = models.IntegerField(default=0, blank=True, null=True)
    desc_uno_porc = models.FloatField(blank=True, null=True)
    desc_uno_monto = models.FloatField(blank=True, null=True)
    desc_dos_cod = models.IntegerField(default=0, blank=True, null=True)
    desc_dos_porc = models.FloatField(blank=True, null=True)
    desc_dos_monto = models.FloatField(blank=True, null=True)
    desc_tre_cod = models.IntegerField(default=0, blank=True, null=True)
    desc_tre_porc = models.FloatField(blank=True, null=True)
    desc_tre_monto = models.FloatField(blank=True, null=True)
    desc_cua_cod = models.IntegerField(default=0, blank=True, null=True)
    desc_cua_porc = models.FloatField(blank=True, null=True)
    desc_cua_monto = models.FloatField(blank=True, null=True)
    recargo_cod = models.IntegerField(default=0, blank=True, null=True)
    recargo_porc = models.FloatField(default=0, blank=True, null=True)
    recargo_monto = models.FloatField(default=0, blank=True, null=True)
    imp_uno_codigo = models.IntegerField(default=0, blank=True, null=True)
    imp_uno_monto = models.FloatField(default=0, blank=True, null=True)
    imp_uno_porc = models.FloatField(default=0, blank=True, null=True)
    imp_dos_codigo = models.IntegerField(default=0, blank=True, null=True)
    imp_dos_monto = models.FloatField(default=0, blank=True, null=True)
    imp_dos_porc = models.FloatField(default=0, blank=True, null=True)
    fecha_entrega = models.DateField(blank=True, null=True)
    total_linea = models.FloatField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    class Meta:
        db_table = 'inet_detpedidoapi'
        ordering = ['nro_linea', 'id']
        constraints = [models.UniqueConstraint(fields=['enc_pedido', 'nro_linea'], name='inet_det_linea_unica')]
