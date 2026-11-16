from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.db import IntegrityError, connection, connections, transaction
from django.test import TestCase, TransactionTestCase, override_settings
from django.urls import NoReverseMatch, reverse
from django.utils import timezone

from modulo.informat.services.stock import ServicioInformatTimeout
from modulo.informat.services.comercial import ResultadoComercial

from ..models import DetPedidoApi, EncPedidoApi
from ..services import procesar_pedido, procesar_pendientes
from ..services.documento import preparar_documento
from ..tasks import procesar_pedidos_inet


@override_settings(PEDIDOS_INET_ENABLED=True, PEDIDOS_INET_DOCUMENTOS_PERMITIDOS={'771', '759'})
class ColaTests(TestCase):
    def setUp(self) -> None:
        self.pedido = EncPedidoApi.objects.create(
            documento_a_generar=771, cliente_codigo='12345678', cliente_secuencia=0,
            concepto_codigo_100=1000, concepto_codigo_160=1000, concepto_codigo_170=190,
            concepto_codigo_200=1190, dyr_descto_uno_codigo=5, dyr_descto_uno_porcentaje=10,
            dyr_descto_uno_monto=100,
        )
        self.detalle = DetPedidoApi.objects.create(
            enc_pedido=self.pedido, nro_linea=1, producto_ventas='SKU-1', cantidad=2,
            precio_neto=500, precio_lista=500, total_linea=1000,
        )
        cliente = patch('modulo.informat.services.comercial.existe_cliente', return_value=True)
        self.cliente = cliente.start()
        self.addCleanup(cliente.stop)
        envio = patch('modulo.informat.services.comercial.insertar_documento')
        self.envio = envio.start()
        self.addCleanup(envio.stop)
        self.envio.return_value = {'RespuestaProceso': {'Tipo': 0, 'Datos': [
            {'NOMBRE': 'DOCUMENTO_NUMERO', 'DATO': '12345'},
            {'NOMBRE': 'DOCUMENTO_CODIGO', 'DATO': '771'},
            {'NOMBRE': 'DOCUMENTO_ATENCION', 'DATO': '500'},
            {'NOMBRE': 'DOCUMENTO_ESTADO', 'DATO': '0'},
        ]}}

    def test_contrato_y_mapeo(self) -> None:
        self.assertEqual(EncPedidoApi._meta.db_table, 'inet_encpedidoapi')
        self.assertEqual(DetPedidoApi._meta.db_table, 'inet_detpedidoapi')
        self.assertEqual(DetPedidoApi._meta.get_field('enc_pedido').column, 'enc_pedido_id')
        documento = preparar_documento(self.pedido, [self.detalle])
        self.assertEqual(documento['Encabezado']['Referencias']['ClienteReferencia'], f'COLA-{self.pedido.uuid}')
        descuento = documento['Encabezado']['DescuentosyRecargos']
        self.assertEqual(descuento['DYRDesctoUnoPorcentaje'], 10)
        self.assertEqual(descuento['DYRDesctoUnoMonto'], 100)
        self.assertEqual(documento['Detalle']['LineasDetalle'][0]['Cantidad'], 2)
        self.assertNotIn('Seguridad', documento)

    def test_confirma_y_no_repite(self) -> None:
        self.assertTrue(procesar_pedido(self.pedido.uuid))
        self.pedido.refresh_from_db()
        self.detalle.refresh_from_db()
        self.assertEqual(self.pedido.estado_envio, 'E')
        self.assertEqual(self.detalle.estado_envio, 'E')
        self.assertEqual(self.pedido.api_documento_numero, '12345')
        self.assertEqual(self.pedido.api_documento_atencion, '500')
        self.assertTrue(self.pedido.solicitud_cifrada)
        self.assertTrue(self.pedido.respuesta_cifrada)
        self.assertIsNone(self.pedido.api_json)
        self.assertIsNone(self.pedido.api_json_response)
        self.assertFalse(procesar_pedido(self.pedido.uuid))
        self.assertEqual(self.envio.call_count, 1)

    def test_solicitud_persistida_antes_del_envio(self) -> None:
        respuesta = self.envio.return_value

        def comprobar(documento: dict) -> dict:
            actual = EncPedidoApi.objects.get(uuid=self.pedido.uuid)
            self.assertEqual(actual.estado_envio, 'PR')
            self.assertTrue(actual.solicitud_cifrada)
            self.assertFalse(procesar_pedido(actual.uuid))
            return respuesta

        self.envio.side_effect = comprobar
        self.assertTrue(procesar_pedido(self.pedido.uuid))
        self.assertEqual(self.envio.call_count, 1)

    def test_timeout_requiere_revision_y_no_reintenta(self) -> None:
        self.envio.side_effect = ServicioInformatTimeout('Tiempo agotado')
        self.assertFalse(procesar_pedido(self.pedido.uuid))
        self.pedido.refresh_from_db()
        self.assertEqual(self.pedido.estado_envio, 'RV')
        self.assertEqual(procesar_pendientes(), 0)
        self.envio.assert_called_once()

    def test_rechazo_no_se_reintenta(self) -> None:
        self.envio.return_value = {'RespuestaProceso': {'Tipo': 1, 'Errores': [
            {'ErrorDescripcion': 'Dato rechazado'}]}}
        self.assertFalse(procesar_pedido(self.pedido.uuid))
        self.pedido.refresh_from_db()
        self.assertEqual(self.pedido.estado_envio, 'ER')
        self.assertEqual(procesar_pendientes(), 0)
        self.envio.assert_called_once()

    def test_interrupcion_en_proceso_no_se_reencola(self) -> None:
        EncPedidoApi.objects.filter(pk=self.pedido.pk).update(
            estado_envio='PR', procesando_desde=timezone.now() - timedelta(minutes=11))
        self.assertEqual(procesar_pendientes(), 0)
        self.pedido.refresh_from_db()
        self.assertEqual(self.pedido.estado_envio, 'RV')
        self.envio.assert_not_called()

    def test_cambiar_a_p_no_repite_un_envio_anterior(self) -> None:
        procesar_pedido(self.pedido.uuid)
        EncPedidoApi.objects.filter(pk=self.pedido.pk).update(estado_envio='P', api_documento_numero='')
        self.assertFalse(procesar_pedido(self.pedido.uuid))
        self.pedido.refresh_from_db()
        self.assertEqual(self.pedido.estado_envio, 'RV')
        self.envio.assert_called_once()

    def test_falta_cliente_no_envia(self) -> None:
        self.cliente.return_value = False
        self.assertFalse(procesar_pedido(self.pedido.uuid))
        self.pedido.refresh_from_db()
        self.assertEqual(self.pedido.estado_envio, 'ER')
        self.envio.assert_not_called()

    def test_sin_detalles_no_envia(self) -> None:
        self.detalle.delete()
        self.assertFalse(procesar_pedido(self.pedido.uuid))
        self.envio.assert_not_called()

    def test_tipo_no_autorizado_no_envia(self) -> None:
        self.pedido.documento_a_generar = 999
        self.pedido.save()
        self.assertFalse(procesar_pedido(self.pedido.uuid))
        self.envio.assert_not_called()

    def test_total_inconsistente_no_envia(self) -> None:
        self.pedido.concepto_codigo_200 = 1
        self.pedido.save()
        self.assertFalse(procesar_pedido(self.pedido.uuid))
        self.envio.assert_not_called()

    def test_descuento_global_conserva_totales_del_productor(self) -> None:
        self.pedido.concepto_codigo_160 = 900
        self.pedido.concepto_codigo_170 = 171
        self.pedido.concepto_codigo_200 = 1071
        documento = preparar_documento(self.pedido, [self.detalle])
        conceptos = {c['ConceptoCodigo']: c['ConceptoValor'] for c in documento['Totales']['ConceptosTotales']}
        self.assertEqual(conceptos[160], 900)

    def test_valor_no_finito_no_envia(self) -> None:
        self.pedido.concepto_codigo_200 = float('nan')
        self.pedido.save()
        self.assertFalse(procesar_pedido(self.pedido.uuid))
        self.envio.assert_not_called()

    def test_respuesta_incompleta_requiere_revision(self) -> None:
        self.envio.return_value = {'RespuestaProceso': {'Tipo': 0, 'Datos': []}}
        self.assertFalse(procesar_pedido(self.pedido.uuid))
        self.pedido.refresh_from_db()
        self.assertEqual(self.pedido.estado_envio, 'RV')

    @patch('modulo.pedidos_inet.services.cola.crear_documento', side_effect=RuntimeError('error simulado'))
    def test_excepcion_durante_envio_no_reencola(self, enviar: object) -> None:
        self.assertFalse(procesar_pedido(self.pedido.uuid))
        self.pedido.refresh_from_db()
        self.assertEqual(self.pedido.estado_envio, 'RV')
        self.assertTrue(self.pedido.solicitud_cifrada)

    def test_cantidad_invalida_no_envia(self) -> None:
        self.detalle.cantidad = -1
        self.detalle.save()
        self.assertFalse(procesar_pedido(self.pedido.uuid))
        self.envio.assert_not_called()

    def test_linea_duplicada_rechazada_por_bd(self) -> None:
        with self.assertRaises(IntegrityError), transaction.atomic():
            DetPedidoApi.objects.create(enc_pedido=self.pedido, nro_linea=1)

    @override_settings(PEDIDOS_INET_ENABLED=False)
    def test_apagado_no_envia(self) -> None:
        self.assertEqual(procesar_pedidos_inet(), 0)
        self.assertFalse(procesar_pedido(self.pedido.uuid))
        self.envio.assert_not_called()

    def test_estado_retenido_no_se_envia(self) -> None:
        self.pedido.estado_envio = 'R'
        self.pedido.save()
        self.assertEqual(procesar_pendientes(), 0)
        self.envio.assert_not_called()

    def test_759_no_incluye_concepto_180(self) -> None:
        self.pedido.documento_a_generar = 759
        documento = preparar_documento(self.pedido, [self.detalle])
        self.assertNotIn(180, [c['ConceptoCodigo'] for c in documento['Totales']['ConceptosTotales']])

    def test_insert_sql_tiene_defaults_para_columnas_nuevas(self) -> None:
        with connection.cursor() as cursor:
            cursor.execute('INSERT INTO inet_encpedidoapi (documento_a_generar) VALUES (%s) RETURNING id', [771])
            pk = cursor.fetchone()[0]
        pedido = EncPedidoApi.objects.get(pk=pk)
        self.assertTrue(pedido.uuid)
        self.assertEqual(pedido.estado_envio, 'P')
        self.assertEqual(pedido.solicitud_cifrada, '')

    def test_nombre_estable_tarea(self) -> None:
        self.assertEqual(procesar_pedidos_inet.name, 'modulo.pedidos_inet.tasks.procesar_pedidos_inet')


