import hashlib
import logging
import re
from pathlib import Path

from django.conf import settings
from django.db import DatabaseError, transaction
from django.utils import timezone
from PIL import Image, ImageOps, UnidentifiedImageError

from modulo.informat.models import ProductoVentaInet

from ..models import EstadoSincronizacion, ImagenProducto, Producto

logger = logging.getLogger(__name__)
PATRON_IMAGEN = re.compile(r'^(?P<sku>.+)_(?P<numero>[1-9][0-9]*)\.(?P<extension>jpg|jpeg|png|webp)$', re.IGNORECASE)
TAMANO_LOTE = 500


def normalizar_texto(valor: str | None) -> str:
    return (valor or '').strip()


class ErrorSincronizacionCatalogo(Exception):
    """Error recuperable al leer una de las fuentes del catálogo."""


def _registrar_inicio(fuente: str) -> EstadoSincronizacion:
    estado, _ = EstadoSincronizacion.objects.get_or_create(fuente=fuente)
    estado.ultimo_inicio = timezone.now()
    estado.mensaje_error = ''
    estado.save(update_fields=['ultimo_inicio', 'mensaje_error'])
    return estado


def _registrar_error(estado: EstadoSincronizacion, error: Exception) -> None:
    estado.ultimo_error = timezone.now()
    estado.mensaje_error = str(error)[:250]
    estado.save(update_fields=['ultimo_error', 'mensaje_error'])


def sincronizar_productos() -> int:
    """Copia el maestro PRODVENT al almacenamiento local sin vaciarlo ante errores."""
    estado = _registrar_inicio('inet')
    try:
        if 'sqlserver' not in settings.DATABASES:
            raise ErrorSincronizacionCatalogo('La conexión SQL Server no está configurada.')
        origen = list(ProductoVentaInet.objects.using('sqlserver').values(
            'codigo', 'descripcion_corta', 'descripcion', 'codigo_existencia', 'codigo_barra', 'estado',
        ).iterator(chunk_size=TAMANO_LOTE))
        ahora = timezone.now()
        productos: list[Producto] = []
        reemplazos_sku: list[tuple[str, str]] = []
        for fila in origen:
            sku_original = fila['codigo'] or ''
            sku = normalizar_texto(sku_original)
            if not sku:
                continue
            if sku != sku_original:
                reemplazos_sku.append((sku_original, sku))
            productos.append(Producto(
                sku=sku,
                descripcion_corta=normalizar_texto(fila['descripcion_corta']),
                descripcion=normalizar_texto(fila['descripcion']),
                codigo_existencia=normalizar_texto(fila['codigo_existencia']),
                codigo_barra=normalizar_texto(fila['codigo_barra']),
                estado=fila['estado'],
                sincronizado_en=ahora,
            ))
        with transaction.atomic():
            for sku_original, sku in reemplazos_sku:
                if not Producto.objects.filter(sku=sku).exists():
                    # Conserva el UUID y las relaciones al limpiar CHAR con espacios de relleno.
                    Producto.objects.filter(sku=sku_original).update(sku=sku)
            for inicio in range(0, len(productos), TAMANO_LOTE):
                Producto.objects.bulk_create(
                    productos[inicio:inicio + TAMANO_LOTE],
                    update_conflicts=True,
                    unique_fields=['sku'],
                    update_fields=['descripcion_corta', 'descripcion', 'codigo_existencia', 'codigo_barra',
                                   'estado', 'sincronizado_en'],
                )
            estado.ultimo_exito = ahora
            estado.mensaje_error = ''
            estado.save(update_fields=['ultimo_exito', 'mensaje_error'])
        return len(productos)
    except (DatabaseError, OSError, ErrorSincronizacionCatalogo) as exc:
        _registrar_error(estado, exc)
        logger.warning('Falló la sincronización del maestro del catálogo: %s', type(exc).__name__)
        raise ErrorSincronizacionCatalogo('No se pudo sincronizar el maestro de I-NET.') from exc


