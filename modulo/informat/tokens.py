"""Token compartido y cifrado para el servicio de productos Informat."""
import base64
import hashlib
import logging
from collections.abc import Callable
from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from redis import Redis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)


class TokenStoreError(Exception):
    pass


@lru_cache(maxsize=1)
def _redis() -> Redis:
    return Redis.from_url(settings.INFORMAT_REDIS_URL, socket_connect_timeout=5, socket_timeout=5)


def _cipher() -> Fernet:
    key = hashlib.sha256(('informat-token-v1:' + settings.SECRET_KEY).encode()).digest()
    return Fernet(base64.urlsafe_b64encode(key))


def _key() -> str:
    # A scope change must not reuse a token issued for another configuration.
    context = '\0'.join((settings.URLTOKEN, settings.EMPRUT, settings.CONID,
                         settings.APLID, settings.WSPRODUCTOSVENTAS))
    return 'informat:token:productos:' + hashlib.sha256(context.encode()).hexdigest()


def _read(client: Redis, key: str) -> str | None:
    value = client.get(key)
    if value is None:
        return None
    try:
        return _cipher().decrypt(value).decode('utf-8')
    except (InvalidToken, UnicodeDecodeError):
        logger.warning('No se pudo descifrar el token compartido de Informat')
        raise TokenStoreError('No se pudo leer el token de Informat.') from None


def obtener_token(renovar: Callable[[], str], rechazado: str | None = None) -> str:
    """Serializa la renovación y evita reemplazar un token actualizado por otro proceso."""
    try:
        client = _redis()
        key = _key()
        with client.lock(key + ':lock', timeout=settings.INFORMAT_TIMEOUT + 30,
                         blocking_timeout=settings.INFORMAT_TIMEOUT + 5):
            actual = _read(client, key)
            if actual and actual != rechazado:
                return actual
            fijo = settings.INFORMAT_TOKEN_PRODUCTOS
            fijo_hash = hashlib.sha256(fijo.encode()).hexdigest() if fijo else ''
            if rechazado and rechazado == fijo:
                client.setex(key + ':rechazado', settings.INFORMAT_TOKEN_TTL, fijo_hash)
            if rechazado is None and fijo and client.get(key + ':rechazado') != fijo_hash.encode():
                return fijo
            if actual and actual == rechazado:
                client.delete(key)
            token = renovar()
            client.setex(key, settings.INFORMAT_TOKEN_TTL, _cipher().encrypt(token.encode()))
            return token
    except RedisError as exc:
        logger.warning('No está disponible el almacenamiento del token de Informat (%s)', type(exc).__name__)
        raise TokenStoreError('No está disponible el almacenamiento del token de Informat.') from exc


def guardar_token_manual(token: str, segundos: int) -> None:
    try:
        client = _redis()
        key = _key()
        with client.lock(key + ':lock', timeout=settings.INFORMAT_TIMEOUT + 30,
                         blocking_timeout=settings.INFORMAT_TIMEOUT + 5):
            client.setex(key, segundos, _cipher().encrypt(token.encode()))
    except RedisError as exc:
        logger.warning('No se pudo guardar el token de Informat (%s)', type(exc).__name__)
        raise TokenStoreError('No está disponible el almacenamiento del token de Informat.') from exc
