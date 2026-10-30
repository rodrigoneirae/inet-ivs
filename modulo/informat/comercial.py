"""Acceso al servicio de documentos comerciales de Informat."""

from typing import Any

from django.conf import settings

from .services import ServicioInformatError, _post_json


class AutenticacionComercialError(ServicioInformatError):
    """No se llegó a enviar el documento comercial."""


def insertar_documento(documento: dict[str, Any]) -> dict[str, Any]:
    """Inserta un documento; una respuesta perdida requiere conciliación externa.

    No se reintenta una escritura: el servidor podría haberla completado antes
    de que se interrumpiera la comunicación.
    """
    funcionalidad = getattr(settings, 'WSCOMERCIAL', '')
    if not all((settings.URLTOKEN, settings.EMPRUT, settings.CONID, settings.APLID,
                funcionalidad, settings.URL_WSCOMERCIAL)):
        raise AutenticacionComercialError('Falta configurar el acceso al servicio comercial Informat.')
    try:
        salida = _post_json(settings.URLTOKEN, {'EntradaAut': {
            'EmpRut': settings.EMPRUT, 'ConId': settings.CONID,
            'AplId': settings.APLID, 'FncId': funcionalidad,
        }}).get('SalidaAut')
    except ServicioInformatError as exc:
        raise AutenticacionComercialError('No fue posible autenticar con Informat.') from exc
    if (not isinstance(salida, dict) or salida.get('CodigoError') != 200
            or not isinstance(salida.get('Token'), str) or not salida['Token']):
        raise AutenticacionComercialError('Informat rechazó la autenticación comercial.')
    cuerpo = {**documento, 'Seguridad': {'Token': salida['Token']}}
    return _post_json(settings.URL_WSCOMERCIAL, {'DocumentoComercial': cuerpo})
