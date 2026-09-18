from datetime import time

import django.db.models.deletion
from django.db import migrations, models


def crear_configuracion_inicial(apps, schema_editor):
    Config = apps.get_model('planificacion', 'ConfiguracionHorarioAcademico')
    Config.objects.get_or_create(
        configuracion_activa=True,
        defaults={
            'nombre_configuracion': 'Hora académica institucional',
            'duracion_bloque_minutos': 45,
            'hora_inicio_jornada': time(7, 0),
            'hora_fin_jornada': time(22, 0),
        },
    )


class Migration(migrations.Migration):

    dependencies = [
        ('planificacion', '0014_activo_peso_catalogo_actividad'),
    ]

    operations = [
        migrations.CreateModel(
            name='ConfiguracionHorarioAcademico',
            fields=[
                ('id_configuracion', models.AutoField(primary_key=True, serialize=False)),
                ('nombre_configuracion', models.CharField(default='Hora académica', max_length=80)),
                ('duracion_bloque_minutos', models.PositiveSmallIntegerField(default=45)),
                ('hora_inicio_jornada', models.TimeField(default=time(7, 0))),
                ('hora_fin_jornada', models.TimeField(default=time(22, 0))),
                ('configuracion_activa', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name': 'Configuración de hora académica',
                'verbose_name_plural': 'Configuración de horas académicas',
                'db_table': 'configuracion_horario_academico',
                'ordering': ('-configuracion_activa', 'id_configuracion'),
            },
        ),
        migrations.AddConstraint(
            model_name='configuracionhorarioacademico',
            constraint=models.CheckConstraint(
                check=models.Q(duracion_bloque_minutos__gt=0),
                name='chk_config_horario_duracion_positiva',
            ),
        ),
        migrations.AddConstraint(
            model_name='configuracionhorarioacademico',
            constraint=models.UniqueConstraint(
                condition=models.Q(configuracion_activa=True),
                fields=('configuracion_activa',),
                name='uq_config_horario_activa',
            ),
        ),
        migrations.RunPython(
            crear_configuracion_inicial,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
                        ALTER TABLE planificacion_aula_horario
                        ADD COLUMN IF NOT EXISTS id_espacio INTEGER NULL;

                        INSERT INTO catalogo_espacio_academico
                            (codigo_espacio, nombre_espacio, tipo_espacio, ubicacion, capacidad, espacio_activo)
                        SELECT
                            'HOR-' || MIN(h.id_horario)::text,
                            LEFT(MIN(h.nombre_aula), 100),
                            'AULA',
                            'Migrado desde horarios',
                            NULL,
                            TRUE
                        FROM planificacion_aula_horario h
                        WHERE NOT EXISTS (
                            SELECT 1
                            FROM catalogo_espacio_academico e
                            WHERE UPPER(BTRIM(e.nombre_espacio)) = UPPER(BTRIM(h.nombre_aula))
                        )
                        GROUP BY UPPER(BTRIM(h.nombre_aula));

                        UPDATE planificacion_aula_horario h
                        SET id_espacio = (
                            SELECT e.id_espacio
                            FROM catalogo_espacio_academico e
                            WHERE UPPER(BTRIM(e.nombre_espacio)) = UPPER(BTRIM(h.nombre_aula))
                            ORDER BY e.espacio_activo DESC, e.id_espacio
                            LIMIT 1
                        )
                        WHERE h.id_espacio IS NULL;

                        ALTER TABLE planificacion_aula_horario
                        ALTER COLUMN id_espacio SET NOT NULL;

                        DO $$ BEGIN
                            IF NOT EXISTS (
                                SELECT 1 FROM pg_constraint
                                WHERE conname = 'fk_pah_espacio'
                            ) THEN
                                ALTER TABLE planificacion_aula_horario
                                ADD CONSTRAINT fk_pah_espacio
                                FOREIGN KEY (id_espacio)
                                REFERENCES catalogo_espacio_academico(id_espacio)
                                ON UPDATE CASCADE ON DELETE RESTRICT;
                            END IF;
                        END $$;

                        ALTER TABLE planificacion_aula_horario
                        DROP CONSTRAINT IF EXISTS uk_pah_periodo_aula_dia_inicio;
                        DROP INDEX IF EXISTS uq_pah_periodo_aula_dia_inicio;
                        CREATE UNIQUE INDEX uq_pah_periodo_espacio_dia_inicio
                        ON planificacion_aula_horario
                            (id_periodo, id_espacio, dia_semana, hora_inicio);
                    """,
                    reverse_sql="""
                        DROP INDEX IF EXISTS uq_pah_periodo_espacio_dia_inicio;
                        CREATE UNIQUE INDEX IF NOT EXISTS uq_pah_periodo_aula_dia_inicio
                        ON planificacion_aula_horario
                            (id_periodo, UPPER(BTRIM(nombre_aula)), dia_semana, hora_inicio);
                        ALTER TABLE planificacion_aula_horario
                        DROP CONSTRAINT IF EXISTS fk_pah_espacio;
                        ALTER TABLE planificacion_aula_horario
                        DROP COLUMN IF EXISTS id_espacio;
                    """,
                ),
            ],
            state_operations=[
                migrations.AddField(
                    model_name='planificacionaulahorario',
                    name='id_espacio',
                    field=models.ForeignKey(
                        db_column='id_espacio',
                        on_delete=django.db.models.deletion.RESTRICT,
                        related_name='horarios',
                        to='planificacion.catalogoespacioacademico',
                    ),
                ),
                migrations.AlterField(
                    model_name='planificacionaulahorario',
                    name='nombre_aula',
                    field=models.CharField(db_column='nombre_aula', editable=False, max_length=50),
                ),
                migrations.AlterUniqueTogether(
                    name='planificacionaulahorario',
                    unique_together={('id_periodo', 'id_espacio', 'dia_semana', 'hora_inicio')},
                ),
            ],
        ),
    ]
