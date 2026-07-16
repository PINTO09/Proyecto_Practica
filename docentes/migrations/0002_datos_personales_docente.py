from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('docentes', '0001_initial')]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql='''
                        ALTER TABLE docente ADD COLUMN IF NOT EXISTS tipo_documento VARCHAR(12) NOT NULL DEFAULT 'CEDULA';
                        ALTER TABLE docente ADD COLUMN IF NOT EXISTS fecha_nacimiento DATE NULL;
                        ALTER TABLE docente ADD COLUMN IF NOT EXISTS foto VARCHAR(100) NULL;
                        ALTER TABLE docente DROP CONSTRAINT IF EXISTS chk_doc_tipo_documento;
                        ALTER TABLE docente ADD CONSTRAINT chk_doc_tipo_documento
                            CHECK (tipo_documento IN ('CEDULA', 'PASAPORTE', 'RUC'));
                        ALTER TABLE docente DROP CONSTRAINT IF EXISTS chk_doc_tipo_sangre;
                        ALTER TABLE docente ADD CONSTRAINT chk_doc_tipo_sangre
                            CHECK (tipo_sangre IS NULL OR BTRIM(tipo_sangre) IN ('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'));
                    ''',
                    reverse_sql='''
                        ALTER TABLE docente DROP CONSTRAINT IF EXISTS chk_doc_tipo_sangre;
                        ALTER TABLE docente DROP CONSTRAINT IF EXISTS chk_doc_tipo_documento;
                        ALTER TABLE docente DROP COLUMN IF EXISTS foto;
                        ALTER TABLE docente DROP COLUMN IF EXISTS fecha_nacimiento;
                        ALTER TABLE docente DROP COLUMN IF EXISTS tipo_documento;
                    ''',
                ),
            ],
            state_operations=[
                migrations.AddField(
                    model_name='docentefcacc', name='tipo_documento',
                    field=models.CharField(
                        choices=[('CEDULA', 'Cédula'), ('PASAPORTE', 'Pasaporte'), ('RUC', 'RUC')],
                        db_column='tipo_documento', default='CEDULA', max_length=12,
                    ),
                ),
                migrations.AddField(
                    model_name='docentefcacc', name='fecha_nacimiento',
                    field=models.DateField(blank=True, db_column='fecha_nacimiento', null=True),
                ),
                migrations.AddField(
                    model_name='docentefcacc', name='foto',
                    field=models.ImageField(blank=True, db_column='foto', null=True, upload_to='docentes/fotos/'),
                ),
                migrations.AlterField(
                    model_name='docentefcacc', name='tipo_sangre',
                    field=models.CharField(
                        blank=True,
                        choices=[('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'), ('AB+', 'AB+'), ('AB-', 'AB-'), ('O+', 'O+'), ('O-', 'O-')],
                        db_column='tipo_sangre', max_length=5, null=True,
                    ),
                ),
            ],
        ),
    ]
