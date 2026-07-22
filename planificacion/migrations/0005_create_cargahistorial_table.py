from django.db import migrations


def create_table_if_missing(apps, schema_editor):
    model = apps.get_model('planificacion', 'CargaHistorial')
    existing_tables = schema_editor.connection.introspection.table_names()
    if model._meta.db_table not in existing_tables:
        schema_editor.create_model(model)


def keep_history_on_reverse(apps, schema_editor):
    # El historial de cargas es evidencia operativa; no se elimina al revertir.
    return None


class Migration(migrations.Migration):
    dependencies = [
        ('planificacion', '0004_cargahistorial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='cargahistorial',
            options={
                'db_table': 'carga_historial',
                'verbose_name': 'Historial de Carga',
                'verbose_name_plural': 'M8 · Cargas de Datos',
            },
        ),
        migrations.RunPython(create_table_if_missing, keep_history_on_reverse),
    ]