class SeguimientoTests(TestCase):
    def setUp(self) -> None:
        self.usuario = get_user_model().objects.create_user(username='operador', is_staff=True)
        self.pedido = EncPedidoApi.objects.create(documento_a_generar=771)
        self.url = reverse('admin:pedidos_inet_encpedidoapi_change', args=[self.pedido.uuid])
        self.lista = reverse('admin:pedidos_inet_encpedidoapi_changelist')

    def test_anonimo_no_accede(self) -> None:
        self.assertEqual(self.client.get(self.url).status_code, 302)

    def test_sin_permiso_no_accede(self) -> None:
        self.client.force_login(self.usuario)
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_con_permiso_solo_lectura_y_enlaces_uuid(self) -> None:
        self.usuario.user_permissions.add(Permission.objects.get(
            content_type__app_label='pedidos_inet', codename='view_encpedidoapi'))
        self.client.force_login(self.usuario)
        self.assertContains(self.client.get(self.lista), self.url)
        self.assertEqual(self.client.get(self.url).status_code, 200)
        self.assertEqual(self.client.post(self.url, {'estado_envio': 'P'}).status_code, 403)

    def test_no_existen_rutas_enteras_ni_eliminar(self) -> None:
        self.client.force_login(self.usuario)
        url_entera = f'/admin/pedidos_inet/encpedidoapi/{self.pedido.pk}/change/'
        self.assertEqual(self.client.get(url_entera).status_code, 404)
        with self.assertRaises(NoReverseMatch):
            reverse('admin:pedidos_inet_encpedidoapi_delete', args=[self.pedido.uuid])


