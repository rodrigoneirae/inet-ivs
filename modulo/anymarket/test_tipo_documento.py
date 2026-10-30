from django.test import SimpleTestCase

from .tipo_documento import tipo_documento_solicitado


class TipoDocumentoTests(SimpleTestCase):
    def test_valores_de_anymarket(self) -> None:
        for clave, valor, esperado in (
            ('invoiceRequired', 'factura', 'factura'),
            ('invoiceRequired', 'boleta', 'boleta'),
            ('invoice_required', True, 'factura'),
            ('invoice_required', False, 'boleta'),
            ('invoice_required', 'true', 'factura'),
            ('invoice_required', 'false', 'boleta'),
        ):
            with self.subTest(clave=clave, valor=valor):
                self.assertEqual(tipo_documento_solicitado({'metadata': {clave: valor}}), esperado)

    def test_faltante_desconocido_y_contradiccion_no_se_adivinan(self) -> None:
        for metadata in ({}, {'needInvoiceXML': True}, {'invoiceRequired': 'desconocido'},
                         {'invoiceRequired': 'factura', 'invoice_required': False}):
            with self.subTest(metadata=metadata):
                self.assertIsNone(tipo_documento_solicitado({'metadata': metadata}))
