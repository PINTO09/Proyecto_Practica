from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('curriculo', '0003_porcentajes_uso_espacios'),
    ]

    operations = [
        migrations.RunSQL(
            sql=(
                'ALTER TABLE curriculo_asignatura '
                'ADD COLUMN IF NOT EXISTS horas_aula numeric(5,2) NOT NULL DEFAULT 0;'
                'ALTER TABLE curriculo_asignatura '
                'ADD COLUMN IF NOT EXISTS horas_laboratorio numeric(5,2) NOT NULL DEFAULT 0;'
                'UPDATE curriculo_asignatura SET '
                'horas_aula = horas_semanales_asignatura * porcentaje_aula / 100.0, '
                'horas_laboratorio = horas_semanales_asignatura * porcentaje_laboratorio / 100.0;'
                'ALTER TABLE curriculo_asignatura '
                'DROP CONSTRAINT IF EXISTS chk_asignatura_porcentajes;'
                'ALTER TABLE curriculo_asignatura '
                'DROP CONSTRAINT IF EXISTS chk_asignatura_horas_espacio;'
                'ALTER TABLE curriculo_asignatura '
                'ADD CONSTRAINT chk_asignatura_horas_espacio CHECK ('
                'horas_aula >= 0 AND horas_laboratorio >= 0 '
                'AND horas_aula + horas_laboratorio = horas_semanales_asignatura);'
                'ALTER TABLE curriculo_asignatura DROP COLUMN IF EXISTS porcentaje_aula;'
                'ALTER TABLE curriculo_asignatura DROP COLUMN IF EXISTS porcentaje_laboratorio;'
            ),
            reverse_sql=(
                'ALTER TABLE curriculo_asignatura '
                'ADD COLUMN IF NOT EXISTS porcentaje_aula smallint NOT NULL DEFAULT 100;'
                'ALTER TABLE curriculo_asignatura '
                'ADD COLUMN IF NOT EXISTS porcentaje_laboratorio smallint NOT NULL DEFAULT 0;'
                'UPDATE curriculo_asignatura SET porcentaje_aula = '
                'CASE WHEN horas_semanales_asignatura > 0 THEN '
                'ROUND(horas_aula * 100.0 / horas_semanales_asignatura) ELSE 100 END, '
                'porcentaje_laboratorio = CASE WHEN horas_semanales_asignatura > 0 THEN '
                '100 - ROUND(horas_aula * 100.0 / horas_semanales_asignatura) ELSE 0 END;'
                'ALTER TABLE curriculo_asignatura '
                'DROP CONSTRAINT IF EXISTS chk_asignatura_horas_espacio;'
                'ALTER TABLE curriculo_asignatura '
                'ADD CONSTRAINT chk_asignatura_porcentajes CHECK ('
                'porcentaje_aula BETWEEN 0 AND 100 '
                'AND porcentaje_laboratorio BETWEEN 0 AND 100 '
                'AND porcentaje_aula + porcentaje_laboratorio = 100);'
                'ALTER TABLE curriculo_asignatura DROP COLUMN IF EXISTS horas_aula;'
                'ALTER TABLE curriculo_asignatura DROP COLUMN IF EXISTS horas_laboratorio;'
            ),
            state_operations=[
                migrations.RemoveField(
                    model_name='curriculoasignatura',
                    name='porcentaje_aula',
                ),
                migrations.RemoveField(
                    model_name='curriculoasignatura',
                    name='porcentaje_laboratorio',
                ),
                migrations.AddField(
                    model_name='curriculoasignatura',
                    name='horas_aula',
                    field=models.DecimalField(
                        verbose_name='Horas semanales en aula',
                        max_digits=5, decimal_places=2, default=0,
                        db_column='horas_aula',
                    ),
                ),
                migrations.AddField(
                    model_name='curriculoasignatura',
                    name='horas_laboratorio',
                    field=models.DecimalField(
                        verbose_name='Horas semanales en laboratorio / centro de cómputo',
                        max_digits=5, decimal_places=2, default=0,
                        db_column='horas_laboratorio',
                    ),
                ),
            ],
        ),
    ]
