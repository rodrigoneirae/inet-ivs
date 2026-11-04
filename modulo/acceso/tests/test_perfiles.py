from django.contrib.auth.models import Group, Permission
from django.core.management import call_command
from django.test import TestCase


class ConfigurarPerfilesTests(TestCase):
    def test_crea_grupo_administrador_con_permisos_de_modulos(self) -> None:
        call_command('configurar_perfiles')

        grupo = Group.objects.get(name='Administrador')
        permisos = set(grupo.permissions.values_list('content_type__app_label', 'codename'))
        self.assertEqual(permisos, {
            ('anymarket', 'view_pedido'),
            ('anymarket', 'change_pedido'),
            ('informat', 'consultar_stock'),
            ('informat', 'consultar_productos_inet'),
            ('informat', 'administrar_token'),
            ('catalogo', 'ver_catalogo'),
            ('catalogo', 'descargar_catalogo'),
        })

    def test_actualiza_permisos_del_grupo_de_forma_idempotente(self) -> None:
        grupo = Group.objects.create(name='Administrador')
        grupo.permissions.add(Permission.objects.get(
            content_type__app_label='catalogo', codename='ver_catalogo',
        ))

        call_command('configurar_perfiles')
        call_command('configurar_perfiles')

        self.assertEqual(grupo.permissions.count(), 7)
