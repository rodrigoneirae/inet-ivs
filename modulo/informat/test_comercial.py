from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from .comercial import insertar_documento
from .services import ServicioInformatError, ServicioInformatTimeout


@override_settings(URLTOKEN='https://ssi.example', EMPRUT='empresa', CONID='conexion',
                   APLID='aplicacion', WSCOMERCIAL='comercial',
                   URL_WSCOMERCIAL='https://inet.example/comercial')
class DocumentoComercialTests(SimpleTestCase):
    @patch('modulo.informat.comercial._post_json')
    def test_usa_funcionalidad_comercial_y_no_modifica_documento(self, post: object) -> None:
        post.side_effect = [
            {'SalidaAut': {'CodigoError': 200, 'Token': 'token-prueba'}},
            {'RespuestaProceso': {'Tipo': 0}},
        ]
        documento = {'Encabezado': {'Referencias': {'ClienteReferencia': 'ANY-1'}}}
        respuesta = insertar_documento(documento)
        self.assertEqual(respuesta['RespuestaProceso']['Tipo'], 0)
        self.assertEqual(post.call_args_list[0].args[1]['EntradaAut']['FncId'], 'comercial')
        self.assertEqual(post.call_args_list[1].args[1]['DocumentoComercial']['Seguridad']['Token'], 'token-prueba')
        self.assertNotIn('Seguridad', documento)

    @patch('modulo.informat.comercial._post_json')
    def test_no_reintenta_escritura_incierta(self, post: object) -> None:
        post.side_effect = [
            {'SalidaAut': {'CodigoError': 200, 'Token': 'token-prueba'}},
            ServicioInformatTimeout('timeout'),
        ]
        with self.assertRaises(ServicioInformatTimeout):
            insertar_documento({})
        self.assertEqual(post.call_count, 2)

    @patch('modulo.informat.comercial._post_json')
    def test_autenticacion_rechazada_no_envia_documento(self, post: object) -> None:
        post.return_value = {'SalidaAut': {'CodigoError': 402}}
        with self.assertRaises(ServicioInformatError):
            insertar_documento({})
        self.assertEqual(post.call_count, 1)
