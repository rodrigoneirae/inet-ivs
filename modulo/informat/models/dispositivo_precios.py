import hashlib
import secrets
import uuid

from django.db import models


class DispositivoPrecios(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    nombre = models.CharField(max_length=100)
    lista_codigo = models.PositiveSmallIntegerField()
    token_hash = models.CharField(max_length=64, unique=True, editable=False)
    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    @classmethod
    def crear_con_token(cls, nombre: str, lista_codigo: int) -> tuple['DispositivoPrecios', str]:
        token = secrets.token_urlsafe(32)
        dispositivo = cls.objects.create(
            nombre=nombre, lista_codigo=lista_codigo,
            token_hash=hashlib.sha256(token.encode('ascii')).hexdigest(),
        )
        return dispositivo, token

    class Meta:
        verbose_name = 'dispositivo de consulta de precios'
        verbose_name_plural = 'dispositivos de consulta de precios'
