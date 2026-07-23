from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [('planificacion', '0007_horas_periodo_y_horarios')]

    operations = [
        migrations.AlterUniqueTogether(
            name='planificacionaulahorario',
            unique_together={('id_periodo', 'nombre_aula', 'dia_semana', 'hora_inicio')},
        ),
        migrations.RunSQL(
            sql=(
                'ALTER TABLE planificacion_aula_horario '
                'DROP CONSTRAINT IF EXISTS uk_pah_periodo_aula_turno;'
                'CREATE UNIQUE INDEX IF NOT EXISTS uq_pah_periodo_aula_dia_inicio '
                'ON planificacion_aula_horario (id_periodo, UPPER(BTRIM(nombre_aula)), dia_semana, hora_inicio);'
            ),
            reverse_sql=(
                'DROP INDEX IF EXISTS uq_pah_periodo_aula_dia_inicio;'
                'ALTER TABLE planificacion_aula_horario '
                'ADD CONSTRAINT uk_pah_periodo_aula_turno UNIQUE (id_periodo, nombre_aula, turno_horario);'
            ),
        ),
    ]
