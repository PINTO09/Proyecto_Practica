from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('planificacion', '0003_remove_actividad_carrera'),
    ]

    operations = [
        migrations.CreateModel(
            name='CargaHistorial',
            fields=[
                ('id_carga', models.BigAutoField(db_column='id_carga', primary_key=True, serialize=False)),
                ('fecha_carga', models.DateTimeField(auto_now_add=True, db_column='fecha_carga')),
                ('tipo_carga', models.CharField(db_column='tipo_carga', max_length=50)),
                ('archivo_origen', models.CharField(db_column='archivo_origen', max_length=255)),
                ('total_registros', models.IntegerField(db_column='total_registros', default=0)),
                ('registros_creados', models.IntegerField(db_column='registros_creados', default=0)),
                ('registros_actualizados', models.IntegerField(db_column='registros_actualizados', default=0)),
                ('registros_omitidos', models.IntegerField(db_column='registros_omitidos', default=0)),
                ('detalle_errores', models.TextField(blank=True, db_column='detalle_errores', null=True)),
                ('estado', models.CharField(db_column='estado', default='COMPLETADO', max_length=20)),
            ],
            options={
                'verbose_name': 'Historial de Carga',
                'verbose_name_plural': 'M8 · Cargas de Datos',
                'db_table': 'carga_historial',
                'managed': False,
            },
        ),
    ]
