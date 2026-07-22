from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db import DatabaseError, ProgrammingError, OperationalError, transaction
from django.urls import reverse
from django.apps import apps

from .forms import LoginForm, UsuarioCreateForm, UsuarioEditForm, DocenteFcaccForm
from .models import (
    Docente, DocenteTransaccional, Titulo, Publicacion, Curso,
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
from seguridad.models import SeguridadUsuario
from auditoria.models import AuditoriaRegistroCambios
from restricciones.models import Limitacion
from accounts.decorators import (
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
                if user.groups.filter(name=ESTUDIANTE).exists():
                    return redirect('core:dashboard')
                if user.is_superuser or user.groups.filter(
                    name__in=[ADMIN, AUTORIDAD, COORDINADOR, USUARIO, FUNCIONARIO]
                ).exists():
                    return redirect('core:dashboard')
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

    modulos_acceso = []
    slug_modulos = [
        ('catalogos', 'Catálogos', 'fa-database', '#0d6efd', 'rgba(13,110,253,0.1)'),
        ('docentes', 'Docentes', 'fa-chalkboard-teacher', '#0d6efd', 'rgba(13,110,253,0.1)'),
        ('seguridad', 'Seguridad', 'fa-shield-alt', '#dc3545', 'rgba(220,53,69,0.1)'),
        ('curriculo', 'Currículo', 'fa-book-open', '#6f42c1', 'rgba(111,66,193,0.1)'),
        ('planificacion', 'Planificación', 'fa-calendar-check', '#ffc107', 'rgba(255,193,7,0.1)'),
        ('auditoria', 'Auditoría', 'fa-history', '#6c757d', 'rgba(108,117,125,0.1)'),
        ('restricciones', 'Restricciones', 'fa-exclamation-triangle', '#dc3545', 'rgba(220,53,69,0.1)'),
    ]
    for slug, nombre, icono, color, bg_color in slug_modulos:
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
    usuarios = Usuario.objects.prefetch_related('groups').order_by('-date_joined')
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
            try:
                from django.contrib.auth.models import Group
                with transaction.atomic():
                    user = form.save()
                    Docente.objects.get_or_create(
                        cedula=user.cedula,
                        defaults={'apellidos_nombres': f'Usuario {user.cedula}'},
                    )
                    group, _ = Group.objects.get_or_create(name=form.cleaned_data['rol'])
                    user.groups.add(group)
            except DatabaseError:
                form.add_error(
                    None,
                    'No fue posible crear el usuario. Verifique que las migraciones estén aplicadas e inténtelo nuevamente.',
                )
            else:
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
                user.groups.remove(*Group.objects.filter(name__in=[ADMIN, AUTORIDAD, COORDINADOR, USUARIO, FUNCIONARIO]))
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
        'descripcion': 'Flujo principal para construir, revisar y controlar la planificacion docente.',
        'acciones': [
            ('Demanda académica', 'planificacion:planificaciondemandaacademica_list', 'fa-list-check', 'Definir materias, niveles y número de paralelos requeridos.'),
            ('Planificación operativa', 'planificacion:planificacion_operativa', 'fa-table-cells', 'Asignar docentes por materia, paralelo y período.'),
            ('Matriz de paralelos', 'planificacion:planificacion_paralelos_matriz', 'fa-grip', 'Detectar visualmente paralelos asignados y pendientes.'),
            ('Asignaciones', 'planificacion:planificacionasignaciondocente_list', 'fa-users', 'Revisar y ajustar las asignaciones docentes registradas.'),
            ('Actividades docentes', 'planificacion:planificacionactividaddocente_list', 'fa-puzzle-piece', 'Registrar horas complementarias sin usar pseudo-carreras.'),
            ('Carga docente', 'planificacion:planificacion_consolidada_docentes', 'fa-clipboard-list', 'Controlar en una sola vista la carga, disponibilidad y cumplimiento por docente.'),
            ('Reportes y exportaciones', 'reportes:centro_reportes', 'fa-file-excel', 'Aplicar filtros y descargar archivos generales, detallados o de apoyo.'),
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

