from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from .models import ReglaDocumentoInet
from .reglas_documento import buscar_regla


class ReglasDocumentoTests(TestCase):
    def test_prioridad_canal_y_regla_general(self) -> None:
        general = ReglaDocumentoInet.objects.create(tipo='factura', canal='', codigo=10, descripcion='General')
        especifica = ReglaDocumentoInet.objects.create(tipo='factura', canal='SHOPIFY', codigo=11, descripcion='Tienda')
        self.assertEqual(buscar_regla('factura', ' shopify '), especifica)
        self.assertEqual(buscar_regla('factura', 'OTRO'), general)
        especifica.activa = False
        especifica.save(update_fields=['activa'])
        self.assertEqual(buscar_regla('factura', 'SHOPIFY'), general)
        self.assertIsNone(buscar_regla('boleta', 'SHOPIFY'))
        self.assertIsNone(buscar_regla('invalido', 'SHOPIFY'))

    def test_base_de_datos_impide_reglas_ambiguas_y_codigos_invalidos(self) -> None:
        ReglaDocumentoInet.objects.create(tipo='factura', canal='SHOPIFY', codigo=11, descripcion='Tienda')
        for valores in ({'tipo': 'factura', 'canal': 'shopify', 'codigo': 12},
                        {'tipo': 'boleta', 'canal': '', 'codigo': 0},
                        {'tipo': 'otro', 'canal': '', 'codigo': 20}):
            with self.subTest(valores=valores), self.assertRaises(IntegrityError), transaction.atomic():
                ReglaDocumentoInet.objects.create(descripcion='Prueba', **valores)

    def test_admin_requiere_permiso_y_usa_uuid(self) -> None:
        regla = ReglaDocumentoInet.objects.create(tipo='factura', codigo=11, descripcion='General')
        usuario = get_user_model().objects.create_user(username='operador', is_staff=True)
        self.client.force_login(usuario)
        url = reverse('admin:anymarket_regladocumentoinet_change', args=[regla.uuid])
        self.assertEqual(self.client.get(url).status_code, 403)
        usuario.user_permissions.add(Permission.objects.get(content_type__app_label='anymarket',
                                                            codename='change_regladocumentoinet'))
        self.client.force_login(get_user_model().objects.get(pk=usuario.pk))
        self.assertEqual(self.client.get(url).status_code, 200)
