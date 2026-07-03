import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_docente.settings')
import django
django.setup()
from core.models import Usuario
from django.contrib.auth.models import Group

cedula = '1712345678'
password = '12345678'

user = Usuario.objects.filter(cedula=cedula).first()
if not user:
    user = Usuario.objects.create_user(cedula=cedula, password=password)
else:
    user.set_password(password)
    user.save()

user.is_active = True
user.is_staff = True
user.is_superuser = True
user.save()

group, _ = Group.objects.get_or_create(name='Administrador')
user.groups.clear()
user.groups.add(group)

print('CREATED', user.cedula, user.is_active, user.is_superuser, group.name)