@override_settings(PEDIDOS_INET_ENABLED=True, PEDIDOS_INET_DOCUMENTOS_PERMITIDOS={'771'})
class ConcurrenciaTests(TransactionTestCase):
    def test_dos_workers_solo_envian_una_vez(self) -> None:
        pedido = EncPedidoApi.objects.create(
            documento_a_generar=771, cliente_codigo='12345678', cliente_secuencia=0,
            concepto_codigo_100=100, concepto_codigo_160=100, concepto_codigo_170=19, concepto_codigo_200=119)
        DetPedidoApi.objects.create(enc_pedido=pedido, nro_linea=1, producto_ventas='SKU',
                                    cantidad=1, precio_neto=100, total_linea=100)
        barrera = Barrier(2)

        def ejecutar() -> bool:
            try:
                barrera.wait(timeout=5)
                return procesar_pedido(pedido.uuid)
            finally:
                connections.close_all()

        with patch('modulo.pedidos_inet.services.cola.validar_cliente_documento'), patch(
            'modulo.pedidos_inet.services.cola.crear_documento',
            return_value=ResultadoComercial('creado', numero='42', tipo_documento='771'),
        ) as enviar, ThreadPoolExecutor(max_workers=2) as pool:
            resultados = [f.result(timeout=10) for f in [pool.submit(ejecutar), pool.submit(ejecutar)]]
        self.assertEqual(sorted(resultados), [False, True])
        enviar.assert_called_once()
        pedido.refresh_from_db()
        self.assertEqual(pedido.estado_envio, 'E')
