from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('catalogos', '0002_limite_por_modalidad'),
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
                          AND con.contype = 'f'
                    ) LOOP
                        EXECUTE 'ALTER TABLE limite_horario DROP CONSTRAINT ' || quote_ident(r.constraint_name);
                    END LOOP;
                END $$;
            ''',
            reverse_sql='''
                ALTER TABLE limite_horario ADD CONSTRAINT limite_horario_id_dedicacion_fkey
                    FOREIGN KEY (id_modalidad) REFERENCES catalogo_dedicacion_horaria(id_dedicacion)
                    ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED;
            ''',
            state_operations=[
                migrations.AlterField(
                    model_name='limitehorario',
                    name='id_modalidad',
                    field=models.ForeignKey(
                        db_column='id_modalidad',
                        on_delete=django.db.models.deletion.CASCADE,
                        to='catalogos.catalogomodalidadcontratacion',
                    ),
                ),
            ],
        ),
    ]
