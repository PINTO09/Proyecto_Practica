from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db import DatabaseError, ProgrammingError, OperationalError, transaction
from django.urls import reverse
from django.apps import apps
from django.core.cache import cache
from django.utils import timezone
import secrets
import string

from .forms import (
    LoginForm, UsuarioCreateForm, UsuarioEditForm, DocenteFcaccForm,
    CambioPasswordObligatorioForm,
)
from .models import (
    Docente, DocenteTransaccional, Titulo, Publicacion, Curso,
    UsuarioAlcanceCarrera, EventoSeguridad,
)
from catalogos.models import (
    CatalogoCarrera, CatalogoPeriodoAcademico, CatalogoTipoDocente,
    CatalogoModalidadContratacion, CatalogoDedicacionHoraria,
)
from docentes.models import (
    DocenteFcacc, DocenteTituloAcademico,
    DocentePublicacionAcademica, DocenteCursoCapacitacion,
    DocenteAsignacionCarreraPeriodo,
)
from curriculo.models import CurriculoAsignatura
from planificacion.models import (
    PlanificacionAsignacionDocente, PlanificacionMatrizF4,
)
from auditoria.models import AuditoriaRegistroCambios
from restricciones.models import Limitacion
from accounts.decorators import (
    role_required, ROLES_ADMIN, ROLES_ADMIN_AUTORIDAD,
    ROLES_ADMIN_AUTORIDAD_COORDINADOR, ROLES_ESCRITURA,
    ADMIN, AUTORIDAD, COORDINADOR, USUARIO, FUNCIONARIO, ESTUDIANTE, DOCENTE,
    funcionario_readonly, can_access_module, module_permission_required,
)

Usuario = get_user_model()


def _client_ip(request):
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
    return (forwarded.split(',')[0].strip() if forwarded else request.META.get('REMOTE_ADDR')) or None


def _security_event(request, event_type, target=None, detail=''):
    EventoSeguridad.objects.create(
        tipo=event_type,
        actor=request.user if request.user.is_authenticated else None,
        usuario_afectado=target,
        direccion_ip=_client_ip(request),
        detalle=detail[:255],
    )


def _temporary_password(length=14):
    alphabet = string.ascii_letters + string.digits + '!@#$%'
    while True:
        value = ''.join(secrets.choice(alphabet) for _ in range(length))
        if (any(c.islower() for c in value) and any(c.isupper() for c in value)
                and any(c.isdigit() for c in value) and any(c in '!@#$%' for c in value)):
            return value


def _set_role_and_scope(user, role, careers, actor):
    from django.contrib.auth.models import Group
    managed_roles = [ADMIN, AUTORIDAD, COORDINADOR, FUNCIONARIO, DOCENTE, USUARIO, ESTUDIANTE]
    user.groups.remove(*Group.objects.filter(name__in=managed_roles))
    group, _ = Group.objects.get_or_create(name=role)
    user.groups.add(group)
    user.is_staff = role == ADMIN
    user.save(update_fields=['is_staff'])
    UsuarioAlcanceCarrera.objects.filter(usuario=user).update(activo=False)
    if role == COORDINADOR:
        for career in careers:
            scope, _ = UsuarioAlcanceCarrera.objects.get_or_create(
                usuario=user, carrera=career,
                defaults={'asignado_por': actor},
            )
            scope.activo = True
            scope.asignado_por = actor
            scope.asignado_el = timezone.now()
            scope.save()


