import base64
from pathlib import Path

from django.conf import settings

from ..models import ImagenProducto

MAX_BYTES_PORTADA = 512_000


def obtener_portada_base64(sku: str) -> str | None:
    """Devuelve la miniatura local del SKU sin exponer rutas ni imágenes del catálogo completo."""
    imagen = (ImagenProducto.objects.filter(producto__sku=sku)
              .only('resolucion_400', 'resolucion_800', 'portada', 'numero')
              .order_by('-portada', 'numero').first())
    if imagen is None:
        return None
    ruta_relativa = imagen.resolucion_400 or imagen.resolucion_800
    if not ruta_relativa:
        return None
    raiz = Path(settings.CATALOGO_STORAGE_ROOT).resolve()
    ruta = (raiz / ruta_relativa).resolve()
    if raiz not in ruta.parents or not ruta.is_file():
        return None
    try:
        with ruta.open('rb') as archivo:
            contenido = archivo.read(MAX_BYTES_PORTADA + 1)
    except OSError:
        return None
    if not contenido or len(contenido) > MAX_BYTES_PORTADA:
        return None
    return base64.b64encode(contenido).decode('ascii')
