import io
import uuid
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import Client, TestCase, override_settings

from modulo.informat.models import AplicacionBodegas, BodegaInet
from modulo.informat.services.bodegas import BodegasNoDisponibles, buscar_bodega, listar_bodegas


@override_settings(CACHES={'api_rate_limit': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}})
class BodegasAPITests(TestCase):
    def setUp(self) -> None:
        self.url = '/api/v1/informat/bodegas/'
        self.user = get_user_model().objects.create_user(username='consulta-bodegas')

    @patch('modulo.informat.views.bodegas.listar_bodegas')
    def test_autorizacion_sesion_y_respuesta_limitada(self, listar: Mock) -> None:
        listar.return_value = ([{'codigo': '1', 'nombre': 'Central', 'estado_stock': 'D',
                                 'sucursal_codigo': 1, 'usa_ubicaciones': 0}], False)
        client = Client()
        self.assertEqual(client.get(self.url).status_code, 401)
        client.force_login(self.user)
        self.assertEqual(client.get(self.url).status_code, 403)
        self.user.user_permissions.add(Permission.objects.get(codename='consultar_bodegas_inet'))
        response = client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['bodegas'][0]['codigo'], '1')
        self.assertNotIn('direccion', response.json()['bodegas'][0])
        self.assertEqual(client.get(self.url, {'pagina': '0'}).status_code, 400)
        listar.assert_called_once_with(pagina=1, tamano=100, busqueda='')

    @patch('modulo.informat.views.bodegas.listar_bodegas')
    def test_token_por_aplicacion_y_revocacion(self, listar: Mock) -> None:
        listar.return_value = ([], False)
        aplicacion, token = AplicacionBodegas.crear_con_token('Otra app')
        client = Client()
        headers = {'HTTP_AUTHORIZATION': f'Bearer {token}'}
        self.assertEqual(client.get(self.url, **headers).status_code, 200)
        self.assertEqual(client.get(self.url, HTTP_AUTHORIZATION='Bearer invalido').status_code, 401)
        self.assertEqual(client.get(self.url, HTTP_AUTHORIZATION='Bearer ' + 'x' * 64).status_code, 401)
        self.assertEqual(client.get(self.url, HTTP_AUTHORIZATION='Bearer ' + 'a' * 48).status_code, 401)
        aplicacion.activa = False
        aplicacion.save(update_fields=['activa'])
        self.assertEqual(client.get(self.url, **headers).status_code, 401)

    @patch('modulo.informat.views.bodegas.listar_bodegas', return_value=([], False))
    def test_supervisor_de_inventario_puede_consultar(self, listar: Mock) -> None:
        self.user.user_permissions.add(Permission.objects.get(codename='supervisar_inventario'))
        client = Client()
        client.force_login(self.user)
        self.assertEqual(client.get(self.url).status_code, 200)

    @patch('modulo.informat.views.bodegas.listar_bodegas', side_effect=BodegasNoDisponibles)
    def test_sql_server_no_disponible(self, listar: Mock) -> None:
        self.user.user_permissions.add(Permission.objects.get(codename='consultar_bodegas_inet'))
        client = Client()
        client.force_login(self.user)
        self.assertEqual(client.get(self.url).status_code, 503)

    def test_comandos_emision_y_revocacion(self) -> None:
        stdout = io.StringIO()
        call_command('crear_token_bodegas', nombre='Otra app', stdout=stdout)
        aplicacion = AplicacionBodegas.objects.get(nombre='Otra app')
        self.assertNotIn(aplicacion.token_hash, stdout.getvalue())
        call_command('revocar_token_bodegas', str(aplicacion.public_id), stdout=io.StringIO())
        aplicacion.refresh_from_db()
        self.assertFalse(aplicacion.activa)
        with self.assertRaises(CommandError):
            call_command('revocar_token_bodegas', str(uuid.uuid4()), stdout=io.StringIO())


class BodegasModeloTests(TestCase):
    def test_modelo_externo_no_administrado(self) -> None:
        self.assertFalse(BodegaInet._meta.managed)
        self.assertEqual(BodegaInet._meta.db_table, 'BODEGAS')

    @patch('modulo.informat.services.bodegas.BodegaInet')
    def test_consulta_por_orm_sqlserver_y_codigos(self, modelo: Mock) -> None:
        modelo.objects.using.return_value.order_by.return_value.values.return_value.__getitem__.return_value = [
            {'codigo': 1, 'nombre': 'Central   ', 'estado_stock': 'D',
             'sucursal_codigo': 2, 'usa_ubicaciones': 0},
        ]
        with patch('modulo.informat.services.bodegas.settings') as configuracion:
            configuracion.DATABASES = {'sqlserver': {'ENGINE': 'mssql'}}
            bodegas, hay_mas = listar_bodegas()
            self.assertEqual(bodegas[0]['nombre'], 'Central')
            self.assertEqual(bodegas[0]['codigo'], '1')
            self.assertFalse(hay_mas)
            modelo.objects.using.assert_called_with('sqlserver')
            modelo.objects.using.return_value.filter.return_value.values.return_value.first.return_value = {
                'codigo': 1, 'nombre': 'Central   ',
            }
            self.assertEqual(buscar_bodega('001'), {'codigo': '1', 'nombre': 'Central'})
            self.assertIsNone(buscar_bodega('fuera'))
