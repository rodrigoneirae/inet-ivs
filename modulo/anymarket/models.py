import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.functions import Lower


class Pedido(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    anymarket_id = models.BigIntegerField(unique=True)
    creado_en = models.DateTimeField()
    estado = models.CharField(max_length=64)
    datos = models.JSONField()
    actualizado_en = models.DateTimeField(auto_now=True)
    inet_estado = models.CharField(max_length=20, default='pendiente')
    inet_numero = models.CharField(max_length=64, blank=True, default='')
    inet_tipo_documento = models.CharField(max_length=64, blank=True, default='')
    inet_error = models.CharField(max_length=500, blank=True, default='')


class IntentoInet(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='intentos_inet')
    fecha = models.DateTimeField(auto_now_add=True)
    resultado = models.CharField(max_length=20)
    detalle = models.CharField(max_length=500, blank=True)
    solicitud_cifrada = models.TextField(blank=True, default='')
    respuesta_cifrada = models.TextField(blank=True, default='')


class ReglaDocumentoInet(models.Model):
    class Tipo(models.TextChoices):
        BOLETA = 'boleta', 'Boleta'
        FACTURA = 'factura', 'Factura'
        PEDIDO = 'pedido', 'Pedido'

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tipo = models.CharField(max_length=10, choices=Tipo.choices)
    canal = models.CharField(max_length=100, blank=True, default='',
                             help_text='Código original del canal AnyMarket; vacío para la regla general.')
    codigo = models.PositiveSmallIntegerField(help_text='Código del documento en el maestro de I-NET (1 a 999).')
    descripcion = models.CharField(max_length=120)
    activa = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'regla de documento I-NET'
        verbose_name_plural = 'reglas de documentos I-NET'
        constraints = [
            models.UniqueConstraint('tipo', Lower('canal'), name='anymarket_documento_tipo_canal_unico'),
            models.CheckConstraint(condition=models.Q(codigo__gte=1, codigo__lte=999),
                                   name='anymarket_documento_codigo_valido'),
            models.CheckConstraint(condition=models.Q(tipo__in=['boleta', 'factura', 'pedido']),
                                   name='anymarket_documento_tipo_valido'),
        ]

    def clean(self) -> None:
        super().clean()
        self.canal = self.canal.strip()
        self.descripcion = self.descripcion.strip()
        if not self.descripcion:
            raise ValidationError({'descripcion': 'Ingresa una descripción.'})

    def __str__(self) -> str:
        return f'{self.get_tipo_display()} · {self.canal or "General"} · {self.codigo}'


class Sincronizacion(models.Model):
    clave = models.CharField(max_length=32, primary_key=True)
    actualizado_hasta = models.DateTimeField(null=True, blank=True)
    carga_inicial_hasta = models.DateTimeField(null=True, blank=True)
    carga_inicial_inicio = models.DateTimeField(null=True, blank=True)
    ultimo_inicio = models.DateTimeField(null=True, blank=True)
    ultimo_exito = models.DateTimeField(null=True, blank=True)
    ultimo_error_en = models.DateTimeField(null=True, blank=True)
    ultimo_error = models.CharField(max_length=200, blank=True, default='')
