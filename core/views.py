from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from .forms import LoginForm, UsuarioCreateForm, UsuarioEditForm
from .models import Docente, Carrera, Periodo, DocenteTransaccional, Titulo, Publicacion, Curso, CursoDocente
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
    context = {}

    if usuario.is_superuser or usuario.groups.filter(name__in=[ADMIN, AUTORIDAD, COORDINADOR]).exists():
        context.update({
            'total_docentes': Docente.objects.count(),
            'total_carreras': Carrera.objects.count(),
            'total_periodos': Periodo.objects.count(),
            'total_asignaciones': DocenteTransaccional.objects.count(),
            'ultimos_docentes': Docente.objects.order_by('-id')[:5],
        })

    docente = Docente.objects.filter(cedula=usuario.cedula).first()
    if docente:
        context['docente'] = docente

    return render(request, 'core/dashboard.html', context)


@login_required
def logout_view(request):
    logout(request)
    return redirect('core:login')


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
    return render(request, 'core/mi_perfil.html', {'form': form, 'docente': docente})


@login_required
@funcionario_readonly
def mis_titulos_view(request):
    usuario = request.user
    docente = Docente.objects.filter(cedula=usuario.cedula).first()
    if docente:
        titulos = Titulo.objects.filter(id_cedula=docente)
    else:
        titulos = []
    return render(request, 'core/mis_titulos.html', {'titulos': titulos})


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
    return render(request, 'core/form_titulo.html', {'form': form, 'accion': 'Nuevo'})


@login_required
@funcionario_readonly
def mis_publicaciones_view(request):
    usuario = request.user
    docente = Docente.objects.filter(cedula=usuario.cedula).first()
    if docente:
        publicaciones = Publicacion.objects.filter(id_docente=docente)
    else:
        publicaciones = []
    return render(request, 'core/mis_publicaciones.html', {'publicaciones': publicaciones})


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
    return render(request, 'core/form_publicacion.html', {'form': form, 'accion': 'Nueva'})


@login_required
@funcionario_readonly
def mis_documentos_view(request):
    usuario = request.user
    docente = Docente.objects.filter(cedula=usuario.cedula).first()
    if docente:
        documentos = DocenteTransaccional.objects.filter(id_docente=docente)
    else:
        documentos = []
    return render(request, 'core/mis_documentos.html', {'documentos': documentos})


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
    return render(request, 'core/mis_cursos.html', {'cursos': cursos})


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
    return render(request, 'core/form_documento.html', {'form': form, 'accion': 'Subir'})


def _require_admin(user):
    if not (user.is_superuser or user.groups.filter(name__in=[ADMIN, AUTORIDAD]).exists()):
        raise PermissionDenied
    return True


@login_required
def usuarios_list_view(request):
    if not _require_admin(request.user):
        return
    usuarios = Usuario.objects.all().order_by('-date_joined')
    return render(request, 'core/usuarios_list.html', {
        'usuarios': usuarios,
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
    })
