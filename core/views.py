from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db import ProgrammingError, OperationalError
from .forms import LoginForm, UsuarioCreateForm, UsuarioEditForm, DocenteFcaccForm
from .models import (
    Docente, Carrera, Periodo, DocenteTransaccional, Titulo, Publicacion, Curso, CursoDocente,
    CatalogoCarrera, CatalogoPeriodoAcademico, CatalogoTipoDocente, CatalogoModalidadContratacion,
    CatalogoDedicacionHoraria, DocenteFcacc, DocenteTituloAcademico,
    DocentePublicacionAcademica, DocenteCursoCapacitacion, DocenteAsignacionCarreraPeriodo,
    CurriculoAsignatura, PlanificacionAsignacionDocente, PlanificacionMatrizF4,
    SeguridadUsuario, AuditoriaRegistroCambios, Limitacion,
)
from .decorators import (
    role_required, ROLES_ADMIN, ROLES_ADMIN_AUTORIDAD,
    ROLES_ADMIN_AUTORIDAD_COORDINADOR, ROLES_ESCRITURA,
    ADMIN, AUTORIDAD, COORDINADOR, USUARIO, FUNCIONARIO, ESTUDIANTE,
    funcionario_readonly,
)

Usuario = get_user_model()


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
            user = authenticate(request, cedula=cedula, password=password)
            if user is not None:
                login(request, user)
                # Estudiante → app de estudiantes (placeholder)
                if user.groups.filter(name=ESTUDIANTE).exists():
                    try:
                        from django.urls import reverse
                        return redirect('estudiantes:dashboard')
                    except Exception:
                        return redirect('core:dashboard')
                # Superuser o roles docentes → core
                if user.is_superuser or user.groups.filter(
                    name__in=[ADMIN, AUTORIDAD, COORDINADOR, USUARIO, FUNCIONARIO]
                ).exists():
                    return redirect('core:dashboard')
                # Sin grupo valido
                logout(request)
                form.add_error(None, 'No tienes un rol asignado. Contacta al administrador.')
            else:
                form.add_error(None, 'Cédula o contraseña incorrectos')
    else:
        form = LoginForm()

    return render(request, 'core/login.html', {'form': form})


@login_required
def dashboard_view(request):
    usuario = request.user
    context = {'active_section': 'dashboard', 'db_ready': False}

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
                'total_usuarios_sistema': SeguridadUsuario.objects.count(),
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
@funcionario_readonly
def mi_docente_view(request):
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
            form = DocenteFcaccForm(request.POST, instance=docente_fcacc, user=usuario, local_docente=local_docente)
            if form.is_valid():
                form.save()
                messages.success(request, 'Datos del docente actualizados correctamente.')
                return redirect('core:mi_docente')
        except (ProgrammingError, OperationalError):
            messages.error(request, 'No se pudo guardar la información porque la tabla FCACC no está disponible.')
            form = DocenteFcaccForm(request.POST, user=usuario, local_docente=local_docente)
    else:
        form = DocenteFcaccForm(instance=docente_fcacc, user=usuario, local_docente=local_docente)

    return render(request, 'core/mi_docente.html', {
        'form': form,
        'docente_fcacc': docente_fcacc,
        'fcacc_error': fcacc_error,
        'active_section': 'mi_docente',
    })


@login_required
@funcionario_readonly
def mi_perfil_view(request):
    from .forms import DocentePerfilForm
    usuario = request.user
    docente, created = Docente.objects.get_or_create(
        cedula=usuario.cedula,
        defaults={'apellidos_nombres': f'Usuario {usuario.cedula}'}
    )
    if request.method == 'POST':
        form = DocentePerfilForm(request.POST, instance=docente)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil actualizado correctamente.')
            return redirect('core:mi_perfil')
    else:
        form = DocentePerfilForm(instance=docente)
    return render(request, 'core/mi_perfil.html', {'form': form, 'docente': docente, 'active_section': 'perfil'})


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
@role_required(*ROLES_ESCRITURA)
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
@role_required(*ROLES_ESCRITURA)
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
            cursos = Curso.objects.filter(cursodocente_set__id_docente=docente).distinct()
        else:
            cursos = []
    return render(request, 'core/mis_cursos.html', {'cursos': cursos, 'active_section': 'cursos'})


@login_required
@role_required(*ROLES_ESCRITURA)
def subir_documento_view(request):
    from .forms import DocumentoForm
    usuario = request.user
    docente, created = Docente.objects.get_or_create(
        cedula=usuario.cedula,
        defaults={'apellidos_nombres': f'Usuario {usuario.cedula}'}
    )
    if request.method == 'POST':
        form = DocumentoForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.id_docente = docente
            doc.save()
            messages.success(request, 'Documento subido correctamente.')
            return redirect('core:mis_documentos')
    else:
        form = DocumentoForm()
    return render(request, 'core/form_documento.html', {'form': form, 'accion': 'Subir', 'active_section': 'documentos'})


