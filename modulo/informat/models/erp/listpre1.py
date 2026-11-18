# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models
from django.forms import model_to_dict

class Listpre1(models.Model):
    liscod = models.SmallIntegerField(db_column='LisCod', primary_key=True)  # Field name made lowercase. The composite primary key (LisCod, BarCod) found, that is not supported. The first column is selected.
    barcod = models.CharField(db_column='BarCod', max_length=30)  # Field name made lowercase.
    lisprenet = models.DecimalField(db_column='LisPreNet', max_digits=13, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    lisprenue = models.DecimalField(db_column='LisPreNue', max_digits=13, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    lisdsccod = models.SmallIntegerField(db_column='LisDscCod', blank=True, null=True)  # Field name made lowercase.
    lisdscpor = models.DecimalField(db_column='LisDscPor', max_digits=10, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    lisllastup = models.DateTimeField(db_column='LisLLastup', blank=True, null=True)  # Field name made lowercase.
    lisdsccod2 = models.SmallIntegerField(db_column='LisDscCod2')  # Field name made lowercase.
    lisdscpor2 = models.DecimalField(db_column='LisDscPor2', max_digits=10, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    lisdsccod3 = models.SmallIntegerField(db_column='LisDscCod3')  # Field name made lowercase.
    lisdscpor3 = models.DecimalField(db_column='LisDscPor3', max_digits=10, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    lisdscmax = models.DecimalField(db_column='LisDscMax', max_digits=10, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    lispresup = models.DecimalField(db_column='LisPreSup', max_digits=14, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    listipflet = models.SmallIntegerField(db_column='LisTipFlet', blank=True, null=True)  # Field name made lowercase.
    lisporflet = models.IntegerField(db_column='LisPorFlet', blank=True, null=True)  # Field name made lowercase.
    lispreflet = models.DecimalField(db_column='LisPreFlet', max_digits=13, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    lisprdflag = models.SmallIntegerField(db_column='LisPrdFlag', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        default_permissions = ()
        managed = False
        db_table = 'LISTPRE1'
        unique_together = (('liscod', 'barcod'),)

    def toJSON(self):
        item = model_to_dict(self)
        return item
