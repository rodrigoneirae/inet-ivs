# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Viades(models.Model):
    vfaviacod = models.SmallIntegerField(db_column='VfaViaCod', primary_key=True)  # Field name made lowercase.
    vfaviadsc = models.CharField(db_column='VfaViaDsc', max_length=25, blank=True, null=True)  # Field name made lowercase.
    vfaviadis = models.SmallIntegerField(db_column='VfaViaDis', blank=True, null=True)  # Field name made lowercase.
    vialastupd = models.DateTimeField(db_column='ViaLastUpd', blank=True, null=True)  # Field name made lowercase.
    viacodcrmk = models.CharField(db_column='ViaCodCrmK', max_length=50)  # Field name made lowercase.

    class Meta:
        default_permissions = ()
        managed = False
        db_table = 'VIADES'
