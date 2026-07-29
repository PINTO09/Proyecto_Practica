from django.apps import AppConfig
from django.db.models.signals import post_migrate


def create_groups(sender, **kwargs):
    from django.contrib.auth.models import Group
    from django.db import connection
    from .decorators import ROLES
    table_name = Group._meta.db_table
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = %s)",
            [table_name]
        )
        exists = cursor.fetchone()[0]
        if not exists:
            return
    for rol in ROLES:
        Group.objects.get_or_create(name=rol)


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        post_migrate.connect(create_groups, sender=self)
