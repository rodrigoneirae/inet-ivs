from django.db import models


class Pvebar(models.Model):
    barcod = models.CharField(db_column='BarCod', primary_key=True, max_length=30)  # Field name made lowercase. The composite primary key (BarCod, BarBarCod) found, that is not supported. The first column is selected.
    barbarcod = models.CharField(db_column='BarBarCod', max_length=20)  # Field name made lowercase.
    barbarlupd = models.DateTimeField(db_column='BarBarLUpd', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'PVEBAR'
        unique_together = (('barcod', 'barbarcod'),)
