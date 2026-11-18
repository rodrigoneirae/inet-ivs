# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Condvent(models.Model):
    covcod = models.SmallIntegerField(db_column='CoVCod', primary_key=True)  # Field name made lowercase.
    covnom = models.CharField(db_column='CoVNom', max_length=25, blank=True, null=True)  # Field name made lowercase.
    covdocadj = models.SmallIntegerField(db_column='CoVDocAdj', blank=True, null=True)  # Field name made lowercase.
    covnumven = models.SmallIntegerField(db_column='CoVNumVen', blank=True, null=True)  # Field name made lowercase.
    covsumdia = models.SmallIntegerField(db_column='CoVSumDia', blank=True, null=True)  # Field name made lowercase.
    covcal = models.SmallIntegerField(db_column='CoVCal', blank=True, null=True)  # Field name made lowercase.
    covretlim = models.SmallIntegerField(db_column='COVRETLIM', blank=True, null=True)  # Field name made lowercase.
    covconven = models.SmallIntegerField(db_column='CovConVen', blank=True, null=True)  # Field name made lowercase.
    covlastupd = models.DateTimeField(db_column='CovLastUpd')  # Field name made lowercase.
    covcodcrmk = models.CharField(db_column='CoVCodCrmK', max_length=50)  # Field name made lowercase.
    covcliadi = models.SmallIntegerField(db_column='CovCliAdi', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        default_permissions = ()
        managed = False
        db_table = 'CONDVENT'
