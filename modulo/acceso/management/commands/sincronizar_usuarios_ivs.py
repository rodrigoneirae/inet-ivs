from django.core.management.base import BaseCommand

from modulo.acceso.services import sincronizar_usuarios


class Command(BaseCommand):
    help = 'Importa y actualiza los usuarios de IVS_SAT.'

    def handle(self, *args: object, **options: object) -> None:
        sincronizados, omitidos = sincronizar_usuarios()
        self.stdout.write(f'Sincronizados: {sincronizados}. Omitidos: {omitidos}.')
