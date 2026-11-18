
from django.db import models
from django.forms import model_to_dict

class InformatVistaBaseproductosventas(models.Model):
    codigo = models.CharField(db_column='Codigo', max_length=30,primary_key=True)  # Field name made lowercase.
    descripcion = models.CharField(db_column='Descripcion', max_length=60, blank=True, null=True)  # Field name made lowercase.
    unidad = models.SmallIntegerField(db_column='Unidad', blank=True, null=True)  # Field name made lowercase.
    nombre_unidad = models.CharField(db_column='Nombre Unidad', max_length=20, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    codigo_atributo_4 = models.DecimalField(db_column='Codigo Atributo 4', max_digits=10, decimal_places=0, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    nombre_atributo_4 = models.CharField(db_column='Nombre Atributo 4', max_length=25, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    codigo_atributo_2 = models.DecimalField(db_column='Codigo Atributo 2', max_digits=10, decimal_places=0, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    nombre_atributo_2 = models.CharField(db_column='Nombre Atributo 2', max_length=25, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    codigo_atributo_3 = models.DecimalField(db_column='Codigo Atributo 3', max_digits=10, decimal_places=0, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    nombre_atributo_3 = models.CharField(db_column='Nombre Atributo 3', max_length=25, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    codigo_atributo_1 = models.DecimalField(db_column='Codigo Atributo 1', max_digits=10, decimal_places=0, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    nombre_atributo_1 = models.CharField(db_column='Nombre Atributo 1', max_length=25, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    cuenta_ventas = models.CharField(db_column='Cuenta Ventas', max_length=9, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    nombre_cuenta_ventas = models.CharField(db_column='Nombre Cuenta Ventas', max_length=30, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    area_negocio_ventas = models.SmallIntegerField(db_column='Area Negocio Ventas', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    nombre_area_negocio_ventas = models.CharField(db_column='Nombre Area Negocio Ventas', max_length=30, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    centro_costo_ventas = models.IntegerField(db_column='Centro Costo Ventas', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    nombre_centro_costo_ventas = models.CharField(db_column='Nombre Centro Costo Ventas', max_length=30, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    item_gasto_ventas = models.SmallIntegerField(db_column='Item Gasto Ventas', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    nombre_iteom_gasto_ventas = models.CharField(db_column='Nombre Iteom Gasto Ventas', max_length=30, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    cuenta_costo_venta = models.CharField(db_column='Cuenta Costo Venta', max_length=9, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    nombre_cuenta_costo_vta = models.CharField(db_column='Nombre Cuenta Costo Vta', max_length=30, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    centro_costo_del_costo_venta = models.IntegerField(db_column='Centro Costo del Costo Venta', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    nombre_centro_costo_del_costo_venta = models.CharField(db_column='Nombre Centro Costo del Costo Venta', max_length=30, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    area_negocio_costo_venta = models.SmallIntegerField(db_column='Area Negocio Costo Venta', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    nombre_area_negocio_costo_venta = models.CharField(db_column='Nombre Area Negocio Costo Venta', max_length=30, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    item_gasto_costo_venta = models.SmallIntegerField(db_column='Item Gasto Costo Venta', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    nombre_item_gsto_costo_venta = models.CharField(db_column='Nombre Item Gsto Costo Venta', max_length=30, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    peso = models.DecimalField(db_column='Peso', max_digits=8, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    volumen = models.DecimalField(db_column='Volumen', max_digits=8, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    largo = models.DecimalField(db_column='Largo', max_digits=8, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    ancho = models.DecimalField(db_column='Ancho', max_digits=8, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    alto = models.DecimalField(db_column='Alto', max_digits=8, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    codigo_de_barra = models.CharField(db_column='Codigo de Barra', max_length=20, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    fecha_modificacion = models.DateTimeField(db_column='Fecha Modificacion', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    estado = models.CharField(db_column='Estado', max_length=9)  # Field name made lowercase.
    producto_descripcion = models.CharField(db_column='Producto+Descripcion', max_length=56, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    unidad_nombre = models.CharField(db_column='Unidad+Nombre', max_length=27, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    cuenta_ventas_nombre = models.CharField(db_column='Cuenta Ventas+Nombre', max_length=40, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    area_negocio_ventas_nombre = models.CharField(db_column='Area Negocio Ventas+Nombre', max_length=37, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    centro_costo_ventas_nombre = models.CharField(db_column='Centro Costo Ventas+Nombre', max_length=43, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    cuenta_costo_vta_nombre = models.CharField(db_column='Cuenta Costo Vta+Nombre', max_length=40, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    centro_costo_venta_nombre = models.CharField(db_column='Centro  Costo Venta+Nombre', max_length=43, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    area_negocio_costo_venta_nombre = models.CharField(db_column='Area Negocio Costo Venta+Nombre', max_length=37, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    field_base_de_productos_de_venta = models.CharField(db_column='&Base de Productos de Venta', max_length=1)  # Field name made lowercase. Field renamed to remove unsuitable characters. Field renamed because it started with '_'.
    emb = models.DecimalField(db_column='EMB', max_digits=10, decimal_places=4, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'INFORMAT_Vista_BaseProductosVentas'

    def to_json(self):
        # item = model_to_dict(self, exclude=['password', 'user_permissions'])
        item = model_to_dict(self)

        return item

