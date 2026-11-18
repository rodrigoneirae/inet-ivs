from django.db import models


class ProductoVentaInet(models.Model):
    codigo = models.CharField(db_column='BarCod', primary_key=True, max_length=30)
    descripcion_corta = models.CharField(db_column='BarDscCor', max_length=25, null=True)
    descripcion = models.CharField(db_column='BarDscLar', max_length=60, null=True)
    codigo_existencia = models.CharField(db_column='PrdCod', max_length=30, null=True)
    codigo_barra = models.CharField(db_column='BarCodBar', max_length=20, null=True)
    estado = models.SmallIntegerField(db_column='BarEst', null=True)

    class Meta:
        managed = False
        db_table = 'PRODVENT'
        default_permissions = ()
        permissions = [('consultar_productos_inet', 'Puede consultar productos de I-NET')]
