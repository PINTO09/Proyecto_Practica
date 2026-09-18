from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('curriculo', '0006_reparar_columnas_distribucion')]

    operations = [
        migrations.RunSQL(
            sql=(
                'ALTER TABLE curriculo_asignatura ADD COLUMN IF NOT EXISTS '
                'importante_certificado boolean NOT NULL DEFAULT TRUE;'
            ),
            reverse_sql=(
                'ALTER TABLE curriculo_asignatura '
                'DROP COLUMN IF EXISTS importante_certificado;'
            ),
            state_operations=[
                migrations.AddField(
                    model_name='curriculoasignatura',
                    name='importante_certificado',
                    field=models.BooleanField(
                        'Incluir en funciones y comisiones', default=True,
                        help_text='Marque si esta asignatura o actividad debe aparecer en el certificado de funciones y comisiones.',
                    ),
                ),
            ],
        ),
    ]
