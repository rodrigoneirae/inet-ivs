from unittest.mock import MagicMock, patch

from django.contrib.auth import authenticate, get_user_model
from django.db import OperationalError
from django.test import TestCase, override_settings
from django.urls import reverse

from ..models import UsuarioOrigen
from ..services import RegistroOrigen, sincronizar_usuarios


@override_settings(STORAGES={
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
})
class AccesoTests(TestCase):
    def setUp(self) -> None:
        self.registro = RegistroOrigen(12, 'operador', 'clave-original', 'usuario@example.com')

    @patch('modulo.acceso.backends.obtener_registros')
    def test_ingreso_importa_y_actualiza_clave(self, obtener: MagicMock) -> None:
        obtener.return_value = [self.registro]
        usuario = authenticate(username='operador', password='clave-original')
        self.assertIsNotNone(usuario)
        self.assertNotEqual(usuario.password, 'clave-original')
        self.assertTrue(usuario.check_password('clave-original'))
        obtener.return_value = [RegistroOrigen(12, 'operador', 'nueva-clave', '')]
        self.assertIsNone(authenticate(username='operador', password='clave-original'))
        usuario = authenticate(username='operador', password='nueva-clave')
        self.assertTrue(usuario.check_password('nueva-clave'))
        self.assertEqual(UsuarioOrigen.objects.count(), 1)

    @patch('modulo.acceso.backends.obtener_registros')
    def test_rechaza_duplicados_y_cuentas_locales(self, obtener: MagicMock) -> None:
        obtener.return_value = [self.registro, RegistroOrigen(13, 'operador', 'otra', '')]
        self.assertIsNone(authenticate(username='operador', password='clave-original'))
        obtener.return_value = [self.registro]
        get_user_model().objects.create_user(username='operador', password='local')
        self.assertIsNone(authenticate(username='operador', password='clave-original'))
        self.assertIsNone(authenticate(username='operador', password='local'))

    @patch('modulo.acceso.backends.obtener_registros', side_effect=OperationalError('sin conexión'))
    def test_no_autentica_si_falla_origen(self, obtener: MagicMock) -> None:
        with self.assertLogs('modulo.acceso.backends', level='ERROR'):
            self.assertIsNone(authenticate(username='operador', password='clave-original'))

    @patch('modulo.acceso.services.sincronizacion_usuarios.obtener_registros')
    def test_sincronizacion_omite_registros_invalidos(self, obtener: MagicMock) -> None:
        obtener.return_value = [self.registro, RegistroOrigen(13, 'sin-clave', '', '')]
        self.assertEqual(sincronizar_usuarios(), (1, 1))
        self.assertTrue(get_user_model().objects.get(username='operador').check_password('clave-original'))

    def test_sesion_y_cierre_de_sesion(self) -> None:
        self.assertIsNone(self.client.get('/api/v1/sesion/').json()['usuario'])
        usuario = get_user_model().objects.create_user(username='prueba', password='clave')
        self.client.force_login(usuario)
        self.assertEqual(self.client.get('/api/v1/sesion/').json()['usuario'], 'prueba')
        self.assertEqual(self.client.post('/api/v1/salir/').status_code, 200)
        self.assertIsNone(self.client.get('/api/v1/sesion/').json()['usuario'])

    def test_login_anterior_redirige_a_astro(self) -> None:
        self.assertRedirects(self.client.get(reverse('login')), '/', fetch_redirect_response=False)
