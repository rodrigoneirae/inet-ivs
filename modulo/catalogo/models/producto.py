import uuid

from django.db import models


class Producto(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    sku = models.CharField(max_length=30, unique=True)
    descripcion_corta = models.CharField(max_length=25, blank=True)
    descripcion = models.CharField(max_length=60, blank=True)
    codigo_existencia = models.CharField(max_length=30, blank=True)
    codigo_barra = models.CharField(max_length=20, blank=True)
    estado = models.SmallIntegerField(null=True, blank=True)
    sincronizado_en = models.DateTimeField()
    detalle_ws = models.JSONField(default=dict, blank=True)
    detalle_ws_actualizado_en = models.DateTimeField(null=True, blank=True)
    detalle_ws_intento_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['sku']
        permissions = [('ver_catalogo', 'Puede consultar el catálogo web')]

    def __str__(self) -> str:
        return f'{self.sku} - {self.descripcion_corta}'
