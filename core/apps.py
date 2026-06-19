from django.apps import AppConfig
from django.db.models.signals import post_migrate


def create_groups(sender, **kwargs):
    from django.contrib.auth.models import Group
    from .decorators import ROLES
    for rol in ROLES:
        Group.objects.get_or_create(name=rol)


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        post_migrate.connect(create_groups, sender=self)
