"""Consulta de existencia en el maestro de clientes I-NET."""

import logging

from django.conf import settings
from django.db import DatabaseError, connections

logger = logging.getLogger(__name__)


class ConsultaClienteError(Exception):
    """No se pudo comprobar el cliente en I-NET."""


def existe_cliente(codigo: str, secuencia: int) -> bool:
    if not codigo.isascii() or not codigo.isdigit() or len(codigo) > 12 or secuencia < 0:
        raise ConsultaClienteError('El código del cliente no es válido.')
    if 'sqlserver' not in settings.DATABASES:
        raise ConsultaClienteError('La conexión al maestro de clientes I-NET no está configurada.')
    try:
        with connections['sqlserver'].cursor() as cursor:
            cursor.execute('SELECT TOP 1 1 FROM dbo.CLIENTD WHERE CliTip = %s AND CliCod = %s AND CliSec = %s',
                           [1, int(codigo), secuencia])
            return cursor.fetchone() is not None
    except DatabaseError as exc:
        logger.warning('No se pudo consultar el maestro de clientes I-NET (%s).', type(exc).__name__)
        raise ConsultaClienteError('No fue posible consultar el maestro de clientes I-NET.') from exc
