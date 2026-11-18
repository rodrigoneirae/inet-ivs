"""Importación del catálogo de I-NET a la copia local del inventario.

El catálogo se copia desde `PRODVENT` (SQL Server) a `ProductoSnapshot` para que
los capturadores cuenten sin conexión. Solo se lee de I-NET: el stock nunca se
modifica. La app móvil orquesta las páginas y después descarga la copia local.

I-NET guarda los códigos de lector en varias tablas: `PRODVENT.BarCodBar` suele
estar vacío, mientras que `PRDBAR.PrdCodBar` y `PVEBAR.BarBarCod` concentran los
EAN reales. Por eso cada página se complementa con esos códigos y con el
embalaje (`PRODUCTO.PrdUniCaj`).
"""

from decimal import Decimal

from django.conf import settings
from django.db import DatabaseError, connections, transaction

from modulo.informat.models import ProductoVentaInet
from modulo.inventario.models import ProductoBarra, ProductoSnapshot


class CatalogoNoDisponible(Exception):
    """I-NET no está configurado o no respondió a la consulta."""


def _marcadores(codigos: list[str]) -> str:
    return ', '.join(['%s'] * len(codigos))


def _codigos_barra(codigos: list[str]) -> dict[str, list[str]]:
    """Códigos de barra de I-NET agrupados por código de producto."""
    if not codigos:
        return {}
    lista = _marcadores(codigos)
    resultado: dict[str, list[str]] = {}
    consultas = (
        f'''SELECT RTRIM(v.BarCod), RTRIM(v.BarCodBar) FROM dbo.PRODVENT AS v
            WHERE v.BarCod IN ({lista}) AND LTRIM(RTRIM(v.BarCodBar)) <> \'\'''',
        f'''SELECT RTRIM(p.PrdCod), RTRIM(p.PrdCodBar) FROM dbo.PRDBAR AS p
            WHERE p.PrdCod IN ({lista}) AND LTRIM(RTRIM(p.PrdCodBar)) <> \'\'''',
        f'''SELECT RTRIM(b.BarCod), RTRIM(b.BarBarCod) FROM dbo.PVEBAR AS b
            WHERE b.BarCod IN ({lista}) AND LTRIM(RTRIM(b.BarBarCod)) <> \'\'''',
    )
    with connections['sqlserver'].cursor() as cursor:
        for sql in consultas:
            cursor.execute(sql, codigos)
            for codigo, barra in cursor.fetchall():
                if codigo and barra:
                    propias = resultado.setdefault(codigo.strip(), [])
                    if barra.strip() not in propias:
                        propias.append(barra.strip())
    return resultado


def _embalajes(codigos: list[str]) -> dict[str, Decimal]:
    """Unidades por caja (`PRODUCTO.PrdUniCaj`) por código de producto."""
    if not codigos:
        return {}
    with connections['sqlserver'].cursor() as cursor:
        cursor.execute(
            f'SELECT RTRIM(p.PrdCod), p.PrdUniCaj FROM dbo.PRODUCTO AS p '
            f'WHERE p.PrdCod IN ({_marcadores(codigos)})',
            codigos,
        )
        return {
            codigo.strip(): valor
            for codigo, valor in cursor.fetchall()
            if codigo and valor is not None
        }


def importar_pagina(pagina: int, tamano: int) -> tuple[int, bool]:
    """Copia una página del catálogo y devuelve ``(importados, hay_mas)``."""
    if 'sqlserver' not in settings.DATABASES:
        raise CatalogoNoDisponible('I-NET no está configurado.')
    inicio = (pagina - 1) * tamano
    try:
        filas = list(ProductoVentaInet.objects.using('sqlserver').order_by('codigo').values(
            'codigo', 'descripcion', 'codigo_barra',
        )[inicio:inicio + tamano + 1])
        pagina_filas = filas[:tamano]
        codigos = [fila['codigo'].strip() for fila in pagina_filas]
        barras = _codigos_barra(codigos)
        embalajes = _embalajes(codigos)
    except DatabaseError as error:
        raise CatalogoNoDisponible('No se pudo consultar I-NET.') from error
    with transaction.atomic():
        for fila, codigo in zip(pagina_filas, codigos):
            propias = barras.get(codigo, [])
            ProductoSnapshot.objects.update_or_create(codigo=codigo, defaults={
                'descripcion': (fila['descripcion'] or '').strip(),
                'codigo_barra': propias[0] if propias else '',
                'embalaje': embalajes.get(codigo),
            })
        ProductoBarra.objects.filter(producto_id__in=codigos).delete()
        ProductoBarra.objects.bulk_create(
            [ProductoBarra(producto_id=codigo, codigo_barra=barra)
             for codigo in codigos for barra in barras.get(codigo, [])],
            ignore_conflicts=True,
        )
        # Las importaciones anteriores guardaban los códigos con relleno a 30
        # caracteres; al normalizarlos quedarían filas duplicadas.
        rellenos = [f'{codigo:<30}' for codigo in codigos]
        ProductoSnapshot.objects.filter(codigo__in=rellenos).exclude(codigo__in=codigos).delete()
    return min(len(filas), tamano), len(filas) > tamano
