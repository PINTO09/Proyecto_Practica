from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('planificacion', '0005_create_cargahistorial_table'),
    ]

    operations = [
        migrations.RunSQL(
            sql=(
                'DELETE FROM planificacion_asignacion_docente AS anterior '
                'USING planificacion_asignacion_docente AS reciente '
                'WHERE anterior.id_asignacion < reciente.id_asignacion '
                'AND anterior.id_asignatura = reciente.id_asignatura '
                'AND anterior.id_carrera = reciente.id_carrera '
                'AND anterior.id_periodo = reciente.id_periodo '
                'AND UPPER(BTRIM(anterior.paralelo_asignado)) = '
                'UPPER(BTRIM(reciente.paralelo_asignado));'
            ),
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql=(
                'CREATE UNIQUE INDEX IF NOT EXISTS '
                'uq_plan_asig_demanda_paralelo_ci '
                'ON planificacion_asignacion_docente '
                '(id_asignatura, id_carrera, id_periodo, UPPER(BTRIM(paralelo_asignado)));'
            ),
            reverse_sql='DROP INDEX IF EXISTS uq_plan_asig_demanda_paralelo_ci;',
        ),
    ]
