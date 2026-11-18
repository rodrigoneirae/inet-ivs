import uuid
from argparse import ArgumentParser

from django.core.management.base import BaseCommand, CommandError

from modulo.informat.models import AplicacionBodegas


class Command(BaseCommand):
    help = 'Revoca un token de bodegas por su UUID público.'

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument('aplicacion', help='UUID público generado al crear el token.')

    def handle(self, *args: object, **options: object) -> None:
        try:
            identificador = uuid.UUID(str(options['aplicacion']))
        except ValueError as exc:
            raise CommandError('UUID inválido.') from exc
        if not AplicacionBodegas.objects.filter(public_id=identificador, activa=True).update(activa=False):
            raise CommandError('No se encontró una aplicación activa con ese UUID.')
        self.stdout.write('Token revocado.')
