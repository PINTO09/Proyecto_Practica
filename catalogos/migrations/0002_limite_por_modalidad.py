from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('catalogos', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(
            sql='''
                ALTER TABLE limite_horario DROP CONSTRAINT IF EXISTS limite_horario_id_dedicacion_fkey;
                ALTER TABLE limite_horario RENAME COLUMN id_dedicacion TO id_modalidad;
                ALTER TABLE limite_horario ADD CONSTRAINT limite_horario_id_modalidad_fkey
                    FOREIGN KEY (id_modalidad) REFERENCES catalogo_modalidad_contratacion(id_modalidad)
                    ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED;
            ''',
            reverse_sql='''
                ALTER TABLE limite_horario DROP CONSTRAINT IF EXISTS limite_horario_id_modalidad_fkey;
                ALTER TABLE limite_horario RENAME COLUMN id_modalidad TO id_dedicacion;
                ALTER TABLE limite_horario ADD CONSTRAINT limite_horario_id_dedicacion_fkey
                    FOREIGN KEY (id_dedicacion) REFERENCES catalogo_dedicacion_horaria(id_dedicacion)
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
                migrations.AlterUniqueTogether(
                    name='limitehorario',
                    unique_together={('id_modalidad',)},
                ),
            ],
        ),
    ]
