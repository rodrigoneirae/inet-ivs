from django.conf import settings
from django.db import models


class UsuarioOrigen(models.Model):
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    identificador_origen = models.BigIntegerField(unique=True)
