from django.db import models


class Sincronizacion(models.Model):
    clave = models.CharField(max_length=32, primary_key=True)
    actualizado_hasta = models.DateTimeField(null=True, blank=True)
    carga_inicial_hasta = models.DateTimeField(null=True, blank=True)
    carga_inicial_inicio = models.DateTimeField(null=True, blank=True)
    ultimo_inicio = models.DateTimeField(null=True, blank=True)
    ultimo_exito = models.DateTimeField(null=True, blank=True)
    ultimo_error_en = models.DateTimeField(null=True, blank=True)
    ultimo_error = models.CharField(max_length=200, blank=True, default='')
