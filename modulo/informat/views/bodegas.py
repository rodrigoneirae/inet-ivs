import hashlib
import logging

from django import forms
from django.core.cache import caches
from django.http import HttpRequest, JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET
from redis.exceptions import RedisError

from modulo.informat.models import AplicacionBodegas
from modulo.informat.services.bodegas import BodegasNoDisponibles, listar_bodegas

logger = logging.getLogger(__name__)


class BuscarBodegasForm(forms.Form):
    pagina = forms.IntegerField(required=False, min_value=1, max_value=10000)
    tamano = forms.IntegerField(required=False, min_value=1, max_value=100)
    busqueda = forms.CharField(required=False, max_length=35)


def _autorizacion(request: HttpRequest) -> JsonResponse | None:
    header = request.headers.get('Authorization', '')
    if header:
        if not header.startswith('Bearer '):
            return JsonResponse({'error': 'Token inválido.'}, status=401)
        token = header[7:]
        if len(token) != 43 or not token.isascii() or not all(c.isalnum() or c in '-_' for c in token):
            return JsonResponse({'error': 'Token inválido.'}, status=401)
        token_hash = hashlib.sha256(token.encode('ascii')).hexdigest()
        if not AplicacionBodegas.objects.filter(token_hash=token_hash, activa=True).exists():
            return JsonResponse({'error': 'Token inválido.'}, status=401)
        try:
            cache = caches['api_rate_limit']
            key = f'bodegas:limite:{token_hash}'
            count = 1 if cache.add(key, 1, timeout=60) else cache.incr(key)
        except (RedisError, ValueError, ConnectionError):
            logger.warning('No se pudo limitar la consulta de bodegas.')
            return JsonResponse({'error': 'Consulta temporalmente no disponible.'}, status=503)
        if count > 120:
            return JsonResponse({'error': 'Demasiadas consultas. Inténtalo en un minuto.'}, status=429)
        return None
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Autenticación requerida.'}, status=401)
    if not request.user.is_active or not (request.user.has_perm('informat.consultar_bodegas_inet') or
                                          request.user.has_perm('inventario.supervisar_inventario')):
        return JsonResponse({'error': 'Acceso denegado.'}, status=403)
    return None


@require_GET
@never_cache
def bodegas(request: HttpRequest) -> JsonResponse:
    denegado = _autorizacion(request)
    if denegado:
        return denegado
    formulario = BuscarBodegasForm(request.GET)
    if not formulario.is_valid():
        return JsonResponse({'error': 'Parámetros inválidos.'}, status=400)
    try:
        filas, hay_mas = listar_bodegas(
            pagina=formulario.cleaned_data['pagina'] or 1,
            tamano=formulario.cleaned_data['tamano'] or 100,
            busqueda=formulario.cleaned_data['busqueda'].strip(),
        )
    except BodegasNoDisponibles:
        logger.warning('No se pudo consultar BODEGAS en I-NET.')
        return JsonResponse({'error': 'Maestro de bodegas no disponible.'}, status=503)
    return JsonResponse({'bodegas': filas, 'pagina': formulario.cleaned_data['pagina'] or 1, 'hay_mas': hay_mas})
