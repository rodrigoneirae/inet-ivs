from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import SimpleTestCase
from PIL import Image

from modulo.catalogo.services.sincronizacion import PATRON_IMAGEN, _guardar_derivada, normalizar_texto


class ImportacionImagenTests(SimpleTestCase):
    def test_normaliza_espacios_de_relleno_del_sku(self) -> None:
        self.assertEqual(normalizar_texto('16060170    '), '16060170')

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
