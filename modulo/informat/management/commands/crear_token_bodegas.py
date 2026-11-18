from argparse import ArgumentParser

from django.core.management.base import BaseCommand, CommandError

from modulo.informat.models import AplicacionBodegas


class Command(BaseCommand):
    help = 'Emite un token de lectura de bodegas para una aplicación (solo se muestra una vez).'

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument('--nombre', required=True, help='Nombre de la aplicación autorizada.')

    def handle(self, *args: object, **options: object) -> None:
        nombre = str(options['nombre']).strip()
        if not nombre or len(nombre) > 100:
            raise CommandError('El nombre debe contener entre 1 y 100 caracteres.')
        aplicacion, token = AplicacionBodegas.crear_con_token(nombre)
        self.stdout.write(f'ID de aplicación: {aplicacion.public_id}')
        self.stdout.write(f'Token (copiar ahora): {token}')
