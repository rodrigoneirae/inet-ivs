"""Cifrado de los mensajes comerciales conservados para auditoría."""

import base64
import hashlib
import json
from typing import Any

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings


class AuditoriaInetError(Exception):
    pass


def _cifrado() -> Fernet:
    clave = hashlib.sha256(('anymarket-auditoria-v1:' + settings.SECRET_KEY).encode()).digest()
    return Fernet(base64.urlsafe_b64encode(clave))


def _sin_secretos(valor: Any) -> Any:
    if isinstance(valor, dict):
        if isinstance(valor.get('NOMBRE'), str) and valor['NOMBRE'].casefold() in ('token', 'password', 'authorization'):
            return {k: ('[reservado]' if k in ('DATO', 'VALOR') else _sin_secretos(v))
                    for k, v in valor.items() if isinstance(k, str)}
        return {k: _sin_secretos(v) for k, v in valor.items()
                if isinstance(k, str) and k.casefold() not in ('token', 'password', 'authorization')}
    if isinstance(valor, list):
        return [_sin_secretos(v) for v in valor]
    return valor


def cifrar_mensaje(valor: dict[str, Any]) -> str:
    contenido = json.dumps(_sin_secretos(valor), ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    return _cifrado().encrypt(contenido).decode('ascii')


def descifrar_mensaje(valor: str) -> dict[str, Any] | None:
    if not valor:
        return None
    try:
        resultado = json.loads(_cifrado().decrypt(valor.encode('ascii')))
        if not isinstance(resultado, dict):
            raise ValueError('Mensaje inválido')
        return resultado
    except (InvalidToken, ValueError, UnicodeError) as exc:
        raise AuditoriaInetError('No fue posible leer el mensaje guardado.') from exc
