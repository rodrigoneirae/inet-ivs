from django.db import models

from .producto import Producto


class ImagenProducto(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='imagenes')
    numero = models.PositiveSmallIntegerField()
    nombre_origen = models.CharField(max_length=255)
    original = models.CharField(max_length=500)
    resolucion_400 = models.CharField(max_length=500, blank=True, default='')
    resolucion_1500 = models.CharField(max_length=500)
    resolucion_800 = models.CharField(max_length=500)
    sha256 = models.CharField(max_length=64)
    portada = models.BooleanField(default=False)

    class Meta:
        ordering = ['numero']
        constraints = [models.UniqueConstraint(fields=['producto', 'numero'], name='catalogo_imagen_producto_numero_uniq')]

    def __str__(self) -> str:
        return f'{self.producto.sku}_{self.numero}'


class AtributoProducto(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='atributos_catalogo')
    clave = models.CharField(max_length=8)
    codigo = models.CharField(max_length=30, blank=True)
    nombre = models.CharField(max_length=200)

    class Meta:
        ordering = ['clave', 'nombre']
        constraints = [models.UniqueConstraint(fields=['producto', 'clave'], name='catalogo_atributo_producto_clave_uniq')]
        indexes = [models.Index(fields=['clave', 'nombre'], name='catalogo_atributo_filtro_idx')]

    def __str__(self) -> str:
        return f'{self.clave}: {self.nombre}'
