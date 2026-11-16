import hashlib
import io
import json
from decimal import Decimal
from unittest.mock import Mock, patch

from django.db import DatabaseError
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import RequestFactory, SimpleTestCase, override_settings

from ..models import DispositivoPrecios
from ..services.precios import consultar_precio
from ..views.precios import precio


TOKEN = 'A' * 43


@override_settings(DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3'},
                              'sqlserver': {'ENGINE': 'django.db.backends.sqlite3'}})
@patch('modulo.informat.views.precios.caches')
class PreciosApiTests(SimpleTestCase):
    def setUp(self) -> None:
        self.request_factory = RequestFactory()

    def solicitud(self, parametros: dict[str, str], token: str = TOKEN) -> object:
        return self.request_factory.get('/api/v1/informat/precios/', parametros,
                                        HTTP_AUTHORIZATION=f'Bearer {token}')

    @patch('modulo.informat.views.precios.DispositivoPrecios.objects.only')
    @patch('modulo.informat.views.precios.consultar_precio')
    def test_autorizacion_y_aislamiento(self, consulta: Mock, manager: Mock, caches: Mock) -> None:
        manager.return_value.get.return_value = Mock(lista_codigo=1)
        self.assertEqual(precio(self.request_factory.get('/api/v1/informat/precios/')).status_code, 401)
        self.assertEqual(precio(self.solicitud({'producto': '0'})).status_code, 400)
        self.assertEqual(precio(self.solicitud({'producto': 'A' * 31})).status_code, 400)
        consulta.assert_not_called()
        manager.return_value.get.assert_called_with(
            token_hash=hashlib.sha256(TOKEN.encode()).hexdigest(), activo=True,
        )

    @patch('modulo.informat.views.precios.DispositivoPrecios.objects.only')
    @patch('modulo.informat.views.precios.consultar_precio')
    @patch('modulo.informat.views.precios.obtener_portada_base64', return_value='base64-portada')
    def test_respuesta_y_no_encontrado(self, portada: Mock, consulta: Mock, manager: Mock, caches: Mock) -> None:
        manager.return_value.get.return_value = Mock(lista_codigo=1)
        consulta.return_value = {'codigo': '0001', 'precio': '1234.5000', 'lista': 1}
        respuesta = precio(self.solicitud({'producto': '0001'}))
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(json.loads(respuesta.content)['producto']['precio'], '1234.5000')
        self.assertEqual(json.loads(respuesta.content)['producto']['imagen'], 'base64-portada')
        portada.assert_called_once_with('0001')
        consulta.assert_called_once_with(1, '0001')
        consulta.return_value = None
        self.assertEqual(precio(self.solicitud({'producto': 'NOEXISTE'})).status_code, 404)
        portada.assert_called_once()

    @patch('modulo.informat.views.precios.DispositivoPrecios.objects.only')
    @patch('modulo.informat.views.precios.consultar_precio')
    def test_error_bd_no_expone_detalles(self, consulta: Mock, manager: Mock, caches: Mock) -> None:
        manager.return_value.get.return_value = Mock(lista_codigo=1)
        consulta.side_effect = DatabaseError('detalle confidencial')
        respuesta = precio(self.solicitud({'producto': '1'}))
        self.assertEqual(respuesta.status_code, 503)
        self.assertNotIn('detalle confidencial', respuesta.content.decode())

    @patch('modulo.informat.views.precios.DispositivoPrecios.objects.only')
    def test_token_revocado(self, manager: Mock, caches: Mock) -> None:
        manager.return_value.get.side_effect = DispositivoPrecios.DoesNotExist()
        self.assertEqual(precio(self.solicitud({'producto': '1'})).status_code, 401)

    @patch('modulo.informat.views.precios.DispositivoPrecios.objects.only')
    @patch('modulo.informat.views.precios.consultar_precio')
    def test_limite_por_dispositivo(self, consulta: Mock, manager: Mock, caches: Mock) -> None:
        manager.return_value.get.return_value = Mock(lista_codigo=1)
        caches.__getitem__.return_value.add.return_value = False
        caches.__getitem__.return_value.incr.return_value = 121
        self.assertEqual(precio(self.solicitud({'producto': '1'})).status_code, 429)
        consulta.assert_not_called()


class PreciosSqlTests(SimpleTestCase):
    @override_settings(DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3'},
                                  'sqlserver': {'ENGINE': 'django.db.backends.sqlite3'}})
    @patch('modulo.informat.services.precios.connections')
    def test_codigo_parametrizado_y_precio_decimal(self, conexiones: Mock) -> None:
        cursor = conexiones.__getitem__.return_value.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value = ('0001', 'Producto', Decimal('1234.5000'), 'Lista', 1)
        resultado = consultar_precio(1, "' OR 1=1 --")
        self.assertEqual(resultado['precio'], '1234.5000')
        self.assertIn('p.LisCod = %s', cursor.execute.call_args.args[0])
        self.assertIn('dbo.PVEBAR', cursor.execute.call_args.args[0])
        self.assertEqual(cursor.execute.call_args.args[1], [1, "' OR 1=1 --", "' OR 1=1 --", "' OR 1=1 --", "' OR 1=1 --"])


class ProvisionTests(SimpleTestCase):
    @patch('modulo.informat.models.dispositivo_precios.DispositivoPrecios.objects.create')
    def test_token_aleatorio_se_guarda_solo_como_hash(self, crear: Mock) -> None:
        crear.return_value = Mock()
        _, token = DispositivoPrecios.crear_con_token('Lector', 1)
        self.assertEqual(len(token), 43)
        self.assertEqual(crear.call_args.kwargs['token_hash'], hashlib.sha256(token.encode()).hexdigest())
        self.assertNotIn(token, str(crear.call_args))

    @override_settings(DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3'},
                                  'sqlserver': {'ENGINE': 'django.db.backends.sqlite3'}})
    @patch('modulo.informat.management.commands.crear_dispositivo_precios.lista_existe', return_value=False)
    @patch('modulo.informat.models.dispositivo_precios.DispositivoPrecios.objects.create')
    def test_no_crea_dispositivo_si_lista_no_existe(self, crear: Mock, existe: Mock) -> None:
        with self.assertRaises(CommandError):
            call_command('crear_dispositivo_precios', nombre='Lector', lista=99, stdout=io.StringIO())
        crear.assert_not_called()
