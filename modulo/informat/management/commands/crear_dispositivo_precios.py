from django.conf import settings
from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.db import DatabaseError

from modulo.informat.models import DispositivoPrecios
from modulo.informat.services.precios import lista_existe


class Command(BaseCommand):
    help = 'Crea un token de consulta de precios para un dispositivo y una lista.'

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument('--nombre', required=True)
        parser.add_argument('--lista', required=True, type=int)

    def handle(self, *args: object, **options: object) -> None:
        nombre = options['nombre'].strip()
        codigo = options['lista']
        if not nombre or len(nombre) > 100 or not 0 <= codigo <= 32767:
            raise CommandError('Nombre o código de lista inválido.')
        if 'sqlserver' not in settings.DATABASES:
            raise CommandError('SQL Server no está configurado.')
        try:
            if not lista_existe(codigo):
                raise CommandError('La lista no existe en I-NET.')
        except DatabaseError as exc:
            raise CommandError('No se pudo verificar la lista en I-NET.') from exc
        dispositivo, token = DispositivoPrecios.crear_con_token(nombre, codigo)
        self.stdout.write(f'Dispositivo: {dispositivo.public_id}\nLista: {codigo}\nToken (se muestra una sola vez): {token}')
