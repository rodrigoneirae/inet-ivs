"""Cola con reclamación atómica antes de cualquier envío externo."""

import logging
from datetime import timedelta
from uuid import UUID

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from modulo.informat.services.clientes import ConsultaClienteError
from modulo.informat.services.comercial import crear_documento, validar_cliente_documento

from ..models import EncPedidoApi
from .auditoria import cifrar
from .documento import preparar_documento

logger = logging.getLogger(__name__)


def procesar_pedido(uuid_pedido: UUID) -> bool:
    if not settings.PEDIDOS_INET_ENABLED:
        return False
    with transaction.atomic():
        pedido = EncPedidoApi.objects.select_for_update().get(uuid=uuid_pedido)
        if pedido.estado_envio != 'P':
            return False
        # Una fila que ya tuvo un envío no se puede reactivar cambiando solo su estado.
        if pedido.api_documento_numero or pedido.solicitud_cifrada:
            pedido.estado_envio = 'RV'
            pedido.api_documento_error = 'Existe un envío anterior. Conciliar en I-NET antes de intervenir.'
            pedido.save(update_fields=['estado_envio', 'api_documento_error', 'updated_at'])
            return False
        detalles = list(pedido.detalles.select_for_update().all()[:1001])
        try:
            documento = preparar_documento(pedido, detalles)
        except ValidationError as exc:
            pedido.estado_envio = 'ER'
            pedido.api_documento_error = '; '.join(exc.messages)[:255]
            pedido.save(update_fields=['estado_envio', 'api_documento_error', 'updated_at'])
            return False
        pedido.estado_envio = 'PR'
        pedido.procesando_desde = timezone.now()
        pedido.save(update_fields=['estado_envio', 'procesando_desde', 'updated_at'])

    # Sin transacciones abiertas durante las llamadas SQL Server/HTTP.
    try:
        validar_cliente_documento(documento)
    except ConsultaClienteError:
        EncPedidoApi.objects.filter(uuid=uuid_pedido, estado_envio='PR').update(
            estado_envio='ER', api_documento_error='No se pudo validar el cliente en I-NET.',
            updated_at=timezone.now())
        return False

    # Persistir ANTES de llamar al servicio. Un fallo posterior nunca habilita un reenvío.
    solicitud = cifrar(documento)
    reclamado = EncPedidoApi.objects.filter(uuid=uuid_pedido, estado_envio='PR').update(
        solicitud_cifrada=solicitud, updated_at=timezone.now())
    if not reclamado:
        return False
    try:
        resultado = crear_documento(documento)
        respuesta = cifrar(resultado.respuesta) if resultado.respuesta is not None else ''
    except Exception:
        # No registrar la excepción: puede contener datos del cliente o del servicio.
        logger.error('Resultado incierto en la cola I-NET para %s.', uuid_pedido)
        EncPedidoApi.objects.filter(uuid=uuid_pedido, estado_envio='PR').update(
            estado_envio='RV', api_documento_error='Resultado incierto. Revisar en I-NET; no reenviar.',
            updated_at=timezone.now())
        return False

    estado = {'creado': 'E', 'error': 'ER', 'revision': 'RV'}.get(resultado.estado, 'RV')
    with transaction.atomic():
        pedido = EncPedidoApi.objects.select_for_update().get(uuid=uuid_pedido)
        # Una conciliación automática por antigüedad puede haberlo pasado a RV.
        if pedido.estado_envio not in ('PR', 'RV'):
            return False
        pedido.estado_envio = estado
        pedido.api_documento_numero = resultado.numero[:255]
        pedido.api_documento_codigo = resultado.tipo_documento[:255]
        pedido.api_documento_error = '' if estado == 'E' else {
            'ER': 'I-NET rechazó el documento o su autenticación. Revisar antes de reenviar.',
            'RV': 'Resultado incierto. Revisar en I-NET; no reenviar.',
        }[estado]
        pedido.respuesta_cifrada = respuesta
        if resultado.respuesta:
            proceso = resultado.respuesta.get('RespuestaProceso', {})
            datos = proceso.get('Datos', []) if isinstance(proceso, dict) else []
            if isinstance(datos, list):
                for dato in datos:
                    if not isinstance(dato, dict):
                        continue
                    campo = {'DOCUMENTO_ATENCION': 'api_documento_atencion',
                             'DOCUMENTO_ESTADO': 'api_documento_estado'}.get(dato.get('NOMBRE'))
                    if campo:
                        setattr(pedido, campo, str(dato.get('DATO', ''))[:255])
        pedido.save(update_fields=['estado_envio', 'api_documento_numero', 'api_documento_codigo',
                                   'api_documento_error', 'respuesta_cifrada', 'api_documento_atencion',
                                   'api_documento_estado', 'updated_at'])
        if estado == 'E':
            pedido.detalles.update(estado_envio='E', updated_at=timezone.now())
    logger.info('Cola I-NET: documento %s finalizó con estado %s.', uuid_pedido, estado)
    return estado == 'E'


def procesar_pendientes(limite: int = 20) -> int:
    if not settings.PEDIDOS_INET_ENABLED:
        return 0
    if not 1 <= limite <= 100:
        raise ValueError('El límite debe estar entre 1 y 100.')
    # Una tarea muerta pudo haber enviado el documento: nunca volver a P automáticamente.
    EncPedidoApi.objects.filter(estado_envio='PR', procesando_desde__lt=timezone.now() - timedelta(minutes=10)).update(
        estado_envio='RV', api_documento_error='Procesamiento interrumpido. Conciliar en I-NET antes de reenviar.',
        updated_at=timezone.now())
    pendientes = list(EncPedidoApi.objects.filter(estado_envio='P').values_list('uuid', flat=True)[:limite])
    enviados = 0
    for uuid_pedido in pendientes:
        try:
            enviados += int(procesar_pedido(uuid_pedido))
        except EncPedidoApi.DoesNotExist:
            continue
    return enviados
