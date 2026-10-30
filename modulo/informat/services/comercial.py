"""Acceso al servicio de documentos comerciales de Informat."""

import logging
import re
from dataclasses import dataclass
from typing import Any

from django.conf import settings

from .stock import ServicioInformatError, _post_json
from .clientes import ConsultaClienteError, existe_cliente

logger = logging.getLogger(__name__)


class AutenticacionComercialError(ServicioInformatError):
    """No se llegó a enviar el documento comercial."""


@dataclass(frozen=True)
class ResultadoComercial:
    estado: str
    detalle: str = ''
    numero: str = ''
    tipo_documento: str = ''
    respuesta: dict[str, Any] | None = None


def validar_cliente_documento(documento: dict[str, Any]) -> None:
    """Comprueba el cliente del documento antes de enviar a Informat."""
    encabezado = documento.get('Encabezado')
    cliente = encabezado.get('Cliente') if isinstance(encabezado, dict) else None
    if not isinstance(cliente, dict) or 'ClienteCodigo' not in cliente:
        raise ConsultaClienteError('El documento no contiene un cliente válido.')
    codigo = cliente['ClienteCodigo']
    secuencia = cliente.get('ClienteSecuencia')
    if not isinstance(secuencia, int) or isinstance(secuencia, bool):
        raise ConsultaClienteError('La secuencia del cliente no es válida.')
    if not existe_cliente(str(codigo), secuencia):
        raise ConsultaClienteError('El cliente no existe en I-NET. Créalo manualmente antes de reintentar.')


def crear_documento(documento: dict[str, Any]) -> ResultadoComercial:
    """Envía un documento preparado y clasifica la respuesta de I-NET.

    El llamador debe persistir la solicitud antes del envío, validar el cliente
    y evitar reintentos cuando el resultado sea incierto.
    """
    try:
        respuesta = insertar_documento(documento)
    except AutenticacionComercialError as exc:
        return ResultadoComercial('error', str(exc))
    except ServicioInformatError:
        logger.warning('Resultado incierto al enviar un documento comercial a I-NET.')
        return ResultadoComercial('revision', 'No se recibió una respuesta confirmada. Verifica la referencia en I-NET antes de volver a enviar.')
    resultado = respuesta.get('RespuestaProceso')
    if isinstance(resultado, dict) and resultado.get('Tipo') == 1:
        errores = resultado.get('Errores')
        mensajes = [str(e.get('ErrorDescripcion', 'Error de I-NET')) for e in errores
                    if isinstance(e, dict)] if isinstance(errores, list) else []
        texto = '; '.join(mensajes) or 'I-NET rechazó el documento.'
        return ResultadoComercial('error', re.sub(r'\b[0-9a-fA-F]{32,}\b', '[dato reservado]', texto),
                                  respuesta=respuesta)
    datos = resultado.get('Datos') if isinstance(resultado, dict) and resultado.get('Tipo') == 0 else None
    numero = next((str(d.get('DATO')) for d in datos if isinstance(d, dict)
                   and d.get('NOMBRE') == 'DOCUMENTO_NUMERO' and d.get('DATO') is not None), '') if isinstance(datos, list) else ''
    if not numero:
        return ResultadoComercial('revision', 'I-NET no devolvió un número de documento válido; verifica la referencia.',
                                  respuesta=respuesta)
    tipo = next((str(d.get('DATO')) for d in datos if isinstance(d, dict)
                 and d.get('NOMBRE') == 'DOCUMENTO_CODIGO' and d.get('DATO') is not None), '')
    return ResultadoComercial('creado', numero=numero, tipo_documento=tipo, respuesta=respuesta)


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
