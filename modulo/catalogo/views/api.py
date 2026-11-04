from pathlib import Path
from tempfile import TemporaryFile
from uuid import UUID
from zipfile import ZIP_DEFLATED, ZipFile

from django import forms
from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import FileResponse, Http404, HttpRequest, JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

from ..services import obtener_detalle_ws
from ..models import AtributoProducto, ImagenProducto, Producto

CLAVES_ATRIBUTOS = ('ATTUNO', 'ATTDOS', 'ATTTRE', 'ATTCUA', 'ATTCIN')


class CatalogoForm(forms.Form):
    busqueda = forms.CharField(required=False, max_length=60)
    pagina = forms.IntegerField(required=False, min_value=1, max_value=10000)
    tamano = forms.IntegerField(required=False, min_value=1, max_value=100)


def _url_imagen(public_id: UUID, numero: int, tamano: str) -> str:
    return reverse('catalogo:imagen', kwargs={'public_id': public_id, 'numero': numero, 'tamano': tamano})


@login_required
@permission_required('catalogo.ver_catalogo', raise_exception=True)
@require_GET
@never_cache
def productos(request: HttpRequest) -> JsonResponse:
    formulario = CatalogoForm(request.GET)
    if not formulario.is_valid():
        return JsonResponse({'error': 'Parámetros de búsqueda o paginación inválidos.'}, status=400)
    filtros_atributo: dict[str, list[str]] = {}
    for clave in CLAVES_ATRIBUTOS:
        valores = request.GET.getlist(clave)
        if len(valores) > 20 or any(len(valor) > 200 for valor in valores):
            return JsonResponse({'error': 'Los filtros de atributos no son válidos.'}, status=400)
        filtros_atributo[clave] = list(dict.fromkeys(valor for valor in valores if valor))
    busqueda = formulario.cleaned_data['busqueda'].strip()
    consulta = Producto.objects.filter(imagenes__isnull=False).distinct().prefetch_related('imagenes').order_by('sku')
    if busqueda:
        consulta = consulta.filter(
            Q(sku__icontains=busqueda)
            | Q(descripcion__icontains=busqueda)
            | Q(descripcion_corta__icontains=busqueda)
            | Q(atributos_catalogo__nombre__icontains=busqueda)
            | Q(atributos_catalogo__codigo__icontains=busqueda)
        )
    for clave in CLAVES_ATRIBUTOS:
        valores = filtros_atributo[clave]
        if valores:
            consulta = consulta.filter(atributos_catalogo__clave=clave, atributos_catalogo__nombre__in=valores)
    tamano = formulario.cleaned_data['tamano'] or 24
    pagina = Paginator(consulta.order_by('sku'), tamano).get_page(formulario.cleaned_data['pagina'])
    resultados = []
    for producto in pagina.object_list:
        portada = next((imagen for imagen in producto.imagenes.all() if imagen.portada), None)
        resultados.append({
            'public_id': str(producto.public_id),
            'sku': producto.sku,
            'descripcion': producto.descripcion or producto.descripcion_corta,
            'imagen': _url_imagen(producto.public_id, portada.numero, 'thumbnail') if portada else None,
        })
    return JsonResponse({
        'productos': resultados,
        'pagina': pagina.number,
        'paginas': pagina.paginator.num_pages,
        'total': pagina.paginator.count,
        'hay_anterior': pagina.has_previous(),
        'hay_siguiente': pagina.has_next(),
    })


@login_required
@permission_required('catalogo.ver_catalogo', raise_exception=True)
@require_GET
@never_cache
def facetas_atributos(request: HttpRequest) -> JsonResponse:
    filas = AtributoProducto.objects.filter(
        producto__imagenes__isnull=False,
        clave__in=CLAVES_ATRIBUTOS,
    ).values('clave', 'nombre').annotate(
        cantidad=Count('producto_id', distinct=True),
    ).order_by('clave', 'nombre')
    grupos = {clave: {'clave': clave, 'nombre': f'Atributo {clave}', 'valores': []} for clave in CLAVES_ATRIBUTOS}
    for fila in filas:
        grupos[fila['clave']]['valores'].append({'nombre': fila['nombre'], 'cantidad': fila['cantidad']})
    return JsonResponse({'atributos': [grupo for grupo in grupos.values() if grupo['valores']]})


