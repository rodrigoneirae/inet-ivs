# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Tabad2(models.Model):
    at2cod = models.CharField(db_column='At2Cod', primary_key=True, max_length=10)  # Field name made lowercase.
    at2nom = models.CharField(db_column='At2Nom', max_length=50, blank=True, null=True)  # Field name made lowercase.
    at2abr = models.CharField(db_column='At2Abr', max_length=20, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'TABAD2'
