"""Importación del catálogo de I-NET a la copia local del inventario.

El catálogo se copia desde `PRODVENT` (SQL Server) a `ProductoSnapshot` para que
los capturadores cuenten sin conexión. Solo se lee de I-NET: el stock nunca se
modifica. La app móvil orquesta las páginas y después descarga la copia local.
"""

from django.conf import settings
from django.db import DatabaseError, transaction

from modulo.informat.models import ProductoVentaInet
from modulo.inventario.models import ProductoSnapshot


class CatalogoNoDisponible(Exception):
    """I-NET no está configurado o no respondió a la consulta."""


def importar_pagina(pagina: int, tamano: int) -> tuple[int, bool]:
    """Copia una página del catálogo y devuelve ``(importados, hay_mas)``."""
    if 'sqlserver' not in settings.DATABASES:
        raise CatalogoNoDisponible('I-NET no está configurado.')
    inicio = (pagina - 1) * tamano
    try:
        filas = list(ProductoVentaInet.objects.using('sqlserver').order_by('codigo').values(
            'codigo', 'descripcion', 'codigo_barra',
        )[inicio:inicio + tamano + 1])
    except DatabaseError as error:
        raise CatalogoNoDisponible('No se pudo consultar I-NET.') from error
    with transaction.atomic():
        for fila in filas[:tamano]:
            ProductoSnapshot.objects.update_or_create(codigo=fila['codigo'], defaults={
                'descripcion': fila['descripcion'] or '',
                'codigo_barra': fila['codigo_barra'] or '',
            })
    return min(len(filas), tamano), len(filas) > tamano
