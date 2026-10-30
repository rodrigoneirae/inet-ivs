"""Resolución de códigos comerciales configurados para AnyMarket."""

from ..models import ReglaDocumentoInet


def buscar_regla(tipo: str, canal: str) -> ReglaDocumentoInet | None:
    """Prioriza el canal; usa la regla general solo si no existe una activa."""
    if tipo not in ReglaDocumentoInet.Tipo.values:
        return None
    canal = canal.strip()
    reglas = ReglaDocumentoInet.objects.filter(tipo=tipo, activa=True)
    if canal:
        especifica = reglas.filter(canal__iexact=canal).first()
        if especifica is not None:
            return especifica
    return reglas.filter(canal='').first()
