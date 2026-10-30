from decimal import Decimal

from django.test import SimpleTestCase

from .importes_inet import ImportePedidoError, calcular_importes


class ImportesInetTests(SimpleTestCase):
    def test_desglosa_total_con_iva_y_agrega_envio(self) -> None:
        resultado = calcular_importes({
            'items': [{'sku': {'partnerId': '00123'}, 'amount': 1, 'total': 11900}],
            'freight': 1190, 'total': 13090,
        })
        self.assertEqual(resultado['neto'], Decimal('11000'))
        self.assertEqual(resultado['iva'], Decimal('2090'))
        self.assertEqual(resultado['lineas'][0]['producto'], '00123')
        self.assertEqual(resultado['lineas'][1]['producto'], '60000')

    def test_rechaza_total_que_no_concilia(self) -> None:
        with self.assertRaises(ImportePedidoError):
            calcular_importes({'items': [{'sku': {'partnerId': '1'}, 'amount': 1, 'total': 119}],
                               'freight': 0, 'total': 120})

    def test_rechaza_producto_sin_codigo(self) -> None:
        with self.assertRaises(ImportePedidoError):
            calcular_importes({'items': [{'sku': {}, 'amount': 1, 'total': 119}],
                               'freight': 0, 'total': 119})
