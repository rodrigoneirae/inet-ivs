import uuid

from django.db import models

from .pedido import Pedido


class IntentoInet(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='intentos_inet')
    fecha = models.DateTimeField(auto_now_add=True)
    resultado = models.CharField(max_length=20)
    detalle = models.CharField(max_length=500, blank=True)
    solicitud_cifrada = models.TextField(blank=True, default='')
    respuesta_cifrada = models.TextField(blank=True, default='')
