# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Bodegas(models.Model):
    bodcod = models.IntegerField(db_column='BodCod', primary_key=True)  # Field name made lowercase.
    bodnom = models.CharField(db_column='BodNom', max_length=35, blank=True, null=True)  # Field name made lowercase.
    bodstkest = models.CharField(db_column='BodStkEst', max_length=1, blank=True, null=True)  # Field name made lowercase.
    boddir = models.CharField(db_column='BodDir', max_length=70, blank=True, null=True)  # Field name made lowercase.
    bodcom = models.CharField(db_column='BodCom', max_length=35, blank=True, null=True)  # Field name made lowercase.
    bodciu = models.CharField(db_column='BodCiu', max_length=35, blank=True, null=True)  # Field name made lowercase.
    bodrut = models.DecimalField(db_column='BodRut', max_digits=11, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    bodres = models.CharField(db_column='BodRes', max_length=50, blank=True, null=True)  # Field name made lowercase.
    bodsuccod = models.SmallIntegerField(db_column='BodSucCod', blank=True, null=True)  # Field name made lowercase.
    exictcod = models.SmallIntegerField(db_column='ExiCTCod', blank=True, null=True)  # Field name made lowercase.
    bodubi = models.SmallIntegerField(db_column='BodUbi', blank=True, null=True)  # Field name made lowercase.
    bodcencod = models.IntegerField(db_column='BodCenCod', blank=True, null=True)  # Field name made lowercase.
    bodlastupd = models.DateTimeField(db_column='BodLastUpd', blank=True, null=True)  # Field name made lowercase.
    bodaccctrl = models.SmallIntegerField(db_column='BodAccCtrl', blank=True, null=True)  # Field name made lowercase.
    bodcodcrmk = models.CharField(db_column='BodCodCrmK', max_length=50)  # Field name made lowercase.
    bodcodpos = models.CharField(db_column='BodCodPos', max_length=30, blank=True, null=True)  # Field name made lowercase.
    bodvtapdv = models.SmallIntegerField(db_column='BodVtaPDV', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        default_permissions = ()
        managed = False
        db_table = 'BODEGAS'
