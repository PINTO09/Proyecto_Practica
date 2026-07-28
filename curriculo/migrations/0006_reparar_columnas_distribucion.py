from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('curriculo', '0005_renombrar_horas_centro_computo'),
    ]

    operations = [
        migrations.RunSQL(
            sql=(
                'ALTER TABLE curriculo_asignatura '
                'ADD COLUMN IF NOT EXISTS horas_aula numeric(5,2) NOT NULL DEFAULT 0;'
                'ALTER TABLE curriculo_asignatura '
                'ADD COLUMN IF NOT EXISTS horas_centro_computo numeric(5,2) NOT NULL DEFAULT 0;'
                'DO $$ BEGIN '
                'IF EXISTS (SELECT 1 FROM information_schema.columns '
                "WHERE table_name = 'curriculo_asignatura' "
                "AND column_name = 'horas_laboratorio') THEN "
                'UPDATE curriculo_asignatura SET '
                'horas_centro_computo = horas_laboratorio '
                'WHERE horas_centro_computo = 0 AND horas_laboratorio > 0; '
                'END IF; END $$;'
                'UPDATE curriculo_asignatura SET horas_centro_computo = '
                'LEAST(GREATEST(horas_centro_computo, 0), horas_semanales_asignatura);'
                'UPDATE curriculo_asignatura SET '
                'horas_aula = GREATEST('
                'horas_semanales_asignatura - horas_centro_computo, 0'
                ') WHERE horas_aula + horas_centro_computo '
                '<> horas_semanales_asignatura;'
                'ALTER TABLE curriculo_asignatura '
                'DROP CONSTRAINT IF EXISTS chk_asignatura_horas_espacio;'
                'ALTER TABLE curriculo_asignatura '
                'ADD CONSTRAINT chk_asignatura_horas_espacio CHECK ('
                'horas_aula >= 0 AND horas_centro_computo >= 0 '
                'AND horas_aula + horas_centro_computo = horas_semanales_asignatura);'
            ),
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
