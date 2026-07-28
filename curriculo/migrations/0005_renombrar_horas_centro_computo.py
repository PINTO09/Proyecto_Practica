from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('curriculo', '0004_distribucion_por_horas'),
    ]

    operations = [
        migrations.RunSQL(
            sql=(
                'ALTER TABLE curriculo_asignatura '
                'RENAME COLUMN horas_laboratorio TO horas_centro_computo;'
            ),
            reverse_sql=(
                'ALTER TABLE curriculo_asignatura '
                'RENAME COLUMN horas_centro_computo TO horas_laboratorio;'
            ),
            state_operations=[
                migrations.RemoveField(
                    model_name='curriculoasignatura',
                    name='horas_laboratorio',
                ),
                migrations.AddField(
                    model_name='curriculoasignatura',
                    name='horas_centro_computo',
                    field=models.DecimalField(
                        verbose_name='Horas semanales en centro de cómputo',
                        max_digits=5, decimal_places=2, default=0,
                        db_column='horas_centro_computo',
                    ),
                ),
            ],
        ),
    ]
