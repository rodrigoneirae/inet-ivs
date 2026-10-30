import uuid
from typing import Any

from django.db import migrations, models


def asignar_uuid(apps: Any, schema_editor: Any) -> None:
    intento = apps.get_model('anymarket', 'IntentoInet')
    for registro in intento.objects.using(schema_editor.connection.alias).filter(uuid__isnull=True).iterator():
        registro.uuid = uuid.uuid4()
        registro.save(using=schema_editor.connection.alias, update_fields=['uuid'])


class Migration(migrations.Migration):
    dependencies = [('anymarket', '0005_regladocumentoinet')]

    operations = [
        migrations.AddField(model_name='intentoinet', name='uuid', field=models.UUIDField(null=True, editable=False)),
        migrations.RunPython(asignar_uuid, migrations.RunPython.noop),
        migrations.AlterField(model_name='intentoinet', name='uuid',
                              field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
        migrations.AddField(model_name='intentoinet', name='solicitud_cifrada',
                            field=models.TextField(blank=True, default='')),
        migrations.AddField(model_name='intentoinet', name='respuesta_cifrada',
                            field=models.TextField(blank=True, default='')),
    ]
