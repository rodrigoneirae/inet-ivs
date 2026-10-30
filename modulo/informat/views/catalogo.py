import logging

from django import forms
from django.conf import settings
from django.db import DatabaseError
from django.http import HttpRequest, JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

from ..models import ProductoVentaInet

logger = logging.getLogger(__name__)


class CatalogoForm(forms.Form):
    busqueda = forms.CharField(required=False, max_length=60)
    pagina = forms.IntegerField(required=False, min_value=1, max_value=10000)
    tamano = forms.IntegerField(required=False, min_value=1, max_value=100)


@require_GET
@never_cache
def productos(request: HttpRequest) -> JsonResponse:
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Inicia sesión.'}, status=401)
    if not request.user.has_perm('informat.consultar_productos_inet'):
        return JsonResponse({'error': 'No tienes permiso para consultar productos.'}, status=403)
    form = CatalogoForm(request.GET)
    if not form.is_valid():
        return JsonResponse({'error': 'Parámetros de búsqueda o paginación inválidos.'}, status=400)
    if 'sqlserver' not in settings.DATABASES:
        return JsonResponse({'error': 'La conexión a I-NET no está configurada.'}, status=503)

    pagina = form.cleaned_data['pagina'] or 1
    tamano = form.cleaned_data['tamano'] or 25
    busqueda = form.cleaned_data['busqueda']
    consulta = ProductoVentaInet.objects.using('sqlserver').order_by('codigo')
    if busqueda:
        from django.db.models import Q
        consulta = consulta.filter(Q(codigo__icontains=busqueda) | Q(descripcion__icontains=busqueda))
    inicio = (pagina - 1) * tamano
    try:
        registros = list(consulta.values('codigo', 'descripcion_corta', 'descripcion',
                                         'codigo_existencia', 'codigo_barra', 'estado')[inicio:inicio + tamano + 1])
    except DatabaseError:
        logger.warning('No se pudo consultar el catálogo de productos I-NET')
        return JsonResponse({'error': 'No fue posible consultar el catálogo de I-NET.'}, status=503)
    return JsonResponse({'productos': registros[:tamano], 'pagina': pagina,
                         'tamano': tamano, 'hay_mas': len(registros) > tamano})
