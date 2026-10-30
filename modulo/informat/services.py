import json
import logging
from urllib.error import URLError
from urllib.parse import urlsplit, urlunsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from django.conf import settings

from .tokens import TokenStoreError, obtener_token

logger = logging.getLogger(__name__)


class ServicioInformatError(Exception):
    pass


class ServicioInformatTimeout(ServicioInformatError):
    pass


class SinRedireccion(HTTPRedirectHandler):
    def redirect_request(self, req: object, fp: object, code: int, msg: str,
                         headers: object, newurl: str) -> None:
        return None


def _post_json(url: str, datos: dict) -> dict:
    partes = urlsplit(url)
    if (partes.scheme not in ('http', 'https') or not partes.hostname
            or partes.username or partes.password or partes.fragment
            or (not settings.DEBUG and partes.scheme != 'https')):
        raise ServicioInformatError('La URL del servicio Informat no es válida.')
    solicitud = Request(url, json.dumps(datos).encode('utf-8'),
                        {'Content-Type': 'application/json', 'Accept': 'application/json'}, method='POST')
    try:
        with build_opener(SinRedireccion()).open(solicitud, timeout=settings.INFORMAT_TIMEOUT) as respuesta:
            contenido = respuesta.read(2_000_001)
        if len(contenido) > 2_000_000:
            raise ServicioInformatError('La respuesta de Informat es demasiado grande.')
        resultado = json.loads(contenido)
        if not isinstance(resultado, dict):
            raise ValueError('Respuesta inesperada')
        return resultado
    except (URLError, TimeoutError, OSError, ValueError) as exc:
        if isinstance(exc, TimeoutError) or (isinstance(exc, URLError) and isinstance(exc.reason, TimeoutError)):
            raise ServicioInformatTimeout('El servicio Informat agotó el tiempo de espera.') from exc
        logger.warning('No se pudo consultar el servicio Informat (%s)', type(exc).__name__)
        raise ServicioInformatError('No fue posible comunicarse con Informat.') from exc


def _renovar_token() -> str:
    if not all((settings.URLTOKEN, settings.EMPRUT, settings.CONID, settings.APLID, settings.WSPRODUCTOSVENTAS)):
        raise ServicioInformatError('Falta configurar el acceso a Informat.')
    try:
        salida = _post_json(settings.URLTOKEN, {'EntradaAut': {
            'EmpRut': settings.EMPRUT, 'ConId': settings.CONID,
            'AplId': settings.APLID, 'FncId': settings.WSPRODUCTOSVENTAS,
        }}).get('SalidaAut')
    except ServicioInformatTimeout as exc:
        logger.warning('Tiempo de espera agotado al autenticar con Informat')
        raise ServicioInformatTimeout('La autenticación de Informat no respondió a tiempo.') from exc
    if not isinstance(salida, dict) or salida.get('CodigoError') != 200 or not isinstance(salida.get('Token'), str) or not salida['Token']:
        raise ServicioInformatError('Informat rechazó la autenticación.')
    return salida['Token']


def _token_rechazado(estado: object) -> bool:
    if not isinstance(estado, dict) or estado.get('Tipo') != 1:
        return False
    errores = estado.get('Errores')
    if not isinstance(errores, list):
        return False
    return any(isinstance(error, dict) and isinstance(error.get('ErrorDescripcion'), str)
               and '413' in error['ErrorDescripcion'] and 'token' in error['ErrorDescripcion'].lower()
               for error in errores)


def consultar_stock(producto: str, bodega: str) -> list[dict]:
    try:
        token = obtener_token(_renovar_token)
    except TokenStoreError as exc:
        raise ServicioInformatError(str(exc)) from exc
    url = settings.URL_WSPRODUCTOSVENTAS
    if not url and settings.URL_WSCOMERCIAL:
        partes = urlsplit(settings.URL_WSCOMERCIAL)
        url = urlunsplit((partes.scheme, partes.netloc, partes.path.rsplit('/', 1)[0] + '/wsProductosVentas', '', ''))
    if not url:
        raise ServicioInformatError('Falta configurar la URL de productos Informat.')
    filtros = [{'Opcion': 0, 'Nombre': 'BODEGA', 'Dato': bodega}]
    if producto:
        filtros.append({'Opcion': 0, 'Nombre': 'PRODUCTO', 'Dato': producto})
    def consultar(token_actual: str) -> dict:
        try:
            return _post_json(url, {'ProcesoFiltros': {'Token': token_actual, 'Accion': 'GET', 'Filtros': filtros}})
        except ServicioInformatTimeout as exc:
            logger.warning('Tiempo de espera agotado al consultar productos en Informat')
            raise ServicioInformatTimeout('El servicio de productos Informat no respondió a tiempo.') from exc

    respuesta = consultar(token)
    if _token_rechazado(respuesta.get('RespuestaProceso')):
        try:
            token = obtener_token(_renovar_token, rechazado=token)
        except TokenStoreError as exc:
            raise ServicioInformatError(str(exc)) from exc
        respuesta = consultar(token)
    estado = respuesta.get('RespuestaProceso')
    if not isinstance(estado, dict) or estado.get('Tipo') != 0:
        raise ServicioInformatError('Informat no pudo completar la consulta de stock.')
    productos = respuesta.get('Productos')
    if not isinstance(productos, list) or any(not isinstance(item, dict) for item in productos):
        raise ServicioInformatError('Informat devolvió una respuesta de productos inesperada.')
    return productos