def _guardar_derivada(origen: Path, destino: Path, lado: int, calidad: int = 92) -> None:
    destino.parent.mkdir(parents=True, exist_ok=True)
    temporal = destino.with_suffix('.tmp.jpg')
    with Image.open(origen) as imagen:
        imagen = ImageOps.exif_transpose(imagen).convert('RGB')
        imagen = ImageOps.pad(imagen, (lado, lado), method=Image.Resampling.LANCZOS, color='white')
        imagen.save(temporal, format='JPEG', quality=calidad, optimize=True, progressive=True)
    temporal.replace(destino)


def imagen_disponible_local(raiz: Path, imagen: ImagenProducto) -> bool:
    raiz_resuelta = raiz.resolve()
    for campo in ('original', 'resolucion_400', 'resolucion_1500', 'resolucion_800'):
        archivo = (raiz_resuelta / getattr(imagen, campo)).resolve()
        if raiz_resuelta not in archivo.parents or not archivo.is_file():
            return False
    return True


def sincronizar_imagenes() -> int:
    """Importa imágenes y derivados; el catálogo sirve copias locales si SMB cae."""
    estado = _registrar_inicio('smb')
    raiz_origen = Path(settings.CATALOGO_SOURCE_DIR)
    raiz_destino = Path(settings.CATALOGO_STORAGE_ROOT)
    try:
        # scandir fuerza la comprobación de disponibilidad antes de considerar el escaneo válido.
        archivos = sorted(ruta for ruta in raiz_origen.iterdir() if ruta.is_file())
        importadas = 0
        for archivo in archivos:
            coincidencia = PATRON_IMAGEN.fullmatch(archivo.name)
            if not coincidencia:
                continue
            datos = coincidencia.groupdict()
            producto = Producto.objects.filter(sku=datos['sku']).first()
            if producto is None:
                continue
            try:
                contenido = archivo.read_bytes()
                contenido_hash = hashlib.sha256(contenido).hexdigest()
                existente = ImagenProducto.objects.filter(producto=producto, numero=int(datos['numero'])).first()
                if (existente and existente.sha256 == contenido_hash
                        and imagen_disponible_local(raiz_destino, existente)):
                    continue
                carpeta = raiz_destino / hashlib.sha256(datos['sku'].encode('utf-8')).hexdigest()
                original = carpeta / archivo.name
                original.parent.mkdir(parents=True, exist_ok=True)
                temporal_original = original.with_name(f'.{original.name}.tmp')
                temporal_original.write_bytes(contenido)
                temporal_original.replace(original)
                variante_1500 = carpeta / f'{archivo.stem}_1500.jpg'
                variante_800 = carpeta / f'{archivo.stem}_800.jpg'
                miniatura_400 = carpeta / f'{archivo.stem}_400.jpg'
                _guardar_derivada(original, variante_1500, 1500)
                _guardar_derivada(original, variante_800, 800)
                _guardar_derivada(original, miniatura_400, 400, calidad=82)
                ImagenProducto.objects.update_or_create(
                    producto=producto,
                    numero=int(datos['numero']),
                    defaults={
                        'nombre_origen': archivo.name,
                        'original': str(original.relative_to(raiz_destino)),
                        'resolucion_400': str(miniatura_400.relative_to(raiz_destino)),
                        'resolucion_1500': str(variante_1500.relative_to(raiz_destino)),
                        'resolucion_800': str(variante_800.relative_to(raiz_destino)),
                        'sha256': contenido_hash,
                        'portada': int(datos['numero']) == 1,
                    },
                )
                importadas += 1
            except (OSError, UnidentifiedImageError, ValueError) as exc:
                logger.warning('No se pudo importar una imagen del catálogo (%s).', type(exc).__name__)
        estado.ultimo_exito = timezone.now()
        estado.mensaje_error = ''
        estado.save(update_fields=['ultimo_exito', 'mensaje_error'])
        return importadas
    except (OSError, DatabaseError) as exc:
        _registrar_error(estado, exc)
        logger.warning('Falló la sincronización de imágenes del catálogo: %s', type(exc).__name__)
        raise ErrorSincronizacionCatalogo('No se pudo leer la carpeta SMB del catálogo.') from exc
