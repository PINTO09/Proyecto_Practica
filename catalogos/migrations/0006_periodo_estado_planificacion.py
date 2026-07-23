from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('catalogos', '0005_carrera_es_actividad')]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    "ALTER TABLE catalogo_periodo_academico "
                    "ADD COLUMN IF NOT EXISTS estado_planificacion VARCHAR(15) NOT NULL DEFAULT 'BORRADOR';",
                    "ALTER TABLE catalogo_periodo_academico DROP COLUMN IF EXISTS estado_planificacion;",
                ),
            ],
            state_operations=[
                migrations.AddField(
                    model_name='catalogoperiodoacademico',
                    name='estado_planificacion',
                    field=models.CharField(
                        choices=[('BORRADOR', 'Borrador'), ('EN_REVISION', 'En revisión'), ('APROBADO', 'Aprobado'), ('CERRADO', 'Cerrado')],
                        db_column='estado_planificacion', default='BORRADOR', max_length=15,
                    ),
                ),
            ],
        ),
    ]
