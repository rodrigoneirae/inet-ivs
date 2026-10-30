from datetime import datetime, timezone
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase

from modulo.informat.services import ServicioInformatTimeout

from .inet import crear_pedido, preparar_documento
from .models import Pedido


class CrearPedidoInetTests(TestCase):
    def setUp(self) -> None:
        self.pedido = Pedido.objects.create(anymarket_id=123, creado_en=datetime(2026, 10, 27, tzinfo=timezone.utc),
            estado='PAID_WAITING_SHIP', datos={'items': [{'sku': {'partnerId': '001'}, 'amount': 1, 'total': 1190}],
                                               'freight': 119, 'total': 1309})

    @patch('modulo.anymarket.inet.insertar_documento')
    def test_creacion_registra_numero_y_no_repite(self, enviar: object) -> None:
        enviar.return_value = {'RespuestaProceso': {'Tipo': 0, 'Datos': [
            {'NOMBRE': 'DOCUMENTO_NUMERO', 'DATO': '12345'},
            {'NOMBRE': 'DOCUMENTO_CODIGO', 'DATO': '771'},
        ]}}
        crear_pedido(self.pedido.uuid)
        self.pedido.refresh_from_db()
        self.assertEqual((self.pedido.inet_estado, self.pedido.inet_numero), ('creado', '12345'))
        self.assertEqual(self.pedido.inet_tipo_documento, '771')
        documento = enviar.call_args.args[0]
        self.assertEqual(documento['Encabezado']['Referencias']['ClienteReferencia'], 'ANYMARKET-123')
        self.assertEqual(documento['Detalle']['LineasDetalle'][1]['ProductoVentas'], '60000')
        with self.assertRaises(ValueError):
            crear_pedido(self.pedido.uuid)
        self.assertEqual(enviar.call_count, 1)

    @patch('modulo.anymarket.inet.insertar_documento')
    def test_respuesta_sin_tipo_conserva_numero_sin_inventar_tipo(self, enviar: object) -> None:
        enviar.return_value = {'RespuestaProceso': {'Tipo': 0, 'Datos': [{'NOMBRE': 'DOCUMENTO_NUMERO', 'DATO': '42'}]}}
        crear_pedido(self.pedido.uuid)
        self.pedido.refresh_from_db()
        self.assertEqual((self.pedido.inet_estado, self.pedido.inet_numero, self.pedido.inet_tipo_documento),
                         ('creado', '42', ''))

    def test_linea_con_descuento_concilia_en_pesos(self) -> None:
        self.pedido.datos = {'items': [{'sku': {'partnerId': '32001210'}, 'amount': 1,
                                      'unit': 59990, 'discount': 5000, 'total': 54990}],
                             'freight': 0, 'total': 54990}
        documento = preparar_documento(self.pedido)
        linea = documento['Detalle']['LineasDetalle'][0]
        self.assertEqual(linea['PrecioLista'], 46210)
        self.assertEqual(linea['TotalLinea'], 46210)
        self.assertEqual({c['ConceptoCodigo']: c['ConceptoValor'] for c in documento['Totales']['ConceptosTotales']}[170], 8780)

    def test_linea_con_multiples_unidades_concilia_al_redondear(self) -> None:
        self.pedido.datos = {'items': [{'sku': {'partnerId': '001'}, 'amount': 3, 'total': 1190}],
                             'freight': 0, 'total': 1190}
        linea = preparar_documento(self.pedido)['Detalle']['LineasDetalle'][0]
        self.assertEqual(linea['PrecioLista'], 333.3333)
        self.assertEqual(linea['TotalLinea'], 1000)

    @patch('modulo.anymarket.inet.insertar_documento')
    def test_error_registra_historial_y_permite_reintento(self, enviar: object) -> None:
        enviar.return_value = {'RespuestaProceso': {'Tipo': 1, 'Errores': [{'ErrorDescripcion': 'Producto inexistente'}]}}
        crear_pedido(self.pedido.uuid)
        self.pedido.refresh_from_db()
        self.assertEqual(self.pedido.inet_estado, 'error')
        self.assertEqual(self.pedido.intentos_inet.get().detalle, 'Producto inexistente')
        crear_pedido(self.pedido.uuid)
        self.assertEqual(enviar.call_count, 2)

    @patch('modulo.anymarket.inet.insertar_documento', side_effect=ServicioInformatTimeout('timeout'))
    def test_timeout_bloquea_reintento(self, enviar: object) -> None:
        crear_pedido(self.pedido.uuid)
        self.pedido.refresh_from_db()
        self.assertEqual(self.pedido.inet_estado, 'revision')
        with self.assertRaises(ValueError):
            crear_pedido(self.pedido.uuid)

    def test_api_exige_sesion_y_permiso(self) -> None:
        url = f'/api/v1/pedidos/{self.pedido.uuid}/inet/'
        self.assertEqual(self.client.post(url).status_code, 401)
        usuario = get_user_model().objects.create_user(username='operador')
        self.client.force_login(usuario)
        self.assertEqual(self.client.post(url).status_code, 403)
        usuario.user_permissions.add(Permission.objects.get(codename='change_pedido', content_type__app_label='anymarket'))
        self.client.force_login(get_user_model().objects.get(pk=usuario.pk))
        with patch('modulo.anymarket.inet.insertar_documento', return_value={'RespuestaProceso': {'Tipo': 1, 'Errores': [{'ErrorDescripcion': 'Error de prueba'}]}}):
            self.assertEqual(self.client.post(url).status_code, 409)
        historial = self.client.get(f'{url}errores/').json()
        self.assertEqual(historial['intentos'][0]['detalle'], 'Error de prueba')
