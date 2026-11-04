from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.test import TestCase


class GestionPerfilesTests(TestCase):
    def setUp(self) -> None:
        call_command('configurar_perfiles', verbosity=0)
        self.superusuario = get_user_model().objects.create_superuser(
            username='supervisor', password='clave-segura',
        )
        self.usuario = get_user_model().objects.create_user(
            username='operador', password='clave-segura',
        )

    def test_solo_superusuario_puede_listar_y_cambiar_perfiles(self) -> None:
        self.client.force_login(self.usuario)
        self.assertEqual(self.client.get('/api/v1/acceso/perfiles/usuarios/').status_code, 403)
        self.assertEqual(self.client.post('/api/v1/acceso/perfiles/usuario/', {
            'username': self.usuario.username,
            'administrador': 'true',
        }).status_code, 403)
        self.assertEqual(self.client.get('/usuarios/').status_code, 403)

    def test_superusuario_lista_y_asigna_retirar_perfil_sin_exponer_ids(self) -> None:
        self.client.force_login(self.superusuario)
        lista = self.client.get('/api/v1/acceso/perfiles/usuarios/')
        self.assertEqual(lista.status_code, 200)
        self.assertTrue(lista.json()['grupo_configurado'])
        self.assertEqual(lista.json()['usuarios'][0]['username'], 'operador')
        self.assertEqual(lista.json()['usuarios'][0]['perfiles'], [])
        self.assertNotIn('id', lista.json()['usuarios'][0])

        asignar = self.client.post('/api/v1/acceso/perfiles/usuario/', {
            'username': self.usuario.username,
            'perfiles': ['Administrador'],
        })
        self.assertEqual(asignar.status_code, 200)
        grupo = Group.objects.get(name='Administrador')
        self.assertTrue(self.usuario.groups.filter(pk=grupo.pk).exists())

        retirar = self.client.post('/api/v1/acceso/perfiles/usuario/', {
            'username': self.usuario.username,
            'perfiles': [],
        })
        self.assertEqual(retirar.status_code, 200)
        self.assertFalse(self.usuario.groups.filter(pk=grupo.pk).exists())

    def test_no_permite_cambiar_el_perfil_de_un_superusuario(self) -> None:
        self.client.force_login(self.superusuario)
        respuesta = self.client.post('/api/v1/acceso/perfiles/usuario/', {
            'username': self.superusuario.username,
            'perfiles': [],
        })
        self.assertEqual(respuesta.status_code, 400)

    def test_superusuario_crea_asigna_y_elimina_perfil_personalizado(self) -> None:
        self.client.force_login(self.superusuario)
        crear = self.client.post('/api/v1/acceso/perfiles/guardar/', {
            'nombre': 'Consulta catálogo',
            'permisos': ['catalogo.ver_catalogo'],
        })
        self.assertEqual(crear.status_code, 200)
        perfil = next(
            perfil for perfil in self.client.get('/api/v1/acceso/perfiles/').json()['perfiles']
            if perfil['nombre'] == 'Consulta catálogo'
        )
        self.assertEqual(perfil['permisos'], ['catalogo.ver_catalogo'])

        crear_descargas = self.client.post('/api/v1/acceso/perfiles/guardar/', {
            'nombre': 'Descargas catálogo',
            'permisos': ['catalogo.ver_catalogo', 'catalogo.descargar_catalogo'],
        })
        self.assertEqual(crear_descargas.status_code, 200)
        permiso_sin_lectura = self.client.post('/api/v1/acceso/perfiles/guardar/', {
            'nombre': 'Descarga inválida',
            'permisos': ['catalogo.descargar_catalogo'],
        })
        self.assertEqual(permiso_sin_lectura.status_code, 400)

        asignar = self.client.post('/api/v1/acceso/perfiles/usuario/', {
            'username': self.usuario.username,
            'perfiles': [perfil['clave']],
        })
        self.assertEqual(asignar.status_code, 200)
        self.assertTrue(self.usuario.has_perm('catalogo.ver_catalogo'))
        no_eliminar_asignado = self.client.post('/api/v1/acceso/perfiles/eliminar/', {'clave': perfil['clave']})
        self.assertEqual(no_eliminar_asignado.status_code, 409)

        self.client.post('/api/v1/acceso/perfiles/usuario/', {
            'username': self.usuario.username,
            'perfiles': [],
        })
        eliminar = self.client.post('/api/v1/acceso/perfiles/eliminar/', {'clave': perfil['clave']})
        self.assertEqual(eliminar.status_code, 200)