def landing_view(request):
    if request.user.is_authenticated:
        return redirect('core:dashboard')
    return render(request, 'core/landing.html')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('core:dashboard')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            cedula = form.cleaned_data['cedula']
            password = form.cleaned_data['password']
            throttle_key = f'login-attempts:{_client_ip(request)}:{cedula}'
            attempts = cache.get(throttle_key, 0)
            if attempts >= 5:
                form.add_error(None, 'Cuenta temporalmente bloqueada por varios intentos. Inténtalo en 15 minutos.')
                return render(request, 'core/login.html', {'form': form}, status=429)
            user = authenticate(request, cedula=cedula, password=password)
            if user is not None:
                cache.delete(throttle_key)
                login(request, user)
                if user.debe_cambiar_password:
                    return redirect('core:cambiar_password_obligatorio')
                if user.groups.filter(name=ESTUDIANTE).exists():
                    return redirect('core:dashboard')
                if user.is_superuser or user.groups.filter(
                    name__in=[ADMIN, AUTORIDAD, COORDINADOR, DOCENTE, USUARIO, FUNCIONARIO]
                ).exists():
                    return redirect('core:dashboard')
                logout(request)
                form.add_error(None, 'No tienes un rol asignado. Contacta al administrador.')
            else:
                cache.set(throttle_key, attempts + 1, timeout=15 * 60)
                target = Usuario.objects.filter(cedula=cedula).first()
                _security_event(request, 'LOGIN_FALLIDO', target, 'Credenciales incorrectas')
                form.add_error(None, 'Cédula o contraseña incorrectos')
    else:
        form = LoginForm()

    return render(request, 'core/login.html', {'form': form})


@login_required
def dashboard_view(request):
    usuario = request.user
    context = {
        'active_section': 'dashboard', 'db_ready': False,
        'institutional_dashboard': can_access_module(usuario, 'planificacion', 'view'),
    }

    def db_stats():
        try:
            return {
                'total_carreras_fcacc': CatalogoCarrera.objects.count(),
                'total_periodos_fcacc': CatalogoPeriodoAcademico.objects.count(),
                'periodo_activo': CatalogoPeriodoAcademico.objects.filter(periodo_activo=True).first(),
                'total_docentes_fcacc': DocenteFcacc.objects.count(),
                'total_titulos': DocenteTituloAcademico.objects.count(),
                'total_publicaciones_fcacc': DocentePublicacionAcademica.objects.count(),
                'total_cursos_capacitacion': DocenteCursoCapacitacion.objects.count(),
                'total_usuarios_sistema': Usuario.objects.count(),
                'total_asignaturas': CurriculoAsignatura.objects.count(),
                'total_asignaciones_docentes': PlanificacionAsignacionDocente.objects.count(),
                'total_matriz_f4': PlanificacionMatrizF4.objects.count(),
                'total_auditoria': AuditoriaRegistroCambios.objects.count(),
                'total_limitaciones': Limitacion.objects.count(),
                'ultimos_docentes_fcacc': list(DocenteFcacc.objects.order_by('-id_docente')[:5]),
                'db_ready': True,
            }
        except (ProgrammingError, OperationalError):
            return {}

    context.update(db_stats())

    modulos_acceso = []
    slug_modulos = [
        ('catalogos', 'Catálogos', 'fa-database', '#0d6efd', 'rgba(13,110,253,0.1)'),
        ('docentes', 'Docentes', 'fa-chalkboard-teacher', '#0d6efd', 'rgba(13,110,253,0.1)'),
        ('curriculo', 'Currículo', 'fa-book-open', '#6f42c1', 'rgba(111,66,193,0.1)'),
        ('planificacion', 'Planificación', 'fa-calendar-check', '#ffc107', 'rgba(255,193,7,0.1)'),
        ('auditoria', 'Auditoría', 'fa-history', '#6c757d', 'rgba(108,117,125,0.1)'),
        ('restricciones', 'Restricciones', 'fa-exclamation-triangle', '#dc3545', 'rgba(220,53,69,0.1)'),
    ]
    for slug, nombre, icono, color, bg_color in slug_modulos:
        if not can_access_module(request.user, slug, 'view'):
            continue
        info = MODULOS.get(slug)
        if info:
            modulos_acceso.append({
                'nombre': nombre,
                'icono': icono,
                'color': color,
                'bg_color': bg_color,
                'url': reverse('core:modulo_' + slug),
                'modelos_count': len(info['modelos']),
            })
    context['modulos_acceso'] = modulos_acceso

    docente = Docente.objects.filter(cedula=usuario.cedula).first()
    if docente:
        context['docente'] = docente

    docente_fcacc = None
    fcacc_error = None
    try:
        if usuario.cedula:
            docente_fcacc = DocenteFcacc.objects.filter(cedula_docente=usuario.cedula).first()
            if not docente_fcacc:
                local_docente = Docente.objects.filter(cedula=usuario.cedula).first()
                if local_docente:
                    tipo_docente = CatalogoTipoDocente.objects.order_by('id_tipo_docente').first()
                    modalidad = CatalogoModalidadContratacion.objects.order_by('id_modalidad').first()
                    dedicacion = CatalogoDedicacionHoraria.objects.order_by('id_dedicacion').first()
                    if tipo_docente and modalidad and dedicacion:
                        docente_fcacc, _ = DocenteFcacc.objects.get_or_create(
                            cedula_docente=usuario.cedula,
                            defaults={
                                'id_tipo_docente': tipo_docente,
                                'id_modalidad': modalidad,
                                'id_dedicacion': dedicacion,
                                'nombres_completos': local_docente.apellidos_nombres or f'Usuario {usuario.cedula}',
                                'correo_institucional': local_docente.correo or None,
                                'numero_celular': local_docente.telefono or None,
                            },
                        )
    except (ProgrammingError, OperationalError) as exc:
        docente_fcacc = None
        fcacc_error = 'No se pudo leer la información FCACC de la base de datos.'

    context['docente_fcacc'] = docente_fcacc
    context['fcacc_error'] = fcacc_error
    if docente_fcacc:
        try:
            context['mis_asignaciones'] = PlanificacionAsignacionDocente.objects.filter(id_docente=docente_fcacc).select_related('id_asignatura', 'id_periodo')[:5]
            context['mis_publicaciones'] = DocentePublicacionAcademica.objects.filter(id_docente=docente_fcacc).order_by('-id_publicacion')[:5]
            periodo_activo = CatalogoPeriodoAcademico.objects.filter(periodo_activo=True).first()
            if periodo_activo:
                from planificacion.views import _build_docente_workload_map, _empty_workload
                wl = _build_docente_workload_map(periodo_id=periodo_activo.id_periodo).get(docente_fcacc.id_docente)
                if wl is None:
                    wl = _empty_workload()
                from catalogos.models import LimiteHorario
                limite = LimiteHorario.objects.filter(
                    id_modalidad=docente_fcacc.id_modalidad, activo=True
                ).first()
                max_total = ((limite.horas_maximas or 0) + (limite.horas_complementarias_maximas or 0)) if limite else 0
                horas_libres = max(0, max_total - (wl.get('total_horas', 0) or 0))
                context['workload'] = wl
                context['periodo_activo'] = periodo_activo
                context['max_total'] = max_total
                context['horas_libres'] = horas_libres
                context['mis_asignaciones_completo'] = PlanificacionAsignacionDocente.objects.filter(
                    id_docente=docente_fcacc, id_periodo=periodo_activo
                ).select_related('id_asignatura', 'id_carrera', 'id_campo')
        except (ProgrammingError, OperationalError):
            context['mis_asignaciones'] = []
            context['mis_publicaciones'] = []
            context['fcacc_error'] = 'No se pudo cargar la información relacionada del docente.'
    else:
        context['mis_asignaciones'] = []
        context['mis_publicaciones'] = []

    return render(request, 'core/dashboard.html', context)


