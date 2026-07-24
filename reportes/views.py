from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from docentes.models import DocenteFcacc, DocenteTituloAcademico, DocenteCampoAfinidad
from planificacion.models import (
    PlanificacionActividadDocente, PlanificacionAsignacionDocente,
    PlanificacionMatrizF4,
)
from curriculo.models import CurriculoAsignatura
from catalogos.models import (
    CatalogoCarrera, CatalogoPeriodoAcademico, LimiteHorario,
)
from accounts.decorators import module_permission_required, allowed_career_ids


THIN_BORDER = Border(
    left=Side(style='thin'), right=Side(style='thin'),
    top=Side(style='thin'), bottom=Side(style='thin'),
)
HEADER_FILL = PatternFill(start_color='2563EB', end_color='2563EB', fill_type='solid')
HEADER_FONT = Font(color='FFFFFF', bold=True, size=11)


def _style_header(ws, row, cols):
    for col in range(1, cols + 1):
        cell = ws.cell(row=row, column=col)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal='center', vertical='center')
        cell.border = THIN_BORDER


def _style_data(ws, row, cols):
    for col in range(1, cols + 1):
        cell = ws.cell(row=row, column=col)
        cell.border = THIN_BORDER
        cell.alignment = Alignment(vertical='center')


def _finish_sheet(ws, widths=None):
    ws.freeze_panes = 'A2'
    ws.auto_filter.ref = ws.dimensions
    widths = widths or {}
    for column in range(1, ws.max_column + 1):
        letter = get_column_letter(column)
        ws.column_dimensions[letter].width = widths.get(column, 20)


def _export_filters(request):
    periodo = (request.GET.get('periodo') or '').strip()
    carrera = (request.GET.get('carrera') or '').strip()
    result = (
        periodo if periodo.isdigit() else None,
        carrera if carrera.isdigit() else None,
    )
    user = getattr(request, 'user', None)
    permitted = allowed_career_ids(user) if user is not None else None
    if permitted is not None and result[1] and int(result[1]) not in permitted:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    return result


def _excel_response(workbook, prefix):
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    filename = f'{prefix}_{timezone.localdate():%Y%m%d}.xlsx'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    workbook.save(response)
    return response


def _filtered_assignments(periodo_id=None, carrera_id=None, user=None):
    qs = PlanificacionAsignacionDocente.objects.select_related(
        'id_docente', 'id_asignatura', 'id_carrera', 'id_periodo', 'id_campo'
    )
    if periodo_id:
        qs = qs.filter(id_periodo_id=periodo_id)
    if carrera_id:
        qs = qs.filter(id_carrera_id=carrera_id)
    permitted = allowed_career_ids(user) if user is not None else None
    if permitted is not None:
        qs = qs.filter(id_carrera_id__in=permitted)
    return qs


def _teacher_ids_for_scope(periodo_id=None, carrera_id=None, user=None):
    """Docentes vinculados a la carrera; None significa sin filtro de carrera."""
    permitted = allowed_career_ids(user) if user is not None else None
    if not carrera_id and permitted is None:
        return None
    assignment_ids = PlanificacionAsignacionDocente.objects.all()
    f4_ids = PlanificacionMatrizF4.objects.all()
    if carrera_id:
        assignment_ids = assignment_ids.filter(id_carrera_id=carrera_id)
        f4_ids = f4_ids.filter(id_carrera_id=carrera_id)
    if permitted is not None:
        assignment_ids = assignment_ids.filter(id_carrera_id__in=permitted)
        f4_ids = f4_ids.filter(id_carrera_id__in=permitted)
    if periodo_id:
        assignment_ids = assignment_ids.filter(id_periodo_id=periodo_id)
        f4_ids = f4_ids.filter(id_periodo_id=periodo_id)
    return set(assignment_ids.values_list('id_docente_id', flat=True)) | set(
        f4_ids.values_list('id_docente_id', flat=True)
    )


