from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('docentes', '0003_validacion_tipo_documento'),
    ]
    operations = [
        migrations.CreateModel(
            name='FirmanteCertificado',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombres_completos', models.CharField(max_length=200)),
                ('cargo', models.CharField(max_length=200)),
                ('firma', models.ImageField(blank=True, null=True, upload_to='certificados/firmas/')),
                ('sello', models.ImageField(blank=True, null=True, upload_to='certificados/sellos/')),
                ('activo', models.BooleanField(default=True)),
                ('orden', models.PositiveSmallIntegerField(default=0)),
            ],
            options={
                'verbose_name': 'Firmante de certificado',
                'verbose_name_plural': 'Firmantes de certificados',
                'ordering': ('orden', 'nombres_completos'),
            },
        ),
        migrations.CreateModel(
            name='CertificadoEmitido',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('codigo', models.CharField(editable=False, max_length=30, unique=True)),
                ('tipo', models.CharField(choices=[('DEDICACION', 'Historial de dedicación'), ('CATEDRAS', 'Historial de cátedras'), ('FUNCIONES', 'Funciones y comisiones')], max_length=20)),
                ('firmante_nombre', models.CharField(max_length=200)),
                ('firmante_cargo', models.CharField(max_length=200)),
                ('fecha_emision', models.DateField(default=django.utils.timezone.localdate)),
                ('ciudad', models.CharField(default='Manta', max_length=80)),
                ('datos_certificados', models.JSONField()),
                ('creado_el', models.DateTimeField(auto_now_add=True)),
                ('docente', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='certificados_emitidos', to='docentes.docentefcacc')),
                ('emitido_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='certificados_generados', to=settings.AUTH_USER_MODEL)),
                ('firmante', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='certificados_emitidos', to='certificados.firmantecertificado')),
            ],
            options={
                'verbose_name': 'Certificado emitido',
                'verbose_name_plural': 'Certificados emitidos',
                'ordering': ('-creado_el',),
            },
        ),
    ]