@login_required
def logout_view(request):
    logout(request)
    return redirect('core:login')


@login_required
def cambiar_password_obligatorio_view(request):
    if not request.user.debe_cambiar_password:
        return redirect('core:dashboard')
    form = CambioPasswordObligatorioForm(request.user, request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        user.debe_cambiar_password = False
        user.password_cambiado_el = timezone.now()
        user.save(update_fields=['debe_cambiar_password', 'password_cambiado_el'])
        update_session_auth_hash(request, user)
        _security_event(request, 'CAMBIAR_CLAVE', user, 'Contraseña temporal reemplazada')
        messages.success(request, 'Tu contraseña se actualizó correctamente.')
        return redirect('core:dashboard')
    return render(request, 'core/cambiar_password_obligatorio.html', {'form': form})


@login_required
def mi_docente_view(request):
    """Compatibilidad con marcadores antiguos; la ficha única vive en Perfil."""
    return redirect('core:mi_perfil')


@login_required
def mi_perfil_view(request):
    usuario = request.user
    docente_fcacc = None
    fcacc_error = None
    try:
        if usuario.cedula:
            docente_fcacc = DocenteFcacc.objects.filter(cedula_docente=usuario.cedula).first()
            if not docente_fcacc:
                local_docente = Docente.objects.filter(cedula=usuario.cedula).first()
                if local_docente:
                    tipo_docente = CatalogoTipoDocente.objects.order_by('id_tipo_docente').first()
                    modalidad = CatalogoModalidadContratacion.objects.order_by('id_modalidad').first()
                    dedicacion = CatalogoDedicacionHoraria.objects.order_by('id_dedicacion').first()
                    if tipo_docente and modalidad and dedicacion:
                        docente_fcacc, _ = DocenteFcacc.objects.get_or_create(
                            cedula_docente=usuario.cedula,
                            defaults={
                                'id_tipo_docente': tipo_docente,
                                'id_modalidad': modalidad,
                                'id_dedicacion': dedicacion,
                                'nombres_completos': local_docente.apellidos_nombres or f'Usuario {usuario.cedula}',
                                'correo_institucional': local_docente.correo or None,
                                'numero_celular': local_docente.telefono or None,
                            },
                        )
    except (ProgrammingError, OperationalError):
        docente_fcacc = None
        fcacc_error = 'No se pudo leer la información FCACC de la base de datos.'

    local_docente = Docente.objects.filter(cedula=usuario.cedula).first()
    if request.method == 'POST':
        try:
            form = DocenteFcaccForm(
                request.POST, request.FILES, instance=docente_fcacc,
                user=usuario, local_docente=local_docente,
            )
            if form.is_valid():
                previous_photo = docente_fcacc.foto.name if docente_fcacc and docente_fcacc.foto else ''
                photo_storage = docente_fcacc.foto.storage if docente_fcacc and docente_fcacc.foto else None
                with transaction.atomic():
                    docente_fcacc = form.save()
                    local_docente, _ = Docente.objects.get_or_create(
                        cedula=usuario.cedula,
                        defaults={'apellidos_nombres': docente_fcacc.nombres_completos},
                    )
                    local_docente.apellidos_nombres = docente_fcacc.nombres_completos
                    local_docente.telefono = docente_fcacc.numero_celular
                    local_docente.correo = docente_fcacc.correo_institucional
                    local_docente.save(update_fields=['apellidos_nombres', 'telefono', 'correo'])
                    if usuario.email != (docente_fcacc.correo_institucional or ''):
                        usuario.email = docente_fcacc.correo_institucional or ''
                        usuario.save(update_fields=['email'])
                    current_photo = docente_fcacc.foto.name if docente_fcacc.foto else ''
                    if previous_photo and previous_photo != current_photo and photo_storage:
                        transaction.on_commit(
                            lambda name=previous_photo, storage=photo_storage: storage.delete(name)
                        )
                messages.success(request, 'Perfil actualizado correctamente.')
                return redirect('core:mi_perfil')
        except (ProgrammingError, OperationalError):
            messages.error(request, 'No se pudo guardar la información porque la tabla FCACC no está disponible.')
            form = DocenteFcaccForm(
                request.POST, request.FILES, user=usuario, local_docente=local_docente
            )
    else:
        form = DocenteFcaccForm(instance=docente_fcacc, user=usuario, local_docente=local_docente)

    return render(request, 'core/mi_perfil.html', {
        'form': form,
        'docente_fcacc': docente_fcacc,
        'fcacc_error': fcacc_error,
        'active_section': 'perfil',
    })


@login_required
@funcionario_readonly
def mis_titulos_view(request):
    usuario = request.user
    docente = Docente.objects.filter(cedula=usuario.cedula).first()
    if docente:
        titulos = Titulo.objects.filter(id_cedula=docente)
    else:
        titulos = []
    return render(request, 'core/mis_titulos.html', {'titulos': titulos, 'active_section': 'titulos'})


@login_required
@module_permission_required('self_service', 'change')
def crear_titulo_view(request):
    from .forms import TituloForm
    usuario = request.user
    docente, created = Docente.objects.get_or_create(
        cedula=usuario.cedula,
        defaults={'apellidos_nombres': f'Usuario {usuario.cedula}'}
    )
    if request.method == 'POST':
        form = TituloForm(request.POST)
        if form.is_valid():
            titulo = form.save(commit=False)
            titulo.id_cedula = docente
            titulo.save()
            messages.success(request, 'Título registrado correctamente.')
            return redirect('core:mis_titulos')
    else:
        form = TituloForm()
    return render(request, 'core/form_titulo.html', {'form': form, 'accion': 'Nuevo', 'active_section': 'titulos'})


@login_required
@funcionario_readonly
def mis_publicaciones_view(request):
    usuario = request.user
    docente = Docente.objects.filter(cedula=usuario.cedula).first()
    if docente:
        publicaciones = Publicacion.objects.filter(id_docente=docente)
    else:
        publicaciones = []
    return render(request, 'core/mis_publicaciones.html', {'publicaciones': publicaciones, 'active_section': 'publicaciones'})


@login_required
@module_permission_required('self_service', 'change')
def crear_publicacion_view(request):
    from .forms import PublicacionForm
    usuario = request.user
    docente, created = Docente.objects.get_or_create(
        cedula=usuario.cedula,
        defaults={'apellidos_nombres': f'Usuario {usuario.cedula}'}
    )
    if request.method == 'POST':
        form = PublicacionForm(request.POST)
        if form.is_valid():
            pub = form.save(commit=False)
            pub.id_docente = docente
            pub.save()
            messages.success(request, 'Publicación registrada correctamente.')
            return redirect('core:mis_publicaciones')
    else:
        form = PublicacionForm()
    return render(request, 'core/form_publicacion.html', {'form': form, 'accion': 'Nueva', 'active_section': 'publicaciones'})


@login_required
@funcionario_readonly
def mis_documentos_view(request):
    usuario = request.user
    docente = Docente.objects.filter(cedula=usuario.cedula).first()
    if docente:
        documentos = DocenteTransaccional.objects.filter(id_docente=docente)
    else:
        documentos = []
    return render(request, 'core/mis_documentos.html', {'documentos': documentos, 'active_section': 'documentos'})


@login_required
@funcionario_readonly
def mis_cursos_view(request):
    usuario = request.user
    if usuario.is_superuser or usuario.groups.filter(name__in=[ADMIN, AUTORIDAD, COORDINADOR]).exists():
        cursos = Curso.objects.all()
    else:
        docente = Docente.objects.filter(cedula=usuario.cedula).first()
        if docente:
            cursos = Curso.objects.filter(cursodocente__id_docente=docente).distinct()
        else:
            cursos = []
    return render(request, 'core/mis_cursos.html', {'cursos': cursos, 'active_section': 'cursos'})


@login_required
@module_permission_required('self_service', 'change')
def subir_documento_view(request):
    from .forms import DocumentoForm
    usuario = request.user
    docente, created = Docente.objects.get_or_create(
        cedula=usuario.cedula,
        defaults={'apellidos_nombres': f'Usuario {usuario.cedula}'}
    )
    docente_fcacc = None
    try:
        docente_fcacc = DocenteFcacc.objects.filter(cedula_docente=usuario.cedula).first()
    except Exception:
        pass
    if request.method == 'POST':
        form = DocumentoForm(request.POST, request.FILES, docente_fcacc=docente_fcacc, cedula_docente=usuario.cedula)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.id_docente = docente
            doc.save()
            messages.success(request, 'Documento subido correctamente.')
            return redirect('core:mis_documentos')
    else:
        form = DocumentoForm(docente_fcacc=docente_fcacc, cedula_docente=usuario.cedula)
    return render(request, 'core/form_documento.html', {'form': form, 'accion': 'Subir', 'active_section': 'documentos'})


def _require_admin(user):
    if not (user.is_superuser or user.groups.filter(name__in=[ADMIN, AUTORIDAD]).exists()):
        raise PermissionDenied
    return True


def _can_manage_target(actor, target):
    if actor.is_superuser:
        return True
    if target.is_superuser or target.groups.filter(name=ADMIN).exists():
        raise PermissionDenied
    return True


@login_required
def usuarios_list_view(request):
    return usuarios_por_rol_view(request, rol=None)


@login_required
def usuarios_por_rol_view(request, rol=None):
    if not _require_admin(request.user):
        return
    usuarios = Usuario.objects.prefetch_related(
        'groups', 'alcances_carrera__carrera'
    ).order_by('-date_joined')
    title = 'Usuarios del Sistema'
    if rol:
        usuarios = usuarios.filter(groups__name=rol)
        title = f'Usuarios - {rol}'
    usuarios = list(usuarios)
    docentes_por_cedula = {
        item.cedula_docente: item
        for item in DocenteFcacc.objects.filter(
            cedula_docente__in=[user.cedula for user in usuarios]
        )
    }
    for user in usuarios:
        user.docente_fcacc = docentes_por_cedula.get(user.cedula)
    return render(request, 'core/usuarios_list.html', {
        'usuarios': usuarios,
        'active_section': 'usuarios',
        'title': title,
        'role_name': rol,
    })


@login_required
def usuario_crear_view(request):
    if not _require_admin(request.user):
        return
    if request.method == 'POST':
        form = UsuarioCreateForm(request.POST, actor=request.user)
        if form.is_valid():
            try:
                from django.contrib.auth.models import Group
                with transaction.atomic():
                    temporary_password = _temporary_password()
                    user = form.save(commit=False)
                    user.set_password(temporary_password)
                    user.debe_cambiar_password = True
                    user.credenciales_emitidas_el = timezone.now()
                    user.credenciales_emitidas_por = request.user
                    user.save()
                    Docente.objects.get_or_create(
                        cedula=user.cedula,
                        defaults={'apellidos_nombres': f'Usuario {user.cedula}', 'correo': user.email},
                    )
                    _set_role_and_scope(
                        user, form.cleaned_data['rol'], form.cleaned_data['carreras'], request.user
                    )
                    _security_event(request, 'CREAR_CUENTA', user, f'Rol: {form.cleaned_data["rol"]}')
                    _security_event(request, 'EMITIR_CLAVE', user, 'Contraseña temporal inicial')
            except DatabaseError:
                form.add_error(
                    None,
                    'No fue posible crear el usuario. Verifique que las migraciones estén aplicadas e inténtelo nuevamente.',
                )
            else:
                return render(request, 'core/credencial_temporal.html', {
                    'usuario_obj': user,
                    'temporary_password': temporary_password,
                    'new_account': True,
                })
    else:
        form = UsuarioCreateForm(actor=request.user)
    return render(request, 'core/usuario_form.html', {
        'form': form,
        'accion': 'Crear',
        'active_section': 'usuarios',
    })


@login_required
def usuario_editar_view(request, usuario_id):
    if not _require_admin(request.user):
        return
    usuario = get_object_or_404(Usuario, pk=usuario_id)
    _can_manage_target(request.user, usuario)
    if request.method == 'POST':
        form = UsuarioEditForm(request.POST, instance=usuario, actor=request.user)
        if form.is_valid():
            if usuario == request.user and not form.cleaned_data.get('is_active'):
                form.add_error('is_active', 'No puedes desactivar tu propia cuenta.')
                return render(request, 'core/usuario_form.html', {
                    'form': form, 'usuario': usuario, 'accion': 'Editar',
                    'active_section': 'usuarios',
                })
            previous_active = usuario.is_active
            user = form.save()
            rol = form.cleaned_data.get('rol')
            if rol:
                _set_role_and_scope(user, rol, form.cleaned_data['carreras'], request.user)
            event_type = 'EDITAR_CUENTA'
            if previous_active != user.is_active:
                event_type = 'ACTIVAR' if user.is_active else 'DESACTIVAR'
            _security_event(request, event_type, user, f'Rol: {rol}')
            messages.success(request, f'Usuario {usuario.cedula} actualizado.')
            return redirect('core:usuarios_list')
    else:
        form = UsuarioEditForm(instance=usuario, actor=request.user)
    return render(request, 'core/usuario_form.html', {
        'form': form,
        'usuario': usuario,
        'accion': 'Editar',
        'active_section': 'usuarios',
    })


@login_required
def eventos_seguridad_view(request):
    _require_admin(request.user)
    eventos = EventoSeguridad.objects.select_related(
        'actor', 'usuario_afectado'
    ).all()[:250]
    return render(request, 'core/eventos_seguridad.html', {
        'eventos': eventos,
        'active_section': 'usuarios',
        'title': 'Eventos de seguridad',
    })


@login_required
def usuario_restablecer_password_view(request, usuario_id):
    _require_admin(request.user)
    if request.method != 'POST':
        raise PermissionDenied
    usuario = get_object_or_404(Usuario, pk=usuario_id)
    _can_manage_target(request.user, usuario)
    temporary_password = _temporary_password()
    usuario.set_password(temporary_password)
    usuario.debe_cambiar_password = True
    usuario.credenciales_emitidas_el = timezone.now()
    usuario.credenciales_emitidas_por = request.user
    usuario.save(update_fields=[
        'password', 'debe_cambiar_password', 'credenciales_emitidas_el',
        'credenciales_emitidas_por',
    ])
    _security_event(request, 'EMITIR_CLAVE', usuario, 'Restablecimiento administrativo')
    return render(request, 'core/credencial_temporal.html', {
        'usuario_obj': usuario,
        'temporary_password': temporary_password,
        'new_account': False,
    })


@login_required
def api_usuario_docente(request):
    _require_admin(request.user)
    cedula = (request.GET.get('cedula') or '').strip()
    if len(cedula) != 10 or not cedula.isdigit():
        return JsonResponse({'found': False, 'error': 'Cédula inválida'}, status=400)
    docente = DocenteFcacc.objects.filter(cedula_docente=cedula).first()
    if not docente:
        return JsonResponse({'found': False})
    return JsonResponse({
        'found': True,
        'nombre': docente.nombres_completos,
        'email': docente.correo_institucional or '',
        'activo': docente.docente_activo,
    })


# ─── Módulos CRUD ───────────────────────────────────────────────────────────

from django.db import ProgrammingError, OperationalError

MODULOS = {
    'catalogos': {
        'nombre': 'Catálogos',
        'icono': 'fa-database',
        'modelos': [
            ('Carreras', 'CatalogoCarrera'),
            ('Modalidades Contratación', 'CatalogoModalidadContratacion'),
            ('Dedicación Horaria', 'CatalogoDedicacionHoraria'),
            ('Tipo Docente', 'CatalogoTipoDocente'),
            ('Tipo Licencia', 'CatalogoTipoLicencia'),
            ('Países', 'CatalogoPais'),
            ('Títulos Posgrado', 'CatalogoTituloPosgrado'),
            ('Campo Conocimiento', 'CatalogoCampoConocimiento'),
            ('Grado Afinidad', 'CatalogoGradoAfinidad'),
            ('Tipo Publicación', 'CatalogoTipoPublicacion'),
            ('Tipo Curso Capacitación', 'CatalogoTipoCursoCapacitacion'),
            ('Períodos Académicos', 'CatalogoPeriodoAcademico'),
            ('Relación Carrera-Período', 'RelacionCarreraPeriodo'),
            ('Límites Horarios', 'LimiteHorario'),
        ],
    },
    'docentes': {
        'nombre': 'Docentes',
        'icono': 'fa-chalkboard-teacher',
        'modelos': [
            ('Docentes FCACC', 'DocenteFcacc'),
            ('Títulos Académicos', 'DocenteTituloAcademico'),
            ('Campos de Afinidad', 'DocenteCampoAfinidad'),
            ('Asignación Carrera-Período', 'DocenteAsignacionCarreraPeriodo'),
            ('Cursos de Capacitación', 'DocenteCursoCapacitacion'),
            ('Participación en Cursos', 'DocenteParticipacionCurso'),
            ('Publicaciones Académicas', 'DocentePublicacionAcademica'),
        ],
    },
    'curriculo': {
        'nombre': 'Currículo',
        'icono': 'fa-book-open',
        'modelos': [
            ('Asignaturas', 'CurriculoAsignatura'),
            ('Asignatura-Campo', 'CurriculoAsignaturaCampo'),
            ('Relación Posgrado-Campo', 'RelacionPosgradoCampo'),
        ],
    },
    'planificacion': {
        'nombre': 'Planificación',
        'icono': 'fa-calendar-check',
        'descripcion': 'Flujo principal para construir, revisar y controlar la planificacion docente.',
        'acciones': [
            ('Planificación', 'planificacion:planificacion_operativa', 'fa-table-cells', 'Gestionar demanda, paralelos, recomendaciones y asignaciones desde un solo flujo.'),
            ('Carga y actividades', 'planificacion:planificacion_consolidada_docentes', 'fa-clipboard-list', 'Revisar la carga docente y registrar las actividades complementarias.'),
            ('Horarios', 'planificacion:planificacionaulahorario_list', 'fa-calendar-days', 'Organizar aulas, días y horas sin cruces de docente o espacio.'),
            ('Reportes y control', 'reportes:centro_reportes', 'fa-file-excel', 'Validar la planificación y descargar reportes generales o detallados.'),
        ],
        'modelos': [],
    },
    'auditoria': {
        'nombre': 'Auditoría',
        'icono': 'fa-history',
        'modelos': [
            ('Registro de Cambios', 'AuditoriaRegistroCambios'),
        ],
    },
    'restricciones': {
        'nombre': 'Restricciones',
        'icono': 'fa-exclamation-triangle',
        'modelos': [
            ('Limitaciones', 'Limitacion'),
            ('Historial Limitaciones', 'HistorialLimitacion'),
            ('Cabecera', 'Cabecera'),
            ('Cuerpo', 'Cuerpo'),
        ],
    },
}


def _obtener_modelo(name):
    for app_config in apps.get_app_configs():
        try:
            model = app_config.get_model(name)
            if model is not None:
                return model
        except LookupError:
            continue
    return None


def _stats_modelo(model_class):
    try:
        return model_class.objects.count()
    except (ProgrammingError, OperationalError):
        return '—'


def _build_crud_url(model_name, action='list'):
    for app_config in apps.get_app_configs():
        try:
            app_config.get_model(model_name)
            return reverse(f'{app_config.label}:{model_name.lower()}_{action}')
        except LookupError:
            continue
    return '#'


@login_required
def modulo_view(request, slug):
    info = MODULOS.get(slug)
    if not info:
        return redirect('core:dashboard')
    if not can_access_module(request.user, slug, 'view'):
        raise PermissionDenied

    modelos_con_stats = []
    for label, class_name in info['modelos']:
        cls = _obtener_modelo(class_name)
        if cls is None:
            continue
        list_url = _build_crud_url(class_name, 'list')
        modelos_con_stats.append({
            'label': label,
            'class_name': class_name,
            'count': _stats_modelo(cls),
            'list_url': list_url if list_url != '#' else '#',
            'add_url': _build_crud_url(class_name, 'create'),
            'crud_url': list_url if list_url != '#' else '#',
        })

    acciones = [
        {
            'label': label,
            'url': reverse(url_name),
            'icon': icon,
            'description': description,
        }
        for label, url_name, icon, description in info.get('acciones', [])
    ]

    context = {
        'active_section': f'modulo_{slug}',
        'modulo': info,
        'modulo_slug': slug,
        'modelos': modelos_con_stats,
        'acciones': acciones,
    }
    return render(request, 'core/modulo.html', context)


# ——— API: Información genérica de modelo (para auto-fill) ——

@login_required
def api_modelo_info(request):
    app_label = request.GET.get('app')
    model_name = request.GET.get('model')
    pk = request.GET.get('pk')
    if not all([app_label, model_name, pk]):
        return JsonResponse({'error': 'app, model y pk requeridos'}, status=400)
    if not can_access_module(request.user, app_label, 'view'):
        raise PermissionDenied
    try:
        Model = apps.get_model(app_label, model_name)
        obj = Model.objects.get(pk=pk)
    except (LookupError, Model.DoesNotExist):
        return JsonResponse({'error': 'no encontrado'}, status=404)

    data = {'pk': obj.pk, '__str__': str(obj)}
    for f in Model._meta.get_fields():
        if f.concrete and not f.auto_created and f.name != Model._meta.pk.name:
            val = getattr(obj, f.name, None)
            if f.is_relation:
                data[f.name] = str(val) if val else ''
                data[f.name + '_id'] = val.pk if val else None
            elif hasattr(val, 'isoformat'):
                data[f.name] = val.isoformat() if val else None
            else:
                data[f.name] = val
    return JsonResponse(data)

