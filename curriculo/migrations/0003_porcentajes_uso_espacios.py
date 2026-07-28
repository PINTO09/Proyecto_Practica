from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('curriculo', '0002_es_actividad'),
    ]

    operations = [
        migrations.RunSQL(
            sql=(
                'ALTER TABLE curriculo_asignatura '
                'ADD COLUMN IF NOT EXISTS porcentaje_aula smallint NOT NULL DEFAULT 100;'
                'ALTER TABLE curriculo_asignatura '
                'ADD COLUMN IF NOT EXISTS porcentaje_laboratorio smallint NOT NULL DEFAULT 0;'
                'ALTER TABLE curriculo_asignatura '
                'DROP CONSTRAINT IF EXISTS chk_asignatura_porcentajes;'
                'ALTER TABLE curriculo_asignatura ADD CONSTRAINT chk_asignatura_porcentajes '
                'CHECK (porcentaje_aula BETWEEN 0 AND 100 '
                'AND porcentaje_laboratorio BETWEEN 0 AND 100 '
                'AND porcentaje_aula + porcentaje_laboratorio = 100);'
            ),
            reverse_sql=(
                'ALTER TABLE curriculo_asignatura DROP CONSTRAINT IF EXISTS chk_asignatura_porcentajes;'
                'ALTER TABLE curriculo_asignatura DROP COLUMN IF EXISTS porcentaje_laboratorio;'
                'ALTER TABLE curriculo_asignatura DROP COLUMN IF EXISTS porcentaje_aula;'
            ),
            state_operations=[
                migrations.AddField(
                    model_name='curriculoasignatura',
                    name='porcentaje_aula',
                    field=models.PositiveSmallIntegerField(default=100, db_column='porcentaje_aula'),
                ),
                migrations.AddField(
                    model_name='curriculoasignatura',
                    name='porcentaje_laboratorio',
                    field=models.PositiveSmallIntegerField(default=0, db_column='porcentaje_laboratorio'),
                ),
            ],
        ),
    ]
