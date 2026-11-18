# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Ateclie2(models.Model):
    cajcod = models.SmallIntegerField(db_column='CajCod', primary_key=True)  # Field name made lowercase. The composite primary key (CajCod, DocCod, AteNumRea, AteLinTot) found, that is not supported. The first column is selected.
    doccod = models.SmallIntegerField(db_column='DocCod')  # Field name made lowercase.
    atenumrea = models.IntegerField(db_column='AteNumRea')  # Field name made lowercase.
    atelintot = models.SmallIntegerField(db_column='AteLinTot')  # Field name made lowercase.
    ccecod = models.SmallIntegerField(db_column='CceCod', blank=True, null=True)  # Field name made lowercase.
    atefor = models.CharField(db_column='AteFor', max_length=100, blank=True, null=True)  # Field name made lowercase.
    atetasa = models.DecimalField(db_column='AteTasa', max_digits=10, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    atebase = models.CharField(db_column='AteBase', max_length=5, blank=True, null=True)  # Field name made lowercase.
    atecollib = models.SmallIntegerField(db_column='AteColLib', blank=True, null=True)  # Field name made lowercase.
    atetotnom = models.CharField(db_column='AteTotNom', max_length=20, blank=True, null=True)  # Field name made lowercase.
    atetotimp = models.SmallIntegerField(db_column='AteTotImp', blank=True, null=True)  # Field name made lowercase.
    atetotval = models.DecimalField(db_column='AteTotVal', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        default_permissions = ()
        managed = False
        db_table = 'ATECLIE2'
        unique_together = (('cajcod', 'doccod', 'atenumrea', 'atelintot'),)
