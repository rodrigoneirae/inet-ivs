from django.db import models
from modulos.inet.models.erp.anacta import Anacta


class Vendores(models.Model):
    ventip = models.SmallIntegerField(db_column='VenTip',
                                      primary_key=True)  # Field name made lowercase. The composite primary key (VenTip, VenCod, VenSec) found, that is not supported. The first column is selected.
    vencod = models.DecimalField(db_column='VenCod', max_digits=12, decimal_places=0)  # Field name made lowercase.
    vensec = models.SmallIntegerField(db_column='VenSec')  # Field name made lowercase.
    vencodalt = models.CharField(db_column='VenCodAlt', max_length=8, blank=True,
                                 null=True)  # Field name made lowercase.
    vensuccod = models.SmallIntegerField(db_column='VenSucCod', blank=True, null=True)  # Field name made lowercase.
    vencat = models.SmallIntegerField(db_column='VenCat', blank=True, null=True)  # Field name made lowercase.
    supvencod = models.DecimalField(db_column='SupVenCod', max_digits=12, decimal_places=0, blank=True,
                                    null=True)  # Field name made lowercase.
    vencencod = models.IntegerField(db_column='VenCenCod', blank=True, null=True)  # Field name made lowercase.
    vencmicod = models.SmallIntegerField(db_column='VenCmiCod', blank=True, null=True)  # Field name made lowercase.
    venmetene = models.DecimalField(db_column='VenMetEne', max_digits=19, decimal_places=4, blank=True,
                                    null=True)  # Field name made lowercase.
    venmetfeb = models.DecimalField(db_column='VenMetFeb', max_digits=19, decimal_places=4, blank=True,
                                    null=True)  # Field name made lowercase.
    venmetmar = models.DecimalField(db_column='VenMetMar', max_digits=19, decimal_places=4, blank=True,
                                    null=True)  # Field name made lowercase.
    venmetabr = models.DecimalField(db_column='VenMetAbr', max_digits=19, decimal_places=4, blank=True,
                                    null=True)  # Field name made lowercase.
    venmetmay = models.DecimalField(db_column='VenMetMay', max_digits=19, decimal_places=4, blank=True,
                                    null=True)  # Field name made lowercase.
    venmetjun = models.DecimalField(db_column='VenMetJun', max_digits=19, decimal_places=4, blank=True,
                                    null=True)  # Field name made lowercase.
    venmetjul = models.DecimalField(db_column='VenMetJul', max_digits=19, decimal_places=4, blank=True,
                                    null=True)  # Field name made lowercase.
    venmetago = models.DecimalField(db_column='VenMetAgo', max_digits=19, decimal_places=4, blank=True,
                                    null=True)  # Field name made lowercase.
    venmetsep = models.DecimalField(db_column='VenMetSep', max_digits=19, decimal_places=4, blank=True,
                                    null=True)  # Field name made lowercase.
    venmetoct = models.DecimalField(db_column='VenMetOct', max_digits=19, decimal_places=4, blank=True,
                                    null=True)  # Field name made lowercase.
    venmetnov = models.DecimalField(db_column='VenMetNov', max_digits=19, decimal_places=4, blank=True,
                                    null=True)  # Field name made lowercase.
    venmetdic = models.DecimalField(db_column='VenMetDic', max_digits=19, decimal_places=4, blank=True,
                                    null=True)  # Field name made lowercase.
    venultlin = models.SmallIntegerField(db_column='VenUltLin', blank=True, null=True)  # Field name made lowercase.
    venest = models.CharField(db_column='VenEst', max_length=1, blank=True, null=True)  # Field name made lowercase.
    venlastupd = models.DateTimeField(db_column='VenLastUpd', blank=True, null=True)  # Field name made lowercase.
    vencodcrmk = models.CharField(db_column='VenCodCrmK', max_length=50)  # Field name made lowercase.
    vencoinve = models.CharField(db_column='VenCoInVe', max_length=60, blank=True,
                                 null=True)  # Field name made lowercase.
    ananom = models.CharField(db_column='AnaNom', max_length=40, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        default_permissions = ()
        managed = False
        db_table = 'VENDORES'
        unique_together = (('ventip', 'vencod', 'vensec'),)

    @property
    def nombre(self):
        anacta = Anacta.objects.using('inet').filter(anacod=self.vencod).last()

        if anacta:
            return anacta.ananom.strip()

        return None