@login_required
@module_permission_required('reportes', 'view')
def centro_reportes(request):
    """Interfaz única para consultar y descargar reportes de planificación."""
    periodo_id, carrera_id = _export_filters(request)
    periodos = CatalogoPeriodoAcademico.objects.order_by(
        '-periodo_activo', '-fecha_inicio_periodo', '-id_periodo'
    )
    if not periodo_id:
        active_period = periodos.filter(periodo_activo=True).first()
        if active_period:
            periodo_id = str(active_period.id_periodo)

    assignments = _filtered_assignments(periodo_id, carrera_id, request.user)
    teacher_ids = _teacher_ids_for_scope(periodo_id, carrera_id, request.user)
    activities = PlanificacionActividadDocente.objects.all()
    f4_rows = PlanificacionMatrizF4.objects.all()
    if periodo_id:
        activities = activities.filter(id_periodo_id=periodo_id)
        f4_rows = f4_rows.filter(id_periodo_id=periodo_id)
    if carrera_id:
        f4_rows = f4_rows.filter(id_carrera_id=carrera_id)
        activities = activities.filter(id_docente_id__in=teacher_ids)

    from planificacion.views import _build_docente_workload_map
    workload = _build_docente_workload_map(periodo_id=periodo_id)
    if teacher_ids is not None:
        workload = {key: value for key, value in workload.items() if key in teacher_ids}
    teachers_with_load = sum(1 for item in workload.values() if item.get('total_horas', 0) > 0)
    query = f'periodo={periodo_id or ""}&carrera={carrera_id or ""}'
    context = {
        'active_section': 'centro_reportes',
        'periodos': periodos,
        'carreras': CatalogoCarrera.objects.filter(
            carrera_activa=True,
            **({'id_carrera__in': allowed_career_ids(request.user)} if allowed_career_ids(request.user) is not None else {})
        ).order_by('nombre_carrera'),
        'periodo_id': int(periodo_id) if periodo_id else None,
        'carrera_id': int(carrera_id) if carrera_id else None,
        'export_query': query,
        'assignment_count': assignments.count(),
        'activity_count': activities.count(),
        'f4_count': f4_rows.count(),
        'teacher_count': teachers_with_load,
        'total_hours': sum(item.get('total_horas', 0) for item in workload.values()),
    }
    return render(request, 'reportes/centro_reportes.html', context)


# ——— API: Reporte Carga Docente ————————————————————————————

@login_required
@module_permission_required('reportes', 'view')
def reporte_carga_docente(request):
    periodo_id = request.GET.get('periodo')
    carrera_id = request.GET.get('carrera')
    qs = PlanificacionAsignacionDocente.objects.select_related(
        'id_docente', 'id_asignatura', 'id_carrera', 'id_periodo', 'id_campo'
    )
    if periodo_id:
        qs = qs.filter(id_periodo_id=periodo_id)
    if carrera_id:
        qs = qs.filter(id_carrera_id=carrera_id)

    data = []
    for a in qs[:500]:
        data.append({
            'docente': str(a.id_docente),
            'cedula': a.id_docente.cedula_docente if a.id_docente_id else '',
            'asignatura': str(a.id_asignatura) if a.id_asignatura_id else '',
            'carrera': str(a.id_carrera.nombre_carrera) if a.id_carrera_id else '',
            'periodo': str(a.id_periodo.nombre_periodo) if a.id_periodo_id else '',
            'horas': a.horas_clase,
            'semanas': a.semanas_planificadas,
            'horas_periodo': a.horas_clase_periodo,
            'campo': str(a.id_campo.nombre_campo_conocimiento) if a.id_campo_id else '',
        })
    return JsonResponse({'data': data})


# ——— API: Reporte Resumen Horas (Matriz F4) ————————————————

@login_required
@module_permission_required('reportes', 'view')
def reporte_resumen_horas(request):
    periodo_id = request.GET.get('periodo')
    carrera_id = request.GET.get('carrera')
    qs = PlanificacionMatrizF4.objects.select_related('id_docente', 'id_carrera', 'id_periodo')
    if periodo_id:
        qs = qs.filter(id_periodo_id=periodo_id)
    if carrera_id:
        qs = qs.filter(id_carrera_id=carrera_id)

    data = []
    for m in qs[:500]:
        data.append({
            'docente': str(m.id_docente),
            'cedula': m.id_docente.cedula_docente if m.id_docente_id else '',
            'carrera': str(m.id_carrera.nombre_carrera) if m.id_carrera_id else '',
            'periodo': str(m.id_periodo.nombre_periodo) if m.id_periodo_id else '',
            'horas_actividad': float(m.horas_actividad or 0),
            'total_horas': float(m.horas_actividad or 0),
        })
    return JsonResponse({'data': data})


# ——— API: Reporte Malla Curricular —————————————————————————