@login_required
@permission_required('catalogo.ver_catalogo', raise_exception=True)
@require_GET
@never_cache
def detalle_producto(request: HttpRequest, public_id: UUID) -> JsonResponse:
    producto = get_object_or_404(Producto.objects.prefetch_related('imagenes'), public_id=public_id)
    detalle_ws = obtener_detalle_ws(producto)
    return JsonResponse({
        'public_id': str(producto.public_id),
        'sku': producto.sku,
        'descripcion': producto.descripcion or producto.descripcion_corta,
        'descripcion_corta': producto.descripcion_corta,
        'estado': producto.estado,
        'codigo_barra': producto.codigo_barra,
        'codigo_existencia': producto.codigo_existencia,
        'detalle_ws': detalle_ws,
        'detalle_ws_actualizado_en': producto.detalle_ws_actualizado_en,
        'imagenes': [{
            'numero': imagen.numero,
            'portada': imagen.portada,
            'nombre': imagen.nombre_origen,
            'preview': _url_imagen(producto.public_id, imagen.numero, 'preview'),
            'miniatura': _url_imagen(producto.public_id, imagen.numero, 'thumbnail'),
            **({
                'original': _url_imagen(producto.public_id, imagen.numero, 'original'),
                'resolucion_1500': _url_imagen(producto.public_id, imagen.numero, '1500'),
                'resolucion_800': _url_imagen(producto.public_id, imagen.numero, '800'),
            } if request.user.has_perm('catalogo.descargar_catalogo') else {}),
        } for imagen in producto.imagenes.all()],
    })


@login_required
@permission_required('catalogo.ver_catalogo', raise_exception=True)
@require_GET
@never_cache
def imagen(request: HttpRequest, public_id: UUID, numero: int, tamano: str) -> FileResponse:
    if tamano not in {'thumbnail', 'preview', 'original', '1500', '800'}:
        raise Http404
    if tamano not in {'thumbnail', 'preview'} and not request.user.has_perm('catalogo.descargar_catalogo'):
        raise PermissionDenied
    registro = get_object_or_404(ImagenProducto, producto__public_id=public_id, numero=numero)
    campo = {'thumbnail': 'resolucion_400', 'preview': 'resolucion_800', 'original': 'original', '1500': 'resolucion_1500',
             '800': 'resolucion_800'}[tamano]
    if tamano == 'thumbnail' and not registro.resolucion_400:
        campo = 'resolucion_800'
    raiz = Path(settings.CATALOGO_STORAGE_ROOT).resolve()
    archivo = (raiz / getattr(registro, campo)).resolve()
    if raiz not in archivo.parents or not archivo.is_file():
        raise Http404
    nombre_base = registro.nombre_origen.rsplit('.', 1)[0]
    nombre = registro.nombre_origen if tamano in {'preview', 'thumbnail', 'original'} else f'{nombre_base}_{tamano}.jpg'
    return FileResponse(archivo.open('rb'), as_attachment=tamano not in {'preview', 'thumbnail'}, filename=nombre)


@login_required
@permission_required(('catalogo.ver_catalogo', 'catalogo.descargar_catalogo'), raise_exception=True)
@require_GET
@never_cache
def descargar_imagenes_producto(request: HttpRequest, public_id: UUID, tamano: str) -> FileResponse:
    campos = {
        'alta': ('original', 'original'),
        '1500': ('resolucion_1500', '1500x1500'),
        '800': ('resolucion_800', '800x800'),
    }
    if tamano not in campos:
        raise Http404
    producto = get_object_or_404(Producto, public_id=public_id)
    raiz = Path(settings.CATALOGO_STORAGE_ROOT).resolve()
    campo, sufijo = campos[tamano]
    archivo_zip = TemporaryFile()
    cantidad = 0
    with ZipFile(archivo_zip, 'w', compression=ZIP_DEFLATED) as bundle:
        for registro in producto.imagenes.all():
            ruta = (raiz / getattr(registro, campo)).resolve()
            if raiz not in ruta.parents or not ruta.is_file():
                continue
            base = Path(registro.nombre_origen).stem
            extension = Path(registro.nombre_origen).suffix if tamano == 'alta' else '.jpg'
            bundle.write(ruta, arcname=f'{base}_{sufijo}{extension}')
            cantidad += 1
    if not cantidad:
        archivo_zip.close()
        raise Http404
    archivo_zip.seek(0)
    return FileResponse(
        archivo_zip,
        as_attachment=True,
        filename=f'{producto.sku}_{sufijo}.zip',
        content_type='application/zip',
    )
