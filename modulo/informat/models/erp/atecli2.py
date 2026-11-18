# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models
from modulos.inet.models.erp.prodvent import Prodvent
from django.forms import model_to_dict
from modulos.inet.models.erp.producto import ProductoInet


class Atecli2(models.Model):
    cajcod = models.SmallIntegerField(db_column='CajCod', primary_key=True)  # Field name made lowercase. The composite primary key (CajCod, DocCod, AteNumRea, AteBarLin) found, that is not supported. The first column is selected.
    doccod = models.SmallIntegerField(db_column='DocCod')  # Field name made lowercase.
    atenumrea = models.IntegerField(db_column='AteNumRea')  # Field name made lowercase.
    atebarlin = models.SmallIntegerField(db_column='AteBarLin')  # Field name made lowercase.
    barcod = models.CharField(db_column='BarCod', max_length=30, blank=True, null=True)  # Field name made lowercase.
    ateprclis = models.DecimalField(db_column='AtePrcLis', max_digits=13, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    ateprcbar = models.DecimalField(db_column='AtePrcBar', max_digits=13, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    ateqxp = models.DecimalField(db_column='AteQxP', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    atedsccodu = models.SmallIntegerField(db_column='AteDscCodU', blank=True, null=True)  # Field name made lowercase.
    atedscptju = models.DecimalField(db_column='AteDscPtjU', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    atedscnntu = models.DecimalField(db_column='AteDscNntU', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    atedsccodd = models.SmallIntegerField(db_column='AteDscCodD', blank=True, null=True)  # Field name made lowercase.
    atedscptjd = models.DecimalField(db_column='AteDscPtjD', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    atedscnntd = models.DecimalField(db_column='AteDscNntD', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    atedsccodt = models.SmallIntegerField(db_column='AteDscCodT', blank=True, null=True)  # Field name made lowercase.
    atedscptjt = models.DecimalField(db_column='AteDscPtjT', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    atedscnntt = models.DecimalField(db_column='AteDscNntT', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    atedsccodc = models.SmallIntegerField(db_column='AteDscCodC', blank=True, null=True)  # Field name made lowercase.
    atedscptjc = models.DecimalField(db_column='AteDscPtjC', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    atedscnntc = models.DecimalField(db_column='AteDscNntC', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    atercacodu = models.SmallIntegerField(db_column='AteRcaCodU', blank=True, null=True)  # Field name made lowercase.
    atercaptjl = models.DecimalField(db_column='AteRcaPtjL', max_digits=10, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    atercanntu = models.DecimalField(db_column='AteRcaNntU', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    prdidoptj = models.DecimalField(db_column='PrdIDoPtj', max_digits=10, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    prdiunptj = models.DecimalField(db_column='PrdIUnPtj', max_digits=10, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    atecanven = models.DecimalField(db_column='AteCanVen', max_digits=13, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    atecandes = models.DecimalField(db_column='AteCanDes', max_digits=13, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    atecanncr = models.DecimalField(db_column='AteCanNCr', max_digits=13, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    atetotlin = models.DecimalField(db_column='AteTotLin', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    atemonimpu = models.DecimalField(db_column='AteMonImpU', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    atemonimpd = models.DecimalField(db_column='AteMonImpD', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    ateobsglo = models.TextField(db_column='AteObsGlo', blank=True, null=True)  # Field name made lowercase. This field type is a guess.
    ateivapcj = models.DecimalField(db_column='AteIvaPcj', max_digits=10, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    ateivacod = models.SmallIntegerField(db_column='AteIvaCod', blank=True, null=True)  # Field name made lowercase.
    ateivamon = models.DecimalField(db_column='AteIvaMon', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    atefchent = models.DateTimeField(db_column='AteFchEnt', blank=True, null=True)  # Field name made lowercase.
    atelinuno = models.CharField(db_column='AteLinUno', max_length=60, blank=True, null=True)  # Field name made lowercase.
    atelindos = models.CharField(db_column='AteLinDos', max_length=60, blank=True, null=True)  # Field name made lowercase.
    atelintre = models.CharField(db_column='AteLinTre', max_length=60, blank=True, null=True)  # Field name made lowercase.
    atecandev = models.DecimalField(db_column='AteCanDev', max_digits=13, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    atecarsec = models.SmallIntegerField(db_column='AteCarSec', blank=True, null=True)  # Field name made lowercase.
    atecarnum = models.IntegerField(db_column='AteCarNum', blank=True, null=True)  # Field name made lowercase.
    atecartip = models.SmallIntegerField(db_column='AteCarTip', blank=True, null=True)  # Field name made lowercase.
    atecarsuc = models.SmallIntegerField(db_column='AteCarSuc', blank=True, null=True)  # Field name made lowercase.
    atecliprd = models.CharField(db_column='AteCliPrd', max_length=30, blank=True, null=True)  # Field name made lowercase.
    ateobsgl7 = models.CharField(db_column='AteObsGl7', max_length=60, blank=True, null=True)  # Field name made lowercase.
    ateobsgl6 = models.CharField(db_column='AteObsGl6', max_length=60, blank=True, null=True)  # Field name made lowercase.
    ateobsgl5 = models.CharField(db_column='AteObsGl5', max_length=60, blank=True, null=True)  # Field name made lowercase.
    ateobsgl4 = models.CharField(db_column='AteObsGl4', max_length=60, blank=True, null=True)  # Field name made lowercase.
    ateobsgl3 = models.CharField(db_column='AteObsGl3', max_length=60, blank=True, null=True)  # Field name made lowercase.
    ateobsgl2 = models.CharField(db_column='AteObsGl2', max_length=60, blank=True, null=True)  # Field name made lowercase.
    ateobsgl1 = models.CharField(db_column='AteObsGl1', max_length=60, blank=True, null=True)  # Field name made lowercase.
    atecosven = models.DecimalField(db_column='AteCosVen', max_digits=20, decimal_places=2, blank=True, null=True)  # Field name made lowercase.
    atecannca = models.DecimalField(db_column='ATECANNCA', max_digits=13, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    ateprcnet = models.DecimalField(db_column='Ateprcnet', max_digits=13, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    atecanfor = models.DecimalField(db_column='ATECANFOR', max_digits=13, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    atevaltdr = models.DecimalField(db_column='AteValTdr', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    atebarlar = models.DecimalField(db_column='AteBarLar', max_digits=8, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    atebaranc = models.DecimalField(db_column='AteBarAnc', max_digits=8, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    ateprepr = models.DecimalField(db_column='AtePrePr', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    atecomi1 = models.DecimalField(db_column='AteComi1', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    atecomi2 = models.DecimalField(db_column='AteComi2', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    atecomi3 = models.DecimalField(db_column='AteComi3', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    atecomi4 = models.DecimalField(db_column='AteComi4', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    ateembsuc = models.SmallIntegerField(db_column='AteEmbSuc', blank=True, null=True)  # Field name made lowercase.
    ateembnum = models.CharField(db_column='AteEmbNum', max_length=20, blank=True, null=True)  # Field name made lowercase.
    atesecalm = models.SmallIntegerField(db_column='AteSecAlm', blank=True, null=True)  # Field name made lowercase.
    ateemcbam = models.IntegerField(db_column='AteEmCbAm', blank=True, null=True)  # Field name made lowercase.
    ateemcbsu = models.SmallIntegerField(db_column='AteEmCbSu', blank=True, null=True)  # Field name made lowercase.
    ateemcbti = models.SmallIntegerField(db_column='AteEmCbTi', blank=True, null=True)  # Field name made lowercase.
    ateemcbnu = models.IntegerField(db_column='AteEmCbNu', blank=True, null=True)  # Field name made lowercase.
    atepreccif = models.DecimalField(db_column='AtePrecCif', max_digits=13, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    ateporimpt = models.DecimalField(db_column='AtePorImpt', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    ateb2bsuc = models.CharField(db_column='AteB2bSuc', max_length=10, blank=True, null=True)  # Field name made lowercase.
    ateb2bdep = models.CharField(db_column='AteB2bDep', max_length=10, blank=True, null=True)  # Field name made lowercase.
    ateb2bbul = models.DecimalField(db_column='AteB2bbul', max_digits=13, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    ateb2bcor = models.DecimalField(db_column='AteB2bCor', max_digits=11, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    atemonimpc = models.DecimalField(db_column='AteMonImpC', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    atefchen2 = models.DateTimeField(db_column='AteFchEn2', blank=True, null=True)  # Field name made lowercase.
    ateagven1 = models.SmallIntegerField(db_column='AteAGVen1', blank=True, null=True)  # Field name made lowercase.
    ateagpor1 = models.DecimalField(db_column='AteAGPor1', max_digits=7, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    ateagven2 = models.SmallIntegerField(db_column='AteAGVen2', blank=True, null=True)  # Field name made lowercase.
    ateagpor2 = models.DecimalField(db_column='AteAGPor2', max_digits=7, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    ateagven3 = models.SmallIntegerField(db_column='AteAGVen3', blank=True, null=True)  # Field name made lowercase.
    ateagpor3 = models.DecimalField(db_column='AteAGPor3', max_digits=7, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    ateagven4 = models.SmallIntegerField(db_column='AteAGVen4', blank=True, null=True)  # Field name made lowercase.
    ateagpor4 = models.DecimalField(db_column='AteAGPor4', max_digits=7, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    ateobsgl8 = models.CharField(db_column='AteObsGl8', max_length=60, blank=True, null=True)  # Field name made lowercase.
    ateobsgl9 = models.CharField(db_column='AteObsGl9', max_length=60, blank=True, null=True)  # Field name made lowercase.
    ateobsgl10 = models.CharField(db_column='AteObsGl10', max_length=60, blank=True, null=True)  # Field name made lowercase.
    ateobsgl11 = models.CharField(db_column='AteObsGl11', max_length=60, blank=True, null=True)  # Field name made lowercase.
    ateobsgl12 = models.CharField(db_column='AteObsGl12', max_length=60, blank=True, null=True)  # Field name made lowercase.
    ateobsgl13 = models.CharField(db_column='AteObsGl13', max_length=60, blank=True, null=True)  # Field name made lowercase.
    ateobsgl14 = models.CharField(db_column='AteObsGl14', max_length=60, blank=True, null=True)  # Field name made lowercase.
    ateobsgl15 = models.CharField(db_column='AteObsGl15', max_length=60, blank=True, null=True)  # Field name made lowercase.
    ateobsgl16 = models.CharField(db_column='AteObsGl16', max_length=60, blank=True, null=True)  # Field name made lowercase.
    ateobsgl17 = models.CharField(db_column='AteObsGl17', max_length=60, blank=True, null=True)  # Field name made lowercase.
    ateobsgl18 = models.CharField(db_column='AteObsGl18', max_length=60, blank=True, null=True)  # Field name made lowercase.
    ateobsgl19 = models.CharField(db_column='AteObsGl19', max_length=60, blank=True, null=True)  # Field name made lowercase.
    ateobsgl20 = models.CharField(db_column='AteObsGl20', max_length=60, blank=True, null=True)  # Field name made lowercase.
    ateb2bnod = models.CharField(db_column='AteB2bNod', max_length=50, blank=True, null=True)  # Field name made lowercase.
    atecli21 = models.SmallIntegerField(db_column='AteCli21', blank=True, null=True)  # Field name made lowercase.
    atecli22 = models.IntegerField(db_column='AteCli22', blank=True, null=True)  # Field name made lowercase.
    atecli23 = models.SmallIntegerField(db_column='AteCli23', blank=True, null=True)  # Field name made lowercase.
    atecli24 = models.IntegerField(db_column='AteCli24', blank=True, null=True)  # Field name made lowercase.
    sfatecosv = models.DecimalField(db_column='SFAteCosV', max_digits=20, decimal_places=2, blank=True, null=True)  # Field name made lowercase.
    atebarulc = models.SmallIntegerField(db_column='AteBarUlC', blank=True, null=True)  # Field name made lowercase.
    atecosotr = models.DecimalField(db_column='AteCosOtr', max_digits=19, decimal_places=4)  # Field name made lowercase.
    atercaptju = models.DecimalField(db_column='AteRcaPtjU', max_digits=19, decimal_places=4)  # Field name made lowercase.
    ateprcsup = models.DecimalField(db_column='AtePrcSup', max_digits=13, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    ateisuptj = models.DecimalField(db_column='AteIsuPtj', max_digits=13, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    atelistipf = models.SmallIntegerField(db_column='AteLisTipF', blank=True, null=True)  # Field name made lowercase.
    atelisporf = models.IntegerField(db_column='AteLisPorF', blank=True, null=True)  # Field name made lowercase.
    atelispref = models.DecimalField(db_column='AteLisPreF', max_digits=13, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    ateprcbarb = models.DecimalField(db_column='AtePrcBarB', max_digits=14, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    ate_paso = models.CharField(db_column='Ate_Paso', max_length=1, blank=True, null=True)  # Field name made lowercase.
    atemonimpt = models.DecimalField(db_column='AteMonImpT', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    atemonimpp = models.DecimalField(db_column='AteMonImpP', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    atelinoc = models.SmallIntegerField(db_column='AteLinOC', blank=True, null=True)  # Field name made lowercase.
    ateobsgl21 = models.CharField(db_column='AteObsGl21', max_length=60, blank=True, null=True)  # Field name made lowercase.
    ateobsgl22 = models.CharField(db_column='AteObsGl22', max_length=60, blank=True, null=True)  # Field name made lowercase.
    ateobsgl23 = models.CharField(db_column='AteObsGl23', max_length=60, blank=True, null=True)  # Field name made lowercase.
    ateobsgl24 = models.CharField(db_column='AteObsGl24', max_length=60, blank=True, null=True)  # Field name made lowercase.
    ateobsgl25 = models.CharField(db_column='AteObsGl25', max_length=60, blank=True, null=True)  # Field name made lowercase.
    ateobsgl26 = models.CharField(db_column='AteObsGl26', max_length=60, blank=True, null=True)  # Field name made lowercase.
    ateobsgl27 = models.CharField(db_column='AteObsGl27', max_length=60, blank=True, null=True)  # Field name made lowercase.
    ateobsgl28 = models.CharField(db_column='AteObsGl28', max_length=60, blank=True, null=True)  # Field name made lowercase.
    ateobsgl29 = models.CharField(db_column='AteObsGl29', max_length=60, blank=True, null=True)  # Field name made lowercase.
    ateobsgl30 = models.CharField(db_column='AteObsGl30', max_length=60, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        default_permissions = ()
        managed = False
        db_table = 'ATECLI2'
        unique_together = (('cajcod', 'doccod', 'atenumrea', 'atebarlin'),)

    @property
    def descripcion_corta(self):

        prod=Prodvent.objects.filter(barcod=self.barcod).using('inet').last()

        if prod:
            return prod.bardsccor

        return ''

    @property
    def data_prod_venta(self):
        return ProductoInet.objects.filter(prdcod=self.barcod).using('inet').last()



    def to_json(self):
        # item = model_to_dict(self, exclude=['password', 'user_permissions'])
        item = model_to_dict(self)

        return item