@login_required
@module_permission_required('reportes', 'view')
def reporte_malla_curricular(request):
    carrera_id = request.GET.get('carrera')
    qs = CurriculoAsignatura.objects.select_related('id_carrera').all()
    if carrera_id:
        qs = qs.filter(id_carrera_id=carrera_id)

    data = []
    for a in qs.order_by('id_carrera_id', 'nivel_semestre', 'nombre_asignatura')[:500]:
        data.append({
            'carrera': str(a.id_carrera.nombre_carrera) if a.id_carrera_id else '',
            'asignatura': a.nombre_asignatura,
            'codigo': a.codigo_asignatura or '',
            'nivel': a.nivel_semestre or 0,
            'horas': a.horas_semanales_asignatura or 0,
        })
    return JsonResponse({'data': data})


# ——— API: Reporte Docentes por Formación —————————————————————

@login_required
@module_permission_required('reportes', 'view')
def reporte_docentes_formacion(request):
    qs = DocenteTituloAcademico.objects.select_related('id_docente', 'id_posgrado').all()[:500]
    data = []
    for t in qs:
        data.append({
            'docente': str(t.id_docente),
            'cedula': t.id_docente.cedula_docente if t.id_docente_id else '',
            'titulo': t.nombre_titulo or '',
            'posgrado': str(t.id_posgrado.nombre_titulo_posgrado) if t.id_posgrado_id else '',
            'fecha_obtencion': str(t.fecha_obtencion_titulo) if t.fecha_obtencion_titulo else '',
            'registro_senescyt': t.numero_registro_senescyt or '',
        })
    return JsonResponse({'data': data})


# ——— API: Reporte Docentes por Campo Conocimiento ——————————

@login_required
@module_permission_required('reportes', 'view')
def reporte_docentes_campos(request):
    qs = DocenteCampoAfinidad.objects.select_related('id_docente', 'id_campo').all()[:500]
    data = []
    for dc in qs:
        data.append({
            'docente': str(dc.id_docente),
            'cedula': dc.id_docente.cedula_docente if dc.id_docente_id else '',
            'campo': str(dc.id_campo.nombre_campo_conocimiento) if dc.id_campo_id else '',
        })
    return JsonResponse({'data': data})


# ═══════════════════════════════════════════════════════════════
# EXPORTACIONES EXCEL
# ═══════════════════════════════════════════════════════════════

@login_required
@module_permission_required('reportes', 'view')
def export_carga_docente_excel(request):
    periodo_id, carrera_id = _export_filters(request)
    wb = Workbook()
    ws = wb.active
    ws.title = 'Carga Docente'

    headers = ['Docente', 'Cédula', 'Asignatura', 'Carrera', 'Período', 'Horas semanales', 'Semanas', 'Horas período', 'Campo']
    ws.append(headers)
    _style_header(ws, 1, len(headers))

    qs = _filtered_assignments(periodo_id, carrera_id, request.user).order_by(
        'id_docente__nombres_completos', 'id_asignatura__nombre_asignatura'
    )
    for i, a in enumerate(qs, start=2):
        ws.append([
            str(a.id_docente),
            a.id_docente.cedula_docente if a.id_docente_id else '',
            str(a.id_asignatura) if a.id_asignatura_id else '',
            str(a.id_carrera.nombre_carrera) if a.id_carrera_id else '',
            str(a.id_periodo.nombre_periodo) if a.id_periodo_id else '',
            a.horas_clase,
            a.semanas_planificadas,
            a.horas_clase_periodo,
            str(a.id_campo.nombre_campo_conocimiento) if a.id_campo_id else '',
        ])
        _style_data(ws, i, len(headers))

    for col_idx in range(1, len(headers) + 1):
        ws.column_dimensions[get_column_letter(col_idx)].width = 22

    _finish_sheet(ws, {1: 36, 2: 14, 3: 36, 4: 30, 5: 22, 9: 30})
    return _excel_response(wb, 'asignaciones_docentes')


@login_required
@module_permission_required('reportes', 'view')
def export_malla_excel(request):
    _, carrera_id = _export_filters(request)
    wb = Workbook()
    ws = wb.active
    ws.title = 'Malla Curricular'

    headers = ['Carrera', 'Asignatura', 'Código', 'Nivel', 'Horas Semanales']
    ws.append(headers)
    _style_header(ws, 1, len(headers))

    qs = CurriculoAsignatura.objects.select_related('id_carrera').order_by(
        'id_carrera_id', 'nivel_semestre', 'nombre_asignatura'
    )
    if carrera_id:
        qs = qs.filter(id_carrera_id=carrera_id)
    permitted = allowed_career_ids(request.user)
    if permitted is not None:
        qs = qs.filter(id_carrera_id__in=permitted)
    for i, a in enumerate(qs, start=2):
        ws.append([
            str(a.id_carrera.nombre_carrera) if a.id_carrera_id else '',
            a.nombre_asignatura,
            a.codigo_asignatura or '',
            a.nivel_semestre or 0,
            a.horas_semanales_asignatura or 0,
        ])
        _style_data(ws, i, len(headers))

    for col_idx in range(1, len(headers) + 1):
        ws.column_dimensions[get_column_letter(col_idx)].width = 24

    _finish_sheet(ws, {1: 32, 2: 38, 3: 18, 4: 12, 5: 18})
    return _excel_response(wb, 'malla_curricular')


