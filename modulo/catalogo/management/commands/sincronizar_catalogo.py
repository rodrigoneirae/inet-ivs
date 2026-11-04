from django.core.management.base import BaseCommand, CommandError

from modulo.catalogo.services import ErrorSincronizacionCatalogo, sincronizar_imagenes, sincronizar_productos


class Command(BaseCommand):
    help = 'Sincroniza manualmente el maestro de I-NET y/o las imágenes del catálogo.'

    def add_arguments(self, parser) -> None:
        parser.add_argument('--solo', choices=('productos', 'imagenes'), help='Limita la sincronización a una fuente.')

    def handle(self, *args: object, **options: object) -> None:
        solo = options['solo']
        try:
            if solo in (None, 'productos'):
                total = sincronizar_productos()
                self.stdout.write(self.style.SUCCESS(f'Productos sincronizados: {total}'))
            if solo in (None, 'imagenes'):
                total = sincronizar_imagenes()
                self.stdout.write(self.style.SUCCESS(f'Imágenes importadas o actualizadas: {total}'))
        except ErrorSincronizacionCatalogo as exc:
            raise CommandError(str(exc)) from exc
