import hashlib
from zoneinfo import ZoneInfo

from django import forms
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.core.cache import caches
from django.core.paginator import Paginator
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.middleware.csrf import get_token
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_POST

from modulo.anymarket.views import consulta_pedidos, exportar_pedidos, solicitar_sincronizacion
from modulo.anymarket.models import Pedido, Sincronizacion


class LoginForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(max_length=256, strip=False)


@require_GET
@never_cache
def sesion(request: HttpRequest) -> JsonResponse:
    return JsonResponse({'csrf': get_token(request), 'usuario': request.user.get_username() if request.user.is_authenticated else None,
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
                         'puede_ver_pedidos': user.has_perm('anymarket.view_pedido'),
                         'puede_sincronizar': user.has_perm('anymarket.change_pedido')})


@require_POST
@never_cache
def salir(request: HttpRequest) -> JsonResponse:
    logout(request)
    return JsonResponse({'csrf': get_token(request)})


@require_POST
@never_cache
def sincronizar(request: HttpRequest) -> JsonResponse:
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Inicia sesión.'}, status=401)
    if not request.user.has_perm('anymarket.change_pedido'):
        return JsonResponse({'error': 'No tienes permiso para ejecutar la sincronización.'}, status=403)
    nivel, mensaje = solicitar_sincronizacion()
    return JsonResponse({'mensaje': mensaje} if nivel == 'success' else {'error': mensaje},
                        status={'success': 200, 'warning': 429, 'error': 503}[nivel])


@require_GET
@never_cache
def exportar(request: HttpRequest) -> HttpResponse:
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Inicia sesión.'}, status=401)
    if not request.user.has_perm('anymarket.view_pedido'):
        return JsonResponse({'error': 'No tienes permiso para exportar pedidos.'}, status=403)
    response = exportar_pedidos(request)
    if response.status_code == 400:
        return JsonResponse({'error': response.content.decode('utf-8')}, status=400)
    return response


@require_GET
@never_cache
def pedidos(request: HttpRequest) -> JsonResponse:
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Inicia sesión.'}, status=401)
    if not request.user.has_perm('anymarket.view_pedido'):
        return JsonResponse({'error': 'No tienes permiso para ver pedidos.'}, status=403)
    queryset, filtros, _, _ = consulta_pedidos(request)
    if not filtros.is_valid():
        return JsonResponse({'error': 'Los filtros no son válidos.'}, status=400)
    pagina = Paginator(queryset, 20).get_page(request.GET.get('page'))
    results = []
    for pedido in pagina:
        datos = pedido.datos
        buyer = datos.get('buyer') or {}
        results.append({'uuid': str(pedido.uuid), 'numero': pedido.numero_mercado,
                        'canal': datos.get('marketPlace'), 'cliente': buyer.get('name') if isinstance(buyer, dict) else None,
                        'fecha': pedido.creado_en.isoformat(),
                        'fecha_local': timezone.localtime(pedido.creado_en, ZoneInfo(settings.ANYMARKET_TIME_ZONE)).strftime('%d/%m/%Y %H:%M:%S'),
                        'items': pedido.cantidad_items,
                        'total': datos.get('total'), 'estado': datos.get('marketPlaceStatus'),
                        'fulfillment': datos.get('fulfillment') is True})
    canales = list(Pedido.objects.exclude(datos__marketPlace__isnull=True)
                   .values_list('datos__marketPlace', flat=True).distinct().order_by('datos__marketPlace')[:200])
    estados = list(Pedido.objects.exclude(datos__marketPlaceStatus__isnull=True)
                   .values_list('datos__marketPlaceStatus', flat=True).distinct()
                   .order_by('datos__marketPlaceStatus')[:100])
    sincronizaciones = {
        registro.clave: {
            'ultimo_exito': registro.ultimo_exito.isoformat() if registro.ultimo_exito else None,
            'ultimo_error_en': registro.ultimo_error_en.isoformat() if registro.ultimo_error_en else None,
            'ultimo_error': registro.ultimo_error,
        }
        for registro in Sincronizacion.objects.filter(clave__in=['pedidos', 'reconciliacion'])
    }
    return JsonResponse({'resultados': results, 'pagina': pagina.number,
                         'paginas': pagina.paginator.num_pages, 'total': pagina.paginator.count,
                         'canales': canales, 'estados': estados, 'sincronizaciones': sincronizaciones,
                         'zona_horaria': settings.ANYMARKET_TIME_ZONE})
