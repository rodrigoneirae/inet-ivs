import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


class Bodega(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    codigo = models.CharField(max_length=30, unique=True)
    nombre = models.CharField(max_length=120)
    activa = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f'{self.codigo} - {self.nombre}'


class Zona(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    bodega = models.ForeignKey(Bodega, on_delete=models.PROTECT, related_name='zonas')
    codigo = models.CharField(max_length=30)
    nombre = models.CharField(max_length=120)
    activa = models.BooleanField(default=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['bodega', 'codigo'], name='inv_zona_codigo')]

    def __str__(self) -> str:
        return f'{self.bodega.codigo} / {self.codigo}'


class Ubicacion(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    zona = models.ForeignKey(Zona, on_delete=models.PROTECT, related_name='ubicaciones')
    codigo = models.CharField(max_length=40)
    activa = models.BooleanField(default=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['zona', 'codigo'], name='inv_ubicacion_codigo')]

    def __str__(self) -> str:
        return f'{self.zona} / {self.codigo}'


class Inventario(models.Model):
    class Estado(models.TextChoices):
        ABIERTO = 'abierto', 'Abierto'
        CERRADO = 'cerrado', 'Cerrado'

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    nombre = models.CharField(max_length=120)
    bodega = models.ForeignKey(Bodega, on_delete=models.PROTECT)
    estado = models.CharField(max_length=10, choices=Estado.choices, default=Estado.ABIERTO)
    creado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='+')
    creado_en = models.DateTimeField(auto_now_add=True)
    cerrado_en = models.DateTimeField(null=True, blank=True)
    cerrado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, related_name='+')

    class Meta:
        ordering = ['-creado_en']
        permissions = [
            ('supervisar_inventario', 'Puede configurar y cerrar inventarios'),
            ('contar_inventario', 'Puede registrar conteos asignados'),
        ]


class Asignacion(models.Model):
    class Tipo(models.TextChoices):
        A = 'a', 'Parte A'
        B = 'b', 'Contraparte B'
        UNICO = 'unico', 'Conteo único'

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    inventario = models.ForeignKey(Inventario, on_delete=models.PROTECT, related_name='asignaciones')
    ubicacion = models.ForeignKey(Ubicacion, on_delete=models.PROTECT, null=True, blank=True)
    zona = models.ForeignKey(Zona, on_delete=models.PROTECT, null=True, blank=True)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    tipo = models.CharField(max_length=5, choices=Tipo.choices)
    finalizada_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['inventario', 'ubicacion', 'tipo'], name='inv_turno_unico'),
            models.UniqueConstraint(fields=['inventario', 'ubicacion', 'usuario'], name='inv_usuario_ubicacion_unico'),
            models.UniqueConstraint(fields=['inventario', 'zona', 'tipo'], condition=Q(zona__isnull=False), name='inv_turno_zona_unico'),
            models.UniqueConstraint(fields=['inventario', 'zona', 'usuario'], condition=Q(zona__isnull=False), name='inv_usuario_zona_unico'),
            models.UniqueConstraint(fields=['inventario', 'tipo'], condition=Q(zona__isnull=True, ubicacion__isnull=True), name='inv_turno_global_unico'),
            models.UniqueConstraint(fields=['inventario', 'usuario'], condition=Q(zona__isnull=True, ubicacion__isnull=True), name='inv_usuario_global_unico'),
        ]

    def clean(self) -> None:
        if self.inventario_id and self.zona_id and self.zona.bodega_id != self.inventario.bodega_id:
            raise ValidationError('La zona no corresponde a la bodega del inventario.')
        if self.inventario_id and self.ubicacion_id and self.ubicacion.zona.bodega_id != self.inventario.bodega_id:
            raise ValidationError('La ubicación no corresponde a la bodega del inventario.')


class Conteo(models.Model):
    # UUID supplied by the device: an immutable, idempotent event. Several scans sum per product.
    public_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    asignacion = models.ForeignKey(Asignacion, on_delete=models.PROTECT, related_name='conteos')
    ubicacion = models.ForeignKey(Ubicacion, on_delete=models.PROTECT, null=True, blank=True)
    producto_codigo = models.CharField(max_length=30)
    cantidad = models.DecimalField(max_digits=15, decimal_places=3)
    registrado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.CheckConstraint(condition=Q(cantidad__gt=0), name='inv_cantidad_positiva')]
        indexes = [models.Index(fields=['asignacion', 'producto_codigo'])]


class ProductoSnapshot(models.Model):
    codigo = models.CharField(max_length=30, primary_key=True)
    descripcion = models.CharField(max_length=120)
    codigo_barra = models.CharField(max_length=30, blank=True, db_index=True)
    embalaje = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    actualizado_en = models.DateTimeField(auto_now=True)


class ProductoBarra(models.Model):
    """Código de lector de un producto. I-NET puede tener varios por producto."""

    producto = models.ForeignKey(ProductoSnapshot, on_delete=models.CASCADE, related_name='barras')
    codigo_barra = models.CharField(max_length=30, db_index=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['producto', 'codigo_barra'],
                                               name='inv_barra_unica')]


class TokenMovil(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    nombre = models.CharField(max_length=80)
    token_hash = models.CharField(max_length=128, unique=True)
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True,
                                   related_name='capturador_inventario')
    vinculacion_hash = models.CharField(max_length=64, unique=True, null=True, blank=True)
    vinculacion_vence = models.DateTimeField(null=True, blank=True)
    vinculacion_asignacion = models.ForeignKey(Asignacion, on_delete=models.PROTECT, null=True, blank=True,
                                               related_name='+')
    vinculado_en = models.DateTimeField(null=True, blank=True)
    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)
