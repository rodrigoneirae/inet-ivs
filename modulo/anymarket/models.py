import uuid

from django.db import models


class Pedido(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    anymarket_id = models.BigIntegerField(unique=True)
    creado_en = models.DateTimeField()
    estado = models.CharField(max_length=64)
    datos = models.JSONField()
    actualizado_en = models.DateTimeField(auto_now=True)


class Sincronizacion(models.Model):
    clave = models.CharField(max_length=32, primary_key=True)
    actualizado_hasta = models.DateTimeField(null=True, blank=True)
    carga_inicial_hasta = models.DateTimeField(null=True, blank=True)
    carga_inicial_inicio = models.DateTimeField(null=True, blank=True)
    ultimo_inicio = models.DateTimeField(null=True, blank=True)
    ultimo_exito = models.DateTimeField(null=True, blank=True)
    ultimo_error_en = models.DateTimeField(null=True, blank=True)
    ultimo_error = models.CharField(max_length=200, blank=True, default='')
