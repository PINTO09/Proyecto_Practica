from .decorators import can_access_module
from django.db import ProgrammingError, OperationalError


def module_access(request):
    user = getattr(request, 'user', None)
    modules = ('catalogos', 'docentes', 'curriculo', 'planificacion', 'reportes', 'auditoria', 'restricciones')
    profile_photo_url = ''
    profile_display_name = ''
    if user and user.is_authenticated:
        try:
            from docentes.models import DocenteFcacc
            docente = DocenteFcacc.objects.only(
                'foto', 'nombres_completos'
            ).filter(cedula_docente=user.cedula).first()
            if docente:
                profile_display_name = docente.nombres_completos
                if docente.foto:
                    profile_photo_url = docente.foto.url
        except (ProgrammingError, OperationalError, ValueError):
            # La navegación debe seguir disponible durante instalación o si la
            # tabla externa de docentes aún no se ha cargado.
            pass
    return {
        'module_access': {
            module: can_access_module(user, module, 'view') for module in modules
        },
        'module_change': {
            module: can_access_module(user, module, 'change') for module in modules
        },
        'profile_photo_url': profile_photo_url,
        'profile_display_name': profile_display_name,
    }
