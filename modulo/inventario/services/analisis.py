from collections import defaultdict
from decimal import Decimal

from django.db.models import Prefetch, QuerySet

from modulo.inventario.models import Asignacion, Conteo, Inventario


def analizar(inventario: Inventario) -> list[dict[str, object]]:
    """Compare totals by location and product, never across distinct locations."""
    asignaciones: QuerySet[Asignacion] = inventario.asignaciones.select_related(
        'ubicacion', 'ubicacion__zona', 'zona', 'usuario',
    ).prefetch_related(Prefetch('conteos', queryset=Conteo.objects.select_related('ubicacion__zona'))).order_by('ubicacion_id', 'tipo')
    por_zona: dict[tuple[str, int], dict[str, Asignacion]] = defaultdict(dict)
    for asignacion in asignaciones:
        clave = (('zona', asignacion.zona_id) if asignacion.zona_id else
                 ('ubicacion', asignacion.ubicacion_id) if asignacion.ubicacion_id else ('global', inventario.pk))
        por_zona[clave][asignacion.tipo] = asignacion
    resultados: list[dict[str, object]] = []
    for turnos in por_zona.values():
        primero = next(iter(turnos.values()))
        unico = turnos.get(Asignacion.Tipo.UNICO)
        a = turnos.get(Asignacion.Tipo.A)
        b = turnos.get(Asignacion.Tipo.B)
        totales: dict[tuple[int, int, str], dict[str, Decimal]] = defaultdict(dict)
        ubicaciones: dict[object, object] = {}
        for turno in turnos.values():
            for conteo in turno.conteos.all():
                ubicacion = conteo.ubicacion or turno.ubicacion
                ubicaciones[ubicacion.pk] = ubicacion
                clave = (ubicacion.zona_id, ubicacion.pk, conteo.producto_codigo)
                anterior = totales[clave].get(turno.tipo, Decimal('0'))
                totales[clave][turno.tipo] = anterior + conteo.cantidad
        for (_, ubicacion_id, producto), cantidades in sorted(totales.items()):
            ubicacion = ubicaciones[ubicacion_id]
            cantidad_a = cantidades.get(Asignacion.Tipo.A)
            cantidad_b = cantidades.get(Asignacion.Tipo.B)
            cantidad_unica = cantidades.get(Asignacion.Tipo.UNICO)
            if unico:
                estado = 'coincidente' if unico.finalizada_en else 'pendiente'
            elif not a or not b or not a.finalizada_en or not b.finalizada_en:
                estado = 'pendiente'
            elif cantidad_a is None or cantidad_b is None:
                estado = 'faltante'
            elif cantidad_a == cantidad_b:
                estado = 'coincidente'
            else:
                estado = 'diferencia'
            resultados.append({
                'ubicacion': str(ubicacion.public_id),
                'ubicacion_codigo': ubicacion.codigo,
                'zona': ubicacion.zona.codigo,
                'producto': producto,
                'a': str(cantidad_a) if cantidad_a is not None else None,
                'b': str(cantidad_b) if cantidad_b is not None else None,
                'unico': str(cantidad_unica) if cantidad_unica is not None else None,
                'estado': estado,
            })
    return resultados
