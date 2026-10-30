import json
from contextlib import nullcontext
from unittest.mock import MagicMock, Mock, patch
from urllib.error import URLError

from django.test import Client, RequestFactory, SimpleTestCase, override_settings

from ..views.stock import stock, token_manual
from ..views.catalogo import productos
from ..services import ServicioInformatError, ServicioInformatTimeout, _post_json, consultar_stock
from ..services.tokens import guardar_token_manual, obtener_token


class FakeRedis:
    def __init__(self) -> None:
        self.values: dict[str, bytes] = {}

    def lock(self, key: str, **kwargs: object) -> object:
        return nullcontext()

    def get(self, key: str) -> bytes | None:
        return self.values.get(key)

    def setex(self, key: str, seconds: int, value: bytes | str) -> None:
        self.values[key] = value.encode() if isinstance(value, str) else value

    def delete(self, key: str) -> None:
        self.values.pop(key, None)


@override_settings(URLTOKEN='https://ssi.example/token', EMPRUT='empresa', CONID='conexion',
                   APLID='aplicacion', WSPRODUCTOSVENTAS='funcion',
                   URL_WSCOMERCIAL='https://inet.example/rest/wscomercial',
                   URL_WSPRODUCTOSVENTAS='', INFORMAT_TOKEN_PRODUCTOS='')
