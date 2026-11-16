from decimal import Decimal

from django.db import connections


def lista_existe(codigo: int) -> bool:
    with connections['sqlserver'].cursor() as cursor:
        cursor.execute('SELECT 1 FROM dbo.LISTPREC WHERE LisCod = %s', [codigo])
        return cursor.fetchone() is not None


def consultar_precio(codigo_lista: int, codigo_producto: str) -> dict[str, str | int] | None:
    # I-NET guarda códigos del lector en PVEBAR.BarBarCod; PRODVENT.BarCodBar
    # puede estar vacío incluso cuando el producto tiene un código en PVEBAR.
    with connections['sqlserver'].cursor() as cursor:
        cursor.execute('''
            SELECT TOP (1) RTRIM(v.BarCod), RTRIM(v.BarDscLar),
                   p.LisPreNet, RTRIM(l.LisNom), l.MonCod
            FROM dbo.LISTPRE1 AS p
            INNER JOIN dbo.LISTPREC AS l ON l.LisCod = p.LisCod
            INNER JOIN dbo.PRODVENT AS v ON v.BarCod = p.BarCod
            WHERE p.LisCod = %s AND (v.BarCod = %s OR v.BarCodBar = %s
                OR EXISTS (SELECT 1 FROM dbo.PVEBAR AS b
                           WHERE b.BarCod = v.BarCod AND b.BarBarCod = %s))
            ORDER BY CASE WHEN v.BarCod = %s THEN 0 ELSE 1 END, v.BarCod
        ''', [codigo_lista, codigo_producto, codigo_producto, codigo_producto, codigo_producto])
        fila = cursor.fetchone()
    if fila is None or not isinstance(fila[2], Decimal):
        return None
    return {
        'codigo': fila[0].strip(),
        'descripcion': (fila[1] or '').strip(),
        'precio': format(fila[2], 'f'),
        'lista': codigo_lista,
        'nombre_lista': (fila[3] or '').strip(),
        'moneda': fila[4],
    }