@login_required
@module_permission_required('reportes', 'view')
def export_resumen_horas_excel(request):
    # Compatibilidad con el botón antiguo: el resumen correcto es ahora la
    # planificación general, que incluye clases y todas las actividades.
    return export_planificacion_general_excel(request)


@login_required
@module_permission_required('reportes', 'view')
def export_planificacion_general_excel(request):
    """Exporta una fila consolidada por docente con su carga total."""
    from planificacion.views import _build_docente_workload_map

    periodo_id, carrera_id = _export_filters(request)
    workload_map = _build_docente_workload_map(periodo_id=periodo_id)
    limites = {
        limite.id_modalidad_id: limite
        for limite in LimiteHorario.objects.filter(activo=True)
    }

    wb = Workbook()
    ws = wb.active
    ws.title = 'Resumen general'
    headers = [
        'Docente', 'Cédula', 'Modalidad', 'Dedicación', 'Horas afinidad',
        'Horas no afinidad', 'Horas unidad básica', 'Total horas clase',
        'Horas complementarias', 'Investigación', 'Gestión', 'Vinculación',
        'Otras actividades', 'Total actividades', 'Total horas', 'Límite',
        'Disponible', 'Cumplimiento %', 'Estado',
    ]
    ws.append(headers)
    _style_header(ws, 1, len(headers))

    docentes = DocenteFcacc.objects.filter(docente_activo=True).select_related(
        'id_modalidad', 'id_dedicacion'
    ).order_by('nombres_completos')
    teacher_ids = _teacher_ids_for_scope(periodo_id, carrera_id, request.user)
    if teacher_ids is not None:
        docentes = docentes.filter(id_docente__in=teacher_ids)
    for row_number, docente in enumerate(docentes, start=2):
        workload = workload_map.get(docente.id_docente, {})
        afinidad = workload.get('horas_afinidad', 0) or 0
        no_afinidad = workload.get('horas_no_afinidad', 0) or 0
        unidad_basica = workload.get('horas_unidad_basica', 0) or 0
        clase = workload.get('total_horas_clase', 0) or 0
        complementarias = workload.get('horas_complementarias', 0) or 0
        investigacion = workload.get('horas_investigacion', 0) or 0
        gestion = workload.get('horas_gestion', 0) or 0
        vinculacion = workload.get('horas_vinculacion', 0) or 0
        actividades = workload.get('horas_actividad', 0) or 0
        total_actividades = workload.get('horas_actividades_total', 0) or 0
        total = workload.get('total_horas', clase + total_actividades) or 0
        limite = limites.get(docente.id_modalidad_id)
        maximo = (
            (limite.horas_maximas or 0) +
            (limite.horas_complementarias_maximas or 0)
        ) if limite else 0
        disponible = max(0, maximo - total)
        porcentaje = round(total * 100 / maximo, 1) if maximo else 0
        if porcentaje > 100:
            estado = 'Sobrecargado'
        elif porcentaje >= 80:
            estado = 'Alerta'
        elif total:
            estado = 'Balanceado'
        else:
            estado = 'Sin carga'
        ws.append([
            docente.nombres_completos,
            docente.cedula_docente,
            str(docente.id_modalidad) if docente.id_modalidad_id else '',
            str(docente.id_dedicacion) if docente.id_dedicacion_id else '',
            afinidad, no_afinidad, unidad_basica, clase, complementarias,
            investigacion, gestion, vinculacion, actividades, total_actividades,
            total, maximo, disponible, porcentaje, estado,
        ])
        _style_data(ws, row_number, len(headers))
        ws.cell(row_number, 5).fill = PatternFill('solid', fgColor='DCFCE7')
        ws.cell(row_number, 6).fill = PatternFill('solid', fgColor='FEE2E2')
        ws.cell(row_number, 7).fill = PatternFill('solid', fgColor='DBEAFE')
        ws.cell(row_number, 19).fill = PatternFill(
            'solid', fgColor='FECACA' if estado == 'Sobrecargado' else
            'FEF3C7' if estado == 'Alerta' else 'DCFCE7' if estado == 'Balanceado' else 'E5E7EB'
        )

    _finish_sheet(ws, {1: 36, 2: 14, 3: 22, 4: 18, 19: 16})
    return _excel_response(wb, 'planificacion_general')


