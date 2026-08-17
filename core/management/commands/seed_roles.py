from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group

from core.models import Rol
from accounts.decorators import (
    ADMIN, AUTORIDAD, DECANO, COORDINADOR, FUNCIONARIO, DOCENTE, USUARIO, ESTUDIANTE,
)


def rol_seed_data():
    """Definición centralizada de roles y sus permisos por módulo."""
    def mod(*modulos):
        """Normaliza a formato {modulo: [view, change]}."""
        result = {}
        for entry in modulos:
            if isinstance(entry, tuple):
                module, actions = entry
            else:
                module, actions = entry, ['view', 'change']
            result[module] = actions
        return result

    return [
        {
            'codigo': ADMIN, 'nombre': 'Administrador',
            'descripcion': 'Control total de la plataforma.',
            'modulos': {'*': ['view', 'change']},
            'alcance': 'global',
        },
        {
            'codigo': AUTORIDAD, 'nombre': 'Autoridad',
            'descripcion': 'Alta dirección de la facultad con escritura institucional.',
            'modulos': mod(
                'catalogos', 'docentes', 'certificados', 'curriculo',
                'planificacion', 'reportes', 'restricciones', 'auditoria',
                'self_service', 'seguridad',
            ),
            'alcance': 'global',
        },
        {
            'codigo': DECANO, 'nombre': 'Decano',
            'descripcion': 'Mantiene la estructura base del docente y suma los '
                          'permisos elevados de autorización y control del decanato.',
            'modulos': mod(
                'catalogos', 'docentes', 'certificados', 'curriculo',
                'planificacion', 'reportes', 'restricciones', 'auditoria',
                'seguridad', 'self_service',
            ),
            'alcance': 'global',
        },
        {
            'codigo': COORDINADOR, 'nombre': 'Coordinador',
            'descripcion': 'Gestión académica limitada a las carreras autorizadas.',
            'modulos': mod(
                ('catalogos', ['view']), ('docentes', ['view']),
                ('curriculo', ['view']),
                ('certificados', ['view', 'change']),
                ('planificacion', ['view', 'change']),
                ('reportes', ['view']), ('restricciones', ['view']),
                ('self_service', ['view', 'change']),
            ),
            'alcance': 'carreras',
        },
        {
            'codigo': FUNCIONARIO, 'nombre': 'Funcionario',
            'descripcion': 'Personal administrativo/secretaría con acceso de lectura.',
            'modulos': mod(
                ('catalogos', ['view']), ('docentes', ['view']),
                ('curriculo', ['view']), ('certificados', ['view']),
                ('planificacion', ['view']), ('reportes', ['view']),
            ),
            'alcance': 'ninguno',
        },
        {
            'codigo': DOCENTE, 'nombre': 'Docente',
            'descripcion': 'Registro de actividad y expediente docente propio.',
            'modulos': mod(('self_service', ['view', 'change'])),
            'alcance': 'propio',
        },
        {
            'codigo': USUARIO, 'nombre': 'Usuario',
            'descripcion': 'Cuentas antiguas compatibles: se comportan como docentes.',
            'modulos': mod(('self_service', ['view', 'change'])),
            'alcance': 'propio',
        },
        {
            'codigo': ESTUDIANTE, 'nombre': 'Estudiante',
            'descripcion': 'Consulta propia de agenda y trámites académicos.',
            'modulos': mod(('self_service', ['view'])),
            'alcance': 'propio',
        },
    ]


class Command(BaseCommand):
    help = 'Crea o actualiza los roles del sistema y sus grupos de asignación.'

    def handle(self, *args, **options):
        created = 0
        updated = 0
        seeds = rol_seed_data()

        for data in seeds:
            Group.objects.get_or_create(name=data['codigo'])
            rol, was_created = Rol.objects.update_or_create(
                codigo=data['codigo'],
                defaults={
                    'nombre': data['nombre'],
                    'descripcion': data['descripcion'],
                    'modulos': data['modulos'],
                    'alcance': data['alcance'],
                    'activo': True,
                },
            )
            if was_created:
                created += 1
            else:
                updated += 1
            self.stdout.write(f'  {data["codigo"]}: {data["nombre"]}')

        self.stdout.write(self.style.SUCCESS(
            f'Roles listos: {created} creados, {updated} actualizados.'
        ))
