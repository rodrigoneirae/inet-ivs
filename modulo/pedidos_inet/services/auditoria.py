"""Auditoría cifrada; los tokens SSI nunca se incluyen en el documento guardado."""

import base64
import hashlib
import json
from typing import Any

from cryptography.fernet import Fernet
from django.conf import settings


def _sin_secretos(valor: Any) -> Any:
    if isinstance(valor, dict):
        if str(valor.get('NOMBRE', '')).casefold() in ('token', 'password', 'authorization'):
            return {'NOMBRE': '[reservado]'}
        return {k: _sin_secretos(v) for k, v in valor.items()
                if k.casefold() not in ('token', 'password', 'authorization', 'seguridad')}
    if isinstance(valor, list):
        return [_sin_secretos(v) for v in valor]
    return valor


def cifrar(valor: dict[str, Any]) -> str:
    clave = hashlib.sha256(('pedidos-inet-auditoria-v1:' + settings.SECRET_KEY).encode()).digest()
    contenido = json.dumps(_sin_secretos(valor), ensure_ascii=False, allow_nan=False).encode()
    return Fernet(base64.urlsafe_b64encode(clave)).encrypt(contenido).decode('ascii')
