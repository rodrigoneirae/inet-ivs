import logging

from django import forms
from django.conf import settings
from django.core.cache import caches
from django.http import HttpRequest, JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_POST
from redis.exceptions import RedisError

from ..services import ServicioInformatError, ServicioInformatTimeout, consultar_stock
from ..tokens import TokenStoreError, guardar_token_manual

logger = logging.getLogger(__name__)


class StockForm(forms.Form):
    producto = forms.CharField(max_length=30)
    bodega = forms.RegexField(r'^\d{1,4}$', required=False, max_length=4)

    def clean_producto(self) -> str:
        producto = self.cleaned_data['producto']
        if producto == '0':
            raise forms.ValidationError('Indica un código de producto distinto de cero.')
        return producto


class TokenManualForm(forms.Form):
    token = forms.RegexField(r'^[A-Za-z0-9_-]{1,512}$', strip=True, max_length=512)
    minutos_vigencia = forms.IntegerField(min_value=1, max_value=1440)

    def clean_minutos_vigencia(self) -> int:
        minutos = self.cleaned_data['minutos_vigencia']
        if minutos * 60 > settings.INFORMAT_TOKEN_TTL:
            raise forms.ValidationError('La vigencia supera el máximo configurado.')
        return minutos


@require_POST
@never_cache
def token_manual(request: HttpRequest) -> JsonResponse:
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Inicia sesión.'}, status=401)
    if not request.user.has_perm('informat.administrar_token'):
        return JsonResponse({'error': 'No tienes permiso para administrar el token.'}, status=403)
    form = TokenManualForm(request.POST)
    if not form.is_valid():
        return JsonResponse({'error': 'Indica un token válido y su vigencia restante en minutos.'}, status=400)
    try:
        cache = caches['informat_tokens']
        if not cache.add(f'informat:manual-token-rate:{request.user.pk}', 1, timeout=10):
            return JsonResponse({'error': 'Espera unos segundos antes de volver a actualizar el token.'}, status=429)
        guardar_token_manual(form.cleaned_data['token'], form.cleaned_data['minutos_vigencia'] * 60)
    except (TokenStoreError, RedisError) as exc:
        if not isinstance(exc, TokenStoreError):
            logger.warning('No se pudo acceder al almacenamiento compartido de Informat (%s)', type(exc).__name__)
        return JsonResponse({'error': 'No fue posible guardar el token de Informat.'}, status=503)
    logger.info('Token de Informat actualizado manualmente; usuario interno %s', request.user.pk)
    return JsonResponse({'mensaje': 'Token actualizado. La vigencia indicada es un límite estimado.'})


@require_GET
@never_cache
def stock(request: HttpRequest) -> JsonResponse:
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Inicia sesión.'}, status=401)
    if not request.user.has_perm('informat.consultar_stock'):
        return JsonResponse({'error': 'No tienes permiso para consultar stock.'}, status=403)
    form = StockForm(request.GET)
    if not form.is_valid():
        return JsonResponse({'error': 'Indica un código de producto distinto de cero y una bodega numérica de hasta 4 dígitos.'}, status=400)
    try:
        productos = consultar_stock(form.cleaned_data['producto'], form.cleaned_data['bodega'])
    except ServicioInformatTimeout as exc:
        return JsonResponse({'error': str(exc)}, status=504)
    except ServicioInformatError as exc:
        return JsonResponse({'error': str(exc)}, status=502)
    # Devolver exclusivamente las secciones necesarias, no precios ni datos contables.
    resultado = []
    for item in productos:
        venta = item.get('VENTA') if isinstance(item.get('VENTA'), dict) else {}
        stock = item.get('STOCK') if isinstance(item.get('STOCK'), dict) else {}
        bodegas = stock.get('STOCK_BODEGA', item.get('STOCK_BODEGA', []))
        if not isinstance(bodegas, list):
            bodegas = []
        resultado.append({
            'producto': venta.get('PRODUCTO_VTA', venta.get('PRODUCTO_VENTA')),
            'descripcion': venta.get('DESC_LARGA', venta.get('DESC_CORTA')),
            'stock_actual': stock.get('STOCK_ACTUAL'),
            'stock_disponible': stock.get('STOCK_DISPONIBLE'),
            'bodegas': [{'bodega': b.get('BODEGA', b.get('STOCK_BODEGA')), 'disponible': b.get('STOCK_DISPONIBLE')}
                        for b in bodegas if isinstance(b, dict)],
        })
    return JsonResponse({'productos': resultado})
