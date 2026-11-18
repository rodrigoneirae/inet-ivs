# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class InformatVistaBasedeclientes(models.Model):
    tipo = models.CharField(db_column='Tipo', max_length=7)  # Field name made lowercase.
    rut = models.DecimalField(db_column='Rut', max_digits=12, decimal_places=0 , primary_key=True)  # Field name made lowercase.
    secuencia = models.SmallIntegerField(db_column='Secuencia')  # Field name made lowercase.
    nombre_cliente = models.CharField(db_column='Nombre Cliente', max_length=40, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    dirección_despacho = models.CharField(db_column='Dirección Despacho', max_length=40, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    ciudad_despacho = models.CharField(db_column='Ciudad Despacho', max_length=40, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    comuna_despacho = models.CharField(db_column='Comuna Despacho', max_length=15, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    iva = models.DecimalField(db_column='IVA', max_digits=10, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    telefono = models.CharField(db_column='Telefono', max_length=20, blank=True, null=True)  # Field name made lowercase.
    fax = models.CharField(db_column='Fax', max_length=20, blank=True, null=True)  # Field name made lowercase.
    correo_electronico = models.CharField(db_column='Correo Electronico', max_length=50, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    pagina_web = models.CharField(db_column='Pagina Web', max_length=50, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    afecto_a_impuesto = models.CharField(db_column='Afecto a Impuesto', max_length=6)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    atributo_1 = models.DecimalField(db_column='Atributo 1', max_digits=10, decimal_places=0, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    nombre_atributo_1 = models.CharField(db_column='Nombre Atributo 1', max_length=25)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    atributo_2 = models.DecimalField(db_column='Atributo 2', max_digits=10, decimal_places=0, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    nombre_atributo_2 = models.CharField(db_column='Nombre Atributo 2', max_length=25)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    atributo_3 = models.DecimalField(db_column='Atributo 3', max_digits=10, decimal_places=0, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    nombre_atributo_3 = models.CharField(db_column='Nombre Atributo 3', max_length=25)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    atributo_4 = models.DecimalField(db_column='Atributo 4', max_digits=10, decimal_places=0, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    nombre_atributo_4 = models.CharField(db_column='Nombre Atributo 4', max_length=25)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    atributo_5 = models.DecimalField(db_column='Atributo 5', max_digits=10, decimal_places=0, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    nombre_atributo_5 = models.CharField(db_column='Nombre Atributo 5', max_length=25)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    estado = models.CharField(db_column='Estado', max_length=9)  # Field name made lowercase.
    facturar_a = models.CharField(db_column='Facturar A', max_length=11)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    rubro = models.SmallIntegerField(db_column='Rubro', blank=True, null=True)  # Field name made lowercase.
    nombre_rubro = models.CharField(db_column='Nombre Rubro', max_length=25, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    sector = models.SmallIntegerField(db_column='Sector', blank=True, null=True)  # Field name made lowercase.
    nombre_sector = models.CharField(db_column='Nombre Sector', max_length=25, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    descuento = models.SmallIntegerField(db_column='Descuento', blank=True, null=True)  # Field name made lowercase.
    nombre_descuento = models.CharField(db_column='Nombre Descuento', max_length=20, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    cobrador = models.DecimalField(db_column='Cobrador', max_digits=12, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    nombre_cobrador = models.CharField(db_column='Nombre Cobrador', max_length=40, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    vendedor = models.DecimalField(db_column='Vendedor', max_digits=12, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    nombre_vendedor = models.CharField(db_column='Nombre Vendedor', max_length=40, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    nivel_de_credito = models.DecimalField(db_column='Nivel de Credito', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    giro = models.CharField(db_column='Giro', max_length=80, blank=True, null=True)  # Field name made lowercase.
    codigo_postal = models.CharField(db_column='Codigo Postal', max_length=30, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    fecha_de_ingreso = models.DateTimeField(db_column='Fecha de Ingreso', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    via_despacho = models.CharField(db_column='Via Despacho', max_length=25)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    notas = models.TextField(db_column='Notas')  # Field name made lowercase. This field type is a guess.
    clave_cliente = models.CharField(db_column='Clave Cliente', max_length=10, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    pedidos_parciales = models.CharField(db_column='Pedidos Parciales', max_length=3)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    condicion_venta = models.SmallIntegerField(db_column='Condicion Venta', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    nombre_condicion = models.CharField(db_column='Nombre Condicion', max_length=25, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    dia_de_pago_1 = models.SmallIntegerField(db_column='Dia de Pago 1', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    dia_de_pago_2 = models.SmallIntegerField(db_column='Dia de Pago 2', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    dia_de_pago_3 = models.SmallIntegerField(db_column='Dia de Pago 3', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    dia_de_pago_4 = models.SmallIntegerField(db_column='Dia de Pago 4', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    cliente_nombre = models.CharField(db_column='Cliente+Nombre', max_length=82, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    rubro_nombre = models.CharField(db_column='Rubro+Nombre', max_length=32, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    atributo_1_nombre = models.CharField(db_column='Atributo 1+Nombre', max_length=67, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    atributo_2_nombre = models.CharField(db_column='Atributo 2+Nombre', max_length=67, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    atributo_3_nombre = models.CharField(db_column='Atributo 3+Nombre', max_length=67, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    atributo_4_nombre = models.CharField(db_column='Atributo 4+Nombre', max_length=67, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    atributo_5_nombre = models.CharField(db_column='Atributo 5+Nombre', max_length=67, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    field_maestro_de_cliente = models.CharField(db_column='&Maestro de Cliente', max_length=1)  # Field name made lowercase. Field renamed to remove unsuitable characters. Field renamed because it started with '_'.
    codlistaprecios = models.SmallIntegerField(db_column='CodListaPrecios', blank=True, null=True)  # Field name made lowercase.
    lista_de_precios = models.CharField(db_column='Lista de Precios', max_length=25, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    dirección_factura = models.CharField(db_column='Dirección Factura', max_length=40, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    ciudad_factura = models.CharField(db_column='Ciudad Factura', max_length=15, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    comuna_factura = models.CharField(db_column='Comuna Factura', max_length=15, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    pila = models.CharField(db_column='Pila', max_length=20, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'INFORMAT_Vista_BasedeClientes'
