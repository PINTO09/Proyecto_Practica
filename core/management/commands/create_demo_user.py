from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from core.models import Usuario, Docente


class Command(BaseCommand):
    help = 'Crea un usuario de prueba para acceder al dashboard'

    def add_arguments(self, parser):
        parser.add_argument('--cedula', default='1712345678')
        parser.add_argument('--password', default='12345678')
        parser.add_argument('--group', default='Usuario')
        parser.add_argument('--superuser', action='store_true')

    def handle(self, *args, **options):
        cedula = options['cedula']
        password = options['password']
        group_name = options['group']
        superuser = options['superuser']

        group, _ = Group.objects.get_or_create(name=group_name)
        user = Usuario.objects.filter(cedula=cedula).first()
        if not user:
            user = Usuario.objects.create_user(cedula=cedula, password=password)
        else:
            user.set_password(password)
            user.save()

        if superuser:
            user.is_staff = True
            user.is_superuser = True
            user.save()

        user.groups.clear()
        user.groups.add(group)
        user.is_active = True
        user.save()

        Docente.objects.get_or_create(
            cedula=cedula,
            defaults={'apellidos_nombres': f'Usuario {cedula}'}
        )

        self.stdout.write(self.style.SUCCESS(f'Usuario listo: cedula={cedula} password={password} grupo={group_name}'))
