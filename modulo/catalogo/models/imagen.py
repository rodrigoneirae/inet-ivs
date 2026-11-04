from django.db import models

from .producto import Producto


class ImagenProducto(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='imagenes')
    numero = models.PositiveSmallIntegerField()
    nombre_origen = models.CharField(max_length=255)
    original = models.CharField(max_length=500)
    resolucion_1500 = models.CharField(max_length=500)
    resolucion_800 = models.CharField(max_length=500)
    sha256 = models.CharField(max_length=64)
    portada = models.BooleanField(default=False)

    class Meta:
        ordering = ['numero']
        constraints = [models.UniqueConstraint(fields=['producto', 'numero'], name='catalogo_imagen_producto_numero_uniq')]

    def __str__(self) -> str:
        return f'{self.producto.sku}_{self.numero}'
