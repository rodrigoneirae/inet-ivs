"""Interpretación de la solicitud de documento en pedidos AnyMarket."""

from typing import Any


def tipo_documento_solicitado(datos: dict[str, Any]) -> str | None:
    """Devuelve boleta o factura únicamente si los indicadores son inequívocos."""
    metadata = datos.get('metadata')
    if not isinstance(metadata, dict):
        return None
    tipos: list[str] = []
    for clave in ('invoiceRequired', 'invoice_required'):
        if clave not in metadata:
            continue
        valor = metadata[clave]
        if isinstance(valor, bool):
            tipos.append('factura' if valor else 'boleta')
        elif isinstance(valor, str) and valor.strip().lower() in ('true', 'false', 'factura', 'boleta'):
            tipos.append({'true': 'factura', 'false': 'boleta',
                          'factura': 'factura', 'boleta': 'boleta'}[valor.strip().lower()])
        else:
            return None
    return tipos[0] if tipos and len(set(tipos)) == 1 else None