@login_required
@module_permission_required('reportes', 'view')
def export_planificacion_detallada_excel(request):
    """Exporta asignaturas, actividades y Matriz F4 en hojas separadas."""
    from planificacion.views import (
        _activity_workload_key, _assignment_hour_category, _excel_normalize_text,
        _knowledge_field_maps, _registered_activity_keys,
    )

    periodo_id, carrera_id = _export_filters(request)
    teacher_ids = _teacher_ids_for_scope(periodo_id, carrera_id, request.user)
    wb = Workbook()

    assignments = PlanificacionAsignacionDocente.objects.select_related(
        'id_docente', 'id_asignatura', 'id_carrera', 'id_periodo', 'id_campo'
    ).order_by('id_docente__nombres_completos', 'id_asignatura__nombre_asignatura')
    if periodo_id:
        assignments = assignments.filter(id_periodo_id=periodo_id)
    if carrera_id:
        assignments = assignments.filter(id_carrera_id=carrera_id)
    permitted = allowed_career_ids(request.user)
    if permitted is not None:
        assignments = assignments.filter(id_carrera_id__in=permitted)
    ws = wb.active
    ws.title = 'Asignaturas'
    headers = [
        'Docente', 'Cédula', 'Carrera', 'Período', 'Código', 'Asignatura',
        'Nivel', 'Paralelo', 'Campo', 'Tipo de horas', 'Horas semanales',
        'Semanas', 'Horas período',
    ]
    ws.append(headers)
    _style_header(ws, 1, len(headers))
    subject_fields, teacher_fields = _knowledge_field_maps()
    category_labels = {
        'afinidad': 'Afinidad',
        'no_afinidad': 'No afinidad',
        'unidad_basica': 'Unidad básica',
    }
    for row_number, item in enumerate(assignments.iterator(), start=2):
        category = _assignment_hour_category(
            item.id_docente_id, item.id_asignatura_id,
            item.id_campo.nombre_campo_conocimiento,
            subject_fields, teacher_fields,
        )
        ws.append([
            item.id_docente.nombres_completos, item.id_docente.cedula_docente,
            item.id_carrera.nombre_carrera, item.id_periodo.nombre_periodo,
            item.id_asignatura.codigo_asignatura, item.id_asignatura.nombre_asignatura,
            item.nivel_semestre_asignado, item.paralelo_asignado,
            item.id_campo.nombre_campo_conocimiento, category_labels[category],
            item.horas_clase, item.semanas_planificadas, item.horas_clase_periodo,
        ])
        _style_data(ws, row_number, len(headers))
        ws.cell(row_number, 10).fill = PatternFill(
            'solid', fgColor={
                'afinidad': 'DCFCE7',
                'no_afinidad': 'FEE2E2',
                'unidad_basica': 'DBEAFE',
            }[category]
        )
    _finish_sheet(ws, {1: 36, 3: 30, 6: 36, 9: 30, 10: 18})

    activities = PlanificacionActividadDocente.objects.select_related(
        'id_docente', 'id_periodo', 'id_actividad'
    ).order_by('id_docente__nombres_completos', 'id_actividad__nombre_actividad')
    if periodo_id:
        activities = activities.filter(id_periodo_id=periodo_id)
    if teacher_ids is not None:
        activities = activities.filter(id_docente_id__in=teacher_ids)
    ws = wb.create_sheet('Actividades')
    headers = ['Docente', 'Cédula', 'Período', 'Código', 'Actividad', 'Tipo', 'Horas', 'Observaciones']
    ws.append(headers)
    _style_header(ws, 1, len(headers))
    for row_number, item in enumerate(activities.iterator(), start=2):
        ws.append([
            item.id_docente.nombres_completos, item.id_docente.cedula_docente,
            item.id_periodo.nombre_periodo, item.id_actividad.codigo_actividad,
            item.id_actividad.nombre_actividad, item.id_actividad.get_tipo_actividad_display(),
            item.horas_asignadas, item.observaciones or '',
        ])
        _style_data(ws, row_number, len(headers))
    _finish_sheet(ws, {1: 36, 3: 24, 5: 38, 8: 45})

    f4_rows = PlanificacionMatrizF4.objects.select_related(
        'id_docente', 'id_carrera', 'id_periodo', 'id_grado_afinidad'
    ).order_by('id_docente__nombres_completos', 'tipo_actividad')
    if periodo_id:
        f4_rows = f4_rows.filter(id_periodo_id=periodo_id)
    if carrera_id:
        f4_rows = f4_rows.filter(id_carrera_id=carrera_id)
    if permitted is not None:
        f4_rows = f4_rows.filter(id_carrera_id__in=permitted)
    ws = wb.create_sheet('F4 adicional')
    headers = [
        'Docente', 'Cédula', 'Carrera', 'Período', 'Tipo', 'Detalle',
        'Nivel', 'Horas', 'Paralelos', 'Total', 'Observaciones',
    ]
    ws.append(headers)
    _style_header(ws, 1, len(headers))
    activity_keys = _registered_activity_keys(periodo_id)
    seen_f4 = set()
    row_number = 2
    for item in f4_rows.iterator():
        total = (item.horas_actividad or 0) * (item.numero_paralelos_actividad or 1)
        duplicate_key = _activity_workload_key(
            item.id_docente_id, item.id_periodo_id,
            item.nombre_asignatura_actividad, total,
        )
        if duplicate_key in activity_keys:
            continue
        f4_key = (
            item.id_docente_id, item.id_periodo_id, item.tipo_actividad,
            _excel_normalize_text(item.nombre_asignatura_actividad),
            item.horas_actividad, item.numero_paralelos_actividad,
        )
        if not carrera_id and f4_key in seen_f4:
            continue
        seen_f4.add(f4_key)
        ws.append([
            item.id_docente.nombres_completos, item.id_docente.cedula_docente,
            item.id_carrera.nombre_carrera, item.id_periodo.nombre_periodo,
            item.tipo_actividad, item.nombre_asignatura_actividad or '',
            item.nivel_semestre_actividad or '', item.horas_actividad,
            item.numero_paralelos_actividad, total, item.observaciones or '',
        ])
        _style_data(ws, row_number, len(headers))
        row_number += 1
    _finish_sheet(ws, {1: 36, 3: 30, 5: 24, 6: 38, 11: 45})

    return _excel_response(wb, 'planificacion_detallada')


