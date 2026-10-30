import uuid

from django.db import models


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
