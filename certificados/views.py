from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import ADMIN, AUTORIDAD, allowed_career_ids, module_permission_required, role_required
from docentes.models import DocenteFcacc

from .forms import FirmanteCertificadoForm, GenerarCertificadoForm
from .models import CertificadoEmitido, FirmanteCertificado
from .services import (
    FUNCTION_FILTERS,
    FUNCTION_FILTER_LABELS,
    build_certificate_snapshot,
    normalize_function_filter,
)


REPORT_TYPES = {
    'dedicacion': {
        'certificate_type': 'DEDICACION',
        'title': 'Dedicación por período',
        'icon': 'fa-business-time',
        'description': 'Períodos, carreras, fechas y tiempo de dedicación registrados.',
    },
    'funciones': {
        'certificate_type': 'FUNCIONES',
        'title': 'Funciones y comisiones',
        'icon': 'fa-people-group',
        'description': 'Cargos, comisiones y actividades institucionales desempeñadas.',
    },
    'catedras': {
        'certificate_type': 'CATEDRAS',
        'title': 'Cátedras impartidas',
        'icon': 'fa-chalkboard-user',
        'description': 'Asignaturas impartidas, unidad académica, dedicación y fechas.',
    },
}


@module_permission_required('certificados', 'view')
def reporte_base(request, tipo):
    report_info = REPORT_TYPES.get(tipo)
    if not report_info:
        from django.http import Http404
        raise Http404('Tipo de reporte no disponible.')

    cedula = (request.GET.get('cedula') or '').strip().upper()
    function_filter = normalize_function_filter(request.GET.get('filtro'))
    context = {
        'active_section': f'reporte_certificado_{tipo}',
        'report_type': tipo,
        'report_info': report_info,
        'report_types': REPORT_TYPES,
        'cedula': cedula,
        'searched': bool(cedula),
        'function_filters': FUNCTION_FILTERS,
        'function_filter': function_filter,
        'function_filter_label': FUNCTION_FILTER_LABELS[function_filter],
    }
    if not cedula:
        return render(request, 'certificados/reporte_base.html', context)
    if not cedula.isalnum() or len(cedula) < 5 or len(cedula) > 13:
        context['error'] = 'Ingrese un número de identificación válido.'
        return render(request, 'certificados/reporte_base.html', context)

    teacher = DocenteFcacc.objects.select_related(
        'id_dedicacion', 'id_modalidad', 'id_tipo_docente'
    ).filter(cedula_docente=cedula).first()
    permitted = allowed_career_ids(request.user)
    if teacher and permitted is not None and not teacher.docenteasignacioncarreraperiodo_set.filter(
        id_carrera_id__in=permitted
    ).exists():
        teacher = None
    if not teacher:
        context['error'] = 'No se encontró un docente con esa identificación.'
        return render(request, 'certificados/reporte_base.html', context)

    data = build_certificate_snapshot(
        report_info['certificate_type'], teacher, function_filter
    )
    context.update({
        'docente': teacher,
        'datos': data,
        'rows': data['filas'],
        'warnings': data['advertencias'],
    })
    if not data['filas']:
        context['error'] = (
            f'El docente no tiene datos registrados para '
            f'“{FUNCTION_FILTER_LABELS[function_filter]}”.'
            if report_info['certificate_type'] == 'FUNCIONES'
            else (
                f'El docente no tiene datos registrados para el reporte '
                f'“{report_info["title"]}”.'
            )
        )
    return render(request, 'certificados/reporte_base.html', context)


@module_permission_required('certificados', 'change')
def generar_certificado(request):
    form = GenerarCertificadoForm(
        request.POST or None, allowed_career_ids=allowed_career_ids(request.user)
    )
    if request.method == 'POST' and form.is_valid():
        snapshot = build_certificate_snapshot(
            form.cleaned_data['tipo'],
            form.cleaned_data['docente'],
            form.cleaned_data['filtro_funciones'],
        )
        if not snapshot['filas']:
            error_field = (
                'filtro_funciones'
                if form.cleaned_data['tipo'] == 'FUNCIONES'
                else 'docente'
            )
            form.add_error(
                error_field,
                'El docente no tiene información registrada para la selección indicada.',
            )
        else:
            signer = form.cleaned_data['firmante']
            with transaction.atomic():
                certificate = CertificadoEmitido.objects.create(
                    tipo=form.cleaned_data['tipo'],
                    docente=form.cleaned_data['docente'],
                    firmante=signer,
                    firmante_nombre=signer.nombres_completos,
                    firmante_cargo=signer.cargo,
                    fecha_emision=form.cleaned_data['fecha_emision'],
                    ciudad=form.cleaned_data['ciudad'],
                    datos_certificados=snapshot,
                    emitido_por=request.user,
                )
            messages.success(request, f'Certificado {certificate.codigo} generado correctamente.')
            return redirect('certificados:previsualizar', pk=certificate.pk)
    return render(request, 'certificados/generar.html', {
        'form': form, 'active_section': 'certificado_generar',
    })


@module_permission_required('certificados', 'view')
def emisiones(request):
    query = (request.GET.get('q') or '').strip()
    items = CertificadoEmitido.objects.select_related('docente', 'firmante', 'emitido_por')
    permitted = allowed_career_ids(request.user)
    if permitted is not None:
        items = items.filter(
            docente__docenteasignacioncarreraperiodo__id_carrera_id__in=permitted
        ).distinct()
    if query:
        from django.db.models import Q
        items = items.filter(
            Q(codigo__icontains=query) |
            Q(docente__cedula_docente__icontains=query) |
            Q(docente__nombres_completos__icontains=query)
        )
    page_obj = Paginator(items.order_by('-creado_el', '-pk'), 25).get_page(
        request.GET.get('page')
    )
    return render(request, 'certificados/emisiones.html', {
        'items': page_obj, 'page_obj': page_obj, 'search_value': query,
        'active_section': 'certificado_emisiones',
    })


@module_permission_required('certificados', 'view')
def previsualizar(request, pk):
    certificate = get_object_or_404(
        CertificadoEmitido.objects.select_related('firmante', 'docente'), pk=pk
    )
    permitted = allowed_career_ids(request.user)
    if permitted is not None and not certificate.docente.docenteasignacioncarreraperiodo_set.filter(
        id_carrera_id__in=permitted
    ).exists():
        raise PermissionDenied
    return render(request, 'certificados/documento.html', {
        'certificado': certificate,
        'datos': certificate.datos_certificados,
        'active_section': 'certificado_emisiones',
    })


@role_required(ADMIN, AUTORIDAD)
@module_permission_required('certificados', 'change')
def firmantes(request, pk=None):
    instance = get_object_or_404(FirmanteCertificado, pk=pk) if pk else None
    form = FirmanteCertificadoForm(request.POST or None, request.FILES or None, instance=instance)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Firmante guardado correctamente.')
        return redirect('certificados:firmantes')
    page_obj = Paginator(
        FirmanteCertificado.objects.order_by('-activo', 'nombres_completos'), 15
    ).get_page(request.GET.get('page'))
    return render(request, 'certificados/firmantes.html', {
        'form': form,
        'editing': instance,
        'items': page_obj,
        'page_obj': page_obj,
        'active_section': 'certificado_firmantes',
    })