@login_required
@module_permission_required('planificacion')
def export_matriz_f4_mkt_excel(request):
    """Exporta Matriz F4 en formato MKT (16 columnas) para el periodo y carrera actual."""
    periodo_id = request.GET.get('periodo')
    carrera_id = request.GET.get('carrera')
    wb = Workbook()
    ws = wb.active
    ws.title = 'MATRIZ F4 V1'

    headers = [
        'N°', 'Cédula', 'Apellidos y Nombres', 'Sexo', 'Unidad Orgánica',
        'Titular', 'Categoría', 'Título de tercer nivel', 'Título de cuarto nivel',
        'Carrera o Tipo de Actividad', 'Asignatura o Actividad',
        'Grado de afinidad', 'Horas', 'Paralelos', 'Total Horas', 'Carga Horaria',
    ]
    ws.append(headers)
    _style_header(ws, 1, len(headers))

    qs = PlanificacionMatrizF4.objects.select_related(
        'id_docente', 'id_carrera', 'id_periodo', 'id_grado_afinidad',
    ).order_by('id_docente__nombres_completos', 'tipo_actividad')

    if periodo_id:
        qs = qs.filter(id_periodo__codigo_periodo=periodo_id)
    if carrera_id:
        qs = qs.filter(id_carrera__codigo_carrera=carrera_id)

    permitted = allowed_career_ids(request.user)
    if permitted is not None:
        qs = qs.filter(id_carrera__codigo_carrera__in=permitted)

    # Pre-fetch titulos por docente
    from django.db.models import Q
    titulos_qs = DocenteTituloAcademico.objects.filter(
        id_docente__in=qs.values_list('id_docente_id', flat=True).distinct()
    ).order_by('id_docente_id', '-nivel_titulo')
    titulos_por_docente = {}
    for t in titulos_qs:
        titulos_por_docente.setdefault(t.id_docente_id, []).append(t)

    row_number = 2
    docente_actual = None
    secuencia = 0
    from django.db.models import Sum, F, Q
    carga_filter = Q()
    if periodo_id:
        carga_filter &= Q(id_periodo__codigo_periodo=periodo_id)
    carga_por_docente = dict(
        PlanificacionMatrizF4.objects.filter(carga_filter)
        .values('id_docente_id')
        .annotate(total=Sum(F('horas_actividad') * F('numero_paralelos_actividad')))
        .values_list('id_docente_id', 'total')
    )

    for item in qs.iterator():
        docente = item.id_docente
        total_linea = (item.horas_actividad or 0) * (item.numero_paralelos_actividad or 1)

        if docente.id_docente != docente_actual:
            secuencia += 1
            docente_actual = docente.id_docente

            titulos = titulos_por_docente.get(docente.id_docente, [])
            tercer_nivel = ''
            cuarto_nivel = ''
            for t in titulos:
                nt = t.nivel_titulo or 0
                if nt >= 4:
                    cuarto_nivel = (cuarto_nivel + '; ' + t.nombre_titulo) if cuarto_nivel else t.nombre_titulo
                else:
                    tercer_nivel = (tercer_nivel + '; ' + t.nombre_titulo) if tercer_nivel else t.nombre_titulo
            if not tercer_nivel and titulos:
                tercer_nivel = titulos[0].nombre_titulo

            modalidad_text = str(docente.id_modalidad or '')
            dedicacion_text = str(docente.id_dedicacion or '')
            categoria = f'{modalidad_text} {dedicacion_text}'.strip()

            carga = carga_por_docente.get(docente.id_docente, '')

            ws.append([
                secuencia,
                docente.cedula_docente or '',
                docente.nombres_completos or '',
                '',
                docente.unidad_organica or '',
                '',
                categoria,
                tercer_nivel,
                cuarto_nivel,
                item.id_carrera.nombre_carrera if item.id_carrera else '',
                item.nombre_asignatura_actividad or '',
                str(item.id_grado_afinidad or ''),
                item.horas_actividad or 0,
                item.numero_paralelos_actividad or 1,
                total_linea,
                carga if carga else '',
            ])
        else:
            ws.append([
                '', '', '', '', '', '', '', '', '',
                item.id_carrera.nombre_carrera if item.id_carrera else '',
                item.nombre_asignatura_actividad or '',
                str(item.id_grado_afinidad or ''),
                item.horas_actividad or 0,
                item.numero_paralelos_actividad or 1,
                total_linea,
                '',
            ])

        _style_data(ws, row_number, len(headers))
        row_number += 1

    _finish_sheet(ws, {1: 5, 2: 14, 3: 36, 5: 30, 7: 30, 8: 30, 9: 30, 10: 30, 11: 40, 12: 30})
    return _excel_response(wb, 'matriz_f4_mkt')


