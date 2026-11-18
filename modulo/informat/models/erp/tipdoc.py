# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models
from django.core.cache import cache


class Tipdoc(models.Model):
    doccod = models.SmallIntegerField(db_column='DocCod', primary_key=True)  # Field name made lowercase.
    grudoc = models.SmallIntegerField(db_column='GruDoc', blank=True, null=True)  # Field name made lowercase.
    libcod = models.SmallIntegerField(db_column='LibCod', blank=True, null=True)  # Field name made lowercase.
    docnom = models.CharField(db_column='DocNom', max_length=25, blank=True, null=True)  # Field name made lowercase.
    docnum = models.SmallIntegerField(db_column='DocNum', blank=True, null=True)  # Field name made lowercase.
    docranbol = models.SmallIntegerField(db_column='DocRanBol', blank=True, null=True)  # Field name made lowercase.
    docfchdoc = models.SmallIntegerField(db_column='DocFchDoc', blank=True, null=True)  # Field name made lowercase.
    docrut = models.SmallIntegerField(db_column='DocRut', blank=True, null=True)  # Field name made lowercase.
    docfchvto = models.SmallIntegerField(db_column='DocFchVto', blank=True, null=True)  # Field name made lowercase.
    docmon = models.SmallIntegerField(db_column='DocMon', blank=True, null=True)  # Field name made lowercase.
    docnumped = models.SmallIntegerField(db_column='DocNumPed', blank=True, null=True)  # Field name made lowercase.
    docnumlind = models.SmallIntegerField(db_column='DocNumLinD', blank=True, null=True)  # Field name made lowercase.
    docnumaso = models.SmallIntegerField(db_column='DocNumAso', blank=True, null=True)  # Field name made lowercase.
    docnumgui = models.SmallIntegerField(db_column='DocNumGui', blank=True, null=True)  # Field name made lowercase.
    docnumbol = models.SmallIntegerField(db_column='DocNumBol', blank=True, null=True)  # Field name made lowercase.
    docnumfac = models.SmallIntegerField(db_column='DocNumFac', blank=True, null=True)  # Field name made lowercase.
    docguifac = models.SmallIntegerField(db_column='DocGuiFac', blank=True, null=True)  # Field name made lowercase.
    docdirant = models.SmallIntegerField(db_column='DocDirAnt', blank=True, null=True)  # Field name made lowercase.
    docchkstk = models.SmallIntegerField(db_column='DocChkStk', blank=True, null=True)  # Field name made lowercase.
    docmovexi = models.SmallIntegerField(db_column='DocMovExi', blank=True, null=True)  # Field name made lowercase.
    docdocglo = models.SmallIntegerField(db_column='DocDocGlo', blank=True, null=True)  # Field name made lowercase.
    docestven = models.SmallIntegerField(db_column='DocEstVen', blank=True, null=True)  # Field name made lowercase.
    docest = models.SmallIntegerField(db_column='DocEst', blank=True, null=True)  # Field name made lowercase.
    docdsc = models.SmallIntegerField(db_column='DocDsc', blank=True, null=True)  # Field name made lowercase.
    docrec = models.SmallIntegerField(db_column='DocRec', blank=True, null=True)  # Field name made lowercase.
    doctmosalt = models.SmallIntegerField(db_column='DocTMoSalT', blank=True, null=True)  # Field name made lowercase.
    doctmosalc = models.SmallIntegerField(db_column='DocTMoSalC', blank=True, null=True)  # Field name made lowercase.
    docguitra = models.SmallIntegerField(db_column='DocGuiTra', blank=True, null=True)  # Field name made lowercase.
    docfacexp = models.SmallIntegerField(db_column='DocFacExp', blank=True, null=True)  # Field name made lowercase.
    docrecven = models.SmallIntegerField(db_column='DocRecVen', blank=True, null=True)  # Field name made lowercase.
    docultlin = models.SmallIntegerField(db_column='DocUltLin', blank=True, null=True)  # Field name made lowercase.
    docfordto = models.SmallIntegerField(db_column='DocForDto', blank=True, null=True)  # Field name made lowercase.
    docori = models.SmallIntegerField(db_column='DocOri', blank=True, null=True)  # Field name made lowercase.
    doclistip = models.CharField(db_column='DocLisTip', max_length=1, blank=True, null=True)  # Field name made lowercase.
    doctmoanut = models.SmallIntegerField(db_column='DocTmoAnuT', blank=True, null=True)  # Field name made lowercase.
    doctmoanuc = models.SmallIntegerField(db_column='DocTmoAnuC', blank=True, null=True)  # Field name made lowercase.
    docvtadir = models.SmallIntegerField(db_column='DocVtaDir', blank=True, null=True)  # Field name made lowercase.
    docforcdo = models.SmallIntegerField(db_column='DocForCDo', blank=True, null=True)  # Field name made lowercase.
    docfor2cd = models.SmallIntegerField(db_column='DocFor2Cd', blank=True, null=True)  # Field name made lowercase.
    doccosto = models.SmallIntegerField(db_column='DOCCOSTO', blank=True, null=True)  # Field name made lowercase.
    docdiscos = models.SmallIntegerField(db_column='DOCDISCOS', blank=True, null=True)  # Field name made lowercase.
    doccodsii = models.SmallIntegerField(db_column='DOCCODSII', blank=True, null=True)  # Field name made lowercase.
    docafeimp = models.SmallIntegerField(db_column='DocAfeImp', blank=True, null=True)  # Field name made lowercase.
    docimpest = models.SmallIntegerField(db_column='DocImpEst', blank=True, null=True)  # Field name made lowercase.
    doclasupde = models.DateTimeField(db_column='DocLasUpdE', blank=True, null=True)  # Field name made lowercase.
    doccodcrmk = models.CharField(db_column='DocCodCrmK', max_length=50)  # Field name made lowercase.
    docsiiex = models.SmallIntegerField(db_column='DocSiiEx', blank=True, null=True)  # Field name made lowercase.
    doclibven = models.SmallIntegerField(db_column='DocLibVen', blank=True, null=True)  # Field name made lowercase.
    docforind = models.SmallIntegerField(db_column='DocFOrInd', blank=True, null=True)  # Field name made lowercase.
    docfornew = models.SmallIntegerField(db_column='DocForNew', blank=True, null=True)  # Field name made lowercase.
    docforma = models.SmallIntegerField(db_column='DocForma', blank=True, null=True)  # Field name made lowercase.
    docrutmand = models.SmallIntegerField(db_column='DocRutMand', blank=True, null=True)  # Field name made lowercase.
    docrettip = models.SmallIntegerField(db_column='DocRetTip', blank=True, null=True)  # Field name made lowercase.
    docflete = models.SmallIntegerField(db_column='DocFlete', blank=True, null=True)  # Field name made lowercase.
    docart17 = models.SmallIntegerField(db_column='DocArt17', blank=True, null=True)  # Field name made lowercase.
    docbolran = models.SmallIntegerField(db_column='DocBolRan', blank=True, null=True)  # Field name made lowercase.
    docbolfis = models.SmallIntegerField(db_column='DocBolFis', blank=True, null=True)  # Field name made lowercase.
    docforpla = models.CharField(db_column='DocForPla', max_length=20, blank=True, null=True)  # Field name made lowercase.
    doclfsen = models.SmallIntegerField(db_column='DocLFSen', blank=True, null=True)  # Field name made lowercase.
    docactivof = models.SmallIntegerField(db_column='DocActivoF', blank=True, null=True)  # Field name made lowercase.
    docrantrb = models.SmallIntegerField(db_column='DOCRANTRB', blank=True, null=True)  # Field name made lowercase.
    docemiced = models.SmallIntegerField(db_column='DocEmiCed', blank=True, null=True)  # Field name made lowercase.
    docindser = models.SmallIntegerField(db_column='DocIndSer', blank=True, null=True)  # Field name made lowercase.
    docreqapr = models.SmallIntegerField(db_column='DOCREQAPR', blank=True, null=True)  # Field name made lowercase.
    docguitip = models.SmallIntegerField(db_column='DocGuiTip', blank=True, null=True)  # Field name made lowercase.
    docmodpre = models.SmallIntegerField(db_column='DOCMODPRE', blank=True, null=True)  # Field name made lowercase.
    dochondir = models.SmallIntegerField(db_column='DocHonDir', blank=True, null=True)  # Field name made lowercase.
    doccolptm = models.SmallIntegerField(db_column='DocColPtm', blank=True, null=True)  # Field name made lowercase.
    doccolret = models.SmallIntegerField(db_column='DocColRet', blank=True, null=True)  # Field name made lowercase.
    docforpro = models.SmallIntegerField(db_column='DOCFORPRO', blank=True, null=True)  # Field name made lowercase.
    docnewrep = models.SmallIntegerField(db_column='DOCNEWREP', blank=True, null=True)  # Field name made lowercase.
    docforpnu = models.SmallIntegerField(db_column='DOCFORPNU', blank=True, null=True)  # Field name made lowercase.
    docageadu = models.SmallIntegerField(db_column='DOCAGEADU', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        default_permissions = ()
        managed = False
        db_table = 'TIPDOC'
    @property
    def nombre_documento(self):
        cache_key = f'tipdoc_nombre_{self.doccod}'
        nombre_documento = cache.get(cache_key)

        if nombre_documento is None:
            nombre_documento = self.docnom
            cache.set(cache_key, nombre_documento, timeout=60*60)  # Cache for 1 hour

        return nombre_documento