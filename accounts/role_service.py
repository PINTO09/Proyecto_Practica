from django.utils import timezone
from django.contrib.auth.models import Group

from core.models import Rol
from .decorators import (
    ADMIN, AUTORIDAD, DECANO, COORDINADOR, FUNCIONARIO, DOCENTE, USUARIO, ESTUDIANTE,
)


MANAGED_ROLES = [
    ADMIN, AUTORIDAD, DECANO, COORDINADOR, FUNCIONARIO, DOCENTE, USUARIO, ESTUDIANTE,
]


def _persistir_rol(role):
    """Garantiza que el rol exista como entidad persistida antes de asignarlo."""
    return Rol.objects.get_or_create(
        codigo=role,
        defaults={'nombre': role, 'alcance': 'propio', 'modulos': {}},
    )


def asignar_rol(user, role, careers, actor):
    """Asigna un rol único al usuario (regla de transición Docente→Decano).

    El cambio de rol es transaccional: se eliminan todos los grupos gestionados
    y se asigna únicamente el nuevo rol.
    """
    _persistir_rol(role)
    user.groups.remove(*Group.objects.filter(name__in=MANAGED_ROLES))
    group, _ = Group.objects.get_or_create(name=role)
    user.groups.add(group)
    user.is_staff = role == ADMIN
    user.save(update_fields=['is_staff'])
    user.alcances_carrera.update(activo=False)
    if role == COORDINADOR:
        for career in careers:
            scope, _ = user.alcances_carrera.get_or_create(
                carrera=career,
                defaults={'asignado_por': actor},
            )
            scope.activo = True
            scope.asignado_por = actor
            scope.asignado_el = timezone.now()
            scope.save()
