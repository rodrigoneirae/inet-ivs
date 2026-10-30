import hashlib

from django import forms
from django.contrib.auth import authenticate, login, logout
from django.core.cache import caches
from django.http import HttpRequest, JsonResponse
from django.middleware.csrf import get_token
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_POST


class LoginForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(max_length=256, strip=False)


@require_GET
@never_cache
def sesion(request: HttpRequest) -> JsonResponse:
    return JsonResponse({'csrf': get_token(request), 'usuario': request.user.get_username() if request.user.is_authenticated else None,
                         'puede_ver_stock': request.user.has_perm('informat.consultar_stock'),
                         'puede_ver_catalogo': request.user.has_perm('informat.consultar_productos_inet'),
                         'puede_administrar_token': request.user.has_perm('informat.administrar_token'),
                         'puede_ver_pedidos': request.user.has_perm('anymarket.view_pedido'),
                         'puede_sincronizar': request.user.has_perm('anymarket.change_pedido')})


@require_POST
@never_cache
def ingresar(request: HttpRequest) -> JsonResponse:
    # A shared Redis counter limits attempts even when several web workers run.
    cache = caches['api_rate_limit']
    ip = request.META.get('REMOTE_ADDR', '')
    key = 'api-login:' + hashlib.sha256(ip.encode()).hexdigest()
    if cache.add(key, 1, timeout=60):
        count = 1
    else:
        try:
            count = cache.incr(key)
        except ValueError:
            cache.add(key, 1, timeout=60)
            count = 1
    if count > 10:
        return JsonResponse({'error': 'Demasiados intentos. Inténtalo en un minuto.'}, status=429)
    form = LoginForm(request.POST)
    if not form.is_valid():
        return JsonResponse({'error': 'Credenciales inválidas.'}, status=400)
    user = authenticate(request, **form.cleaned_data)
    if user is None:
        return JsonResponse({'error': 'Credenciales inválidas.'}, status=401)
    login(request, user)
    return JsonResponse({'csrf': get_token(request), 'usuario': user.get_username(),
                         'puede_ver_stock': user.has_perm('informat.consultar_stock'),
                         'puede_ver_catalogo': user.has_perm('informat.consultar_productos_inet'),
                         'puede_administrar_token': user.has_perm('informat.administrar_token'),
                         'puede_ver_pedidos': user.has_perm('anymarket.view_pedido'),
                         'puede_sincronizar': user.has_perm('anymarket.change_pedido')})


@require_POST
@never_cache
def salir(request: HttpRequest) -> JsonResponse:
    logout(request)
    return JsonResponse({'csrf': get_token(request)})
