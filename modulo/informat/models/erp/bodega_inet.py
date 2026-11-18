from django.db import models


class BodegaInet(models.Model):
    """Maestro I-NET de solo lectura; no crear ni migrar la tabla externa."""

    codigo = models.IntegerField(db_column='BodCod', primary_key=True)
    nombre = models.CharField(db_column='BodNom', max_length=35, null=True)
    estado_stock = models.CharField(db_column='BodStkEst', max_length=1, null=True)
    sucursal_codigo = models.SmallIntegerField(db_column='BodSucCod', null=True)
    usa_ubicaciones = models.SmallIntegerField(db_column='BodUbi', null=True)

    class Meta:
        managed = False
        db_table = 'BODEGAS'
        default_permissions = ()
        permissions = [('consultar_bodegas_inet', 'Puede consultar bodegas de I-NET')]
