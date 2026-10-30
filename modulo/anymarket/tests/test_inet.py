from datetime import datetime, timezone
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase, override_settings

from modulo.informat.services import ServicioInformatTimeout
from modulo.informat.clientes import ConsultaClienteError

from ..inet import crear_pedido, preparar_documento, preparar_venta
from ..importes_inet import ImportePedidoError
from ..models import Pedido, ReglaDocumentoInet
from ..auditoria_inet import descifrar_mensaje


class CrearPedidoInetTests(TestCase):
    def setUp(self) -> None:
        patcher = patch('modulo.informat.comercial.existe_cliente', return_value=True)
        self.cliente_existe = patcher.start()
        self.addCleanup(patcher.stop)
        self.pedido = Pedido.objects.create(anymarket_id=123, creado_en=datetime(2026, 10, 27, tzinfo=timezone.utc),
            estado='PAID_WAITING_SHIP', datos={'items': [{'sku': {'partnerId': '001'}, 'amount': 1, 'total': 1190}],
                                               'freight': 119, 'total': 1309})

    @patch('modulo.informat.comercial.insertar_documento')
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

    @patch('modulo.informat.comercial.insertar_documento')
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

    @patch('modulo.informat.comercial.insertar_documento')
    def test_error_registra_historial_y_permite_reintento(self, enviar: object) -> None:
        enviar.return_value = {'RespuestaProceso': {'Tipo': 1, 'Errores': [{'ErrorDescripcion': 'Producto inexistente'}]}}
        crear_pedido(self.pedido.uuid)
        self.pedido.refresh_from_db()
        self.assertEqual(self.pedido.inet_estado, 'error')
        self.assertEqual(self.pedido.intentos_inet.get().detalle, 'Producto inexistente')
        crear_pedido(self.pedido.uuid)
        self.assertEqual(enviar.call_count, 2)

    @patch('modulo.informat.comercial.insertar_documento', side_effect=ServicioInformatTimeout('timeout'))
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
        with patch('modulo.informat.comercial.insertar_documento') as enviar:
            respuesta = self.client.post(url)
            self.assertEqual(respuesta.status_code, 409)
            self.assertIn('No se puede determinar', respuesta.json()['error'])
            enviar.assert_not_called()

    def test_fulfillment_no_envia_por_servicio_ni_api(self) -> None:
        self.pedido.datos['fulfillment'] = True
        self.pedido.save(update_fields=['datos'])
        usuario = get_user_model().objects.create_user(username='emisor_full')
        usuario.user_permissions.add(Permission.objects.get(codename='change_pedido', content_type__app_label='anymarket'))
        self.client.force_login(usuario)
        with patch('modulo.informat.comercial.insertar_documento') as enviar:
            for venta in (False, True):
                with self.subTest(venta=venta), self.assertRaisesMessage(ValueError, 'fulfillment'):
                    crear_pedido(self.pedido.uuid, venta=venta)
            respuesta = self.client.post(f'/api/v1/pedidos/{self.pedido.uuid}/inet/')
            self.assertEqual(respuesta.status_code, 409)
            self.assertIn('fulfillment', respuesta.json()['error'])
            enviar.assert_not_called()
        self.cliente_existe.assert_not_called()
        self.assertEqual(self.pedido.intentos_inet.count(), 0)

    @override_settings(INET_RECAUDACION_EQUIPO='1', INET_RECAUDACION_CAJERO='0', INET_RECAUDACION_FORMA_PAGO='0')
    def test_boleta_usa_maestro_precio_bruto_y_recaudacion(self) -> None:
        ReglaDocumentoInet.objects.create(tipo='boleta', codigo=756, descripcion='Boleta')
        self.pedido.datos.update({'marketPlace': 'SHOPIFY', 'metadata': {'invoiceRequired': 'boleta'}})
        documento = preparar_venta(self.pedido)
        facturacion = documento['Encabezado']['Facturacion']
        self.assertEqual((facturacion['DocumentoOrigen'], facturacion['DocumentoaGenerar']), (0, 756))
        self.assertEqual(facturacion['Equipo'], 1)
        recaudacion = documento['Recaudacion']
        self.assertEqual(recaudacion['Encabezado']['RETotalRecaudacion'], '1309.00')
        self.assertEqual(recaudacion['Encabezado']['REClienteCodigo'], documento['Encabezado']['Cliente']['ClienteCodigo'])
        self.assertEqual(recaudacion['Detalle'][0]['RDCodigo'], 0)
        self.assertEqual(recaudacion['Detalle'][0]['RDMonto'], '1309.00')
        self.assertEqual(documento['Detalle']['LineasDetalle'][0]['TotalLinea'], 1190)
        self.assertEqual(documento['Detalle']['LineasDetalle'][0]['PrecioBruto'], 1190)

    def test_precision_neto_e_iva_de_la_respuesta_inet(self) -> None:
        ReglaDocumentoInet.objects.create(tipo='boleta', codigo=756, descripcion='Boleta')
        self.pedido.datos = {'metadata': {'invoiceRequired': 'boleta'}, 'marketPlace': 'SHOPIFY',
                             'items': [{'sku': {'partnerId': '32001202'}, 'amount': 1, 'total': 54990}],
                             'freight': 3990, 'total': 58980}
        documento = preparar_venta(self.pedido)
        producto, envio = documento['Detalle']['LineasDetalle']
        self.assertEqual((producto['PrecioNeto'], producto['Iva']), (46210.084, 8779.92))
        self.assertEqual((envio['PrecioNeto'], envio['Iva']), (3352.9412, 637.06))
        totales = {c['ConceptoCodigo']: c['ConceptoValor'] for c in documento['Totales']['ConceptosTotales']}
        self.assertEqual(totales[100], 49563)
        self.assertEqual(totales[160], 49563)
        self.assertEqual(totales[170], 9417)
        self.assertEqual(totales[200], 58980)
        self.assertNotIn(180, totales)

    def test_api_crea_boleta_y_guarda_tipo_y_numero(self) -> None:
        ReglaDocumentoInet.objects.create(tipo='boleta', codigo=756, descripcion='Boleta')
        self.pedido.datos['metadata'] = {'invoiceRequired': 'boleta'}
        self.pedido.save(update_fields=['datos'])
        usuario = get_user_model().objects.create_user(username='emisor')
        usuario.user_permissions.add(Permission.objects.get(codename='change_pedido', content_type__app_label='anymarket'))
        self.client.force_login(usuario)
        respuesta_inet = {'RespuestaProceso': {'Tipo': 0, 'Datos': [
            {'NOMBRE': 'DOCUMENTO_CODIGO', 'DATO': '756'},
            {'NOMBRE': 'DOCUMENTO_NUMERO', 'DATO': '123'},
        ]}}
        with patch('modulo.informat.comercial.insertar_documento', return_value=respuesta_inet) as enviar:
            respuesta = self.client.post(f'/api/v1/pedidos/{self.pedido.uuid}/inet/')
        self.assertEqual(respuesta.status_code, 200)
        self.cliente_existe.assert_called_once_with('85644700', 0)
        self.assertEqual(respuesta.json()['tipo_documento'], '756')
        self.assertEqual(enviar.call_args.args[0]['Encabezado']['Facturacion']['DocumentoOrigen'], 0)
        self.pedido.refresh_from_db()
        self.assertEqual((self.pedido.inet_tipo_documento, self.pedido.inet_numero), ('756', '123'))
        intento = self.pedido.intentos_inet.get()
        self.assertNotIn('DocumentoComercial', intento.solicitud_cifrada)
        self.assertNotIn('DOCUMENTO_NUMERO', intento.respuesta_cifrada)
        self.assertEqual(descifrar_mensaje(intento.respuesta_cifrada), respuesta_inet)
        self.assertNotIn('Token', str(descifrar_mensaje(intento.solicitud_cifrada)))
        detalle = self.client.get(f'/api/v1/pedidos/{self.pedido.uuid}/inet/intentos/{intento.uuid}/')
        self.assertEqual(detalle.status_code, 200)
        self.assertEqual(detalle.json()['respuesta'], respuesta_inet)
        self.assertIn('no-store', detalle['Cache-Control'])
        self.client.logout()
        self.assertEqual(self.client.get(f'/api/v1/pedidos/{self.pedido.uuid}/inet/intentos/{intento.uuid}/').status_code, 401)

    def test_cliente_inexistente_permanece_pendiente_y_no_contacta_ws(self) -> None:
        ReglaDocumentoInet.objects.create(tipo='boleta', codigo=756, descripcion='Boleta')
        self.pedido.datos['metadata'] = {'invoiceRequired': 'boleta'}
        self.pedido.save(update_fields=['datos'])
        self.cliente_existe.return_value = False
        with patch('modulo.informat.comercial.insertar_documento') as enviar:
            crear_pedido(self.pedido.uuid, venta=True)
        enviar.assert_not_called()
        self.pedido.refresh_from_db()
        self.assertEqual(self.pedido.inet_estado, 'pendiente')
        self.assertIn('Créalo manualmente', self.pedido.inet_error)
        self.assertEqual(self.pedido.intentos_inet.get().resultado, 'pendiente')
        self.cliente_existe.return_value = True
        with patch('modulo.informat.comercial.insertar_documento', return_value={'RespuestaProceso': {'Tipo': 0, 'Datos': [{'NOMBRE': 'DOCUMENTO_NUMERO', 'DATO': '123'}]}}) as enviar:
            crear_pedido(self.pedido.uuid, venta=True)
        enviar.assert_called_once()

    def test_fallo_del_maestro_permanece_pendiente_sin_enviar(self) -> None:
        ReglaDocumentoInet.objects.create(tipo='boleta', codigo=756, descripcion='Boleta')
        self.pedido.datos['metadata'] = {'invoiceRequired': 'boleta'}
        self.pedido.save(update_fields=['datos'])
        self.cliente_existe.side_effect = ConsultaClienteError('Maestro no disponible.')
        with patch('modulo.informat.comercial.insertar_documento') as enviar:
            crear_pedido(self.pedido.uuid, venta=True)
        enviar.assert_not_called()
        self.pedido.refresh_from_db()
        self.assertEqual((self.pedido.inet_estado, self.pedido.inet_error), ('pendiente', 'Maestro no disponible.'))

    def test_auditoria_retira_tokens_de_la_respuesta(self) -> None:
        ReglaDocumentoInet.objects.create(tipo='boleta', codigo=756, descripcion='Boleta')
        self.pedido.datos['metadata'] = {'invoiceRequired': 'boleta'}
        self.pedido.save(update_fields=['datos'])
        respuesta = {'RespuestaProceso': {'Tipo': 0, 'Datos': [
            {'NOMBRE': 'DOCUMENTO_NUMERO', 'DATO': '123'}], 'Token': 'secreto'}}
        with patch('modulo.informat.comercial.insertar_documento', return_value=respuesta):
            crear_pedido(self.pedido.uuid, venta=True)
        guardada = descifrar_mensaje(self.pedido.intentos_inet.get().respuesta_cifrada)
        self.assertNotIn('Token', guardada['RespuestaProceso'])

    def test_factura_usa_cliente_y_codigo_configurado(self) -> None:
        ReglaDocumentoInet.objects.create(tipo='factura', codigo=777, descripcion='Factura')
        self.pedido.datos.update({'marketPlace': 'FALABELLA',
            'metadata': {'invoiceRequired': 'factura', 'buyerDNI': '76.123.456-7',
                         'razon': 'Empresa de prueba', 'giro': 'Comercio'},
            'buyer': {'email': 'prueba@example.test'},
            'billingAddress': {'address': 'Calle 123', 'neighborhood': 'Santiago', 'city': 'Santiago'}})
        documento = preparar_venta(self.pedido)
        self.assertEqual(documento['Encabezado']['Facturacion']['DocumentoaGenerar'], 777)
        self.assertEqual(documento['Encabezado']['Cliente']['ClienteCodigo'], '76123456')
        self.assertEqual(documento['Encabezado']['Cliente']['ClienteGiro'], 'Comercio')
        self.assertEqual(documento['Recaudacion']['Encabezado']['REClienteCodigo'], '76123456')

    @override_settings(INET_RECAUDACION_EQUIPO='1', INET_RECAUDACION_CAJERO='0', INET_RECAUDACION_FORMA_PAGO='invalido')
    def test_rechaza_configuracion_invalida_de_recaudacion(self) -> None:
        ReglaDocumentoInet.objects.create(tipo='boleta', codigo=756, descripcion='Boleta')
        self.pedido.datos['metadata'] = {'invoiceRequired': 'boleta'}
        with self.assertRaises(ImportePedidoError):
            preparar_venta(self.pedido)

    def test_venta_sin_regla_o_factura_incompleta_no_se_envia(self) -> None:
        self.pedido.datos['metadata'] = {'invoiceRequired': 'factura'}
        with self.assertRaises(ImportePedidoError):
            preparar_venta(self.pedido)
        ReglaDocumentoInet.objects.create(tipo='factura', codigo=777, descripcion='Factura')
        with self.assertRaises(ImportePedidoError):
            preparar_venta(self.pedido)