class ConsultaStockTests(SimpleTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.redis = FakeRedis()
        patcher = patch('modulo.informat.services.tokens._redis', return_value=self.redis)
        patcher.start()
        self.addCleanup(patcher.stop)

    @patch('modulo.informat.services.stock._post_json')
    def test_autenticacion_y_filtros(self, post: Mock) -> None:
        post.side_effect = [
            {'SalidaAut': {'CodigoError': 200, 'Token': 'temporal'}},
            {'RespuestaProceso': {'Tipo': 0}, 'Productos': []},
        ]
        self.assertEqual(consultar_stock('00123', ''), [])
        self.assertEqual(post.call_args_list[0].args[1]['EntradaAut']['FncId'], 'funcion')
        url, payload = post.call_args_list[1].args
        self.assertEqual(url, 'https://inet.example/rest/wsProductosVentas')
        self.assertEqual(payload['ProcesoFiltros']['Token'], 'temporal')
        self.assertEqual(payload['ProcesoFiltros']['Filtros'][1]['Dato'], '00123')
        self.assertEqual(payload['ProcesoFiltros']['Filtros'][0]['Dato'], '')

    @patch('modulo.informat.services.stock._post_json')
    def test_error_negocio_no_devuelve_productos(self, post: Mock) -> None:
        post.side_effect = [{'SalidaAut': {'CodigoError': 200, 'Token': 'temporal'}},
                            {'RespuestaProceso': {'Tipo': 1}, 'Productos': []}]
        with self.assertRaises(ServicioInformatError):
            consultar_stock('123', '1')

    @patch('modulo.informat.services.stock._post_json')
    def test_listado_sin_codigo_omite_filtro_producto(self, post: Mock) -> None:
        post.side_effect = [{'SalidaAut': {'CodigoError': 200, 'Token': 'temporal'}},
                            {'RespuestaProceso': {'Tipo': 0}, 'Productos': []}]
        consultar_stock('', '1')
        filtros = post.call_args_list[1].args[1]['ProcesoFiltros']['Filtros']
        self.assertEqual(filtros, [{'Opcion': 0, 'Nombre': 'BODEGA', 'Dato': '1'}])

    @patch('modulo.informat.views.stock.consultar_stock')
    def test_permisos_filtros_y_datos_permitidos(self, consulta: Mock) -> None:
        request = RequestFactory().get('/api/v1/informat/stock/', {'producto': '00123', 'bodega': '1'})
        request.user = Mock(is_authenticated=False)
        self.assertEqual(stock(request).status_code, 401)
        request.user = Mock(is_authenticated=True)
        request.user.has_perm.return_value = False
        self.assertEqual(stock(request).status_code, 403)
        request.user.has_perm.return_value = True
        consulta.return_value = [{'VENTA': {'PRODUCTO_VTA': '00123', 'DESC_CORTA': 'Producto'},
                                 'STOCK': {'STOCK_ACTUAL': 5, 'STOCK_DISPONIBLE': 4,
                                           'STOCK_BODEGA': [{'BODEGA': 1, 'STOCK_DISPONIBLE': 2}]},
                                 'PRECIOS': {'PRECIO_LISTA': 500}}]
        respuesta = stock(request)
        self.assertEqual(respuesta.status_code, 200)
        datos = json.loads(respuesta.content)['productos'][0]
        self.assertEqual(datos['bodegas'][0]['bodega'], 1)
        self.assertEqual(datos['bodegas'][0]['disponible'], 2)
        self.assertNotIn('PRECIOS', datos)
        consulta.assert_called_once_with('00123', '1')

    @patch('modulo.informat.views.stock.consultar_stock')
    def test_filtros_invalidos_no_consultan(self, consulta: Mock) -> None:
        request = RequestFactory().get('/api/v1/informat/stock/', {'producto': '0', 'bodega': 'abc'})
        request.user = Mock(is_authenticated=True)
        request.user.has_perm.return_value = True
        self.assertEqual(stock(request).status_code, 400)
        consulta.assert_not_called()

    @patch('modulo.informat.views.stock.consultar_stock')
    def test_producto_obligatorio(self, consulta: Mock) -> None:
        request = RequestFactory().get('/api/v1/informat/stock/', {'bodega': '1'})
        request.user = Mock(is_authenticated=True)
        request.user.has_perm.return_value = True
        self.assertEqual(stock(request).status_code, 400)
        consulta.assert_not_called()

    @override_settings(DEBUG=False)
    def test_produccion_rechaza_http(self) -> None:
        with self.assertRaises(ServicioInformatError):
            _post_json('http://inet.example/rest/wsproductosventas', {})

    @override_settings(INFORMAT_TIMEOUT=30)
    @patch('modulo.informat.services.stock.build_opener')
    def test_timeout_directo_y_envuelto(self, opener: Mock) -> None:
        for error in (TimeoutError(), URLError(TimeoutError())):
            with self.subTest(error=type(error).__name__):
                opener.return_value.open.side_effect = error
                with self.assertRaises(ServicioInformatTimeout):
                    _post_json('https://inet.example/rest/wsproductosventas', {})
                self.assertEqual(opener.return_value.open.call_args.kwargs['timeout'], 30)

    @patch('modulo.informat.services.stock._post_json')
    def test_timeout_identifica_etapa(self, post: Mock) -> None:
        post.side_effect = ServicioInformatTimeout('timeout')
        with self.assertRaisesMessage(ServicioInformatTimeout, 'autenticación'):
            consultar_stock('123', '')
        post.side_effect = [
            {'SalidaAut': {'CodigoError': 200, 'Token': 'temporal'}},
            ServicioInformatTimeout('timeout'),
        ]
        with self.assertRaisesMessage(ServicioInformatTimeout, 'productos'):
            consultar_stock('123', '')

    @patch('modulo.informat.views.stock.consultar_stock')
    def test_timeout_devuelve_504(self, consulta: Mock) -> None:
        request = RequestFactory().get('/api/v1/informat/stock/', {'producto': '123'})
        request.user = Mock(is_authenticated=True)
        request.user.has_perm.return_value = True
        consulta.side_effect = ServicioInformatTimeout('El servicio de productos no respondió a tiempo.')
        respuesta = stock(request)
        self.assertEqual(respuesta.status_code, 504)
        self.assertIn('productos', json.loads(respuesta.content)['error'])

    def test_token_se_reutiliza_y_se_guarda_cifrado(self) -> None:
        renovar = Mock(return_value='token-secreto')
        self.assertEqual(obtener_token(renovar), 'token-secreto')
        self.assertEqual(obtener_token(renovar), 'token-secreto')
        renovar.assert_called_once()
        self.assertNotIn(b'token-secreto', next(iter(self.redis.values.values())))

    def test_token_manual_sustituye_token_y_no_renueva(self) -> None:
        guardar_token_manual('token-manual', 300)
        renovar = Mock()
        self.assertEqual(obtener_token(renovar), 'token-manual')
        renovar.assert_not_called()

    def test_token_vencido_se_renueva(self) -> None:
        renovar = Mock(side_effect=['anterior', 'nuevo'])
        self.assertEqual(obtener_token(renovar), 'anterior')
        self.redis.values.clear()  # Redis elimina la clave al vencer el TTL.
        self.assertEqual(obtener_token(renovar), 'nuevo')
        self.assertEqual(renovar.call_count, 2)

    def test_rechazo_de_token_antiguo_no_sobrescribe_un_token_manual(self) -> None:
        guardar_token_manual('manual-nuevo', 300)
        renovar = Mock()
        self.assertEqual(obtener_token(renovar, rechazado='antiguo'), 'manual-nuevo')
        renovar.assert_not_called()

    @patch('modulo.informat.services.stock._post_json')
    def test_token_rechazado_renueva_una_vez(self, post: Mock) -> None:
        guardar_token_manual('anterior', 300)
        post.side_effect = [
            {'RespuestaProceso': {'Tipo': 1, 'Errores': [{'ErrorDescripcion': '413, Token no está autorizado'}]}},
            {'SalidaAut': {'CodigoError': 200, 'Token': 'nuevo'}},
            {'RespuestaProceso': {'Tipo': 0}, 'Productos': []},
        ]
        self.assertEqual(consultar_stock('123', '1'), [])
        self.assertEqual(post.call_count, 3)
        self.assertEqual(post.call_args_list[2].args[1]['ProcesoFiltros']['Token'], 'nuevo')

    @patch('modulo.informat.services.stock._post_json')
    def test_error_negocio_no_renueva_token(self, post: Mock) -> None:
        guardar_token_manual('manual', 300)
        post.return_value = {'RespuestaProceso': {'Tipo': 1, 'Errores': [{'ErrorDescripcion': 'Producto inválido'}]}}
        with self.assertRaises(ServicioInformatError):
            consultar_stock('123', '1')
        self.assertEqual(post.call_count, 1)

    @patch('modulo.informat.views.stock.guardar_token_manual')
    @patch('modulo.informat.views.stock.caches')
    def test_token_manual_permisos_y_validacion(self, caches_mock: Mock, guardar: Mock) -> None:
        caches_mock.__getitem__ = Mock(return_value=Mock(add=Mock(return_value=True)))
        request = RequestFactory().post('/api/v1/informat/token/', {'token': 'manual', 'minutos_vigencia': '30'})
        request.user = Mock(is_authenticated=False)
        self.assertEqual(token_manual(request).status_code, 401)
        request.user = Mock(is_authenticated=True, pk=1)
        request.user.has_perm.return_value = False
        self.assertEqual(token_manual(request).status_code, 403)
        request.user.has_perm.return_value = True
        self.assertEqual(token_manual(request).status_code, 200)
        guardar.assert_called_once_with('manual', 1800)
        request = RequestFactory().post('/api/v1/informat/token/', {'token': 'manual', 'minutos_vigencia': '1441'})
        request.user = Mock(is_authenticated=True)
        request.user.has_perm.return_value = True
        self.assertEqual(token_manual(request).status_code, 400)

    def test_token_manual_requiere_csrf(self) -> None:
        respuesta = Client(enforce_csrf_checks=True).post(
            '/api/v1/informat/token/', {'token': 'manual', 'minutos_vigencia': '30'}
        )
        self.assertEqual(respuesta.status_code, 403)


class CatalogoTests(SimpleTestCase):
    @patch('modulo.informat.views.catalogo.ProductoVentaInet')
    def test_autenticacion_permiso_y_validacion(self, modelo: Mock) -> None:
        request = RequestFactory().get('/api/v1/informat/productos/')
        request.user = Mock(is_authenticated=False)
        self.assertEqual(productos(request).status_code, 401)
        request.user = Mock(is_authenticated=True)
        request.user.has_perm.return_value = False
        self.assertEqual(productos(request).status_code, 403)
        request.user.has_perm.return_value = True
        request.GET = request.GET.copy()
        request.GET['tamano'] = '101'
        self.assertEqual(productos(request).status_code, 400)
        modelo.objects.using.assert_not_called()

    @override_settings(DATABASES={'default': {'ENGINE': 'django.db.backends.dummy'},
                                 'sqlserver': {'ENGINE': 'django.db.backends.dummy'}})
    @patch('modulo.informat.views.catalogo.ProductoVentaInet')
    def test_paginacion_y_busqueda(self, modelo: Mock) -> None:
        request = RequestFactory().get('/api/v1/informat/productos/',
                                       {'busqueda': '250', 'pagina': '2', 'tamano': '1'})
        request.user = Mock(is_authenticated=True)
        request.user.has_perm.return_value = True
        consulta = modelo.objects.using.return_value.order_by.return_value.filter.return_value
        consulta.values.return_value = MagicMock()
        consulta.values.return_value.__getitem__.return_value = [{'codigo': '250'}, {'codigo': '251'}]
        respuesta = productos(request)
        datos = json.loads(respuesta.content)
        self.assertEqual(datos['productos'], [{'codigo': '250'}])
        self.assertTrue(datos['hay_mas'])
        self.assertEqual(datos['pagina'], 2)
        self.assertEqual(consulta.values.return_value.__getitem__.call_args.args[0], slice(1, 3))
        modelo.objects.using.assert_called_once_with('sqlserver')
