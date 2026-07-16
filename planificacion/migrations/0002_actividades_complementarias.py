import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('catalogos', '0002_limite_por_modalidad'),
        ('docentes', '0002_datos_personales_docente'),
        ('planificacion', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CatalogoActividadComplementaria',
            fields=[
                ('id_actividad', models.AutoField(primary_key=True, serialize=False)),
                ('codigo_actividad', models.CharField(max_length=20, unique=True)),
                ('nombre_actividad', models.CharField(max_length=150)),
                ('tipo_actividad', models.CharField(
                    choices=[
                        ('COMPLEMENTARIA', 'Actividad complementaria'),
                        ('INVESTIGACION', 'Investigación'),
                        ('GESTION', 'Gestión académica'),
                        ('VINCULACION', 'Vinculación'),
                    ], default='COMPLEMENTARIA', max_length=20,
                )),
                ('actividad_activa', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name': 'Actividad complementaria',
                'verbose_name_plural': 'M5 · Planificación · Actividades complementarias',
                'db_table': 'catalogo_actividad_complementaria',
                'ordering': ('tipo_actividad', 'nombre_actividad'),
            },
        ),
        migrations.CreateModel(
            name='PlanificacionActividadDocente',
            fields=[
                ('id_actividad_docente', models.BigAutoField(primary_key=True, serialize=False)),
                ('horas_asignadas', models.PositiveSmallIntegerField(default=0)),
                ('observaciones', models.TextField(blank=True, null=True)),
                ('id_actividad', models.ForeignKey(
                    db_column='id_actividad', on_delete=django.db.models.deletion.RESTRICT,
                    to='planificacion.catalogoactividadcomplementaria',
                )),
                ('id_carrera', models.ForeignKey(
                    db_column='id_carrera', on_delete=django.db.models.deletion.RESTRICT,
                    to='catalogos.catalogocarrera',
                )),
                ('id_docente', models.ForeignKey(
                    db_column='id_docente', on_delete=django.db.models.deletion.RESTRICT,
                    to='docentes.docentefcacc',
                )),
                ('id_periodo', models.ForeignKey(
                    db_column='id_periodo', on_delete=django.db.models.deletion.RESTRICT,
                    to='catalogos.catalogoperiodoacademico',
                )),
            ],
            options={
                'verbose_name': 'Actividad asignada a docente',
                'verbose_name_plural': 'M5 · Planificación · Actividades de docentes',
                'db_table': 'planificacion_actividad_docente',
            },
        ),
        migrations.AddConstraint(
            model_name='planificacionactividaddocente',
            constraint=models.UniqueConstraint(
                fields=('id_docente', 'id_periodo', 'id_actividad'),
                name='uk_actividad_docente_periodo',
            ),
        ),
        migrations.AddConstraint(
            model_name='planificacionactividaddocente',
            constraint=models.CheckConstraint(
                check=models.Q(horas_asignadas__gt=0),
                name='chk_actividad_horas_positivas',
            ),
        ),
        migrations.RunPython(
            code=lambda apps, schema_editor: _seed_activities(apps),
            reverse_code=migrations.RunPython.noop,
        ),
    ]


def _seed_activities(apps):
    activity = apps.get_model('planificacion', 'CatalogoActividadComplementaria')
    rows = [
        ('INV', 'Investigación', 'INVESTIGACION'),
        ('GEST-ACA', 'Gestión académica', 'GESTION'),
        ('VINC', 'Vinculación con la sociedad', 'VINCULACION'),
        ('TUT', 'Tutorías y acompañamiento estudiantil', 'COMPLEMENTARIA'),
        ('PREP', 'Preparación y evaluación académica', 'COMPLEMENTARIA'),
    ]
    for code, name, kind in rows:
        activity.objects.get_or_create(
            codigo_actividad=code,
            defaults={'nombre_actividad': name, 'tipo_actividad': kind},
        )
