# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Listprec(models.Model):
    liscod = models.SmallIntegerField(db_column='LisCod', primary_key=True)  # Field name made lowercase.
    succod = models.SmallIntegerField(db_column='SucCod', blank=True, null=True)  # Field name made lowercase.
    lisnom = models.CharField(db_column='LisNom', max_length=25, blank=True, null=True)  # Field name made lowercase.
    lisfchini = models.DateTimeField(db_column='LisFchIni', blank=True, null=True)  # Field name made lowercase.
    lisfchfin = models.DateTimeField(db_column='LisFchFin', blank=True, null=True)  # Field name made lowercase.
    lisest = models.SmallIntegerField(db_column='LisEst', blank=True, null=True)  # Field name made lowercase.
    listip = models.SmallIntegerField(db_column='LisTip', blank=True, null=True)  # Field name made lowercase.
    moncod = models.SmallIntegerField(db_column='MonCod', blank=True, null=True)  # Field name made lowercase.
    listippre = models.CharField(db_column='Listippre', max_length=1, blank=True, null=True)  # Field name made lowercase.
    lislastupd = models.DateTimeField(db_column='LisLastUpd', blank=True, null=True)  # Field name made lowercase.
    lishorini = models.CharField(db_column='LisHorIni', max_length=10, blank=True, null=True)  # Field name made lowercase.
    lishorfin = models.CharField(db_column='LisHorFin', max_length=10, blank=True, null=True)  # Field name made lowercase.
    lisprepdv = models.SmallIntegerField(db_column='LisPrePDV', blank=True, null=True)  # Field name made lowercase.
    lishor = models.CharField(db_column='LisHor', max_length=10, blank=True, null=True)  # Field name made lowercase.
    lisfledsc = models.SmallIntegerField(db_column='LisFleDsc', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        default_permissions = ()
        managed = False
        db_table = 'LISTPREC'
