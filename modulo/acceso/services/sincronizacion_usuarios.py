import logging
from collections import Counter
from dataclasses import dataclass

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser
from django.db import connections, transaction

from ..models import UsuarioOrigen

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RegistroOrigen:
    identificador: int
    nombre: str
    clave: str
    correo: str


def obtener_registros(nombre: str | None = None) -> list[RegistroOrigen]:
    """Read the source in one query; never write to the external database."""
    with connections['ivs_sat'].cursor() as cursor:
        sql = 'SELECT "ID", "USUARIO", "CONTRASENA", "CORREO" FROM public.ivs_sysusuarios'
        if nombre is not None:
            sql += ' WHERE "USUARIO" = %s'
            cursor.execute(sql, [nombre])
        else:
            cursor.execute(sql)
        return [RegistroOrigen(pk, nombre, clave, correo or '') for pk, nombre, clave, correo in cursor.fetchall()]


def registros_validos(registros: list[RegistroOrigen]) -> list[RegistroOrigen]:
    nombres = Counter(r.nombre for r in registros)
    max_nombre = get_user_model()._meta.get_field('username').max_length
    max_correo = get_user_model()._meta.get_field('email').max_length
    return [r for r in registros if isinstance(r.nombre, str) and r.nombre and
            len(r.nombre) <= max_nombre and nombres[r.nombre] == 1 and
            isinstance(r.clave, str) and r.clave and len(r.correo) <= max_correo]


@transaction.atomic
def sincronizar_registro(registro: RegistroOrigen) -> AbstractBaseUser | None:
    User = get_user_model()
    enlace = UsuarioOrigen.objects.select_for_update().select_related('usuario').filter(
        identificador_origen=registro.identificador
    ).first()
    if enlace:
        usuario = enlace.usuario
        if User.objects.exclude(pk=usuario.pk).filter(username=registro.nombre).exists():
            logger.warning('Conflicto de nombre al sincronizar una cuenta de IVS_SAT')
            return None
    else:
        if User.objects.filter(username=registro.nombre).exists():
            logger.warning('Una cuenta local impide importar un usuario de IVS_SAT')
            return None
        usuario = User(username=registro.nombre)
        usuario.set_unusable_password()
        usuario.save()
        UsuarioOrigen.objects.create(usuario=usuario, identificador_origen=registro.identificador)

    usuario.username = registro.nombre
    usuario.email = registro.correo
    if not usuario.check_password(registro.clave):
        usuario.set_password(registro.clave)
    usuario.save(update_fields=['username', 'email', 'password'])
    return usuario


def sincronizar_usuarios() -> tuple[int, int]:
    registros = obtener_registros()
    validos = registros_validos(registros)
    sincronizados = 0
    for registro in validos:
        if sincronizar_registro(registro) is not None:
            sincronizados += 1
    return sincronizados, len(registros) - sincronizados
