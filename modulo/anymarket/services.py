import json
import logging
from datetime import datetime, time, timedelta
from typing import Any, Iterator
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener
from zoneinfo import ZoneInfo

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import connection, transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from .models import Pedido, Sincronizacion

logger = logging.getLogger(__name__)
INICIO = datetime(2026, 10, 27)
PAGADO = 'PAID_WAITING_SHIP'
URLS = {
    'sandbox': 'https://sandbox-api.anymarket.com.br/v2',
    'production': 'https://api.anymarket.com.br/v2',
}


class AnyMarketError(Exception):
    pass


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req: Request, fp: Any, code: int, msg: str,
                         headers: Any, newurl: str) -> None:
        return None


def consultar_pedidos(filtros: dict[str, str]) -> Iterator[dict[str, Any]]:
    if not settings.ANYMARKET_TOKEN or not settings.ANYMARKET_PLATFORM:
        raise ImproperlyConfigured('Configura ANYMARKET_TOKEN y ANYMARKET_PLATFORM.')
    if settings.ANYMARKET_ENVIRONMENT not in URLS:
        raise ImproperlyConfigured('ANYMARKET_ENVIRONMENT debe ser sandbox o production.')
    offset = 0
    while True:
        params = {**filtros, 'limit': '100', 'offset': str(offset)}
        request = Request(
            f"{URLS[settings.ANYMARKET_ENVIRONMENT]}/orders?{urlencode(params)}",
            headers={'gumgaToken': settings.ANYMARKET_TOKEN, 'platform': settings.ANYMARKET_PLATFORM,
                     'Accept': 'application/json'},
        )
        try:
            with build_opener(NoRedirect()).open(request, timeout=30) as response:
                data = json.load(response)
        except HTTPError as exc:
            raise AnyMarketError(f'AnyMarket respondió HTTP {exc.code}.') from exc
        except (URLError, TimeoutError, ValueError) as exc:
            raise AnyMarketError('No se pudo consultar AnyMarket.') from exc
        if not isinstance(data, dict) or not isinstance(data.get('content'), list):
            raise AnyMarketError('Respuesta de pedidos inválida.')
        content = data['content']
        yield from content
        page = data.get('page')
        if isinstance(page, dict) and isinstance(page.get('totalPages'), int) and isinstance(page.get('number'), int):
            if page['number'] >= page['totalPages']:
                break
        else:
            links = data.get('links')
            if not isinstance(links, list):
                raise AnyMarketError('Paginación de AnyMarket inválida.')
            if not any(isinstance(link, dict) and link.get('rel') == 'next' for link in links):
                break
        if not content:
            raise AnyMarketError('Página vacía con enlace siguiente.')
        offset += len(content)


def guardar_pedido(datos: dict[str, Any], inicio: datetime) -> None:
    if not isinstance(datos, dict):
        raise AnyMarketError('Pedido inválido.')
    identificador, estado = datos.get('id'), datos.get('status')
    fecha = parse_datetime(datos.get('createdAt', '')) if isinstance(datos.get('createdAt'), str) else None
    if (not isinstance(identificador, int) or isinstance(identificador, bool) or identificador <= 0
            or not isinstance(estado, str) or not estado or len(estado) > 64
            or fecha is None or timezone.is_naive(fecha)):
        raise AnyMarketError('Pedido con identificador, estado o fecha inválidos.')
    if fecha < inicio:
        return
    existente = Pedido.objects.filter(anymarket_id=identificador).exists()
    if estado == PAGADO or existente:
        Pedido.objects.update_or_create(
            anymarket_id=identificador,
            defaults={'creado_en': fecha, 'estado': estado, 'datos': datos},
        )


def procesar_bloques(filtros: dict[str, str], inicio: datetime) -> None:
    lote: list[dict[str, Any]] = []
    for datos in consultar_pedidos(filtros):
        lote.append(datos)
        if len(lote) == 100:
            with transaction.atomic():
                for pedido in lote:
                    guardar_pedido(pedido, inicio)
            lote.clear()
    if lote:
        with transaction.atomic():
            for pedido in lote:
                guardar_pedido(pedido, inicio)


def ejecutar_sincronizacion(reconciliacion: bool = False) -> None:
    inicio = timezone.make_aware(datetime.combine(INICIO.date(), time.min), ZoneInfo(settings.ANYMARKET_TIME_ZONE))
    # PostgreSQL session lock covers all runs without holding an open transaction over HTTP.
    with connection.cursor() as db:
        db.execute('SELECT pg_try_advisory_lock(%s)', [731984601241])
        adquirido = db.fetchone()[0]
    if not adquirido:
        logger.info('Sincronización AnyMarket omitida: otra ejecución está activa.')
        if reconciliacion:
            raise AnyMarketError('Otra sincronización está activa; reintentar reconciliación.')
        return
    try:
        clave = 'reconciliacion' if reconciliacion else 'pedidos'
        control, _ = Sincronizacion.objects.get_or_create(clave=clave)
        ahora = timezone.now()
        control.ultimo_inicio = ahora
        control.save(update_fields=['ultimo_inicio'])
        try:
            if reconciliacion:
                cursor = max(inicio, ahora - timedelta(days=7))
                while cursor < ahora:
                    fin = min(cursor + timedelta(days=6), ahora)
                    procesar_bloques({'updatedAfter': cursor.isoformat(), 'updatedBefore': fin.isoformat()}, inicio)
                    cursor = fin
            else:
                if control.actualizado_hasta is None:
                    if control.carga_inicial_inicio is None:
                        control.carga_inicial_inicio = ahora
                        control.carga_inicial_hasta = inicio
                        control.save(update_fields=['carga_inicial_inicio', 'carga_inicial_hasta'])
                    cursor = control.carga_inicial_hasta or inicio
                    while cursor < control.carga_inicial_inicio:
                        fin = min(cursor + timedelta(days=119), control.carga_inicial_inicio)
                        procesar_bloques({'createdAfter': cursor.isoformat(), 'createdBefore': fin.isoformat(),
                                          'status': PAGADO}, inicio)
                        control.carga_inicial_hasta = fin
                        control.save(update_fields=['carga_inicial_hasta'])
                        cursor = fin
                    control.actualizado_hasta = control.carga_inicial_inicio - timedelta(minutes=5)
                    control.save(update_fields=['actualizado_hasta'])
                cursor = control.actualizado_hasta - timedelta(minutes=5)
                while cursor < ahora:
                    fin = min(cursor + timedelta(days=6), ahora)
                    procesar_bloques({'updatedAfter': cursor.isoformat(), 'updatedBefore': fin.isoformat()}, inicio)
                    control.actualizado_hasta = fin
                    control.save(update_fields=['actualizado_hasta'])
                    cursor = fin
            control.ultimo_exito = timezone.now()
            control.ultimo_error = ''
            control.save(update_fields=['ultimo_exito', 'ultimo_error'])
            logger.info('Proceso AnyMarket %s completado.', clave)
        except Exception as exc:
            control.ultimo_error_en = timezone.now()
            control.ultimo_error = 'No se pudo completar la consulta o el procesamiento de AnyMarket.'
            control.save(update_fields=['ultimo_error_en', 'ultimo_error'])
            logger.error('Falló el proceso AnyMarket %s (%s).', clave, type(exc).__name__)
            raise
    finally:
        with connection.cursor() as db:
            db.execute('SELECT pg_advisory_unlock(%s)', [731984601241])


def sincronizar() -> None:
    ejecutar_sincronizacion()


def reconciliar() -> None:
    ejecutar_sincronizacion(reconciliacion=True)
