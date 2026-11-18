import locale
from django.core.cache import cache
from django.db import models
from django.forms import model_to_dict
from modulos.inet.models.erp.vendores import Vendores
from modulos.inet.models.erp.tipdoc import Tipdoc
from modulos.inet.models.erp.ateclie2 import Ateclie2
from modulos.inet.models.erp.atecli2 import Atecli2
from modulos.inet.models.erp.clientd import Clientd
from modulos.inet.models.erp.condvent import Condvent



class Ateclien(models.Model):
    cajcod = models.SmallIntegerField(db_column='CajCod',
                                      primary_key=True)
    doccod = models.SmallIntegerField(db_column='DocCod')
    atenumrea = models.IntegerField(db_column='AteNumRea')
    atecomnum = models.IntegerField(db_column='AteComNum', blank=True, null=True)
    atecomref = models.IntegerField(db_column='AteComRef', blank=True, null=True)
    atenum = models.IntegerField(db_column='AteNum', blank=True, null=True)
    aterefrea = models.IntegerField(db_column='AteRefRea', blank=True, null=True)
    aterefdoc = models.SmallIntegerField(db_column='AteRefDoc', blank=True, null=True)
    aterefnum = models.IntegerField(db_column='AteRefNum', blank=True, null=True)
    atereffac = models.IntegerField(db_column='AteRefFac', blank=True, null=True)
    atecliref = models.IntegerField(db_column='AteCliRef', blank=True, null=True)
    atesuccod = models.SmallIntegerField(db_column='AteSucCod', blank=True, null=True)
    atebodcod = models.IntegerField(db_column='AteBodCod', blank=True, null=True)
    atebodcen = models.IntegerField(db_column='AteBodCEn', blank=True, null=True)
    atemoncod = models.SmallIntegerField(db_column='AteMonCod', blank=True, null=True)
    atectacod = models.CharField(db_column='Atectacod', max_length=9, blank=True,
                                 null=True)
    atemarare = models.SmallIntegerField(db_column='AteMarAre', blank=True, null=True)
    atetipgui = models.SmallIntegerField(db_column='AteTipGui', blank=True, null=True)
    ateglo = models.CharField(db_column='AteGlo', max_length=60, blank=True, null=True)
    ateobsuno = models.CharField(db_column='AteObsUno', max_length=80, blank=True,
                                 null=True)
    ateobsdos = models.CharField(db_column='AteObsDos', max_length=80, blank=True,
                                 null=True)
    ateduncod = models.SmallIntegerField(db_column='AteDUncod', blank=True, null=True)
    atedunpcj = models.DecimalField(db_column='AteDUnPcj', max_digits=10, decimal_places=4, blank=True,
                                    null=True)
    atedunmon = models.DecimalField(db_column='AteDUnMon', max_digits=19, decimal_places=4, blank=True,
                                    null=True)
    ateddomon = models.DecimalField(db_column='AteDDoMon', max_digits=19, decimal_places=4, blank=True,
                                    null=True)
    atedtrmon = models.DecimalField(db_column='AteDTrMon', max_digits=19, decimal_places=4, blank=True,
                                    null=True)
    atedcumon = models.DecimalField(db_column='AteDCuMon', max_digits=19, decimal_places=4, blank=True,
                                    null=True)
    ateddocod = models.SmallIntegerField(db_column='AteDDocod', blank=True, null=True)
    ateddopcj = models.DecimalField(db_column='AteDDoPcj', max_digits=10, decimal_places=4, blank=True,
                                    null=True)
    atedtrcod = models.SmallIntegerField(db_column='AteDTrcod', blank=True, null=True)
    atedtrpcj = models.DecimalField(db_column='AteDTrPcj', max_digits=10, decimal_places=4, blank=True,
                                    null=True)
    atedcucod = models.SmallIntegerField(db_column='AteDCucod', blank=True, null=True)
    atedcupcj = models.DecimalField(db_column='AteDCuPcj', max_digits=10, decimal_places=4, blank=True,
                                    null=True)
    atercacod = models.SmallIntegerField(db_column='AteRcaCod', blank=True, null=True)
    atefchate = models.DateTimeField(db_column='AteFchAte', blank=True, null=True)
    atefchdoc = models.DateTimeField(db_column='AteFchDoc', blank=True, null=True)
    ateest = models.SmallIntegerField(db_column='AteEst', blank=True, null=True)
    ateestpro = models.SmallIntegerField(db_column='AteEstPro', blank=True, null=True)
    clicod = models.DecimalField(db_column='CliCod', max_digits=12, decimal_places=0, blank=True,
                                 null=True)
    clisec = models.SmallIntegerField(db_column='CliSec', blank=True, null=True)
    clitip = models.SmallIntegerField(db_column='CliTip', blank=True, null=True)
    atecovcod = models.SmallIntegerField(db_column='AteCoVCod', blank=True, null=True)
    atecvadir = models.CharField(db_column='AteCvaDir', max_length=40, blank=True,
                                 null=True)
    atecvadve = models.CharField(db_column='AteCvaDve', max_length=1, blank=True,
                                 null=True)
    atecvanom = models.CharField(db_column='AteCvaNom', max_length=40, blank=True,
                                 null=True)
    atecvarut = models.DecimalField(db_column='AteCvaRut', max_digits=12, decimal_places=0, blank=True,
                                    null=True)
    vencod = models.DecimalField(db_column='VenCod', max_digits=12, decimal_places=0, blank=True,
                                 null=True)
    vensec = models.SmallIntegerField(db_column='VenSec', blank=True, null=True)
    ventip = models.SmallIntegerField(db_column='VenTip', blank=True, null=True)
    ateliscod = models.SmallIntegerField(db_column='AteLisCod', blank=True, null=True)
    atetipcam = models.DecimalField(db_column='AteTipCam', max_digits=9, decimal_places=4, blank=True,
                                    null=True)
    atetotult = models.SmallIntegerField(db_column='AteTotUlt', blank=True, null=True)
    atebarult = models.SmallIntegerField(db_column='AteBarUlt', blank=True, null=True)
    atedocrec = models.SmallIntegerField(db_column='AteDocRec', blank=True, null=True)
    ateguifac = models.SmallIntegerField(db_column='AteGuiFac', blank=True, null=True)
    ateprocan = models.DecimalField(db_column='AteProCan', max_digits=13, decimal_places=4, blank=True,
                                    null=True)
    ateprodes = models.DecimalField(db_column='AteProDes', max_digits=13, decimal_places=4, blank=True,
                                    null=True)
    ateproncr = models.DecimalField(db_column='AteProNCr', max_digits=13, decimal_places=4, blank=True,
                                    null=True)
    atecvaciu = models.CharField(db_column='AteCvaCiu', max_length=15, blank=True,
                                 null=True)
    atecvacom = models.CharField(db_column='AteCvaCom', max_length=15, blank=True,
                                 null=True)
    atecvagir = models.CharField(db_column='AteCvaGir', max_length=80, blank=True,
                                 null=True)
    atecvaraz = models.CharField(db_column='AteCvaRaz', max_length=40, blank=True,
                                 null=True)
    atecvasec = models.SmallIntegerField(db_column='AteCvasec', blank=True, null=True)
    atecvatel = models.CharField(db_column='AteCvatel', max_length=20, blank=True,
                                 null=True)
    libcod = models.SmallIntegerField(db_column='LibCod', blank=True, null=True)
    grudoc = models.SmallIntegerField(db_column='GruDoc', blank=True, null=True)
    grutip = models.SmallIntegerField(db_column='GruTip', blank=True, null=True)
    gruafe = models.SmallIntegerField(db_column='GruAfe', blank=True, null=True)
    atenomtra = models.CharField(db_column='AteNomTra', max_length=40, blank=True,
                                 null=True)
    atepatveh = models.CharField(db_column='AtePatVeh', max_length=15, blank=True,
                                 null=True)
    ateori = models.SmallIntegerField(db_column='AteOri', blank=True, null=True)
    atefchcpe = models.DateTimeField(db_column='AteFchCPe', blank=True, null=True)
    ateestcot = models.SmallIntegerField(db_column='AteEstCot', blank=True, null=True)
    ateestped = models.SmallIntegerField(db_column='AteEstPed', blank=True, null=True)
    atedirdes = models.CharField(db_column='AteDirDes', max_length=40, blank=True,
                                 null=True)
    ateciudes = models.CharField(db_column='AteCiuDes', max_length=40, blank=True,
                                 null=True)
    atecomdes = models.CharField(db_column='AteComDes', max_length=15, blank=True,
                                 null=True)
    atecampre = models.SmallIntegerField(db_column='AteCamPre', blank=True, null=True)
    ateultfch = models.DateTimeField(db_column='AteUltFch', blank=True, null=True)
    ateultobs = models.TextField(db_column='AteUltObs', blank=True,
                                 null=True)
    ateretcre = models.SmallIntegerField(db_column='AteRetCre', blank=True, null=True)
    ateobscre = models.CharField(db_column='AteObsCre', max_length=80, blank=True,
                                 null=True)
    ateobsadm = models.CharField(db_column='AteObsAdm', max_length=80, blank=True,
                                 null=True)
    ateretadm = models.SmallIntegerField(db_column='AteRetAdm', blank=True, null=True)
    ateobssat = models.CharField(db_column='AteObsSat', max_length=80, blank=True,
                                 null=True)
    aterefori = models.SmallIntegerField(db_column='AteRefOri', blank=True, null=True)
    ateordcom = models.CharField(db_column='AteOrdCom', max_length=18, blank=True,
                                 null=True)
    motcod = models.SmallIntegerField(db_column='MotCod', blank=True, null=True)
    ateprxcon = models.DateTimeField(db_column='AtePrxCon', blank=True, null=True)
    atemotdsc = models.CharField(db_column='AteMotDsc', max_length=200, blank=True,
                                 null=True)
    admusucod = models.CharField(db_column='AdmUsuCod', max_length=10, blank=True,
                                 null=True)
    creusucod = models.CharField(db_column='CreUsuCod', max_length=10, blank=True,
                                 null=True)
    ateanomes = models.IntegerField(db_column='AteAnoMes', blank=True, null=True)
    ateviacod = models.SmallIntegerField(db_column='AteViaCod', blank=True, null=True)
    ateusucod = models.CharField(db_column='AteUsuCod', max_length=10, blank=True,
                                 null=True)
    atesconum = models.IntegerField(db_column='AteScoNum', blank=True, null=True)
    atescotip = models.SmallIntegerField(db_column='AteScoTip', blank=True, null=True)
    atescomes = models.SmallIntegerField(db_column='AteScoMes', blank=True, null=True)
    atescoano = models.SmallIntegerField(db_column='AteScoAno', blank=True, null=True)
    atescosuc = models.SmallIntegerField(db_column='AteScoSuc', blank=True, null=True)
    ateenvimp = models.SmallIntegerField(db_column='AteEnvIMP', blank=True, null=True)
    atetipcal = models.SmallIntegerField(db_column='AteTipCal', blank=True, null=True)
    atevenpc2 = models.DecimalField(db_column='AteVenPc2', max_digits=8, decimal_places=4, blank=True,
                                    null=True)
    atevense2 = models.SmallIntegerField(db_column='AteVenSe2', blank=True, null=True)
    atevenco2 = models.DecimalField(db_column='AteVenCo2', max_digits=12, decimal_places=0, blank=True,
                                    null=True)
    ateventi2 = models.SmallIntegerField(db_column='AteVenTi2', blank=True, null=True)
    atevenpc1 = models.DecimalField(db_column='AteVenPc1', max_digits=8, decimal_places=4, blank=True,
                                    null=True)
    atearecod = models.SmallIntegerField(db_column='AteAreCod', blank=True, null=True)
    atecencod = models.IntegerField(db_column='AteCenCod', blank=True, null=True)
    ateitecod = models.SmallIntegerField(db_column='AteIteCod', blank=True, null=True)
    ateprofor = models.DecimalField(db_column='ATEPROFOR', max_digits=13, decimal_places=4, blank=True,
                                    null=True)
    atecrmcli = models.DecimalField(db_column='ATECRMCLI', max_digits=12, decimal_places=0, blank=True,
                                    null=True)
    atecrmsec = models.SmallIntegerField(db_column='ATECRMSEC', blank=True, null=True)
    vfaprecod = models.SmallIntegerField(db_column='VfaPreCod', blank=True, null=True)
    vfapricod = models.SmallIntegerField(db_column='VfaPriCod', blank=True, null=True)
    ateaprdg1 = models.DateTimeField(db_column='AteAprDg1', blank=True, null=True)
    ateaprdg2 = models.DateTimeField(db_column='AteAprDg2', blank=True, null=True)
    ateaprdg3 = models.DateTimeField(db_column='AteAprDg3', blank=True, null=True)
    ateusupre = models.CharField(db_column='AteUsuPre', max_length=10, blank=True,
                                 null=True)
    ateusuvta = models.CharField(db_column='AteUsuVta', max_length=10, blank=True,
                                 null=True)
    ateusudis = models.CharField(db_column='AteUsuDis', max_length=10, blank=True,
                                 null=True)
    ateplsuc = models.SmallIntegerField(db_column='AtePlSuc', blank=True, null=True)
    ateplnum = models.IntegerField(db_column='AtePlNum', blank=True, null=True)
    ateplscsu = models.SmallIntegerField(db_column='AtePlScSu', blank=True, null=True)
    ateplscnu = models.IntegerField(db_column='AtePlScNu', blank=True, null=True)
    vfatipco1 = models.SmallIntegerField(db_column='VfaTipCo1', blank=True, null=True)
    vfarutco1 = models.DecimalField(db_column='VfaRutCo1', max_digits=12, decimal_places=0, blank=True,
                                    null=True)
    vfasecco1 = models.SmallIntegerField(db_column='VfaSecCo1', blank=True, null=True)
    vfatipco2 = models.SmallIntegerField(db_column='VfaTipCo2', blank=True, null=True)
    vfarutco2 = models.DecimalField(db_column='VfaRutCo2', max_digits=12, decimal_places=0, blank=True,
                                    null=True)
    vfasecco2 = models.SmallIntegerField(db_column='VfaSecCo2', blank=True, null=True)
    vfatipco3 = models.SmallIntegerField(db_column='VfaTipCo3', blank=True, null=True)
    vfarutco3 = models.DecimalField(db_column='VfaRutCo3', max_digits=12, decimal_places=0, blank=True,
                                    null=True)
    vfasecco3 = models.SmallIntegerField(db_column='VfaSecCo3', blank=True, null=True)
    vfatipco4 = models.SmallIntegerField(db_column='VfaTipCo4', blank=True, null=True)
    vfarutco4 = models.DecimalField(db_column='VfaRutCo4', max_digits=12, decimal_places=0, blank=True,
                                    null=True)
    vfasecco4 = models.SmallIntegerField(db_column='VfaSecCo4', blank=True, null=True)
    vfacomi1 = models.DecimalField(db_column='VfaComi1', max_digits=19, decimal_places=4, blank=True,
                                   null=True)
    vfacomi2 = models.DecimalField(db_column='VfaComi2', max_digits=19, decimal_places=4, blank=True,
                                   null=True)
    vfacomi3 = models.DecimalField(db_column='VfaComi3', max_digits=19, decimal_places=4, blank=True,
                                   null=True)
    vfacomi4 = models.DecimalField(db_column='VfaComi4', max_digits=19, decimal_places=4, blank=True,
                                   null=True)
    pertip = models.SmallIntegerField(db_column='PerTip', blank=True, null=True)
    percod = models.DecimalField(db_column='PerCod', max_digits=12, decimal_places=0, blank=True,
                                 null=True)
    persec = models.SmallIntegerField(db_column='PerSec', blank=True, null=True)
    prvtip = models.SmallIntegerField(db_column='PrvTip', blank=True, null=True)
    prvcod = models.DecimalField(db_column='PrvCod', max_digits=12, decimal_places=0, blank=True,
                                 null=True)
    prvsec = models.SmallIntegerField(db_column='PrvSec', blank=True, null=True)
    vfaforpa = models.SmallIntegerField(db_column='VFaForPa', blank=True, null=True)
    vfaimpfe = models.DateTimeField(db_column='VfaImpFe', blank=True, null=True)
    vfaimpcl = models.SmallIntegerField(db_column='VfaImpCl', blank=True, null=True)
    vfaimppa = models.SmallIntegerField(db_column='VfaImpPa', blank=True, null=True)
    vfacarnum = models.IntegerField(db_column='VfaCarNum', blank=True, null=True)
    vfaimppo = models.SmallIntegerField(db_column='VfaImpPo', blank=True, null=True)
    vfaemcbam = models.IntegerField(db_column='VfaEmCbAm', blank=True, null=True)
    vfaemcbnu = models.IntegerField(db_column='VfaEmCbNu', blank=True, null=True)
    vfaemcbsu = models.SmallIntegerField(db_column='VfaEmCbSu', blank=True, null=True)
    vfaemcbti = models.SmallIntegerField(db_column='VfaEmCbTi', blank=True, null=True)
    atenumotr = models.IntegerField(db_column='AteNumOtr', blank=True, null=True)
    ateimpalm = models.SmallIntegerField(db_column='AteImpalm', blank=True, null=True)
    vfacalaut = models.SmallIntegerField(db_column='VfaCalAut', blank=True, null=True)
    aterefmod = models.CharField(db_column='ATEREFMOD', max_length=3, blank=True,
                                 null=True)
    ategenncd = models.SmallIntegerField(db_column='AteGenNcD', blank=True, null=True)
    ateemihse = models.SmallIntegerField(db_column='AteEmiHse', blank=True, null=True)
    ateemistr = models.SmallIntegerField(db_column='AteEmiStr', blank=True, null=True)
    ateemican = models.SmallIntegerField(db_column='AteEmiCAn', blank=True, null=True)
    aterefseg = models.SmallIntegerField(db_column='AteRefSeg', blank=True, null=True)
    atetartra = models.SmallIntegerField(db_column='AteTarTra', blank=True, null=True)
    atecodalf = models.CharField(db_column='ATECODALF', max_length=14, blank=True,
                                 null=True)
    atenumord = models.DecimalField(db_column='ATENUMORD', max_digits=14, decimal_places=0, blank=True,
                                    null=True)
    atenumenv = models.CharField(db_column='ATENUMENV', max_length=50, blank=True,
                                 null=True)
    ateestfel = models.SmallIntegerField(db_column='ATEESTFEL', blank=True, null=True)
    ateestsii = models.CharField(db_column='ATEESTSII', max_length=50, blank=True,
                                 null=True)
    atepasapo = models.CharField(db_column='AtePasapo', max_length=15, blank=True,
                                 null=True)
    ateestfed = models.CharField(db_column='AteEstFED', max_length=100, blank=True,
                                 null=True)
    atedocent = models.SmallIntegerField(db_column='ATEDOCENT', blank=True, null=True)
    atefecent = models.DateTimeField(db_column='ATEFECENT', blank=True, null=True)
    ateb2bgen = models.SmallIntegerField(db_column='AteB2bGen', blank=True, null=True)
    atepedres = models.SmallIntegerField(db_column='AtePedRes', blank=True, null=True)
    atevtores = models.DateTimeField(db_column='AteVtoRes', blank=True, null=True)
    movbodres = models.IntegerField(db_column='MovBodRes', blank=True, null=True)
    movnumres = models.IntegerField(db_column='MovNumRes', blank=True, null=True)
    movnumfre = models.IntegerField(db_column='MovNumFRe', blank=True, null=True)
    ateestres = models.SmallIntegerField(db_column='AteEstRes', blank=True, null=True)
    aterdvcho = models.CharField(db_column='AteRDvCho', max_length=1, blank=True,
                                 null=True)
    aterdvtra = models.CharField(db_column='AteRDvTra', max_length=1, blank=True,
                                 null=True)
    aterutcho = models.DecimalField(db_column='AteRutCho', max_digits=12, decimal_places=0, blank=True,
                                    null=True)
    ateruttra = models.DecimalField(db_column='AteRutTra', max_digits=12, decimal_places=0, blank=True,
                                    null=True)
    ateenvfab = models.SmallIntegerField(db_column='AteEnvFab', blank=True, null=True)
    ateseccod = models.SmallIntegerField(db_column='ATESECCOD', blank=True, null=True)
    ateemides = models.SmallIntegerField(db_column='AteEmiDes', blank=True, null=True)
    atenumfel = models.DecimalField(db_column='AteNumFel', max_digits=10, decimal_places=0, blank=True,
                                    null=True)
    atelastupd = models.DateTimeField(db_column='AteLastUpd', blank=True, null=True)
    ateclie1 = models.SmallIntegerField(db_column='AteClie1', blank=True, null=True)
    ateclie2 = models.IntegerField(db_column='AteClie2', blank=True, null=True)
    ateclie3 = models.SmallIntegerField(db_column='AteClie3', blank=True, null=True)
    ateclie4 = models.IntegerField(db_column='AteClie4', blank=True, null=True)
    ateclien1 = models.IntegerField(db_column='AteClien1', blank=True, null=True)
    ateclien2 = models.IntegerField(db_column='AteClien2', blank=True, null=True)
    atepedgen = models.SmallIntegerField(db_column='AtePedGen', blank=True, null=True)
    atemovnro = models.IntegerField(db_column='AteMovNro', blank=True, null=True)
    atemovest = models.SmallIntegerField(db_column='AteMovEst', blank=True, null=True)
    atemovtra = models.SmallIntegerField(db_column='AteMovTra', blank=True, null=True)
    aterefkey = models.CharField(db_column='AteRefKey', max_length=60, blank=True,
                                 null=True)
    ateestfec = models.SmallIntegerField(db_column='AteEstFEC', blank=True, null=True)
    atecliperf = models.IntegerField(db_column='AteCliPerf', blank=True, null=True)
    atercamon = models.DecimalField(db_column='AteRcaMon', max_digits=19,
                                    decimal_places=4)
    atercaptj = models.DecimalField(db_column='AteRcaPtj', max_digits=10,
                                    decimal_places=4)
    ateestfera = models.SmallIntegerField(db_column='AteEstFeRa')
    clicodadi = models.DecimalField(db_column='CliCodAdi', max_digits=12, decimal_places=0, blank=True,
                                    null=True)
    clisecadi = models.SmallIntegerField(db_column='CliSecAdi', blank=True, null=True)
    clitipadi = models.SmallIntegerField(db_column='CliTipAdi', blank=True, null=True)
    clitipman = models.SmallIntegerField(db_column='CliTipMan')
    clicodman = models.DecimalField(db_column='CliCodMan', max_digits=12,
                                    decimal_places=0)
    clisecman = models.SmallIntegerField(db_column='CliSecMan')
    atenumhas = models.IntegerField(db_column='AteNumHas', blank=True, null=True)
    atetrknum = models.DecimalField(db_column='AteTrkNum', max_digits=12, decimal_places=0, blank=True,
                                    null=True)
    atetrkaut = models.CharField(db_column='AteTrkAut', max_length=20, blank=True,
                                 null=True)
    atetiptra = models.SmallIntegerField(db_column='AteTipTra', blank=True, null=True)
    atesectra = models.SmallIntegerField(db_column='AteSecTra', blank=True, null=True)
    atedesemp = models.SmallIntegerField(db_column='ATEDESEMP', blank=True, null=True)
    pdvflgsync = models.SmallIntegerField(db_column='PdvFlgSync', blank=True, null=True)
    atedesest = models.SmallIntegerField(db_column='AteDesEst', blank=True, null=True)
    atefchven = models.DateField(db_column='AteFchVen', blank=True, null=True)
    ateestces = models.SmallIntegerField(db_column='AteEstCes', blank=True, null=True)
    ateestcesm = models.CharField(db_column='AteEstCesM', max_length=100, blank=True,
                                  null=True)
    atecompra = models.SmallIntegerField(blank=True, null=True)
    ateventa = models.SmallIntegerField(blank=True, null=True)
    atenint = models.IntegerField(db_column='ATENINT', blank=True, null=True)
    atenint1 = models.IntegerField(db_column='ATENINT1', blank=True, null=True)
    atenint2 = models.IntegerField(db_column='ATENINT2', blank=True, null=True)
    atenint3 = models.IntegerField(db_column='ATENINT3', blank=True, null=True)
    atenint4 = models.IntegerField(db_column='ATENINT4', blank=True, null=True)
    apecod = models.DecimalField(db_column='ApeCod', max_digits=12, decimal_places=0, blank=True,
                                 null=True)
    apetip = models.SmallIntegerField(db_column='ApeTip', blank=True, null=True)
    apesec = models.SmallIntegerField(db_column='ApeSec', blank=True, null=True)
    atensec = models.SmallIntegerField(db_column='ATENSEC', blank=True, null=True)
    atensec1 = models.SmallIntegerField(db_column='ATENSEC1', blank=True, null=True)
    atensec2 = models.SmallIntegerField(db_column='ATENSEC2', blank=True, null=True)
    atensec3 = models.SmallIntegerField(db_column='ATENSEC3', blank=True, null=True)
    atensec4 = models.SmallIntegerField(db_column='ATENSEC4', blank=True, null=True)
    ageclitip = models.SmallIntegerField(db_column='AGECLITIP', blank=True, null=True)
    ageclicod = models.DecimalField(db_column='AGECLICOD', max_digits=12, decimal_places=0, blank=True,
                                    null=True)
    ageclisec = models.SmallIntegerField(db_column='AGECLISEC', blank=True, null=True)
    agefeccar = models.DateTimeField(db_column='AGEFECCAR', blank=True, null=True)
    agefecoco = models.DateTimeField(db_column='AGEFECOCO', blank=True, null=True)
    agefecenv = models.DateTimeField(db_column='AGEFECENV', blank=True, null=True)
    ageocolis = models.DateTimeField(db_column='AGEOCOLIS', blank=True, null=True)
    ageccocod = models.SmallIntegerField(db_column='AGECCOCOD', blank=True, null=True)
    agetotcaj = models.IntegerField(db_column='AGETOTCAJ', blank=True, null=True)
    agetotcon = models.IntegerField(db_column='AGETOTCON', blank=True, null=True)
    agetotpal = models.IntegerField(db_column='AGETOTPAL', blank=True, null=True)
    agetempli = models.IntegerField(db_column='AGETEMPLI', blank=True, null=True)
    ageinsexp1 = models.CharField(db_column='AGEINSEXP1', max_length=100, blank=True,
                                  null=True)
    ageinsexp2 = models.CharField(db_column='AGEINSEXP2', max_length=100, blank=True,
                                  null=True)
    ageinsexp3 = models.CharField(db_column='AGEINSEXP3', max_length=100, blank=True,
                                  null=True)
    ageinsexp4 = models.CharField(db_column='AGEINSEXP4', max_length=100, blank=True,
                                  null=True)
    ageinsexp5 = models.CharField(db_column='AGEINSEXP5', max_length=100, blank=True,
                                  null=True)
    ageinsexp6 = models.CharField(db_column='AGEINSEXP6', max_length=100, blank=True,
                                  null=True)
    ageinsexp7 = models.CharField(db_column='AGEINSEXP7', max_length=100, blank=True,
                                  null=True)
    ageinsexp8 = models.CharField(db_column='AGEINSEXP8', max_length=100, blank=True,
                                  null=True)
    ageinsexp9 = models.CharField(db_column='AGEINSEXP9', max_length=100, blank=True,
                                  null=True)
    atesmarc = models.SmallIntegerField(db_column='AteSMArc', blank=True, null=True)

    class Meta:
        default_permissions = ()
        managed = False
        db_table = 'ATECLIEN'
        unique_together = (('cajcod', 'doccod', 'atenumrea'),)
    @property
    def estado(self):
        if self.ateestped == 0:
            return 'Activo'
        elif self.ateestped == 1:
            return 'Retenido'
        elif self.ateestped == 2:
            return 'Pendiente'
        elif self.ateestped == 3:
            return 'Cumplido'
        elif self.ateestped == 9:
            return 'Ingresado'

        return self.ateestped

    @property
    def condicion_venta(self):
        cache_key = f'condicion_venta_{self.clicod}'
        condicion_venta = cache.get(cache_key)
        if condicion_venta is None:
            condicion_venta = Condvent.objects.using('inet').filter(covcod=self.atecovcod).last()
            if condicion_venta:
                condicion_venta = condicion_venta.covnom
                cache.set(cache_key, condicion_venta, timeout=60 * 60)
            else:
                condicion_venta = ''

        return condicion_venta

    @property
    def cliente_email(self):
        cache_key = f'cliente_email_{self.clicod}'
        cliente_email = cache.get(cache_key)
        cliente_email=None
        if cliente_email is None:
            cliente = Clientd.objects.using('inet').filter(clicod=self.clicod).last()
            if cliente:
                cliente_email = cliente.to_cliente()
                # print(cliente_email)
                # cliente_email.email = cliente_email.email.strip()
                cache.set(cache_key, cliente_email, timeout=60 * 60)
            else:
                cliente_email = ''

        return cliente_email


    @property
    def vendedor_nombre(self):
        cache_key = f'vendedor_nombre_{self.vencod}'
        vendedor_nombre = cache.get(cache_key)

        if vendedor_nombre is None:
            vendedor = Vendores.objects.using('inet').filter(vencod=self.vencod).last()
            if vendedor:
                vendedor_nombre = vendedor.nombre
                cache.set(cache_key, vendedor_nombre, timeout=60 * 60)  # Cache for 1 hour
            else:
                vendedor_nombre = self.vencod

        return vendedor_nombre

    @property
    def nombre_documento(self):
        cache_key = f'tipdoc_nombre_{self.doccod}'
        nombre_documento = cache.get(cache_key)

        if nombre_documento is None:
            tipdoc = Tipdoc.objects.using('inet').filter(doccod=self.doccod).first()
            if tipdoc:
                nombre_documento = tipdoc.nombre_documento.strip()
                cache.set(cache_key, nombre_documento, timeout=60 * 60)  # Cache for 1 hour
            else:
                nombre_documento = 'Desconocido'  # Valor por defecto si no se encuentra el documento

        return nombre_documento

    @property
    def fecha_documento(self):
        return self.atefchcpe.strftime('%Y-%m-%dT%H:%M') if self.atefchcpe else None

    @property
    def neto(self):
        neto = Ateclie2.objects.filter().using('inet').filter(cajcod=self.cajcod, doccod=self.doccod,
                                                              atenumrea=self.atenumrea, ccecod=100).last()
        locale.setlocale(locale.LC_ALL, 'es_CL.UTF-8')

        return locale.format_string("%.0f", round(neto.atetotval, 0), grouping=True) if neto else 0


    @property
    def iva(self):
        neto = Ateclie2.objects.filter().using('inet').filter(cajcod=self.cajcod, doccod=self.doccod,
                                                              atenumrea=self.atenumrea, ccecod=170).last()

        locale.setlocale(locale.LC_ALL, 'es_CL.UTF-8')

        return locale.format_string("%.0f", round(neto.atetotval, 0), grouping=True) if neto else 0

    @property
    def total(self):
        neto = Ateclie2.objects.filter().using('inet').filter(cajcod=self.cajcod, doccod=self.doccod,
                                                              atenumrea=self.atenumrea, ccecod=200).last()

        locale.setlocale(locale.LC_ALL, 'es_CL.UTF-8')

        return locale.format_string("%.0f", round(neto.atetotval, 0), grouping=True) if neto else 0


    @property
    def detalles(self):
        import locale

        locale.setlocale(locale.LC_ALL, 'es_CL.UTF-8')
        detalle=[]
        suma_cajas=0
        for det in Atecli2.objects.filter().using('inet').filter(cajcod=self.cajcod, doccod=self.doccod,
                                                             atenumrea=self.atenumrea):
            suma_cajas+=det.atecanven/det.data_prod_venta.prdunicaj
            detalle_data = {
                "barcod": det.barcod,
                "atecanven": locale.format_string("%.0f", det.atecanven, grouping=True),
                "descripcion_corta": det.descripcion_corta,
                "embalaje": locale.format_string("%.0f", det.data_prod_venta.prdunicaj, grouping=True),
                "cajas": locale.format_string("%.1f", det.atecanven / det.data_prod_venta.prdunicaj, grouping=True),
                "ateqxp": locale.format_string("%.0f", det.ateqxp, grouping=True),
                "desc1": det.atedsccodu,
                "desc2": det.atedsccodd,
                "atetotlin": locale.format_string("%.0f", det.atetotlin, grouping=True),
            }

            detalle.append(detalle_data)

        return {"items": detalle, "suma_cajas": locale.format_string("%.1f", suma_cajas, grouping=True)}




    def to_json(self):
        # item = model_to_dict(self, exclude=['password', 'user_permissions'])
        item = model_to_dict(self)

        return item
