from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch
from uuid import uuid4
from zipfile import ZipFile

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from modulo.catalogo.models import AtributoProducto, ImagenProducto, Producto
from modulo.informat.services.stock import ServicioInformatError


class CatalogoApiTests(TestCase):
    def setUp(self) -> None:
        self.temporal = TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        self.raiz = Path(self.temporal.name)
        self.override = override_settings(CATALOGO_STORAGE_ROOT=self.raiz)
        self.override.enable()
        self.addCleanup(self.override.disable)
        usuario_modelo = get_user_model()
        self.usuario = usuario_modelo.objects.create_user(username='catalogo-test', password='test-pass')
        permiso = Permission.objects.get(codename='ver_catalogo', content_type__app_label='catalogo')
        self.usuario.user_permissions.add(permiso)
        self.producto = Producto.objects.create(
            sku='16060170', descripcion='Copa de prueba', descripcion_corta='Copa', sincronizado_en=timezone.now(),
        )
        self.imagen = ImagenProducto.objects.create(
            producto=self.producto, numero=1, nombre_origen='16060170_1.jpg',
            original='sku/original.jpg', resolucion_400='sku/400.jpg',
            resolucion_1500='sku/1500.jpg', resolucion_800='sku/800.jpg',
            sha256='a' * 64, portada=True,
        )
        for campo in ('original', 'resolucion_400', 'resolucion_1500', 'resolucion_800'):
            ruta = self.raiz / getattr(self.imagen, campo)
            ruta.parent.mkdir(parents=True, exist_ok=True)
            ruta.write_bytes(b'imagen-de-prueba')
        self.client.force_login(self.usuario)

    def test_listado_y_detalle_exponen_uuid_y_urls_de_imagen(self) -> None:
        Producto.objects.create(
            sku='SIN-IMAGEN', descripcion='No debe mostrarse', sincronizado_en=timezone.now(),
        )
        listado = self.client.get(reverse('catalogo:productos'), {'busqueda': '16060170'})
        self.assertEqual(listado.status_code, 200)
        dato = listado.json()['productos'][0]
        self.assertEqual(dato['public_id'], str(self.producto.public_id))
        self.assertTrue(dato['imagen'].endswith('/thumbnail/'))

        listado_completo = self.client.get(reverse('catalogo:productos'))
        self.assertEqual([item['sku'] for item in listado_completo.json()['productos']], ['16060170'])

        detalle = self.client.get(reverse('catalogo:detalle_producto', kwargs={'public_id': self.producto.public_id}))
        self.assertEqual(detalle.status_code, 200)
        self.assertEqual(detalle.json()['imagenes'][0]['numero'], 1)

    def test_imagen_se_sirve_inline_y_validando_uuid(self) -> None:
        respuesta = self.client.get(reverse('catalogo:imagen', kwargs={
            'public_id': self.producto.public_id, 'numero': 1, 'tamano': 'preview',
        }))
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(b''.join(respuesta.streaming_content), b'imagen-de-prueba')
        self.assertEqual(respuesta['Content-Disposition'].split(';')[0], 'inline')
        miniatura = self.client.get(reverse('catalogo:imagen', kwargs={
            'public_id': self.producto.public_id, 'numero': 1, 'tamano': 'thumbnail',
        }))
        self.assertEqual(miniatura.status_code, 200)
        self.assertEqual(b''.join(miniatura.streaming_content), b'imagen-de-prueba')
        self.assertEqual(self.client.get(reverse('catalogo:detalle_producto', kwargs={'public_id': uuid4()})).status_code, 404)

    def test_descarga_por_resolucion_incluye_las_imagenes_en_zip(self) -> None:
        respuesta = self.client.get(reverse('catalogo:descargar_imagenes_producto', kwargs={
            'public_id': self.producto.public_id,
            'tamano': '800',
        }))
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta['Content-Type'], 'application/zip')
        contenido = b''.join(respuesta.streaming_content)
        with ZipFile(BytesIO(contenido)) as archivo_zip:
            self.assertEqual(archivo_zip.namelist(), ['16060170_1_800x800.jpg'])
            self.assertEqual(archivo_zip.read('16060170_1_800x800.jpg'), b'imagen-de-prueba')

    def test_listado_filtra_por_varios_atributos_y_expone_facetas(self) -> None:
        AtributoProducto.objects.create(producto=self.producto, clave='ATTDOS', codigo='2010', nombre='CRISTAR_')
        AtributoProducto.objects.create(producto=self.producto, clave='ATTTRE', codigo='3020', nombre='MESA')
        respuesta = self.client.get(reverse('catalogo:productos'), {
            'ATTDOS': ['CRISTAR_', 'CHURCHILL'],
            'ATTTRE': 'MESA',
        })
        self.assertEqual([fila['sku'] for fila in respuesta.json()['productos']], ['16060170'])
        query_repetida = self.client.get(
            f"{reverse('catalogo:productos')}?ATTDOS=CRISTAR_&ATTDOS=CHURCHILL&ATTTRE=MESA"
        )
        self.assertEqual([fila['sku'] for fila in query_repetida.json()['productos']], ['16060170'])
        por_nombre_atributo = self.client.get(reverse('catalogo:productos'), {'busqueda': 'cristar'})
        self.assertEqual([fila['sku'] for fila in por_nombre_atributo.json()['productos']], ['16060170'])
        por_codigo_atributo = self.client.get(reverse('catalogo:productos'), {'busqueda': '2010'})
        self.assertEqual([fila['sku'] for fila in por_codigo_atributo.json()['productos']], ['16060170'])
        sin_resultados = self.client.get(reverse('catalogo:productos'), {'ATTDOS': 'OTRA-LINEA'})
        self.assertEqual(sin_resultados.json()['total'], 0)
        facetas = self.client.get(reverse('catalogo:facetas_atributos')).json()['atributos']
        self.assertEqual(facetas[0]['valores'], [{'nombre': 'CRISTAR_', 'cantidad': 1}])

    def test_api_rechaza_usuario_sin_permiso(self) -> None:
        usuario_sin_permiso = get_user_model().objects.create_user(username='sin-permiso', password='test-pass')
        self.client.force_login(usuario_sin_permiso)
        self.assertEqual(self.client.get(reverse('catalogo:productos')).status_code, 403)

    @patch('modulo.catalogo.services.detalle.consultar_producto_venta')
    def test_detalle_ws_se_cachea_y_se_reutiliza(self, consulta: Mock) -> None:
        consulta.return_value = {
            'VENTA': {
                'PRODUCTO_VTA': '16060170', 'DESC_CORTA': 'Copa', 'DESC_LARGA': 'Copa de prueba larga',
                'ESPEC_TECNICAS': 'Vidrio', 'CODIGO_BARRA': ['7700000000001'],
            },
            'EXISTENCIAS': {'ESTADO': 0, 'UNIDADNOM_EXI': 'UNIDAD', 'UNIDADABR_EXI': 'Un',
                            'CLASIFICACION_DES': 'Producto Terminado'},
            'ATRIBUTOS': {'ATTUNO_COD': '1003', 'ATTUNO_DSC': 'DESCONTINUADO'},
            'METRICAS': {'PESO': '0.2000', 'ALTO': '7.9000', 'LARGO': '8.5000', 'ANCHO': '8.5000'},
            'PRECIOS': {'PRECIO_LISTA': '999.00'},
            'STOCK': {'STOCK_ACTUAL': '341'},
        }
        url = reverse('catalogo:detalle_producto', kwargs={'public_id': self.producto.public_id})
        respuesta = self.client.get(url)
        detalle = respuesta.json()['detalle_ws']
        self.assertEqual(detalle['venta']['descripcion_larga'], 'Copa de prueba larga')
        self.assertEqual(detalle['atributos'][0]['nombre'], 'DESCONTINUADO')
        self.assertNotIn('precios', detalle)
        self.assertNotIn('stock', detalle)
        self.assertTrue(AtributoProducto.objects.filter(
            producto=self.producto, clave='ATTUNO', nombre='DESCONTINUADO',
        ).exists())
        consulta.assert_called_once_with('16060170')

        segunda_respuesta = self.client.get(url)
        self.assertEqual(segunda_respuesta.json()['detalle_ws'], detalle)
        consulta.assert_called_once()

    @patch('modulo.catalogo.services.detalle.consultar_producto_venta', side_effect=ServicioInformatError('offline'))
    def test_falla_ws_conserva_detalle_cacheado(self, consulta: Mock) -> None:
        self.producto.detalle_ws = {'venta': {'descripcion_larga': 'Dato almacenado'}}
        self.producto.save(update_fields=['detalle_ws'])
        respuesta = self.client.get(reverse('catalogo:detalle_producto', kwargs={'public_id': self.producto.public_id}))
        self.assertEqual(respuesta.json()['detalle_ws']['venta']['descripcion_larga'], 'Dato almacenado')
