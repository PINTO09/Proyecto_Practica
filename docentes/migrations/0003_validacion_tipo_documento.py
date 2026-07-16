from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [('docentes', '0002_datos_personales_docente')]

    operations = [
        migrations.RunSQL(
            sql='''
                ALTER TABLE docente DROP CONSTRAINT IF EXISTS chk_doc_cedula_formato;
                ALTER TABLE docente ADD CONSTRAINT chk_doc_documento_formato CHECK (
                    (tipo_documento = 'CEDULA' AND cedula_docente ~ '^[0-9]{10}$') OR
                    (tipo_documento = 'RUC' AND cedula_docente ~ '^[0-9]{13}$') OR
                    (tipo_documento = 'PASAPORTE' AND cedula_docente ~ '^[A-Z0-9]{5,13}$')
                );
            ''',
            reverse_sql='''
                ALTER TABLE docente DROP CONSTRAINT IF EXISTS chk_doc_documento_formato;
                ALTER TABLE docente ADD CONSTRAINT chk_doc_cedula_formato CHECK (
                    cedula_docente ~ '^[0-9]{10}$' OR cedula_docente ~ '^[0-9]{13}$'
                );
            ''',
        ),
    ]
