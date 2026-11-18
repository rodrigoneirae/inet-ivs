# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models
from django.forms import model_to_dict
from pyasn1_modules.rfc2985 import ietf_at

from modulos.inet.models.erp.listpre1 import Listpre1
from apps_satventas.settings import BASE_DIR
import os,base64

class Prodvent(models.Model):
    barcod = models.CharField(db_column='BarCod', primary_key=True, max_length=30)  # Field name made lowercase.
    barcmicod = models.SmallIntegerField(db_column='BarCmiCod', blank=True, null=True)  # Field name made lowercase.
    bardsccor = models.CharField(db_column='BarDscCor', max_length=25, blank=True, null=True)  # Field name made lowercase.
    bardsclar = models.CharField(db_column='BarDscLar', max_length=60, blank=True, null=True)  # Field name made lowercase.
    barfac = models.DecimalField(db_column='BarFac', max_digits=8, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    barunicod = models.SmallIntegerField(db_column='BarUniCod', blank=True, null=True)  # Field name made lowercase.
    prdcod = models.CharField(db_column='PrdCod', max_length=30, blank=True, null=True)  # Field name made lowercase.
    prdidocod = models.SmallIntegerField(db_column='PrdIDoCod', blank=True, null=True)  # Field name made lowercase.
    prdiuncod = models.SmallIntegerField(db_column='PrdIUnCod', blank=True, null=True)  # Field name made lowercase.
    avecuacod = models.DecimalField(db_column='AVeCuaCod', max_digits=10, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    avedoscod = models.DecimalField(db_column='AVeDosCod', max_digits=10, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    avetrecod = models.DecimalField(db_column='AVeTreCod', max_digits=10, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    aveunocod = models.DecimalField(db_column='AVeUnoCod', max_digits=10, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    barplacod = models.CharField(db_column='BarPlaCod', max_length=9, blank=True, null=True)  # Field name made lowercase.
    bararecod = models.SmallIntegerField(db_column='BarAreCod', blank=True, null=True)  # Field name made lowercase.
    barcencod = models.IntegerField(db_column='BarCenCod', blank=True, null=True)  # Field name made lowercase.
    baritecod = models.SmallIntegerField(db_column='BarIteCod', blank=True, null=True)  # Field name made lowercase.
    barplacoc = models.CharField(db_column='BarPlaCoc', max_length=9, blank=True, null=True)  # Field name made lowercase.
    barcencoc = models.IntegerField(db_column='BarCenCoc', blank=True, null=True)  # Field name made lowercase.
    bararecoc = models.SmallIntegerField(db_column='BarAreCoc', blank=True, null=True)  # Field name made lowercase.
    baritecoc = models.SmallIntegerField(db_column='BarIteCoc', blank=True, null=True)  # Field name made lowercase.
    barpes = models.DecimalField(db_column='BarPes', max_digits=8, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    barvol = models.DecimalField(db_column='BarVol', max_digits=8, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    barima = models.CharField(db_column='BarIma', max_length=50, blank=True, null=True)  # Field name made lowercase.
    baresptec = models.TextField(db_column='BarEspTec', blank=True, null=True)  # Field name made lowercase. This field type is a guess.
    avecincod = models.DecimalField(db_column='AVeCinCod', max_digits=10, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    barlar = models.DecimalField(db_column='BarLar', max_digits=8, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    baranc = models.DecimalField(db_column='BarAnc', max_digits=8, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    baralt = models.DecimalField(db_column='BarAlt', max_digits=8, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    barlaranc = models.SmallIntegerField(db_column='BarLarAnc', blank=True, null=True)  # Field name made lowercase.
    barimpori = models.SmallIntegerField(db_column='BarImpOri', blank=True, null=True)  # Field name made lowercase.
    barcodori = models.CharField(db_column='BarCodOri', max_length=30, blank=True, null=True)  # Field name made lowercase.
    barcomim = models.SmallIntegerField(db_column='BarComIm', blank=True, null=True)  # Field name made lowercase.
    barcodbar = models.CharField(db_column='BarCodBar', max_length=20, blank=True, null=True)  # Field name made lowercase.
    barattbi1 = models.CharField(db_column='BarAttBI1', max_length=15, blank=True, null=True)  # Field name made lowercase.
    barattbi2 = models.CharField(db_column='BarAttBI2', max_length=15, blank=True, null=True)  # Field name made lowercase.
    barattbi3 = models.CharField(db_column='BarAttBI3', max_length=15, blank=True, null=True)  # Field name made lowercase.
    barattbi4 = models.CharField(db_column='BarAttBI4', max_length=15, blank=True, null=True)  # Field name made lowercase.
    barattbi5 = models.CharField(db_column='BarAttBI5', max_length=15, blank=True, null=True)  # Field name made lowercase.
    barafe = models.SmallIntegerField(db_column='BarAfe', blank=True, null=True)  # Field name made lowercase.
    barvigenc = models.DateTimeField(db_column='BarVigenc', blank=True, null=True)  # Field name made lowercase.
    barregsan = models.CharField(db_column='BarRegSan', max_length=16, blank=True, null=True)  # Field name made lowercase.
    bardscint = models.CharField(db_column='BarDscInt', max_length=50, blank=True, null=True)  # Field name made lowercase.
    barfaces = models.DecimalField(db_column='BarFacEs', max_digits=8, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    baradiuno = models.CharField(db_column='BarAdiUno', max_length=30, blank=True, null=True)  # Field name made lowercase.
    baradidos = models.CharField(db_column='BarAdiDos', max_length=30, blank=True, null=True)  # Field name made lowercase.
    baraditre = models.CharField(db_column='BarAdiTre', max_length=30, blank=True, null=True)  # Field name made lowercase.
    baradicua = models.CharField(db_column='BarAdiCua', max_length=30, blank=True, null=True)  # Field name made lowercase.
    baradicin = models.CharField(db_column='BarAdiCin', max_length=30, blank=True, null=True)  # Field name made lowercase.
    barlastupd = models.DateTimeField(db_column='BarLastUpd', blank=True, null=True)  # Field name made lowercase.
    barest = models.SmallIntegerField(db_column='BarEst', blank=True, null=True)  # Field name made lowercase.
    barcodcrmk = models.CharField(db_column='BarCodCrmK', max_length=50)  # Field name made lowercase.
    prdisucod = models.SmallIntegerField(db_column='PrdISuCod', blank=True, null=True)  # Field name made lowercase.
    barnofac = models.SmallIntegerField(db_column='BarNoFac', blank=True, null=True)  # Field name made lowercase.
    barccenfa = models.SmallIntegerField(db_column='BarCCeNFa', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        default_permissions = ()
        managed = False
        db_table = 'PRODVENT'

    @property
    def producto(self):
        return

    def to_json(self):
        item = model_to_dict(self)

        return item





