from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('catalogos', '0003_fix_fk_constraint'),
    ]

    operations = [
        migrations.RunSQL(
            sql='''
                DO $$
                DECLARE
                    r RECORD;
                BEGIN
                    FOR r IN (
                        SELECT con.conname AS constraint_name
                        FROM pg_constraint con
                        JOIN pg_class tab ON tab.oid = con.conrelid
                        WHERE tab.relname = 'limite_horario'
                          AND con.contype = 'u'
                          AND con.conname LIKE 'limite_horario_id_dedicacion%'
                    ) LOOP
                        EXECUTE 'ALTER TABLE limite_horario DROP CONSTRAINT ' || quote_ident(r.constraint_name);
                    END LOOP;
                END $$;
                ALTER TABLE limite_horario ADD UNIQUE (id_modalidad);
            ''',
            reverse_sql='''
                ALTER TABLE limite_horario DROP CONSTRAINT IF EXISTS limite_horario_id_modalidad_key;
                ALTER TABLE limite_horario ADD UNIQUE (id_modalidad);
            ''',
            state_operations=[
                migrations.AlterUniqueTogether(
                    name='limitehorario',
                    unique_together={('id_modalidad',)},
                ),
            ],
        ),
    ]
