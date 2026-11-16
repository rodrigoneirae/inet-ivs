import base64
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

from django.test import SimpleTestCase, override_settings

from ..services.imagenes import MAX_BYTES_PORTADA, obtener_portada_base64


class PortadaPrecioTests(SimpleTestCase):
    def test_portada_del_sku_y_fallback_sin_imagen(self) -> None:
        with TemporaryDirectory() as temporal, override_settings(CATALOGO_STORAGE_ROOT=temporal):
            Path(temporal, 'portada.jpg').write_bytes(b'contenido-imagen')
            with patch('modulo.catalogo.services.imagenes.ImagenProducto.objects.filter') as filtro:
                filtro.return_value.only.return_value.order_by.return_value.first.return_value = Mock(
                    resolucion_400='portada.jpg', resolucion_800='otra.jpg',
                )
                self.assertEqual(obtener_portada_base64('SKU-1'), base64.b64encode(b'contenido-imagen').decode())
                filtro.assert_called_once_with(producto__sku='SKU-1')
                filtro.return_value.only.return_value.order_by.return_value.first.return_value = None
                self.assertIsNone(obtener_portada_base64('SKU-2'))

    def test_rutas_fuera_del_catalogo_y_archivos_grandes_no_se_exponen(self) -> None:
        with TemporaryDirectory() as temporal, override_settings(CATALOGO_STORAGE_ROOT=temporal):
            archivo = Path(temporal, 'grande.jpg')
            archivo.write_bytes(b'x' * (MAX_BYTES_PORTADA + 1))
            with patch('modulo.catalogo.services.imagenes.ImagenProducto.objects.filter') as filtro:
                imagen = filtro.return_value.only.return_value.order_by.return_value.first.return_value
                imagen.resolucion_400 = '../secreto.txt'
                self.assertIsNone(obtener_portada_base64('SKU'))
                imagen.resolucion_400 = 'grande.jpg'
                self.assertIsNone(obtener_portada_base64('SKU'))
