# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models
from django.forms import model_to_dict
from modulos.inet.models.erp.listpre1 import Listpre1
from modulos.inet.models.erp.tabad2 import Tabad2
from apps_satventas.settings import BASE_DIR
import os,base64


class ProductoInet(models.Model):
    prdcod = models.CharField(db_column='PrdCod', primary_key=True, max_length=30)  # Field name made lowercase.
    prddestra = models.CharField(db_column='PrdDesTra', max_length=50, blank=True, null=True)  # Field name made lowercase.
    prddescom = models.CharField(db_column='PrdDesCom', max_length=50, blank=True, null=True)  # Field name made lowercase.
    prdmessto = models.IntegerField(db_column='PrdMesSto', blank=True, null=True)  # Field name made lowercase.
    prdsuscod = models.CharField(db_column='PrdSusCod', max_length=30, blank=True, null=True)  # Field name made lowercase.
    prdctlser = models.SmallIntegerField(db_column='PrdCtlSer', blank=True, null=True)  # Field name made lowercase.
    prdfaccon = models.DecimalField(db_column='PrdFacCon', max_digits=6, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    prdunicod = models.SmallIntegerField(db_column='PrdUniCod', blank=True, null=True)  # Field name made lowercase.
    prddeslar = models.TextField(db_column='PrdDesLar', blank=True, null=True)  # Field name made lowercase. This field type is a guess.
    prdexipla = models.CharField(db_column='PrdExiPla', max_length=9, blank=True, null=True)  # Field name made lowercase.
    prdcom = models.SmallIntegerField(db_column='PrdCom', blank=True, null=True)  # Field name made lowercase.
    prdori = models.SmallIntegerField(db_column='PrdOri', blank=True, null=True)  # Field name made lowercase.
    prdpes = models.DecimalField(db_column='PrdPes', max_digits=8, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    prdvol = models.DecimalField(db_column='PrdVol', max_digits=8, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    prdmoncod = models.SmallIntegerField(db_column='PrdMonCod', blank=True, null=True)  # Field name made lowercase.
    at1cod = models.CharField(db_column='At1Cod', max_length=10, blank=True, null=True)  # Field name made lowercase.
    at2cod = models.CharField(db_column='At2Cod', max_length=10, blank=True, null=True)  # Field name made lowercase.
    at3cod = models.CharField(db_column='At3Cod', max_length=10, blank=True, null=True)  # Field name made lowercase.
    at4cod = models.CharField(db_column='At4Cod', max_length=10, blank=True, null=True)  # Field name made lowercase.
    at5cod = models.CharField(db_column='At5Cod', max_length=10, blank=True, null=True)  # Field name made lowercase.
    prdctllot = models.SmallIntegerField(db_column='PrdCtlLot', blank=True, null=True)  # Field name made lowercase.
    prdsdeent = models.SmallIntegerField(db_column='PrdSDeEnt', blank=True, null=True)  # Field name made lowercase.
    prdsdesal = models.SmallIntegerField(db_column='PrdSDeSal', blank=True, null=True)  # Field name made lowercase.
    prdsfeent = models.SmallIntegerField(db_column='PrdSFeEnt', blank=True, null=True)  # Field name made lowercase.
    prdsfesal = models.SmallIntegerField(db_column='PrdSFeSal', blank=True, null=True)  # Field name made lowercase.
    prdlotnum = models.CharField(db_column='PrdLotNum', max_length=20, blank=True, null=True)  # Field name made lowercase.
    prdlotdes = models.CharField(db_column='PrdLotDes', max_length=20, blank=True, null=True)  # Field name made lowercase.
    prdlotfec = models.CharField(db_column='PrdLotFec', max_length=20, blank=True, null=True)  # Field name made lowercase.
    prdldeent = models.SmallIntegerField(db_column='PrdLDeEnt', blank=True, null=True)  # Field name made lowercase.
    prdldesal = models.SmallIntegerField(db_column='PrdLDeSal', blank=True, null=True)  # Field name made lowercase.
    prdlfeent = models.SmallIntegerField(db_column='PrdLFeEnt', blank=True, null=True)  # Field name made lowercase.
    prdlfesal = models.SmallIntegerField(db_column='PrdLFeSal', blank=True, null=True)  # Field name made lowercase.
    prdsernum = models.CharField(db_column='PrdSerNum', max_length=20, blank=True, null=True)  # Field name made lowercase.
    prdserdes = models.CharField(db_column='PrdSerDes', max_length=20, blank=True, null=True)  # Field name made lowercase.
    prdserfec = models.CharField(db_column='PrdSerFec', max_length=20, blank=True, null=True)  # Field name made lowercase.
    prdcos = models.DecimalField(db_column='PrdCos', max_digits=13, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    prdest = models.SmallIntegerField(db_column='PrdEst', blank=True, null=True)  # Field name made lowercase.
    prdultpre = models.DecimalField(db_column='PrdUltPre', max_digits=13, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    prdprerep = models.DecimalField(db_column='PrdPreRep', max_digits=13, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    prduniequ = models.DecimalField(db_column='PrdUniEqu', max_digits=8, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    prdultfec = models.DateTimeField(db_column='PrdultFec', blank=True, null=True)  # Field name made lowercase.
    prducocod = models.SmallIntegerField(db_column='PrdUCoCod', blank=True, null=True)  # Field name made lowercase.
    prdbarcod = models.CharField(db_column='PrdBarCod', max_length=20, blank=True, null=True)  # Field name made lowercase.
    prdim1cod = models.SmallIntegerField(db_column='PrdIm1Cod', blank=True, null=True)  # Field name made lowercase.
    prdim2cod = models.SmallIntegerField(db_column='PrdIm2Cod', blank=True, null=True)  # Field name made lowercase.
    prdimpfac = models.DecimalField(db_column='PrdImpFac', max_digits=9, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    prdimpume = models.SmallIntegerField(db_column='PrdImpUMe', blank=True, null=True)  # Field name made lowercase.
    prdgarare = models.SmallIntegerField(db_column='PrdGarAre', blank=True, null=True)  # Field name made lowercase.
    prdgarcen = models.IntegerField(db_column='PrdGarCen', blank=True, null=True)  # Field name made lowercase.
    prdgarite = models.SmallIntegerField(db_column='PrdGarIte', blank=True, null=True)  # Field name made lowercase.
    exiclcod = models.SmallIntegerField(db_column='ExiClCod', blank=True, null=True)  # Field name made lowercase.
    prdfacmax = models.DecimalField(db_column='PrdFacMax', max_digits=10, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    prdfacmin = models.DecimalField(db_column='PrdFacMin', max_digits=10, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    prdfaccri = models.DecimalField(db_column='PrdFacCri', max_digits=10, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    prdcosotr = models.DecimalField(db_column='PRDCOSOTR', max_digits=13, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    prdcunpro = models.SmallIntegerField(db_column='PRDCUNPRO', blank=True, null=True)  # Field name made lowercase.
    prdfunpro = models.DecimalField(db_column='PRDFUNPRO', max_digits=8, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    prdarecod = models.SmallIntegerField(db_column='PrdAreCod', blank=True, null=True)  # Field name made lowercase.
    prdcencod = models.IntegerField(db_column='PrdCencod', blank=True, null=True)  # Field name made lowercase.
    prdunicaj = models.DecimalField(db_column='PrdUniCaj', max_digits=10, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    prdlotfch = models.CharField(db_column='PrdLotFch', max_length=20, blank=True, null=True)  # Field name made lowercase.
    prdlfcent = models.SmallIntegerField(db_column='PrdLFcEnt', blank=True, null=True)  # Field name made lowercase.
    prdlfcsal = models.SmallIntegerField(db_column='PrdLFcSal', blank=True, null=True)  # Field name made lowercase.
    prdcodnu = models.CharField(db_column='PrdCodNu', max_length=6, blank=True, null=True)  # Field name made lowercase.
    prdclase = models.CharField(db_column='PrdClase', max_length=3, blank=True, null=True)  # Field name made lowercase.
    prddirhsp = models.CharField(db_column='PrdDirHsP', max_length=80, blank=True, null=True)  # Field name made lowercase.
    prddirhsr = models.CharField(db_column='PrdDirHsR', max_length=80, blank=True, null=True)  # Field name made lowercase.
    prddircer = models.CharField(db_column='PrdDirCer', max_length=80, blank=True, null=True)  # Field name made lowercase.
    prdcodres = models.SmallIntegerField(db_column='PrdCodRes', blank=True, null=True)  # Field name made lowercase.
    prdregsan = models.CharField(db_column='PRDREGSAN', max_length=16, blank=True, null=True)  # Field name made lowercase.
    prdregvig = models.DateTimeField(db_column='PRDREGVIG', blank=True, null=True)  # Field name made lowercase.
    prdimpfaco = models.SmallIntegerField(db_column='PrdImpFacO', blank=True, null=True)  # Field name made lowercase.
    prducoope = models.SmallIntegerField(db_column='PrdUCoOpe', blank=True, null=True)  # Field name made lowercase.
    prdcosfin = models.DecimalField(db_column='PrdCosFin', max_digits=14, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    prdcosfio = models.DecimalField(db_column='PrdCosFiO', max_digits=14, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    prdmarval = models.SmallIntegerField(db_column='PrdMarVal', blank=True, null=True)  # Field name made lowercase.
    prddaemite = models.SmallIntegerField(db_column='PrdDAEmite', blank=True, null=True)  # Field name made lowercase.
    prddachas = models.CharField(db_column='PrdDAChas', max_length=30, blank=True, null=True)  # Field name made lowercase.
    prddacod1 = models.CharField(db_column='PrdDACod1', max_length=10, blank=True, null=True)  # Field name made lowercase.
    prddacod2 = models.CharField(db_column='PrdDACod2', max_length=10, blank=True, null=True)  # Field name made lowercase.
    prddacod3 = models.CharField(db_column='PrdDACod3', max_length=10, blank=True, null=True)  # Field name made lowercase.
    prddacod4 = models.CharField(db_column='PrdDACod4', max_length=10, blank=True, null=True)  # Field name made lowercase.
    prddacod5 = models.CharField(db_column='PrdDACod5', max_length=10, blank=True, null=True)  # Field name made lowercase.
    prddacod6 = models.CharField(db_column='PrdDACod6', max_length=10, blank=True, null=True)  # Field name made lowercase.
    prddammot = models.CharField(db_column='PrdDAMMot', max_length=30, blank=True, null=True)  # Field name made lowercase.
    prddanmot = models.CharField(db_column='PrdDANMot', max_length=30, blank=True, null=True)  # Field name made lowercase.
    prddapot = models.CharField(db_column='PrdDAPot', max_length=30, blank=True, null=True)  # Field name made lowercase.
    prddapesb = models.IntegerField(db_column='PrdDAPesB', blank=True, null=True)  # Field name made lowercase.
    prddaano = models.SmallIntegerField(db_column='PrdDAAno', blank=True, null=True)  # Field name made lowercase.
    imppaicod = models.SmallIntegerField(db_column='ImpPaiCod', blank=True, null=True)  # Field name made lowercase.
    prddatipc = models.CharField(db_column='PrdDATipC', max_length=2, blank=True, null=True)  # Field name made lowercase.
    prddaest = models.CharField(db_column='PrdDAEst', max_length=2, blank=True, null=True)  # Field name made lowercase.
    prddaacc = models.CharField(db_column='PrdDAAcc', max_length=100, blank=True, null=True)  # Field name made lowercase.
    prddahor = models.IntegerField(db_column='PrdDaHor', blank=True, null=True)  # Field name made lowercase.
    prddans = models.CharField(db_column='PrdDaNs', max_length=20, blank=True, null=True)  # Field name made lowercase.
    prddani = models.CharField(db_column='PrdDaNi', max_length=20, blank=True, null=True)  # Field name made lowercase.
    prddatm = models.SmallIntegerField(db_column='PrdDaTM', blank=True, null=True)  # Field name made lowercase.
    prddase = models.CharField(db_column='PrdDaSe', max_length=20, blank=True, null=True)  # Field name made lowercase.
    prddacap = models.IntegerField(db_column='PrdDaCap', blank=True, null=True)  # Field name made lowercase.
    prddaac = models.SmallIntegerField(db_column='PrdDaAC', blank=True, null=True)  # Field name made lowercase.
    prddastr = models.CharField(db_column='PrdDaStr', max_length=23, blank=True, null=True)  # Field name made lowercase.
    prdpack = models.SmallIntegerField(db_column='PrdPack', blank=True, null=True)  # Field name made lowercase.
    prddapbt = models.CharField(db_column='PrdDAPBT', max_length=30, blank=True, null=True)  # Field name made lowercase.
    prditecod = models.SmallIntegerField(db_column='PRDITECOD', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        default_permissions = ()
        managed = False
        db_table = 'PRODUCTO'

    def toJSON(self):
        item = model_to_dict(self)
        return item

    def to_consulta_precio(self):
        # item = model_to_dict(self)
        item={}
        item['codigo'] = self.prdcod.strip()
        item['descripcion'] = self.prddestra.strip()
        item['precio_lista'] = self.precio_lista(900)
        item['precio_base'] = self.precio_lista(1)
        item['linea']=self.get_linea()
        item['emb']=self.prdunicaj
        item['imagen'] = self.images()
        item['bg_line'] = self.line_images(self.get_linea())

        return item

    def precio_lista(self, lista):
        precio = Listpre1.objects.using('inet').filter(barcod=self.prdcod, liscod=lista).first()
        if precio:
            return precio.lisprenet
        return None

    def get_linea(self):
        linea = Tabad2.objects.using('inet').filter(at2cod=self.at2cod).first()
        if linea:
            return linea.at2nom
        return None

    def images(self):
        path = os.path.join(BASE_DIR, 'static') + '/assets/images/catalogo/media/'
        img_path = f'{path}{self.prdcod.strip()}_1.jpg'
        if not os.path.exists(img_path):
            return None

        with open(img_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read())
            encoded_string = encoded_string.decode('utf-8')

        return encoded_string

    def line_images(self,line):
        path = os.path.join(BASE_DIR, 'static') + '/assets/images/catalogo/salon_precios/lines/'
        img_path = f'{path}{line.strip()}.jpg'
        print(img_path)
        if not os.path.exists(img_path):
            return None

        with open(img_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read())
            encoded_string = encoded_string.decode('utf-8')

        return encoded_string