def _require_admin(user):
    if not (user.is_superuser or user.groups.filter(name__in=[ADMIN, AUTORIDAD, COORDINADOR]).exists()):
        raise PermissionDenied
    return True


@login_required
def usuarios_list_view(request):
    return usuarios_por_rol_view(request, rol=None)


@login_required
def usuarios_por_rol_view(request, rol=None):
    if not _require_admin(request.user):
        return
    usuarios = Usuario.objects.all().order_by('-date_joined')
    title = 'Usuarios del Sistema'
    if rol:
        usuarios = usuarios.filter(groups__name=rol)
        title = f'Usuarios - {rol}'
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
        form = UsuarioCreateForm(request.POST)
        if form.is_valid():
            user = form.save()
            Docente.objects.get_or_create(
                cedula=user.cedula,
                defaults={'apellidos_nombres': f'Usuario {user.cedula}'}
            )
            rol = form.cleaned_data.get('rol')
            if rol:
                from django.contrib.auth.models import Group
                group, _ = Group.objects.get_or_create(name=rol)
                user.groups.add(group)
            messages.success(request, f'Usuario {user.cedula} creado correctamente.')
            return redirect('core:usuarios_list')
    else:
        form = UsuarioCreateForm()
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
    if request.method == 'POST':
        form = UsuarioEditForm(request.POST, instance=usuario)
        if form.is_valid():
            user = form.save()
            rol = form.cleaned_data.get('rol')
            if rol:
                from django.contrib.auth.models import Group
                user.groups.clear()
                group, _ = Group.objects.get_or_create(name=rol)
                user.groups.add(group)
            messages.success(request, f'Usuario {usuario.cedula} actualizado.')
            return redirect('core:usuarios_list')
    else:
        form = UsuarioEditForm(instance=usuario)
    return render(request, 'core/usuario_form.html', {
        'form': form,
        'usuario': usuario,
        'accion': 'Editar',
        'active_section': 'usuarios',
    })


# ─── Módulos CRUD ───────────────────────────────────────────────────────────

from django.urls import reverse
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
    'seguridad': {
        'nombre': 'Seguridad',
        'icono': 'fa-shield-alt',
        'modelos': [
            ('Roles', 'SeguridadRol'),
            ('Usuarios', 'SeguridadUsuario'),
            ('Usuario-Rol', 'SeguridadUsuarioRol'),
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
        'modelos': [
            ('Demanda Académica', 'PlanificacionDemandaAcademica'),
            ('Asignación Docente', 'PlanificacionAsignacionDocente'),
            ('Reparto de Horas', 'PlanificacionRepartoHoras'),
            ('Matriz F4', 'PlanificacionMatrizF4'),
            ('Aula / Horario', 'PlanificacionAulaHorario'),
        ],
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
    import core.models as m
    return getattr(m, name, None)


def _stats_modelo(model_class):
    try:
        return model_class.objects.count()
    except (ProgrammingError, OperationalError):
        return '—'


def _build_admin_url(model_name, action='changelist'):
    return reverse(f'admin:core_{model_name.lower()}_{action}')


@login_required
def modulo_view(request, slug):
    info = MODULOS.get(slug)
    if not info:
        return redirect('core:dashboard')

    from django.contrib.admin import site
    modelos_con_stats = []
    for label, class_name in info['modelos']:
        cls = _obtener_modelo(class_name)
        if cls is None:
            continue
        modelos_con_stats.append({
            'label': label,
            'class_name': class_name,
            'count': _stats_modelo(cls),
            'list_url': _build_admin_url(class_name, 'changelist'),
            'add_url': _build_admin_url(class_name, 'add'),
            'crud_url': reverse('core:crud_spa', args=[class_name]),
        })

    context = {
        'active_section': f'modulo_{slug}',
        'modulo': info,
        'modulo_slug': slug,
        'modelos': modelos_con_stats,
    }
    return render(request, 'core/modulo.html', context)


@login_required
def crud_spa_view(request, model_name):
    modelo_cls = _obtener_modelo(model_name)
    if modelo_cls is None:
        return redirect('core:dashboard')
    context = {
        'active_section': 'dashboard',
        'model_name': model_name,
        'model_verbose_plural': getattr(modelo_cls._meta, 'verbose_name_plural', model_name),
        'model_verbose': getattr(modelo_cls._meta, 'verbose_name', model_name),
    }
    return render(request, 'core/crud_spa.html', context)
