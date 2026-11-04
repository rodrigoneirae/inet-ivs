from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import SimpleTestCase
from PIL import Image

from modulo.catalogo.models import ImagenProducto
from modulo.catalogo.services.sincronizacion import (
    PATRON_IMAGEN,
    _guardar_derivada,
    imagen_disponible_local,
    normalizar_texto,
)
from modulo.catalogo.services.detalle import normalizar_detalle_ws


class ImportacionImagenTests(SimpleTestCase):
    def test_normaliza_espacios_de_relleno_del_sku(self) -> None:
        self.assertEqual(normalizar_texto('16060170    '), '16060170')

    def test_normaliza_campos_de_ficha_y_omite_datos_internos(self) -> None:
        detalle = normalizar_detalle_ws({
            'VENTA': {'DESC_LARGA': 'Copa', 'CODIGO_BARRA': ['77001']},
            'ATRIBUTOS': {'ATTUNO_COD': '1003', 'ATTUNO_DSC': 'DESCONTINUADO'},
            'METRICAS': {'PESO': '0.2000'},
            'PRECIOS': {'PRECIO_LISTA': '999'},
            'STOCK': {'STOCK_ACTUAL': '10'},
        })
        self.assertEqual(detalle['venta']['descripcion_larga'], 'Copa')
        self.assertEqual(detalle['atributos'], [
            {'clave': 'ATTUNO', 'codigo': '1003', 'nombre': 'DESCONTINUADO'},
        ])
        self.assertEqual(detalle['metricas']['peso'], '0.2000')
        self.assertNotIn('precios', detalle)
        self.assertNotIn('stock', detalle)

    def test_patron_separa_sku_y_numero_final(self) -> None:
        coincidencia = PATRON_IMAGEN.fullmatch('SKU_CON_GUION_12.PNG')
        self.assertIsNotNone(coincidencia)
        assert coincidencia is not None
        self.assertEqual(coincidencia.group('sku'), 'SKU_CON_GUION')
        self.assertEqual(coincidencia.group('numero'), '12')
        self.assertIsNone(PATRON_IMAGEN.fullmatch('sin_sufijo.png'))

    def test_derivada_es_cuadrada_sin_deformar_fuente(self) -> None:
        with TemporaryDirectory() as temporal:
            origen = Path(temporal) / 'origen.png'
            destino = Path(temporal) / 'salida.jpg'
            Image.new('RGB', (320, 180), color='red').save(origen)
            _guardar_derivada(origen, destino, 800)
            with Image.open(destino) as imagen:
                self.assertEqual(imagen.size, (800, 800))
                self.assertEqual(imagen.getpixel((400, 20)), (255, 255, 255))

    def test_detecta_archivos_ausentes_en_almacenamiento_local(self) -> None:
        with TemporaryDirectory() as temporal:
            raiz = Path(temporal)
            imagen = ImagenProducto(
                original='sku/foto.jpg',
                resolucion_400='sku/foto_400.jpg',
                resolucion_1500='sku/foto_1500.jpg',
                resolucion_800='sku/foto_800.jpg',
            )
            self.assertFalse(imagen_disponible_local(raiz, imagen))
            for ruta in (imagen.original, imagen.resolucion_400, imagen.resolucion_1500, imagen.resolucion_800):
                destino = raiz / ruta
                destino.parent.mkdir(parents=True, exist_ok=True)
                destino.touch()
            self.assertTrue(imagen_disponible_local(raiz, imagen))
