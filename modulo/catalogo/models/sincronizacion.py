from django.db import models


class EstadoSincronizacion(models.Model):
    fuente = models.CharField(max_length=30, unique=True)
    ultimo_inicio = models.DateTimeField(null=True, blank=True)
    ultimo_exito = models.DateTimeField(null=True, blank=True)
    ultimo_error = models.DateTimeField(null=True, blank=True)
    mensaje_error = models.CharField(max_length=250, blank=True)

    def __str__(self) -> str:
        return self.fuente
