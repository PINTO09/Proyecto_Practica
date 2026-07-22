from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('catalogos', '0004_rename_unique_constraint'),
    ]

    operations = [
        migrations.RunSQL(
            sql=(
                'ALTER TABLE catalogo_carrera '
                'ADD COLUMN IF NOT EXISTS es_actividad boolean DEFAULT FALSE;'
            ),
            reverse_sql=(
                'ALTER TABLE catalogo_carrera '
                'DROP COLUMN IF EXISTS es_actividad;'
            ),
            state_operations=[
                migrations.AddField(
                    model_name='catalogocarrera',
                    name='es_actividad',
                    field=models.BooleanField(default=False, db_column='es_actividad'),
                ),
            ],
        ),
    ]
