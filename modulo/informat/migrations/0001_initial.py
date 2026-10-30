from django.db import migrations


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name='ConsultaStock',
            fields=[],
            options={
                'managed': False,
                'default_permissions': (),
                'permissions': [('consultar_stock', 'Puede consultar el stock de Informat')],
                'verbose_name': 'consulta de stock',
            },
        ),
    ]
