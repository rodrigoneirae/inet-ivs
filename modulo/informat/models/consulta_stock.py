from django.db import models


class ConsultaStock(models.Model):
    class Meta:
        managed = False
        default_permissions = ()
        permissions = [
            ('consultar_stock', 'Puede consultar el stock de Informat'),
            ('administrar_token', 'Puede administrar el token de Informat'),
        ]
        verbose_name = 'consulta de stock'
