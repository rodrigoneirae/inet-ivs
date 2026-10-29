from unittest.mock import Mock, patch
import json

from django.contrib.auth.models import AnonymousUser
from django.test import Client, RequestFactory, SimpleTestCase, override_settings

from . import api


@override_settings(CACHES={
    'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'},
    'api_rate_limit': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'},
})
class ApiTests(SimpleTestCase):
    def setUp(self) -> None:
        self.factory = RequestFactory()

    def test_pedidos_requires_authentication(self) -> None:
        request = self.factory.get('/api/v1/pedidos/')
        request.user = AnonymousUser()
        self.assertEqual(api.pedidos(request).status_code, 401)

    def test_pedidos_requires_permission(self) -> None:
        request = self.factory.get('/api/v1/pedidos/')
        request.user = Mock(is_authenticated=True)
        request.user.has_perm.return_value = False
        self.assertEqual(api.pedidos(request).status_code, 403)

    def test_actions_require_authentication_and_permission(self) -> None:
        for view, method in ((api.exportar, self.factory.get), (api.sincronizar, self.factory.post)):
            request = method('/api/v1/pedidos/accion/')
            request.user = AnonymousUser()
            self.assertEqual(view(request).status_code, 401)
            request.user = Mock(is_authenticated=True)
            request.user.has_perm.return_value = False
            self.assertEqual(view(request).status_code, 403)

    @patch('modulo.acceso.api.solicitar_sincronizacion')
    def test_sync_returns_task_status(self, solicitar: Mock) -> None:
        request = self.factory.post('/api/v1/pedidos/sincronizar/')
        request.user = Mock(is_authenticated=True)
        request.user.has_perm.return_value = True
        for result, status in (('success', 200), ('warning', 429), ('error', 503)):
            solicitar.return_value = (result, 'mensaje')
            self.assertEqual(api.sincronizar(request).status_code, status)

    def test_sync_requires_csrf(self) -> None:
        response = Client(enforce_csrf_checks=True).post('/api/v1/pedidos/sincronizar/')
        self.assertEqual(response.status_code, 403)

    @patch('modulo.anymarket.views.sincronizar_pedidos.apply_async')
    def test_web_and_api_share_sync_rate_limit(self, enqueue: Mock) -> None:
        from django.core.cache import cache
        from modulo.anymarket.views import solicitar_sincronizacion
        cache.clear()
        self.addCleanup(cache.clear)
        self.assertEqual(solicitar_sincronizacion()[0], 'success')
        request = self.factory.post('/api/v1/pedidos/sincronizar/')
        request.user = Mock(is_authenticated=True)
        request.user.has_perm.return_value = True
        self.assertEqual(api.sincronizar(request).status_code, 429)
        enqueue.assert_called_once_with(retry=False)

    @patch('modulo.acceso.api.exportar_pedidos')
    def test_export_passes_filters_to_existing_view(self, exportar: Mock) -> None:
        from django.http import HttpResponse
        request = self.factory.get('/api/v1/pedidos/exportar/', {'canal': 'shopify'})
        request.user = Mock(is_authenticated=True)
        request.user.has_perm.return_value = True
        exportar.return_value = HttpResponse(b'excel')
        self.assertEqual(api.exportar(request).status_code, 200)
        exportar.assert_called_once_with(request)

    def test_invalid_date_range_is_rejected(self) -> None:
        request = self.factory.get('/api/v1/pedidos/', {'desde': '2026-10-20', 'hasta': '2026-10-01'})
        request.user = Mock(is_authenticated=True)
        request.user.has_perm.return_value = True
        self.assertEqual(api.pedidos(request).status_code, 400)

    @patch('modulo.acceso.api.Pedido.objects')
    @patch('modulo.acceso.api.consulta_pedidos')
    def test_filters_and_options(self, consulta: Mock, manager: Mock) -> None:
        request = self.factory.get('/api/v1/pedidos/', {
            'desde': '2026-10-01', 'hasta': '2026-10-20', 'canal': 'shopify',
            'estado': 'paid', 'orden': 'cliente', 'direccion': 'asc', 'page': '1',
        })
        request.user = Mock(is_authenticated=True)
        request.user.has_perm.return_value = True
        filtros = Mock()
        filtros.is_valid.return_value = True
        consulta.return_value = ([], filtros, 'cliente', 'asc')
        choices = manager.exclude.return_value.values_list.return_value.distinct.return_value.order_by.return_value
        choices.__getitem__.side_effect = [['shopify'], ['paid']]
        response = api.pedidos(request)
        self.assertEqual(response.status_code, 200)
        consulta.assert_called_once_with(request)
        self.assertEqual(request.GET['desde'], '2026-10-01')
        self.assertEqual(request.GET['canal'], 'shopify')
        self.assertEqual(request.GET['orden'], 'cliente')
        self.assertEqual(json.loads(response.content)['canales'], ['shopify'])

    @patch('modulo.acceso.api.authenticate')
    def test_invalid_login_is_rejected(self, authenticate: Mock) -> None:
        request = self.factory.post('/api/v1/ingresar/', {'username': 'usuario', 'password': 'clave'})
        authenticate.return_value = None
        self.assertEqual(api.ingresar(request).status_code, 401)

    def test_login_rejects_missing_password(self) -> None:
        request = self.factory.post('/api/v1/ingresar/', {'username': 'usuario'})
        self.assertEqual(api.ingresar(request).status_code, 400)
