from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('curriculo', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(
            sql='ALTER TABLE curriculo_asignatura ADD COLUMN IF NOT EXISTS es_actividad boolean DEFAULT FALSE;',
            reverse_sql='ALTER TABLE curriculo_asignatura DROP COLUMN IF EXISTS es_actividad;',
            state_operations=[
                migrations.AddField(
                    model_name='curriculoasignatura',
                    name='es_actividad',
                    field=models.BooleanField(default=False, db_column='es_actividad'),
                ),
            ],
        ),
    ]
