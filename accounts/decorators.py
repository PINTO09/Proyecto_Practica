from functools import wraps
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages
from django.utils.http import url_has_allowed_host_and_scheme

ADMIN = 'Administrador'
AUTORIDAD = 'Autoridad'
DECANO = 'Decano'
COORDINADOR = 'Coordinador'
USUARIO = 'Usuario'
FUNCIONARIO = 'Funcionario'
ESTUDIANTE = 'Estudiante'
DOCENTE = 'Docente'

ROLES = [ADMIN, AUTORIDAD, DECANO, COORDINADOR, FUNCIONARIO, DOCENTE, USUARIO, ESTUDIANTE]

ROLES_ADMIN = [ADMIN]
ROLES_ADMIN_AUTORIDAD = [ADMIN, AUTORIDAD]
ROLES_ADMIN_AUTORIDAD_DECANO = [ADMIN, AUTORIDAD, DECANO]
ROLES_ADMIN_AUTORIDAD_COORDINADOR = [ADMIN, AUTORIDAD, COORDINADOR]
ROLES_ESCRITURA = [ADMIN, AUTORIDAD, DECANO, COORDINADOR]
ROLES_TODOS = ROLES

# Permisos efectivos. Ocultar enlaces no es una medida de seguridad: esta
# matriz también se evalúa cuando se escribe una URL directamente.
MODULE_ACCESS = {
    ADMIN: {'*': {'view', 'change'}},
    AUTORIDAD: {
        'catalogos': {'view', 'change'}, 'docentes': {'view', 'change'},
        'certificados': {'view', 'change'},
        'curriculo': {'view', 'change'}, 'planificacion': {'view', 'change'},
        'reportes': {'view'}, 'restricciones': {'view', 'change'},
        'auditoria': {'view'}, 'self_service': {'view', 'change'},
        'seguridad': {'view', 'change'},
    },
    COORDINADOR: {
        'catalogos': {'view'}, 'docentes': {'view'}, 'curriculo': {'view'},
        'certificados': {'view', 'change'},
        'planificacion': {'view', 'change'}, 'reportes': {'view'},
        'restricciones': {'view'}, 'self_service': {'view', 'change'},
    },
    # El Decano conserva la estructura base del flujo del docente
    # (self_service, registro de actividad) y suma los permisos elevados de
    # autorización y control propios de su decanato.
    DECANO: {
        'catalogos': {'view', 'change'}, 'docentes': {'view', 'change'},
        'certificados': {'view', 'change'},
        'curriculo': {'view', 'change'}, 'planificacion': {'view', 'change'},
        'reportes': {'view'}, 'restricciones': {'view', 'change'},
        'auditoria': {'view'}, 'self_service': {'view', 'change'},
        'seguridad': {'view', 'change'},
    },
    FUNCIONARIO: {
        'catalogos': {'view'}, 'docentes': {'view'}, 'curriculo': {'view'},
        'certificados': {'view'},
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


def _rol_desde_bd(codigo):
    """Rol persistido en la BD o None si aún no está disponible."""
    from django.db import ProgrammingError, OperationalError
    from core.models import Rol
    try:
        return Rol.objects.filter(codigo=codigo, activo=True).first()
    except (ProgrammingError, OperationalError):
        return None


def _modulos_efectivos(codigo):
    """Permisos efectivos por módulo: prioriza la BD; cae al dict en instalación/tests."""
    from django.db import ProgrammingError, OperationalError
    from core.models import Rol
    try:
        rol = Rol.objects.filter(codigo=codigo, activo=True).first()
    except (ProgrammingError, OperationalError):
        rol = None
    if rol is None:
        return MODULE_ACCESS.get(codigo, {})
    return rol.modulos_efectivos()


def _alcance_rol(codigo):
    """Alcance del rol desde la BD; fallback al comportamiento previo."""
    from django.db import ProgrammingError, OperationalError
    from core.models import Rol
    try:
        rol = Rol.objects.filter(codigo=codigo, activo=True).first()
    except (ProgrammingError, OperationalError):
        rol = None
    if rol is None:
        if codigo in (ADMIN, AUTORIDAD, DECANO):
            return 'global'
        if codigo == COORDINADOR:
            return 'carreras'
        return 'propio'
    return rol.alcance


def can_access_module(user, module, action='view'):
    if not getattr(user, 'is_authenticated', False):
        return False
    if user.is_superuser:
        return True
    for role in get_user_roles(user):
        permissions = _modulos_efectivos(role)
        if action in permissions.get('*', set()) or action in permissions.get(module, set()):
            return True
    return False


def allowed_career_ids(user):
    """None indica alcance global; un conjunto vacío indica ningún alcance."""
    if user.is_superuser:
        return None
    roles = get_user_roles(user)
    if any(_alcance_rol(r) == 'global' for r in roles):
        return None
    if any(_alcance_rol(r) == 'carreras' for r in roles):
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
            referer = request.META.get('HTTP_REFERER')
            # No confiar en el Referer tal cual: un valor externo forzado
            # (open redirect) mandaría al usuario fuera del sitio después de
            # un intento de escritura bloqueado.
            if referer and url_has_allowed_host_and_scheme(
                referer, allowed_hosts={request.get_host()}, require_https=request.is_secure(),
            ):
                return redirect(referer)
            return redirect('core:dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped_view
