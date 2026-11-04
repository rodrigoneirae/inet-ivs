import time

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from django.utils import timezone

from modulo.catalogo.models import Producto
from modulo.catalogo.services.detalle import DETALLE_VIGENTE_POR, obtener_detalle_ws


class Command(BaseCommand):
    help = 'Precarga gradualmente atributos I-NET para productos del catálogo que tienen imágenes.'

    def add_arguments(self, parser) -> None:
        parser.add_argument('--pausa', type=float, default=1.0,
                            help='Segundos entre consultas a la WS (por defecto: 1).')
        parser.add_argument('--limite', type=int, default=0,
                            help='Máximo de productos a procesar; 0 procesa todos los vencidos.')

    def handle(self, *args: object, **options: object) -> None:
        pausa = options['pausa']
        limite = options['limite']
        if pausa < 0 or pausa > 60:
            raise CommandError('--pausa debe estar entre 0 y 60 segundos.')
        if limite < 0:
            raise CommandError('--limite no puede ser negativo.')

        ahora = timezone.now()
        productos = Producto.objects.filter(imagenes__isnull=False).distinct().order_by('sku')
        productos = productos.filter(
            Q(detalle_ws_actualizado_en__isnull=True)
            | Q(detalle_ws_actualizado_en__lte=ahora - DETALLE_VIGENTE_POR)
            | Q(atributos_catalogo__isnull=True)
        ).distinct()
        if limite:
            productos = productos[:limite]
        total = productos.count()
        procesados = 0
        con_atributos = 0
        fallidos = 0
        for producto in productos.iterator(chunk_size=100):
            actualizado_antes = producto.detalle_ws_actualizado_en
            detalle = obtener_detalle_ws(producto)
            producto.refresh_from_db(fields=['detalle_ws_actualizado_en'])
            if producto.detalle_ws_actualizado_en != actualizado_antes:
                procesados += 1
                if detalle.get('atributos'):
                    con_atributos += 1
            else:
                fallidos += 1
            if procesados and procesados % 100 == 0:
                self.stdout.write(f'Consultados: {procesados}/{total}; con atributos: {con_atributos}; fallidos: {fallidos}')
            if pausa:
                time.sleep(pausa)

        self.stdout.write(self.style.SUCCESS(
            f'Carga terminada. Consultados: {procesados}; con atributos: {con_atributos}; '
            f'fallidos/reintentar: {fallidos}.'
        ))
