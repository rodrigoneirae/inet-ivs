from django.db import models
from django.forms import model_to_dict
from modulos.inet.models.erp.anacta import Anacta
from modulos.inet.models.erp.listprec import Listprec
from modulos.inet.models.erp.condvent import Condvent
from modulos.comercial.views.ventas.utils.dias_despacho import DiasDespacho

class Clientd(models.Model):
    clitip = models.SmallIntegerField(db_column='CliTip',
                                      primary_key=True)  # Field name made lowercase. The composite primary key (CliTip, CliCod, CliSec) found, that is not supported. The first column is selected.
    clicod = models.DecimalField(db_column='CliCod', max_digits=12, decimal_places=0)  # Field name made lowercase.
    clisec = models.SmallIntegerField(db_column='CliSec')  # Field name made lowercase.
    clidirdes = models.CharField(db_column='CliDirDes', max_length=40, blank=True,
                                 null=True)  # Field name made lowercase.
    cliciudes = models.CharField(db_column='CliCiuDes', max_length=40, blank=True,
                                 null=True)  # Field name made lowercase.
    clicomdes = models.CharField(db_column='CliComDes', max_length=15, blank=True,
                                 null=True)  # Field name made lowercase.
    clicmicod = models.SmallIntegerField(db_column='CliCmiCod', blank=True, null=True)  # Field name made lowercase.
    retimptas = models.DecimalField(db_column='RetImpTas', max_digits=10, decimal_places=4, blank=True,
                                    null=True)  # Field name made lowercase.
    retimpcod = models.SmallIntegerField(db_column='RetImpCod', blank=True, null=True)  # Field name made lowercase.
    cliimptas = models.DecimalField(db_column='CliImpTas', max_digits=10, decimal_places=4, blank=True,
                                    null=True)  # Field name made lowercase.
    cliimpcod = models.SmallIntegerField(db_column='CliImpCod', blank=True, null=True)  # Field name made lowercase.
    cliafeimp = models.SmallIntegerField(db_column='CliAfeImp', blank=True, null=True)  # Field name made lowercase.
    aclunocod = models.DecimalField(db_column='AClUnoCod', max_digits=10, decimal_places=0, blank=True,
                                    null=True)  # Field name made lowercase.
    acltrecod = models.DecimalField(db_column='AClTreCod', max_digits=10, decimal_places=0, blank=True,
                                    null=True)  # Field name made lowercase.
    acldoscod = models.DecimalField(db_column='AClDosCod', max_digits=10, decimal_places=0, blank=True,
                                    null=True)  # Field name made lowercase.
    aclcuacod = models.DecimalField(db_column='AClCuaCod', max_digits=10, decimal_places=0, blank=True,
                                    null=True)  # Field name made lowercase.
    aclcincod = models.DecimalField(db_column='AClCinCod', max_digits=10, decimal_places=0, blank=True,
                                    null=True)  # Field name made lowercase.
    cliliscod = models.SmallIntegerField(db_column='CliLisCod', blank=True, null=True)  # Field name made lowercase.
    cliest = models.SmallIntegerField(db_column='CliEst', blank=True, null=True)  # Field name made lowercase.
    clitipfac = models.SmallIntegerField(db_column='CliTipFac', blank=True, null=True)  # Field name made lowercase.
    rubcod = models.SmallIntegerField(db_column='RubCod', blank=True, null=True)  # Field name made lowercase.
    seccod = models.SmallIntegerField(db_column='SecCod', blank=True, null=True)  # Field name made lowercase.
    clidsccod = models.SmallIntegerField(db_column='CliDscCod', blank=True, null=True)  # Field name made lowercase.
    cobtip = models.SmallIntegerField(db_column='CobTip', blank=True, null=True)  # Field name made lowercase.
    cobsec = models.SmallIntegerField(db_column='CobSec', blank=True, null=True)  # Field name made lowercase.
    cobcod = models.DecimalField(db_column='CobCod', max_digits=12, decimal_places=0, blank=True,
                                 null=True)  # Field name made lowercase.
    clivensec = models.SmallIntegerField(db_column='CliVenSec', blank=True, null=True)  # Field name made lowercase.
    clivencod = models.DecimalField(db_column='CliVenCod', max_digits=12, decimal_places=0, blank=True,
                                    null=True)  # Field name made lowercase.
    cliventip = models.SmallIntegerField(db_column='CliVenTip', blank=True, null=True)  # Field name made lowercase.
    clinivcre = models.DecimalField(db_column='CliNivCre', max_digits=19, decimal_places=4, blank=True,
                                    null=True)  # Field name made lowercase.
    cligir = models.CharField(db_column='CliGir', max_length=80, blank=True, null=True)  # Field name made lowercase.
    clicodpos = models.CharField(db_column='CliCodPos', max_length=30, blank=True,
                                 null=True)  # Field name made lowercase.
    clifching = models.DateTimeField(db_column='CliFchIng', blank=True, null=True)  # Field name made lowercase.
    vfaviacod = models.SmallIntegerField(db_column='VfaViaCod', blank=True, null=True)  # Field name made lowercase.
    clinot = models.TextField(db_column='CliNot', blank=True,
                              null=True)  # Field name made lowercase. This field type is a guess.
    clicla = models.CharField(db_column='CliCla', max_length=10, blank=True, null=True)  # Field name made lowercase.
    clipedpar = models.SmallIntegerField(db_column='CliPedPar', blank=True, null=True)  # Field name made lowercase.
    clicovcod = models.SmallIntegerField(db_column='CliCovCod', blank=True, null=True)  # Field name made lowercase.
    clifactip = models.SmallIntegerField(db_column='ClifacTip', blank=True, null=True)  # Field name made lowercase.
    clidoccod = models.SmallIntegerField(db_column='CliDocCod', blank=True, null=True)  # Field name made lowercase.
    clidsctot = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)
    vfanivcod = models.CharField(db_column='VfaNivCod', max_length=2, blank=True,
                                 null=True)  # Field name made lowercase.
    cliultlin = models.SmallIntegerField(db_column='CliUltLin', blank=True, null=True)  # Field name made lowercase.
    clifvecre = models.DateTimeField(db_column='CliFVeCre', blank=True, null=True)  # Field name made lowercase.
    clisinret = models.SmallIntegerField(db_column='CliSinRet', blank=True, null=True)  # Field name made lowercase.
    cliattbi1 = models.CharField(db_column='CliAttBI1', max_length=5, blank=True,
                                 null=True)  # Field name made lowercase.
    cliattbi2 = models.CharField(db_column='CliAttBI2', max_length=5, blank=True,
                                 null=True)  # Field name made lowercase.
    cliattbi3 = models.CharField(db_column='CliAttBI3', max_length=5, blank=True,
                                 null=True)  # Field name made lowercase.
    cliattbi4 = models.CharField(db_column='CliAttBI4', max_length=5, blank=True,
                                 null=True)  # Field name made lowercase.
    cliattbi5 = models.CharField(db_column='CliAttBI5', max_length=5, blank=True,
                                 null=True)  # Field name made lowercase.
    clirutpad = models.SmallIntegerField(db_column='CLIRUTPAD', blank=True, null=True)  # Field name made lowercase.
    clirutemi = models.SmallIntegerField(db_column='CLIRUTEMI', blank=True, null=True)  # Field name made lowercase.
    imppaicod = models.SmallIntegerField(db_column='IMPPAICOD', blank=True, null=True)  # Field name made lowercase.
    clidipag1 = models.SmallIntegerField(db_column='CliDiPag1', blank=True, null=True)  # Field name made lowercase.
    clidipag2 = models.SmallIntegerField(db_column='CliDiPag2', blank=True, null=True)  # Field name made lowercase.
    clidipag3 = models.SmallIntegerField(db_column='CliDiPag3', blank=True, null=True)  # Field name made lowercase.
    clidipag4 = models.SmallIntegerField(db_column='CliDiPag4', blank=True, null=True)  # Field name made lowercase.
    cliemihse = models.SmallIntegerField(db_column='CliEmiHse', blank=True, null=True)  # Field name made lowercase.
    cliemistr = models.SmallIntegerField(db_column='CliEmiStr', blank=True, null=True)  # Field name made lowercase.
    cliemican = models.SmallIntegerField(db_column='CliEmiCAn', blank=True, null=True)  # Field name made lowercase.
    cligennca = models.SmallIntegerField(db_column='CliGenNcA', blank=True, null=True)  # Field name made lowercase.
    cliconcob = models.CharField(db_column='CliConCob', max_length=35, blank=True,
                                 null=True)  # Field name made lowercase.
    clicontel = models.CharField(db_column='CliConTel', max_length=20, blank=True,
                                 null=True)  # Field name made lowercase.
    cliatuno = models.CharField(db_column='CliAtUno', max_length=20, blank=True,
                                null=True)  # Field name made lowercase.
    cliatdos = models.CharField(db_column='CliAtDos', max_length=20, blank=True,
                                null=True)  # Field name made lowercase.
    cliattre = models.CharField(db_column='CliAtTre', max_length=20, blank=True,
                                null=True)  # Field name made lowercase.
    cliatcua = models.CharField(db_column='CliAtCua', max_length=20, blank=True,
                                null=True)  # Field name made lowercase.
    cliatcin = models.CharField(db_column='CliAtCin', max_length=20, blank=True,
                                null=True)  # Field name made lowercase.
    cliretcre = models.SmallIntegerField(db_column='CLIRETCRE', blank=True, null=True)  # Field name made lowercase.
    cliprca = models.SmallIntegerField(db_column='CliPrCa', blank=True, null=True)  # Field name made lowercase.
    clib2b = models.SmallIntegerField(db_column='CliB2B', blank=True, null=True)  # Field name made lowercase.
    clinoprot = models.SmallIntegerField(db_column='CliNoProt', blank=True, null=True)  # Field name made lowercase.
    clifecupr = models.DateTimeField(db_column='CliFecUpr', blank=True, null=True)  # Field name made lowercase.
    clifecrcr = models.DateTimeField(db_column='CliFecRcr', blank=True, null=True)  # Field name made lowercase.
    clientiva = models.SmallIntegerField(db_column='CliEntIva', blank=True, null=True)  # Field name made lowercase.
    clifecent = models.DateTimeField(db_column='CliFecEnt', blank=True, null=True)  # Field name made lowercase.
    climonase = models.DecimalField(db_column='CliMonAse', max_digits=19, decimal_places=4, blank=True,
                                    null=True)  # Field name made lowercase.
    clifecvse = models.DateTimeField(db_column='CliFecVse', blank=True, null=True)  # Field name made lowercase.
    cliconpse = models.SmallIntegerField(db_column='CliConPse', blank=True, null=True)  # Field name made lowercase.
    cliusecta = models.SmallIntegerField(db_column='CliUSeCta', blank=True, null=True)  # Field name made lowercase.
    clientmer = models.SmallIntegerField(db_column='CliEntMer', blank=True, null=True)  # Field name made lowercase.
    clipagp1 = models.SmallIntegerField(db_column='CliPagP1', blank=True, null=True)  # Field name made lowercase.
    clipaga1 = models.SmallIntegerField(db_column='CliPagA1', blank=True, null=True)  # Field name made lowercase.
    clipagp2 = models.SmallIntegerField(db_column='CliPagP2', blank=True, null=True)  # Field name made lowercase.
    clipaga2 = models.SmallIntegerField(db_column='CliPagA2', blank=True, null=True)  # Field name made lowercase.
    clipagts = models.SmallIntegerField(db_column='CliPagTS', blank=True, null=True)  # Field name made lowercase.
    clipagsm = models.SmallIntegerField(db_column='CliPagSM', blank=True, null=True)  # Field name made lowercase.
    clipagdi = models.SmallIntegerField(db_column='CliPagDi', blank=True, null=True)  # Field name made lowercase.
    clipagds = models.SmallIntegerField(db_column='CliPagDS', blank=True, null=True)  # Field name made lowercase.
    clilastupd = models.DateTimeField(db_column='CliLastUpd', blank=True, null=True)  # Field name made lowercase.
    cliultcto = models.SmallIntegerField(db_column='CliUltCto', blank=True, null=True)  # Field name made lowercase.
    climoddsc = models.SmallIntegerField(db_column='CliModDsc', blank=True, null=True)  # Field name made lowercase.
    clicodcrmk = models.CharField(db_column='CliCodCrmK', max_length=50)  # Field name made lowercase.
    clivaduli = models.SmallIntegerField(db_column='CliVadULi', blank=True, null=True)  # Field name made lowercase.
    cliemlpdf = models.SmallIntegerField(db_column='CliEmlPdf')  # Field name made lowercase.
    cliemlxml = models.SmallIntegerField(db_column='CliEmlXml')  # Field name made lowercase.
    cliemlint = models.CharField(db_column='CliEmlInt', max_length=100, blank=True,
                                 null=True)  # Field name made lowercase.
    clirutext = models.SmallIntegerField(db_column='CliRutExt')  # Field name made lowercase.
    cliposdir = models.CharField(db_column='CliPosDir', max_length=60, blank=True,
                                 null=True)  # Field name made lowercase.
    clidirpos = models.CharField(db_column='CliDirPos', max_length=10, blank=True,
                                 null=True)  # Field name made lowercase.
    cliestana = models.SmallIntegerField(db_column='CliEstAna', blank=True, null=True)  # Field name made lowercase.
    clicodfis = models.CharField(db_column='CliCodFis', max_length=20, blank=True,
                                 null=True)  # Field name made lowercase.
    clirefoc = models.SmallIntegerField(db_column='CliRefOC', blank=True, null=True)  # Field name made lowercase.
    clinomxml = models.CharField(db_column='CLINOMXML', max_length=100, blank=True,
                                 null=True)  # Field name made lowercase.
    cliposcom = models.CharField(db_column='CliPosCom', max_length=20, blank=True,
                                 null=True)  # Field name made lowercase.
    cliposciu = models.CharField(db_column='CliPosCiu', max_length=20, blank=True,
                                 null=True)  # Field name made lowercase.
    clixmlprd = models.SmallIntegerField(db_column='CliXmlPrd', blank=True, null=True)  # Field name made lowercase.
    clidirxml = models.CharField(db_column='CLIDIRXML', max_length=70, blank=True,
                                 null=True)  # Field name made lowercase.
    clirtncli = models.SmallIntegerField(db_column='CliRtNCli', blank=True, null=True)  # Field name made lowercase.
    clirtcc = models.SmallIntegerField(db_column='CliRtCC', blank=True, null=True)  # Field name made lowercase.
    clirtcc01 = models.SmallIntegerField(db_column='CliRtCC01', blank=True, null=True)  # Field name made lowercase.
    clirtcc02 = models.SmallIntegerField(db_column='CliRtCC02', blank=True, null=True)  # Field name made lowercase.
    clirtcc03 = models.SmallIntegerField(db_column='CliRtCC03', blank=True, null=True)  # Field name made lowercase.
    clirtcc04 = models.SmallIntegerField(db_column='CliRtCC04', blank=True, null=True)  # Field name made lowercase.
    clirtcc05 = models.SmallIntegerField(db_column='CliRtCC05', blank=True, null=True)  # Field name made lowercase.
    clirtcc06 = models.SmallIntegerField(db_column='CliRtCC06', blank=True, null=True)  # Field name made lowercase.
    clirtcc07 = models.DecimalField(db_column='CliRtCC07', max_digits=19, decimal_places=4, blank=True,
                                    null=True)  # Field name made lowercase.
    clirtcc08 = models.SmallIntegerField(db_column='CliRtCC08', blank=True, null=True)  # Field name made lowercase.
    clirtcc09 = models.SmallIntegerField(db_column='CliRtCC09', blank=True, null=True)  # Field name made lowercase.
    clirtav = models.SmallIntegerField(db_column='CliRtAV', blank=True, null=True)  # Field name made lowercase.
    clirtav01 = models.DecimalField(db_column='CliRtAV01', max_digits=10, decimal_places=4, blank=True,
                                    null=True)  # Field name made lowercase.
    clirtav02 = models.DecimalField(db_column='CliRtAV02', max_digits=10, decimal_places=4, blank=True,
                                    null=True)  # Field name made lowercase.
    clirtav03 = models.SmallIntegerField(db_column='CliRtAV03', blank=True, null=True)  # Field name made lowercase.
    clirtav04 = models.SmallIntegerField(db_column='CliRtAV04', blank=True, null=True)  # Field name made lowercase.
    clirtav05 = models.SmallIntegerField(db_column='CliRtAV05', blank=True, null=True)  # Field name made lowercase.
    clirtav06 = models.SmallIntegerField(db_column='CliRtAV06', blank=True, null=True)  # Field name made lowercase.
    clirtav07 = models.SmallIntegerField(db_column='CliRtAV07', blank=True, null=True)  # Field name made lowercase.
    clirtav08 = models.SmallIntegerField(db_column='CliRtAV08', blank=True, null=True)  # Field name made lowercase.
    clirtav09 = models.SmallIntegerField(db_column='CliRtAV09', blank=True, null=True)  # Field name made lowercase.
    clirtav10 = models.DecimalField(db_column='CliRtAV10', max_digits=10, decimal_places=4, blank=True,
                                    null=True)  # Field name made lowercase.
    clirtav11 = models.SmallIntegerField(db_column='CliRtAV11', blank=True, null=True)  # Field name made lowercase.
    clirtav12 = models.SmallIntegerField(db_column='CliRtAV12', blank=True, null=True)  # Field name made lowercase.
    clirtav13 = models.SmallIntegerField(db_column='CliRtAV13', blank=True, null=True)  # Field name made lowercase.
    clirtav14 = models.DecimalField(db_column='CliRtAv14', max_digits=19, decimal_places=4, blank=True,
                                    null=True)  # Field name made lowercase.
    ananom = models.CharField(db_column='AnaNom', max_length=40, blank=True, null=True)  # Field name made lowercase.
    clidocped = models.SmallIntegerField(db_column='CliDocPed', blank=True, null=True)  # Field name made lowercase.
    clidiavis = models.CharField(db_column='CliDiaVis', max_length=8, blank=True,
                                 null=True)  # Field name made lowercase.
    clisemvis = models.SmallIntegerField(db_column='CliSemVis', blank=True, null=True)  # Field name made lowercase.
    clifrcvis = models.SmallIntegerField(db_column='CliFrcVis', blank=True, null=True)  # Field name made lowercase.
    clifchprx = models.DateField(db_column='CliFchPrx', blank=True, null=True)  # Field name made lowercase.
    clirfrcvis = models.SmallIntegerField(db_column='CliRFrcVis', blank=True, null=True)  # Field name made lowercase.
    clirdiavis = models.CharField(db_column='CliRDiaVis', max_length=8, blank=True,
                                  null=True)  # Field name made lowercase.
    clirsemvis = models.SmallIntegerField(db_column='CliRSemVis', blank=True, null=True)  # Field name made lowercase.
    clirfchprx = models.DateField(db_column='CliRFchPrx', blank=True, null=True)  # Field name made lowercase.
    clivennom = models.CharField(db_column='CliVenNom', max_length=40, blank=True,
                                 null=True)  # Field name made lowercase.
    clivendve = models.CharField(db_column='CliVenDve', max_length=1, blank=True,
                                 null=True)  # Field name made lowercase.

    def __str__(self):
        return self.clinomxml.title()

    class Meta:
        default_permissions = ()
        managed = False
        db_table = 'CLIENTD'
        unique_together = (('clitip', 'clicod', 'clisec'),)

    def to_json(self):
        # item = model_to_dict(self, exclude=['password', 'user_permissions'])
        item = model_to_dict(self)
        item['clinomxml'] = self.clinomxml.title()
        return item

    # 76645437
    def cond_venta(self):
        condventa = Condvent.objects.filter(covcod=self.clicovcod).using('inet').last()
        return condventa.covnom.title() if condventa else None

    def desc_vendedor(self):
        anacta = Anacta.objects.filter(anatip=1, anacod=self.clivencod, anasec=self.clisec,
                                       anacodfis=self.clivencod).using('inet').last()

        return anacta.ananom.title() if anacta else None

    def desc_lista(self):
        listprec = Listprec.objects.filter(liscod=self.cliliscod).using('inet').last()
        return listprec.lisnom.title() if listprec else None

    def to_cliente(self):
        try:
            anacta = Anacta.objects.filter(anatip=self.clitip, anacod=self.clicod, anasec=self.clisec).using(
                'inet').last()
            # print(anacta)
            rut = f"{anacta.anacod}-{anacta.anadve}"
            # dias despacho
            dias_despacho = 2
            despacho = DiasDespacho()
            fecha_despacho = despacho.calcular_fecha_despacho(dias_despacho)

            return {
                'Codigo': self.clicod,
                'Secuencia': self.clisec,
                'Oc': '',
                'Rut': rut,
                'RazonSocial': anacta.ananom.title().strip() if anacta.ananom else None,
                'DireccionDespacho': self.clidirdes.title().strip() if self.clidirdes else None,
                'ComunaDespacho': self.clicomdes.title().strip() if self.clicomdes else None,
                'CiudadDespacho': self.cliciudes.title().strip() if self.cliciudes else None,
                'Region': anacta.anareg.title().strip() if anacta.anareg else None,
                'Giro': self.cligir.title().strip() if self.cligir else None,
                'CasillaIntercambio': self.cliemlint.strip() if self.cliemlint else None,
                'Email': anacta.anaeml.strip() if anacta.anaeml else None,
                'CliVenCod': self.clivencod,
                'CliVenDesc': self.desc_vendedor().strip() if self.desc_vendedor() else None,
                'CliLisCod': self.cliliscod,
                'CliLisDesc': self.desc_lista().strip() if self.desc_lista() else None,
                'CondVentaCod': self.clicovcod,
                'CondVentaDesc': self.cond_venta().strip() if self.cond_venta() else None,
                'CondBodCod': 1,
                'CondBodDesc': 'HUECHURABA',
                'Observacion': '',
                'ViaDes': None,
                'FechaDespacho': fecha_despacho.strftime('%Y-%m-%d'),
            }
        except Anacta.DoesNotExist:
            return {
                'Codigo': self.clicod,
                'Secuencia': self.clisec,
                'Oc': '',
                'Rut': None,
                'RazonSocial': None,
                'DireccionDespacho': self.clidirdes.title().strip() if self.clidirdes else None,
                'ComunaDespacho': self.clicomdes.title().strip() if self.clicomdes else None,
                'CiudadDespacho': self.cliciudes.title().strip() if self.cliciudes else None,
                'Region': None,
                'Giro': self.cligir.title().strip() if self.cligir else None,
                'CasillaIntercambio': self.cliemlint,
                'Email': None,
                'CliVenCod': self.clivencod,
                'CliLisCod': self.cliliscod,
                'ViaDes': None,
                'FechaDespacho': fecha_despacho.strftime('%Y-%m-%d'),
            }
    def to_cliente_informe(self):
        try:
            anacta = Anacta.objects.filter(anatip=self.clitip, anacod=self.clicod, anasec=self.clisec).using(
                'inet').last()
            # print(anacta)
            rut = f"{anacta.anacod}-{anacta.anadve}"
            # dias despacho
            dias_despacho = 2
            despacho = DiasDespacho()
            fecha_despacho = despacho.calcular_fecha_despacho(dias_despacho)

            return {
                'Codigo': self.clicod,
                'Secuencia': self.clisec,
                'Oc': '',
                'Rut': rut,
                'RazonSocial': anacta.ananom.title().strip() if anacta.ananom else None,
                'DireccionDespacho': self.clidirdes.title().strip(),
                'ComunaDespacho': self.clicomdes.title().strip() if self.clicomdes else None,
                'CiudadDespacho': self.cliciudes.title().strip() if self.cliciudes else None,
                'Region': anacta.anareg.title().strip() if anacta.anareg else None,
                'Giro': self.cligir.title().strip() if self.cligir else None,
                'CasillaIntercambio': self.cliemlint.strip() if self.cliemlint else None,
                'Email': anacta.anaeml.strip() if anacta.anaeml else None,
                'CliVenCod': self.clivencod,
                'CliVenDesc': self.desc_vendedor().strip() if self.desc_vendedor() else None,
                'CliLisCod': self.cliliscod,
                'CliLisDesc': self.desc_lista().strip() if self.desc_lista() else None,
                'CondVentaCod': self.clicovcod,
                'CondVentaDesc': self.cond_venta().strip() if self.cond_venta() else None,
                'CondBodCod': 1,
                'CondBodDesc': 'HUECHURABA',
                'Observacion': '',
                'ViaDes': None,
                'FechaDespacho': fecha_despacho.strftime('%Y-%m-%d'),
            }
        except Anacta.DoesNotExist:
            return {
                'Codigo': self.clicod,
                'Secuencia': self.clisec,
                'Oc': '',
                'Rut': None,
                'RazonSocial': None,
                'DireccionDespacho': self.clidirdes.title().strip() if self.clidirdes else None,
                'ComunaDespacho': self.clicomdes.title().strip() if self.clicomdes else None,
                'CiudadDespacho': self.cliciudes.title().strip() if self.cliciudes else None,
                'Region': None,
                'Giro': self.cligir.title().strip() if self.cligir else None,
                'CasillaIntercambio': self.cliemlint,
                'Email': None,
                'CliVenCod': self.clivencod,
                'CliLisCod': self.cliliscod,
                'ViaDes': None,
                'FechaDespacho': fecha_despacho.strftime('%Y-%m-%d'),
            }