from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [('planificacion', '0008_horario_unique_slot')]

    operations = [
        migrations.RunSQL(
            sql=(
                'CREATE TABLE IF NOT EXISTS planificacion_capacidad_especial ('
                'id_capacidad BIGSERIAL PRIMARY KEY,'
                'id_periodo INTEGER NOT NULL REFERENCES catalogo_periodo_academico(id_periodo),'
                'id_carrera INTEGER NOT NULL REFERENCES catalogo_carrera(id_carrera),'
                'estudiante_nombre VARCHAR(200) NOT NULL,'
                'condicion VARCHAR(200),'
                'informes_adjuntos TEXT,'
                'nivel_asignado VARCHAR(10),'
                'paralelo_asignado VARCHAR(20)'
                ');'
            ),
            reverse_sql='DROP TABLE IF EXISTS planificacion_capacidad_especial CASCADE;',
        ),
    ]
