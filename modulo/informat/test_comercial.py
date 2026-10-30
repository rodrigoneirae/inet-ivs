from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from .comercial import crear_documento, insertar_documento
from .services import ServicioInformatError, ServicioInformatTimeout


@override_settings(URLTOKEN='https://ssi.example', EMPRUT='empresa', CONID='conexion',
                   APLID='aplicacion', WSCOMERCIAL='comercial',
                   URL_WSCOMERCIAL='https://inet.example/comercial')
class DocumentoComercialTests(SimpleTestCase):
    @patch('modulo.informat.comercial.insertar_documento')
    def test_servicio_global_conserva_respuesta_y_numero(self, enviar: object) -> None:
        respuesta = {'RespuestaProceso': {'Tipo': 0, 'Datos': [
            {'NOMBRE': 'DOCUMENTO_NUMERO', 'DATO': '42'},
            {'NOMBRE': 'DOCUMENTO_CODIGO', 'DATO': '777'}]}}
        enviar.return_value = respuesta
        resultado = crear_documento({'Encabezado': {}})
        self.assertEqual((resultado.estado, resultado.tipo_documento, resultado.numero), ('creado', '777', '42'))
        self.assertEqual(resultado.respuesta, respuesta)

    @patch('modulo.informat.comercial.insertar_documento')
    def test_servicio_global_clasifica_errores_e_incertidumbre(self, enviar: object) -> None:
        enviar.return_value = {'RespuestaProceso': {'Tipo': 1, 'Errores': [{'ErrorDescripcion': 'Cliente inválido'}]}}
        self.assertEqual((crear_documento({}).estado, crear_documento({}).detalle), ('error', 'Cliente inválido'))
        enviar.side_effect = ServicioInformatTimeout('timeout')
        self.assertEqual(crear_documento({}).estado, 'revision')
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
