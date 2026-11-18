import hashlib
import secrets
from datetime import timedelta
from uuid import UUID

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.db import transaction
from django.utils import timezone

from modulo.inventario.models import Asignacion, Inventario, TokenMovil


def huella(valor: str) -> str:
    return hashlib.sha256(valor.encode('utf-8')).hexdigest()


@transaction.atomic
def crear_capturador(nombre: str) -> TokenMovil:
    identificador = secrets.token_hex(16)
    usuario = get_user_model().objects.create_user(username=f'capturador_{identificador}')
    usuario.set_unusable_password()
    usuario.save(update_fields=['password'])
    usuario.user_permissions.add(Permission.objects.get(content_type__app_label='inventario',
                                                        codename='contar_inventario'))
    return TokenMovil.objects.create(nombre=nombre, usuario=usuario,
                                     token_hash=huella(secrets.token_urlsafe(48)))


def identificar_capturador(token: str) -> TokenMovil | None:
    if not 40 <= len(token) <= 128:
        return None
    dispositivo = TokenMovil.objects.filter(token_hash=huella(token), activo=True,
                                            usuario__is_active=True).select_related('usuario').first()
    if dispositivo is None or dispositivo.usuario_id is None:
        return None
    return dispositivo if secrets.compare_digest(dispositivo.token_hash, huella(token)) else None


@transaction.atomic
def vincular_capturador(codigo: str) -> tuple[TokenMovil, str] | None:
    if not 40 <= len(codigo) <= 128:
        return None
    dispositivo = TokenMovil.objects.select_for_update().filter(vinculacion_hash=huella(codigo), activo=True,
                                                                 vinculacion_vence__gt=timezone.now(),
                                                                 vinculacion_asignacion__isnull=False,
                                                                 usuario__is_active=True).first()
    if dispositivo is None or dispositivo.usuario_id is None:
        return None
    if not secrets.compare_digest(dispositivo.vinculacion_hash or '', huella(codigo)):
        return None
    token = secrets.token_urlsafe(48)
    dispositivo.token_hash = huella(token)
    dispositivo.vinculacion_hash = None
    dispositivo.vinculacion_vence = None
    dispositivo.vinculado_en = timezone.now()
    dispositivo.save(update_fields=['token_hash', 'vinculacion_hash', 'vinculacion_vence', 'vinculado_en'])
    return dispositivo, token


@transaction.atomic
def generar_vinculacion(public_id: UUID, inventario_id: UUID,
                        asignacion_id: UUID | None = None) -> tuple[TokenMovil, Asignacion, str] | None:
    """Emite un código temporal de vinculación para un capturador y su turno.

    ``asignacion_id`` fija el turno concreto: sin él se toma el primero del
    capturador en ese inventario. Se puede reemitir el código (por ejemplo tras
    reinstalar la app); el anterior queda invalidado y el nuevo vence en 10
    minutos y es de un solo uso.
    """
    dispositivo = TokenMovil.objects.select_for_update().filter(public_id=public_id, activo=True,
                                                                 usuario__isnull=False,
                                                                 usuario__is_active=True).first()
    if dispositivo is None:
        return None
    turnos = Asignacion.objects.filter(usuario=dispositivo.usuario, inventario__public_id=inventario_id,
                                        inventario__estado=Inventario.Estado.ABIERTO,
                                        zona__isnull=False).select_related('inventario__bodega', 'zona')
    if asignacion_id is not None:
        turnos = turnos.filter(public_id=asignacion_id)
    turno = turnos.first()
    if turno is None:
        return None
    codigo = secrets.token_urlsafe(32)
    dispositivo.vinculacion_hash = huella(codigo)
    dispositivo.vinculacion_vence = timezone.now() + timedelta(minutes=10)
    dispositivo.vinculacion_asignacion = turno
    dispositivo.save(update_fields=['vinculacion_hash', 'vinculacion_vence', 'vinculacion_asignacion'])
    return dispositivo, turno, codigo