@login_required
@module_permission_required('planificacion')
def descargar_planificacion_original(request):
    """
    Clona la plantilla original EXACTA (formato, merged cells, formulas,
    todo) y solo sobrescribe los valores de las celdas F4 con datos
    actualizados de la BD — sin tocar merges, sin alterar estructura.
    """
    from pathlib import Path
    from openpyxl import load_workbook, Workbook
    from openpyxl.cell.cell import MergedCell
    from copy import copy
    from docentes.models import DocenteFcacc, DocenteTituloAcademico
    from planificacion.models import PlanificacionMatrizF4
    from django.db.models import Prefetch

    base = Path(__file__).resolve().parents[1] / '_excel_input'
    matches = sorted(base.glob('*MKT*.xlsx'))
    if not matches:
        from django.http import Http404
        raise Http404('Archivo de planificacion original no encontrado.')

    wb_src = load_workbook(matches[0])
    ws_src = wb_src['MATRIZ F4 V1']

    # ── 1) Clone original sheet cell-by-cell ──────────────────────────────
    wb_dst = Workbook()
    ws_dst = wb_dst.active
    ws_dst.title = 'MATRIZ F4 V1'

    for row in ws_src.iter_rows():
        for cell in row:
            nc = ws_dst.cell(row=cell.row, column=cell.column)
            nc.value = cell.value
            if cell.has_style:
                nc.font = copy(cell.font)
                nc.border = copy(cell.border)
                nc.fill = copy(cell.fill)
                nc.number_format = copy(cell.number_format)
                nc.protection = copy(cell.protection)
                nc.alignment = copy(cell.alignment)

    for mr in ws_src.merged_cells.ranges:
        ws_dst.merge_cells(str(mr))

    for c_idx, dim in ws_src.column_dimensions.items():
        if dim.width:
            ws_dst.column_dimensions[c_idx].width = dim.width

    for r_idx, dim in ws_src.row_dimensions.items():
        if dim.height:
            ws_dst.row_dimensions[r_idx].height = dim.height

    # ── 2) Pre-scan template: detect F4 rows and docente-group starts ──
    DATA_START = 8
    MAX_ROW = ws_src.max_row or 268

    template_f4_rows = []
    first_of_group = set()
    prev_cedula = None
    for r in range(DATA_START, MAX_ROW + 1):
        col1 = ws_src.cell(r, 1).value
        col2 = ws_src.cell(r, 2).value
        col10 = ws_src.cell(r, 10).value
        col11 = ws_src.cell(r, 11).value

        is_new = bool(col2 and str(col2).strip())
        if is_new:
            prev_cedula = col2
            first_of_group.add(r)

        has_f4 = bool(col10 and col11 and str(col10).strip() and str(col11).strip())
        if has_f4:
            template_f4_rows.append(r)

    # ── 3) DB records en orden de importacion (mismo orden que el template) ──
    records = list(
        PlanificacionMatrizF4.objects
        .select_related('id_docente', 'id_carrera', 'id_grado_afinidad')
        .order_by('id_registro_f4')
    )

    docente_ids = list({r.id_docente_id for r in records})
    titulos_map = {}
    if docente_ids:
        docs = DocenteFcacc.objects.filter(id_docente__in=docente_ids).prefetch_related(
            Prefetch('docentetituloacademico_set', queryset=DocenteTituloAcademico.objects.all())
        )
        for d in docs:
            tercer = [t.nombre_titulo for t in d.docentetituloacademico_set.all() if t.nivel_titulo == 3]
            cuarto = [t.nombre_titulo for t in d.docentetituloacademico_set.all() if t.nivel_titulo == 4]
            titulos_map[d.id_docente] = {
                'tercer': tercer[0] if tercer else '',
                'cuarto': cuarto[0] if cuarto else '',
            }

    # ── 4) Matchear DB records a template rows y sobrescribir solo valores ──
    def _safe_write(row, col, value, fmt=None):
        """Sobrescribe solo si la celda no es MergedCell."""
        cell = ws_dst.cell(row, col)
        if isinstance(cell, MergedCell):
            return
        cell.value = value
        if fmt:
            cell.number_format = fmt

    ded_cache = {}
    def _get_ded(docente):
        did = docente.id_docente
        if did not in ded_cache:
            ded_cache[did] = docente.id_dedicacion
        return ded_cache[did]

    seq = 0
    prev_did = None
    for db_rec, template_row in zip(records, template_f4_rows):
        doc = db_rec.id_docente
        ded = _get_ded(doc)
        seq += 1
        is_first = template_row in first_of_group

        _safe_write(template_row, 10, db_rec.id_carrera.nombre_carrera if db_rec.id_carrera else db_rec.tipo_actividad)
        _safe_write(template_row, 11, db_rec.nombre_asignatura_actividad or '')
        if db_rec.id_grado_afinidad:
            _safe_write(template_row, 12, db_rec.id_grado_afinidad.nombre_grado_afinidad)
        _safe_write(template_row, 13, db_rec.horas_actividad)
        _safe_write(template_row, 14, db_rec.numero_paralelos_actividad)

        if is_first:
            _safe_write(template_row, 1, seq)
            _safe_write(template_row, 2, doc.cedula_docente, '@')
            _safe_write(template_row, 3, doc.nombres_completos)
            _safe_write(template_row, 5, doc.unidad_organica or '')
            _safe_write(template_row, 7, ded.codigo_dedicacion if ded else '')

            if doc.id_docente in titulos_map:
                _safe_write(template_row, 8, titulos_map[doc.id_docente]['tercer'])
                _safe_write(template_row, 9, titulos_map[doc.id_docente]['cuarto'])
        elif doc.id_docente != prev_did:
            pass
        prev_did = doc.id_docente

    # ── 5) Limpiar filas F4 del template que NO tienen matching en BD ──
    matched = set(template_f4_rows[:len(records)])
    for r in template_f4_rows[len(records):]:
        for col in [1, 2, 3, 5, 7, 8, 9, 10, 11, 12, 13, 14]:
            cell = ws_dst.cell(r, col)
            if isinstance(cell, MergedCell):
                continue
            if cell.data_type != 'f':
                cell.value = None

    # ── 6) Responder ────────────────────────────────────────────────────
    from io import BytesIO
    output = BytesIO()
    wb_dst.save(output)
    output.seek(0)
    content = output.read()

    response = HttpResponse(content, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="MATRIZ_F4_V1.xlsx"'
    response['Content-Length'] = len(content)
    return response
