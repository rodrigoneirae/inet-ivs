from pathlib import Path
from uuid import UUID

from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.http import FileResponse, Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET

from ..models import ImagenProducto, Producto


@login_required
@permission_required('catalogo.ver_catalogo', raise_exception=True)
@require_GET
def inicio(request: HttpRequest) -> HttpResponse:
    busqueda = request.GET.get('q', '').strip()[:60]
    productos = Producto.objects.prefetch_related('imagenes')
    if busqueda:
        productos = productos.filter(sku__icontains=busqueda) | productos.filter(
            descripcion__icontains=busqueda
        )
    pagina = Paginator(productos.order_by('sku'), 24).get_page(request.GET.get('page'))
    return render(request, 'catalogo/inicio.html', {'pagina': pagina, 'busqueda': busqueda})


@login_required
@permission_required('catalogo.ver_catalogo', raise_exception=True)
@require_GET
def detalle(request: HttpRequest, public_id: UUID) -> HttpResponse:
    producto = get_object_or_404(Producto.objects.prefetch_related('imagenes'), public_id=public_id)
    return render(request, 'catalogo/detalle.html', {'producto': producto})


@login_required
@permission_required('catalogo.ver_catalogo', raise_exception=True)
@require_GET
def descargar_imagen(request: HttpRequest, public_id: UUID, numero: int, tamano: str) -> FileResponse:
    if tamano not in {'original', '1500', '800', 'preview'}:
        raise Http404
    imagen = get_object_or_404(ImagenProducto, producto__public_id=public_id, numero=numero)
    atributo = {'original': 'original', '1500': 'resolucion_1500', '800': 'resolucion_800',
                'preview': 'resolucion_800'}[tamano]
    raiz = Path(settings.CATALOGO_STORAGE_ROOT).resolve()
    archivo = (raiz / getattr(imagen, atributo)).resolve()
    if raiz not in archivo.parents or not archivo.is_file():
        raise Http404
    nombre_base = imagen.nombre_origen.rsplit('.', 1)[0]
    nombre = imagen.nombre_origen if tamano == 'original' else f'{nombre_base}_{tamano}.jpg'
    return FileResponse(archivo.open('rb'), as_attachment=tamano != 'preview', filename=nombre)
