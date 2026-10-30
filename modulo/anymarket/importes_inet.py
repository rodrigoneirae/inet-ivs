"""Validación de importes de pedidos AnyMarket para documentos I-NET."""

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any


class ImportePedidoError(ValueError):
    """Los importes no pueden conciliarse sin intervención."""


def _importe(valor: Any) -> Decimal:
    if isinstance(valor, bool) or not isinstance(valor, (int, float, str, Decimal)):
        raise ImportePedidoError('Importe inválido.')
    try:
        numero = Decimal(str(valor))
    except InvalidOperation as exc:
        raise ImportePedidoError('Importe inválido.') from exc
    if not numero.is_finite() or numero < 0:
        raise ImportePedidoError('Importe inválido.')
    return numero


def calcular_importes(datos: dict[str, Any], tasa_iva: Decimal = Decimal('0.19')) -> dict[str, Any]:
    """Comprueba el total y desglosa IVA incluido sin enviar ningún documento."""
    if not tasa_iva.is_finite() or tasa_iva < 0:
        raise ImportePedidoError('Tasa de IVA inválida.')
    items = datos.get('items')
    if not isinstance(items, list) or not items:
        raise ImportePedidoError('El pedido no tiene líneas.')
    lineas = []
    for item in items:
        if not isinstance(item, dict) or not isinstance(item.get('sku'), dict):
            raise ImportePedidoError('Línea de pedido inválida.')
        codigo = item['sku'].get('partnerId')
        if not isinstance(codigo, str) or not codigo.strip() or len(codigo) > 30:
            raise ImportePedidoError('La línea no tiene un código de producto válido.')
        cantidad = _importe(item.get('amount'))
        if cantidad <= 0:
            raise ImportePedidoError('Cantidad inválida.')
        total = _importe(item.get('total'))
        lineas.append({'producto': codigo.strip(), 'cantidad': cantidad, 'total_con_iva': total})
    envio = _importe(datos.get('freight'))
    if envio:
        lineas.append({'producto': '60000', 'cantidad': Decimal('1'), 'total_con_iva': envio})
    total = _importe(datos.get('total'))
    if sum((linea['total_con_iva'] for linea in lineas), Decimal('0')) != total:
        raise ImportePedidoError('Las líneas y el envío no coinciden con el total del pedido.')
    neto = (total / (1 + tasa_iva)).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
    return {'lineas': lineas, 'neto': neto, 'iva': total - neto, 'total': total}
