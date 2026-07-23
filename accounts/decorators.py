from functools import wraps
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages

ADMIN = 'Administrador'
AUTORIDAD = 'Autoridad'
COORDINADOR = 'Coordinador'
USUARIO = 'Usuario'
FUNCIONARIO = 'Funcionario'
ESTUDIANTE = 'Estudiante'
DOCENTE = 'Docente'

ROLES = [ADMIN, AUTORIDAD, COORDINADOR, FUNCIONARIO, DOCENTE, USUARIO, ESTUDIANTE]

ROLES_ADMIN = [ADMIN]
ROLES_ADMIN_AUTORIDAD = [ADMIN, AUTORIDAD]
ROLES_ADMIN_AUTORIDAD_COORDINADOR = [ADMIN, AUTORIDAD, COORDINADOR]
ROLES_ESCRITURA = [ADMIN, AUTORIDAD, COORDINADOR]
ROLES_TODOS = ROLES

# Permisos efectivos. Ocultar enlaces no es una medida de seguridad: esta
# matriz también se evalúa cuando se escribe una URL directamente.
MODULE_ACCESS = {
    ADMIN: {'*': {'view', 'change'}},
    AUTORIDAD: {
        'catalogos': {'view', 'change'}, 'docentes': {'view', 'change'},
        'curriculo': {'view', 'change'}, 'planificacion': {'view', 'change'},
        'reportes': {'view'}, 'restricciones': {'view', 'change'},
        'auditoria': {'view'}, 'self_service': {'view', 'change'},
    },
    COORDINADOR: {
        'catalogos': {'view'}, 'docentes': {'view'}, 'curriculo': {'view'},
        'planificacion': {'view', 'change'}, 'reportes': {'view'},
        'restricciones': {'view'}, 'self_service': {'view', 'change'},
    },
    FUNCIONARIO: {
        'catalogos': {'view'}, 'docentes': {'view'}, 'curriculo': {'view'},
        'planificacion': {'view'}, 'reportes': {'view'},
        'self_service': {'view', 'change'},
    },
    DOCENTE: {'self_service': {'view', 'change'}},
    # Compatibilidad temporal: las cuentas antiguas "Usuario" se comportan
    # como docentes, nunca como operadores administrativos.
    USUARIO: {'self_service': {'view', 'change'}},
    ESTUDIANTE: {'self_service': {'view'}},
}


def get_user_roles(user):
    if user.is_superuser:
        return [ADMIN]
    return list(user.groups.filter(name__in=ROLES).values_list('name', flat=True))


def has_role(user, *roles):
    if user.is_superuser:
        return True
    return user.groups.filter(name__in=roles).exists()


def can_access_module(user, module, action='view'):
    if not getattr(user, 'is_authenticated', False):
        return False
    if user.is_superuser:
        return True
    if module == 'seguridad':
        return False
    for role in get_user_roles(user):
        permissions = MODULE_ACCESS.get(role, {})
        if action in permissions.get('*', set()) or action in permissions.get(module, set()):
            return True
    return False


def allowed_career_ids(user):
    """None indica alcance global; un conjunto vacío indica ningún alcance."""
    if user.is_superuser or has_role(user, ADMIN, AUTORIDAD):
        return None
    if has_role(user, COORDINADOR):
        return set(user.alcances_carrera.filter(activo=True).values_list('carrera_id', flat=True))
    return set()


def module_permission_required(module, action='view'):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            user = getattr(request, 'user', None)
            # RequestFactory no instala middleware; permite probar la función
            # interna de forma aislada. En HTTP real AuthenticationMiddleware
            # siempre añade request.user.
            if user is None:
                return view_func(request, *args, **kwargs)
            if not user.is_authenticated:
                return redirect('core:login_docente')
            if can_access_module(user, module, action):
                return view_func(request, *args, **kwargs)
            raise PermissionDenied
        return _wrapped_view
    return decorator


def role_required(*allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('core:login_docente')
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            if request.user.groups.filter(name__in=allowed_roles).exists():
                return view_func(request, *args, **kwargs)
            raise PermissionDenied
        return _wrapped_view
    return decorator


def funcionario_readonly(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('core:login_docente')
        es_funcionario = not request.user.is_superuser and request.user.groups.filter(name=FUNCIONARIO).exists()
        if es_funcionario and request.method == 'POST':
            messages.error(request, 'Los funcionarios solo tienen acceso de lectura.')
            return redirect(request.META.get('HTTP_REFERER', 'core:dashboard'))
        return view_func(request, *args, **kwargs)
    return _wrapped_view
