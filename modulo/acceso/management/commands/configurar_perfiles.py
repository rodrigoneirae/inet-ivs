from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand, CommandError


PERMISOS_ADMINISTRADOR = (
    ('anymarket', 'view_pedido'),
    ('anymarket', 'change_pedido'),
    ('informat', 'consultar_stock'),
    ('informat', 'consultar_productos_inet'),
    ('informat', 'administrar_token'),
    ('catalogo', 'ver_catalogo'),
    ('catalogo', 'descargar_catalogo'),
)


class Command(BaseCommand):
    help = 'Crea o actualiza el grupo Administrador con todos los permisos operativos.'

    def handle(self, *args: object, **options: object) -> None:
        permisos: list[Permission] = []
        for app_label, codename in PERMISOS_ADMINISTRADOR:
            try:
                permisos.append(Permission.objects.get(
                    content_type__app_label=app_label,
                    codename=codename,
                ))
            except Permission.DoesNotExist as exc:
                raise CommandError(
                    f'No existe el permiso {app_label}.{codename}; ejecuta primero las migraciones.'
                ) from exc

        grupo, creado = Group.objects.get_or_create(name='Administrador')
        grupo.permissions.set(permisos)
        accion = 'Creado' if creado else 'Actualizado'
        self.stdout.write(self.style.SUCCESS(
            f'{accion} el grupo Administrador con {len(permisos)} permisos operativos.'
        ))
