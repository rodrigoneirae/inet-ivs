from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.http import FileResponse, HttpRequest, HttpResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_safe


@require_safe
@never_cache
def inicio(request: HttpRequest) -> HttpResponse:
    """Entregar la interfaz Astro compilada mediante el middleware de Django."""
    try:
        archivo = (settings.BASE_DIR / 'frontend' / 'dist' / 'index.html').open('rb')
    except FileNotFoundError:
        return HttpResponse('La interfaz Astro aún no está compilada.', status=503, content_type='text/plain')
    return FileResponse(archivo, content_type='text/html; charset=utf-8')


@login_required
@permission_required('anymarket.view_pedido', raise_exception=True)
@require_safe
@never_cache
def pedidos(request: HttpRequest) -> HttpResponse:
    return inicio(request)
