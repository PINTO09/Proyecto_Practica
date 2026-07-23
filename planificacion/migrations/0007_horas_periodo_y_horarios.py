from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('catalogos', '0006_periodo_estado_planificacion'),
        ('planificacion', '0006_unique_assignment_parallel'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql=(
                        "ALTER TABLE planificacion_asignacion_docente "
                        "ADD COLUMN IF NOT EXISTS semanas_planificadas SMALLINT NOT NULL DEFAULT 16;"
                        "ALTER TABLE planificacion_aula_horario "
                        "ADD COLUMN IF NOT EXISTS id_asignacion BIGINT NULL;"
                        "ALTER TABLE planificacion_aula_horario "
                        "ADD COLUMN IF NOT EXISTS dia_semana SMALLINT NOT NULL DEFAULT 1;"
                        "ALTER TABLE planificacion_aula_horario "
                        "ADD COLUMN IF NOT EXISTS hora_inicio TIME NULL;"
                        "ALTER TABLE planificacion_aula_horario "
                        "ADD COLUMN IF NOT EXISTS hora_fin TIME NULL;"
                        "DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_pah_asignacion') THEN "
                        "ALTER TABLE planificacion_aula_horario ADD CONSTRAINT fk_pah_asignacion "
                        "FOREIGN KEY (id_asignacion) REFERENCES planificacion_asignacion_docente(id_asignacion) ON DELETE RESTRICT; "
                        "END IF; END $$;"
                    ),
                    reverse_sql=(
                        "ALTER TABLE planificacion_aula_horario DROP CONSTRAINT IF EXISTS fk_pah_asignacion;"
                        "ALTER TABLE planificacion_aula_horario DROP COLUMN IF EXISTS hora_fin;"
                        "ALTER TABLE planificacion_aula_horario DROP COLUMN IF EXISTS hora_inicio;"
                        "ALTER TABLE planificacion_aula_horario DROP COLUMN IF EXISTS dia_semana;"
                        "ALTER TABLE planificacion_aula_horario DROP COLUMN IF EXISTS id_asignacion;"
                        "ALTER TABLE planificacion_asignacion_docente DROP COLUMN IF EXISTS semanas_planificadas;"
                    ),
                ),
            ],
            state_operations=[
                migrations.AddField(
                    model_name='planificacionasignaciondocente', name='semanas_planificadas',
                    field=models.PositiveSmallIntegerField(db_column='semanas_planificadas', default=16),
                ),
                migrations.AddField(
                    model_name='planificacionaulahorario', name='id_asignacion',
                    field=models.ForeignKey(blank=True, db_column='id_asignacion', null=True, on_delete=django.db.models.deletion.RESTRICT, to='planificacion.planificacionasignaciondocente'),
                ),
                migrations.AddField(
                    model_name='planificacionaulahorario', name='dia_semana',
                    field=models.PositiveSmallIntegerField(choices=[(1, 'Lunes'), (2, 'Martes'), (3, 'Miércoles'), (4, 'Jueves'), (5, 'Viernes'), (6, 'Sábado')], db_column='dia_semana', default=1),
                ),
                migrations.AddField(
                    model_name='planificacionaulahorario', name='hora_inicio',
                    field=models.TimeField(blank=True, db_column='hora_inicio', null=True),
                ),
                migrations.AddField(
                    model_name='planificacionaulahorario', name='hora_fin',
                    field=models.TimeField(blank=True, db_column='hora_fin', null=True),
                ),
            ],
        ),
    ]
