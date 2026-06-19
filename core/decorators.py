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

ROLES = [ADMIN, AUTORIDAD, COORDINADOR, USUARIO, FUNCIONARIO, ESTUDIANTE]

ROLES_ADMIN = [ADMIN]
ROLES_ADMIN_AUTORIDAD = [ADMIN, AUTORIDAD]
ROLES_ADMIN_AUTORIDAD_COORDINADOR = [ADMIN, AUTORIDAD, COORDINADOR]
ROLES_ESCRITURA = [ADMIN, AUTORIDAD, COORDINADOR, USUARIO]
ROLES_TODOS = ROLES


def get_user_roles(user):
    if user.is_superuser:
        return [ADMIN]
    return list(user.groups.filter(name__in=ROLES).values_list('name', flat=True))


def has_role(user, *roles):
    if user.is_superuser:
        return True
    return user.groups.filter(name__in=roles).exists()


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
