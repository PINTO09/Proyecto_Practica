from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('planificacion', '0002_actividades_complementarias'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='planificacionactividaddocente',
            name='id_carrera',
        ),
    ]
