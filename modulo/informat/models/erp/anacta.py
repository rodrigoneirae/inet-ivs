# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Anacta(models.Model):
    anatip = models.SmallIntegerField(db_column='AnaTip', primary_key=True)  # Field name made lowercase. The composite primary key (AnaTip, AnaCod, AnaSec) found, that is not supported. The first column is selected.
    anacod = models.DecimalField(db_column='AnaCod', max_digits=12, decimal_places=0)  # Field name made lowercase.
    anasec = models.SmallIntegerField(db_column='AnaSec')  # Field name made lowercase.
    anadve = models.CharField(db_column='AnaDve', max_length=1, blank=True, null=True)  # Field name made lowercase.
    ananom = models.CharField(db_column='AnaNom', max_length=40, blank=True, null=True)  # Field name made lowercase.
    anadir = models.CharField(db_column='AnaDir', max_length=40, blank=True, null=True)  # Field name made lowercase.
    anaciu = models.CharField(db_column='AnaCiu', max_length=15, blank=True, null=True)  # Field name made lowercase.
    anacom = models.CharField(db_column='AnaCom', max_length=15, blank=True, null=True)  # Field name made lowercase.
    anaprv = models.CharField(db_column='AnaPrv', max_length=40, blank=True, null=True)  # Field name made lowercase.
    anareg = models.CharField(db_column='AnaReg', max_length=30, blank=True, null=True)  # Field name made lowercase.
    anatel = models.CharField(db_column='AnaTel', max_length=20, blank=True, null=True)  # Field name made lowercase.
    anafax = models.CharField(db_column='AnaFax', max_length=20, blank=True, null=True)  # Field name made lowercase.
    anaeml = models.CharField(db_column='AnaEml', max_length=50, blank=True, null=True)  # Field name made lowercase.
    anawww = models.CharField(db_column='AnaWWW', max_length=50, blank=True, null=True)  # Field name made lowercase.
    anaapepat = models.CharField(db_column='AnaApePat', max_length=15, blank=True, null=True)  # Field name made lowercase.
    anaapemat = models.CharField(db_column='AnaApeMat', max_length=15, blank=True, null=True)  # Field name made lowercase.
    ananompil = models.CharField(db_column='AnaNomPil', max_length=20, blank=True, null=True)  # Field name made lowercase.
    anacodpos = models.CharField(db_column='AnaCodPos', max_length=10, blank=True, null=True)  # Field name made lowercase.
    egrfacod = models.CharField(db_column='EGRFACOD', max_length=3, blank=True, null=True)  # Field name made lowercase.
    ananumccc = models.CharField(db_column='ANANUMCCC', max_length=22, blank=True, null=True)  # Field name made lowercase.
    anaretru1 = models.IntegerField(db_column='AnaRetRu1', blank=True, null=True)  # Field name made lowercase.
    anaretdv1 = models.CharField(db_column='AnaRetDv1', max_length=1, blank=True, null=True)  # Field name made lowercase.
    anaretap1 = models.CharField(db_column='AnaRetAP1', max_length=15, blank=True, null=True)  # Field name made lowercase.
    anaretam1 = models.CharField(db_column='AnaRetAM1', max_length=15, blank=True, null=True)  # Field name made lowercase.
    anaretno1 = models.CharField(db_column='AnaRetNo1', max_length=15, blank=True, null=True)  # Field name made lowercase.
    anaretru2 = models.IntegerField(db_column='AnaRetRu2', blank=True, null=True)  # Field name made lowercase.
    anaretdv2 = models.CharField(db_column='AnaRetDv2', max_length=1, blank=True, null=True)  # Field name made lowercase.
    anaretap2 = models.CharField(db_column='AnaRetAP2', max_length=15, blank=True, null=True)  # Field name made lowercase.
    anaretam2 = models.CharField(db_column='AnaRetAM2', max_length=15, blank=True, null=True)  # Field name made lowercase.
    anaretno2 = models.CharField(db_column='AnaRetNo2', max_length=15, blank=True, null=True)  # Field name made lowercase.
    anasucbco = models.SmallIntegerField(db_column='AnaSucBco', blank=True, null=True)  # Field name made lowercase.
    egraecod = models.CharField(db_column='EGRAECOD', max_length=2, blank=True, null=True)  # Field name made lowercase.
    anacodmed = models.SmallIntegerField(db_column='ANACODMED', blank=True, null=True)  # Field name made lowercase.
    analastupd = models.DateTimeField(db_column='AnaLastUpd', blank=True, null=True)  # Field name made lowercase.
    anabcocod = models.SmallIntegerField(db_column='AnaBcoCod', blank=True, null=True)  # Field name made lowercase.
    anaindfac = models.SmallIntegerField(db_column='AnaIndFac', blank=True, null=True)  # Field name made lowercase.
    anaest = models.SmallIntegerField(db_column='AnaEst', blank=True, null=True)  # Field name made lowercase.
    anacodfis = models.CharField(db_column='AnaCodFis', max_length=20, blank=True, null=True)  # Field name made lowercase.
    anapaicod = models.SmallIntegerField(db_column='AnaPaiCod', blank=True, null=True)  # Field name made lowercase.
    anaiban = models.CharField(db_column='AnaIBAN', max_length=34, blank=True, null=True)  # Field name made lowercase.
    anaswift = models.CharField(db_column='AnaSWIFT', max_length=20, blank=True, null=True)  # Field name made lowercase.
    anactacte = models.CharField(db_column='AnaCtaCte', max_length=34, blank=True, null=True)  # Field name made lowercase.
    anaaba = models.CharField(db_column='AnaABA', max_length=10, blank=True, null=True)  # Field name made lowercase.
    anabancod = models.SmallIntegerField(db_column='AnaBanCod', blank=True, null=True)  # Field name made lowercase.
    anadirbco = models.CharField(db_column='AnaDirBco', max_length=80, blank=True, null=True)  # Field name made lowercase.
    anapobbco = models.CharField(db_column='AnaPobBco', max_length=25, blank=True, null=True)  # Field name made lowercase.
    anatippag = models.SmallIntegerField(db_column='AnaTipPag', blank=True, null=True)  # Field name made lowercase.
    anapaibco = models.SmallIntegerField(db_column='AnaPaiBco', blank=True, null=True)  # Field name made lowercase.
    anadirpos = models.CharField(db_column='AnaDirPos', max_length=60, blank=True, null=True)  # Field name made lowercase.
    anaaute = models.SmallIntegerField(db_column='ANAAUTE', blank=True, null=True)  # Field name made lowercase.
    anatipabo = models.SmallIntegerField(db_column='ANATIPABO', blank=True, null=True)  # Field name made lowercase.
    anafacod = models.SmallIntegerField(db_column='AnaFaCod', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        default_permissions = ()
        managed = False
        db_table = 'ANACTA'
        unique_together = (('anatip', 'anacod', 'anasec'),)



