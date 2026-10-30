import logging
import secrets

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import AbstractBaseUser
from django.db import DatabaseError, IntegrityError
from django.utils.crypto import constant_time_compare

from modulo.acceso.services import obtener_registros, registros_validos, sincronizar_registro

logger = logging.getLogger(__name__)


class IVSBackend(ModelBackend):
    def authenticate(self, request: object, username: str | None = None,
                     password: str | None = None, **kwargs: object) -> AbstractBaseUser | None:
        if not username or not password:
            return None
        try:
            registros = registros_validos(obtener_registros(username))
            registro = next((r for r in registros if r.nombre == username), None)
            if registro is None:
                constant_time_compare(password, secrets.token_urlsafe(32))
                return None
            if not constant_time_compare(registro.clave, password):
                return None
            usuario = sincronizar_registro(registro)
            return usuario if usuario and self.user_can_authenticate(usuario) else None
        except (DatabaseError, IntegrityError, KeyError):
            logger.exception('No se pudo validar el acceso con IVS_SAT')
            return None
