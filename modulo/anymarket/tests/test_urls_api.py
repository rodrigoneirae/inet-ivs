from django.test import SimpleTestCase
from django.urls import resolve

from modulo.acceso.views import api as acceso_api
from modulo.anymarket.views import api as pedidos_api


class RutasApiTests(SimpleTestCase):
    def test_rutas_publicas_conservan_su_vista(self) -> None:
        uuid_pedido = '7f730a72-5707-42c2-8d23-08f7a9c7fa1a'
        uuid_intento = '6b472e94-2ee0-433a-bb9d-31d9e8921b94'
        rutas = {
            '/api/v1/sesion/': acceso_api.sesion,
            '/api/v1/ingresar/': acceso_api.ingresar,
            '/api/v1/salir/': acceso_api.salir,
            '/api/v1/pedidos/': pedidos_api.pedidos,
            '/api/v1/pedidos/exportar/': pedidos_api.exportar,
            '/api/v1/pedidos/sincronizar/': pedidos_api.sincronizar,
            f'/api/v1/pedidos/{uuid_pedido}/inet/': pedidos_api.crear_pedido_inet,
            f'/api/v1/pedidos/{uuid_pedido}/inet/errores/': pedidos_api.errores_pedido_inet,
            f'/api/v1/pedidos/{uuid_pedido}/inet/intentos/{uuid_intento}/': pedidos_api.detalle_intento_inet,
        }
        for ruta, vista in rutas.items():
            with self.subTest(ruta=ruta):
                self.assertIs(resolve(ruta).func, vista)
