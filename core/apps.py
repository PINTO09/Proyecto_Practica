from django.apps import AppConfig
from django.db.models.signals import post_migrate


def _table_exists(table_name):
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = %s)",
            [table_name]
        )
        return cursor.fetchone()[0]


def create_groups(sender, **kwargs):
    from django.contrib.auth.models import Group
    # ROLES vive en accounts.decorators (core.decorators es un módulo
    # anterior sin usar que se quedó desactualizado: le faltan Docente y
    # Decano, por eso esos grupos nunca se pre-creaban tras un migrate).
    from accounts.decorators import ROLES
    if not _table_exists(Group._meta.db_table):
        return
    for rol in ROLES:
        Group.objects.get_or_create(name=rol)


def seed_roles(sender, **kwargs):
    """Crea/actualiza los roles (core.Rol) apenas existe la tabla, para que
    ningún flujo (p. ej. asignar un rol por primera vez) pueda encontrarse
    con un Rol a medio crear y sin permisos reales."""
    from django.core.management import call_command
    from .models import Rol
    if not _table_exists(Rol._meta.db_table):
        return
    call_command('seed_roles', verbosity=0)


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        post_migrate.connect(create_groups, sender=self)
        post_migrate.connect(seed_roles, sender=self)
