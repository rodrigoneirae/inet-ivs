from unittest.mock import Mock
from pathlib import Path
from tempfile import TemporaryDirectory

from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.http import FileResponse
from django.test import RequestFactory, SimpleTestCase, override_settings

from . import views


class RutasAstroTests(SimpleTestCase):
    def setUp(self) -> None:
        self.factory = RequestFactory()
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        directory = root / 'frontend' / 'dist'
        directory.mkdir(parents=True)
        (directory / 'index.html').write_text('<html lang="es"></html>', encoding='utf-8')
        settings_override = override_settings(BASE_DIR=root)
        settings_override.enable()
        self.addCleanup(settings_override.disable)

    def test_pagina_principal_pasa_por_middleware(self) -> None:
        response = self.client.get('/')
        self.assertIsInstance(response, FileResponse)
        self.assertIn(b'<html', b''.join(response.streaming_content))
        self.assertEqual(response['X-Content-Type-Options'], 'nosniff')
        self.assertIn('no-store', response['Cache-Control'])

    def test_pedidos_requiere_sesion_y_permiso(self) -> None:
        request = self.factory.get('/pedidos/')
        request.user = AnonymousUser()
        self.assertEqual(views.pedidos(request).status_code, 302)
        request.user = Mock(is_authenticated=True)
        request.user.has_perms.return_value = False
        with self.assertRaises(PermissionDenied):
            views.pedidos(request)

    def test_pedidos_autorizado_entrega_astro(self) -> None:
        request = self.factory.get('/pedidos/')
        request.user = Mock(is_authenticated=True)
        request.user.has_perms.return_value = True
        response = views.pedidos(request)
        self.assertIsInstance(response, FileResponse)
        response.close()
