import hashlib
import secrets
import uuid

from django.db import models


class AplicacionBodegas(models.Model):
    """Credencial revocable exclusivamente para lectura del maestro de bodegas."""

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    nombre = models.CharField(max_length=100)
    token_hash = models.CharField(max_length=64, unique=True, editable=False)
    activa = models.BooleanField(default=True)
    creada_en = models.DateTimeField(auto_now_add=True)

    @classmethod
    def crear_con_token(cls, nombre: str) -> tuple['AplicacionBodegas', str]:
        token = secrets.token_urlsafe(32)
        aplicacion = cls.objects.create(nombre=nombre, token_hash=hashlib.sha256(token.encode('ascii')).hexdigest())
        return aplicacion, token
