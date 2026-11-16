import hashlib
import logging

from django import forms
from django.conf import settings
from django.core.cache import caches
from django.db import DatabaseError
from django.http import HttpRequest, JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET
from redis.exceptions import RedisError

from modulo.catalogo.services.imagenes import obtener_portada_base64

from ..models import DispositivoPrecios
from ..services.precios import consultar_precio

logger = logging.getLogger(__name__)


class ConsultaPrecioForm(forms.Form):
    producto = forms.CharField(max_length=30)

    def clean_producto(self) -> str:
        producto = self.cleaned_data['producto'].strip()
        if not producto or producto == '0':
            raise forms.ValidationError('Código de producto inválido.')
        return producto


@require_GET
@never_cache
def precio(request: HttpRequest) -> JsonResponse:
    authorization = request.headers.get('Authorization', '')
    if not authorization.startswith('Bearer '):
        return JsonResponse({'error': 'Autenticación requerida.'}, status=401)
    token = authorization.removeprefix('Bearer ')
    if len(token) != 43 or not token.isascii() or not all(c.isalnum() or c in '-_' for c in token):
        return JsonResponse({'error': 'Autenticación requerida.'}, status=401)
    token_hash = hashlib.sha256(token.encode('ascii')).hexdigest()
    try:
        dispositivo = DispositivoPrecios.objects.only('lista_codigo').get(token_hash=token_hash, activo=True)
    except DispositivoPrecios.DoesNotExist:
        return JsonResponse({'error': 'Autenticación requerida.'}, status=401)
    try:
        cache = caches['api_rate_limit']
        clave = f'precios:limite:{token_hash}'
        if cache.add(clave, 1, timeout=60):
            cantidad = 1
        else:
            cantidad = cache.incr(clave)
    except (RedisError, ValueError, ConnectionError):
        logger.warning('No se pudo verificar el límite de consultas de precios')
        return JsonResponse({'error': 'La consulta de precios no está disponible.'}, status=503)
    if cantidad > 120:
        return JsonResponse({'error': 'Demasiadas consultas. Inténtalo en un minuto.'}, status=429)
    form = ConsultaPrecioForm(request.GET)
    if not form.is_valid():
        return JsonResponse({'error': 'Indica un producto válido.'}, status=400)
    if 'sqlserver' not in settings.DATABASES:
        return JsonResponse({'error': 'La consulta de precios no está disponible.'}, status=503)
    try:
        resultado = consultar_precio(dispositivo.lista_codigo, form.cleaned_data['producto'])
    except DatabaseError:
        logger.warning('No se pudo consultar un precio en I-NET')
        return JsonResponse({'error': 'La consulta de precios no está disponible.'}, status=503)
    if resultado is None:
        return JsonResponse({'error': 'Precio no encontrado.'}, status=404)
    try:
        portada = obtener_portada_base64(str(resultado['codigo']))
    except DatabaseError:
        logger.warning('No se pudo consultar una portada del catálogo')
        portada = None
    return JsonResponse({'producto': {**resultado, 'imagen': portada}})
