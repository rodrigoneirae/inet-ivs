"""Reglas de dominio para asignar y reconfigurar turnos de conteo.

El turno (:class:`~modulo.inventario.models.Asignacion`) es la configuración que
el supervisor define en la web y que el capturador recibe: inventario, bodega,
zona y tipo de conteo. Estas reglas no deben relajarse.
"""

from django.db import IntegrityError, transaction
from django.db.models import QuerySet

from modulo.inventario.models import Asignacion, Inventario, Zona


class ErrorTurno(Exception):
    """Solicitud de turno rechazada por las reglas del inventario."""

    def __init__(self, mensaje: str, estado: int = 409) -> None:
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.estado = estado


def _conflictos_de_tipo(turnos: list[Asignacion], tipo: str, usuario_id: int) -> str | None:
    """Motivo del conflicto de tipos dentro de una misma zona, o None si es legal."""
    if not turnos:
        return None
    etiqueta = Asignacion.Tipo(tipo).label
    if tipo == Asignacion.Tipo.UNICO:
        return 'El conteo único no puede compartir zona con otro turno.'
    for turno in turnos:
        if turno.tipo == Asignacion.Tipo.UNICO:
            return 'La zona ya tiene un conteo único: no admite un segundo turno.'
        if turno.tipo == tipo:
            contrario = Asignacion.Tipo.B.label if tipo == Asignacion.Tipo.A else Asignacion.Tipo.A.label
            return f'Ya existe un turno «{Asignacion.Tipo(turno.tipo).label}» en esta zona. Asigna «{contrario}» para la contraprova.'
        if turno.usuario_id == usuario_id:
            return 'El capturador ya tiene un turno en esta zona.'
    return None


def _crear_zona(inventario: Inventario, codigo_zona: str) -> Zona:
    """Devuelve la zona de la bodega del inventario, creándola si no existe."""
    zona, _ = Zona.objects.get_or_create(bodega=inventario.bodega, codigo=codigo_zona,
                                          defaults={'nombre': codigo_zona})
    if not zona.activa:
        raise ErrorTurno('Zona desactivada.')
    return zona


def _turnos_del_inventario(inventario: Inventario) -> list[Asignacion]:
    return list(Asignacion.objects.filter(inventario=inventario).select_related('zona'))


def asignar_turno(inventario: Inventario, usuario: object, tipo: str, codigo_zona: str) -> Asignacion:
    """Asigna un turno a un capturador respetando el alcance de zonas y tipos.

    ``codigo_zona`` vacío crea un turno global (histórico); los capturadores
    exigen siempre zona porque el análisis compara dentro de la misma zona.
    """
    existentes = _turnos_del_inventario(inventario)
    if codigo_zona:
        otras = [e for e in existentes if e.zona_id is None or e.zona.codigo != codigo_zona]
        if otras:
            zona_del_inventario = next((e.zona.codigo for e in existentes if e.zona_id), None)
            detalle = (f'Este inventario ya tiene turnos en la zona {zona_del_inventario}. '
                       'Los turnos A/B deben compartir zona: usa esa zona o reconfigura el turno existente.'
                       if zona_del_inventario else
                       'Este inventario ya tiene turnos sin zona: reasigna ese turno antes de agregar otro.')
            raise ErrorTurno(detalle)
        mismo_ambito = [e for e in existentes if e.zona_id and e.zona.codigo == codigo_zona]
    else:
        if any(e.zona_id or e.ubicacion_id for e in existentes):
            raise ErrorTurno('Este inventario ya tiene turnos con zona: los capturadores necesitan una zona de conteo.')
        mismo_ambito = existentes
    conflicto = _conflictos_de_tipo(mismo_ambito, tipo, usuario.pk)
    if conflicto:
        raise ErrorTurno(conflicto)
    zona = _crear_zona(inventario, codigo_zona) if codigo_zona else None
    try:
        return Asignacion.objects.create(inventario=inventario, usuario=usuario, zona=zona, tipo=tipo)
    except IntegrityError as error:
        raise ErrorTurno('El turno ya está asignado.') from error


@transaction.atomic
def actualizar_turno(turno: Asignacion, codigo_zona: str, tipo: str | None) -> tuple[Asignacion, int]:
    """Reconfigura la zona y el tipo de un turno ya asignado.

    Los turnos A/B de un inventario comparten zona, así que mover la zona arrastra
    al turno homólogo de esa misma zona: de lo contrario el inventario quedaría
    con conteos de zonas distintas y el análisis no podría compararlos.
    """
    inventario = turno.inventario
    if inventario.estado != Inventario.Estado.ABIERTO:
        raise ErrorTurno('Inventario cerrado.')
    if turno.finalizada_en is not None:
        raise ErrorTurno('El turno ya está finalizado.')
    destino_codigo = (codigo_zona or '').strip()
    if not destino_codigo:
        raise ErrorTurno('Indica la zona de conteo.', 400)
    origen = turno.zona
    if origen is not None and origen.codigo == destino_codigo:
        movibles = [turno]
    elif origen is not None:
        movibles = list(Asignacion.objects.filter(inventario=inventario, zona=origen))
    else:
        movibles = [turno]
    if any(t.conteos.exists() for t in movibles):
        raise ErrorTurno('El turno ya tiene conteos; no se puede cambiar su configuración.')
    otros = [e for e in _turnos_del_inventario(inventario) if e.pk not in {t.pk for t in movibles}]
    if any(e.zona_id is None or e.zona.codigo != destino_codigo for e in otros):
        raise ErrorTurno('Los turnos del inventario deben compartir la misma zona.')
    en_destino = [e for e in otros if e.zona_id and e.zona.codigo == destino_codigo]
    tipo_destino = tipo or turno.tipo
    conflicto = _conflictos_de_tipo(en_destino, tipo_destino, turno.usuario_id)
    if conflicto:
        raise ErrorTurno(conflicto)
    try:
        destino = _crear_zona(inventario, destino_codigo)
        for otro in movibles:
            if otro.pk == turno.pk:
                continue
            otro.zona = destino
            otro.save(update_fields=['zona'])
        turno.zona = destino
        if turno.tipo != tipo_destino:
            turno.tipo = tipo_destino
        turno.save(update_fields=['zona', 'tipo'])
    except IntegrityError as error:
        raise ErrorTurno('El turno ya está asignado.') from error
    return turno, len(movibles)


def turnos_de_capturador(usuario_id: int) -> QuerySet[Asignacion]:
    """Turnos de un capturador, del inventario más reciente al más antiguo."""
    return Asignacion.objects.filter(usuario_id=usuario_id).select_related(
        'inventario', 'inventario__bodega', 'zona',
    ).order_by('-inventario__creado_en', '-pk')
