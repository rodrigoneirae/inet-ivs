import re

from django.conf import settings
from django.db import DatabaseError

from modulo.informat.models import BodegaInet


class BodegasNoDisponibles(Exception):
    """No se pudo consultar el maestro externo."""


def listar_bodegas(*, pagina: int = 1, tamano: int = 100, busqueda: str = '') -> tuple[list[dict[str, object]], bool]:
    if 'sqlserver' not in settings.DATABASES:
        raise BodegasNoDisponibles
    inicio = (pagina - 1) * tamano
    consulta = BodegaInet.objects.using('sqlserver').order_by('codigo')
    if busqueda:
        consulta = consulta.filter(nombre__icontains=busqueda)
    try:
        filas = list(consulta.values('codigo', 'nombre', 'estado_stock', 'sucursal_codigo',
                                     'usa_ubicaciones')[inicio:inicio + tamano + 1])
    except DatabaseError as exc:
        raise BodegasNoDisponibles from exc
    return ([{
        'codigo': str(fila['codigo']),
        'nombre': (fila['nombre'] or '').strip(),
        'estado_stock': (fila['estado_stock'] or '').strip(),
        'sucursal_codigo': fila['sucursal_codigo'],
        'usa_ubicaciones': fila['usa_ubicaciones'],
    } for fila in filas[:tamano]], len(filas) > tamano)


def buscar_bodega(codigo: str) -> dict[str, str] | None:
    """Valida el código recibido de la web antes de asociarlo a un inventario local."""
    if not re.fullmatch(r'\d{1,10}', codigo) or int(codigo) > 2147483647:
        return None
    if 'sqlserver' not in settings.DATABASES:
        raise BodegasNoDisponibles
    try:
        registro = BodegaInet.objects.using('sqlserver').filter(codigo=int(codigo)).values('codigo', 'nombre').first()
    except DatabaseError as exc:
        raise BodegasNoDisponibles from exc
    if registro is None:
        return None
    return {'codigo': str(registro['codigo']), 'nombre': (registro['nombre'] or '').strip()}
