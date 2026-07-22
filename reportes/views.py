from django.http import HttpResponse, JsonResponse
from django.db.models import Sum, Count, Q
from django.db import ProgrammingError, OperationalError
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from docentes.models import DocenteFcacc, DocenteTituloAcademico, DocenteCampoAfinidad, DocenteAsignacionCarreraPeriodo
from planificacion.models import (
    PlanificacionActividadDocente, PlanificacionAsignacionDocente,
    PlanificacionMatrizF4,
)
from curriculo.models import CurriculoAsignatura
from catalogos.models import (
    CatalogoCarrera, CatalogoPeriodoAcademico, CatalogoCampoConocimiento,
    LimiteHorario,
)


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
    return (
        periodo if periodo.isdigit() else None,
        carrera if carrera.isdigit() else None,
    )


def _excel_response(workbook, prefix):
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    filename = f'{prefix}_{timezone.localdate():%Y%m%d}.xlsx'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    workbook.save(response)
    return response


# ——— API: Reporte Carga Docente ————————————————————————————

@login_required
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
            'campo': str(a.id_campo.nombre_campo_conocimiento) if a.id_campo_id else '',
        })
    return JsonResponse({'data': data})


# ——— API: Reporte Resumen Horas (Matriz F4) ————————————————

@login_required
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
def export_carga_docente_excel(request):
    wb = Workbook()
    ws = wb.active
    ws.title = 'Carga Docente'

    headers = ['Docente', 'Cédula', 'Asignatura', 'Carrera', 'Período', 'Horas', 'Campo']
    ws.append(headers)
    _style_header(ws, 1, len(headers))

    qs = PlanificacionAsignacionDocente.objects.select_related(
        'id_docente', 'id_asignatura', 'id_carrera', 'id_periodo', 'id_campo'
    ).all()[:1000]
    for i, a in enumerate(qs, start=2):
        ws.append([
            str(a.id_docente),
            a.id_docente.cedula_docente if a.id_docente_id else '',
            str(a.id_asignatura) if a.id_asignatura_id else '',
            str(a.id_carrera.nombre_carrera) if a.id_carrera_id else '',
            str(a.id_periodo.nombre_periodo) if a.id_periodo_id else '',
            a.horas_clase,
            str(a.id_campo.nombre_campo_conocimiento) if a.id_campo_id else '',
        ])
        _style_data(ws, i, len(headers))

    for col_idx in range(1, len(headers) + 1):
        ws.column_dimensions[get_column_letter(col_idx)].width = 22

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="carga_docente.xlsx"'
    wb.save(response)
    return response


@login_required
def export_malla_excel(request):
    wb = Workbook()
    ws = wb.active
    ws.title = 'Malla Curricular'

    headers = ['Carrera', 'Asignatura', 'Código', 'Nivel', 'Horas Semanales']
    ws.append(headers)
    _style_header(ws, 1, len(headers))

    qs = CurriculoAsignatura.objects.select_related('id_carrera').all().order_by('id_carrera_id', 'nivel_semestre')[:1000]
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

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="malla_curricular.xlsx"'
    wb.save(response)
    return response


@login_required
def export_resumen_horas_excel(request):
    wb = Workbook()
    ws = wb.active
    ws.title = 'Resumen Horas'

    headers = ['Docente', 'Cédula', 'Carrera', 'Período', 'Hrs Actividad', 'Total']
    ws.append(headers)
    _style_header(ws, 1, len(headers))

    qs = PlanificacionMatrizF4.objects.select_related('id_docente', 'id_carrera', 'id_periodo').all()[:1000]
    for i, m in enumerate(qs, start=2):
        ha = float(m.horas_actividad or 0)
        ws.append([
            str(m.id_docente),
            m.id_docente.cedula_docente if m.id_docente_id else '',
            str(m.id_carrera.nombre_carrera) if m.id_carrera_id else '',
            str(m.id_periodo.nombre_periodo) if m.id_periodo_id else '',
            ha,
            ha,
        ])
        _style_data(ws, i, len(headers))

    for col_idx in range(1, len(headers) + 1):
        ws.column_dimensions[get_column_letter(col_idx)].width = 20

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="resumen_horas.xlsx"'
    wb.save(response)
    return response


@login_required
def export_planificacion_general_excel(request):
    """Exporta una fila consolidada por docente con su carga total."""
    from planificacion.views import _build_docente_workload_map

    periodo_id, carrera_id = _export_filters(request)
    workload_map = _build_docente_workload_map(
        periodo_id=periodo_id,
        carrera_id=carrera_id,
    )
    limites = {
        limite.id_modalidad_id: limite
        for limite in LimiteHorario.objects.filter(activo=True)
    }

    wb = Workbook()
    ws = wb.active
    ws.title = 'Resumen general'
    headers = [
        'Docente', 'Cédula', 'Modalidad', 'Dedicación', 'Horas clase',
        'Horas complementarias', 'Investigación', 'Otras actividades',
        'Total', 'Límite', 'Disponible', 'Cumplimiento %', 'Estado',
    ]
    ws.append(headers)
    _style_header(ws, 1, len(headers))

    docentes = DocenteFcacc.objects.filter(docente_activo=True).select_related(
        'id_modalidad', 'id_dedicacion'
    ).order_by('nombres_completos')
    for row_number, docente in enumerate(docentes, start=2):
        workload = workload_map.get(docente.id_docente, {})
        clase = workload.get('horas_clase', 0) or 0
        complementarias = workload.get('horas_complementarias', 0) or 0
        investigacion = workload.get('horas_investigacion', 0) or 0
        actividades = workload.get('horas_actividad', 0) or 0
        total = workload.get('total_horas', clase + complementarias + investigacion + actividades) or 0
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
            clase, complementarias, investigacion, actividades, total, maximo,
            disponible, porcentaje, estado,
        ])
        _style_data(ws, row_number, len(headers))

    _finish_sheet(ws, {1: 36, 2: 14, 3: 22, 4: 18, 13: 16})
    return _excel_response(wb, 'planificacion_general')


@login_required
def export_planificacion_detallada_excel(request):
    """Exporta asignaturas, actividades y Matriz F4 en hojas separadas."""
    periodo_id, carrera_id = _export_filters(request)
    wb = Workbook()

    assignments = PlanificacionAsignacionDocente.objects.select_related(
        'id_docente', 'id_asignatura', 'id_carrera', 'id_periodo', 'id_campo'
    ).order_by('id_docente__nombres_completos', 'id_asignatura__nombre_asignatura')
    if periodo_id:
        assignments = assignments.filter(id_periodo_id=periodo_id)
    if carrera_id:
        assignments = assignments.filter(id_carrera_id=carrera_id)
    ws = wb.active
    ws.title = 'Asignaturas'
    headers = [
        'Docente', 'Cédula', 'Carrera', 'Período', 'Código', 'Asignatura',
        'Nivel', 'Paralelo', 'Campo', 'Horas clase',
    ]
    ws.append(headers)
    _style_header(ws, 1, len(headers))
    for row_number, item in enumerate(assignments.iterator(), start=2):
        ws.append([
            item.id_docente.nombres_completos, item.id_docente.cedula_docente,
            item.id_carrera.nombre_carrera, item.id_periodo.nombre_periodo,
            item.id_asignatura.codigo_asignatura, item.id_asignatura.nombre_asignatura,
            item.nivel_semestre_asignado, item.paralelo_asignado,
            item.id_campo.nombre_campo_conocimiento, item.horas_clase,
        ])
        _style_data(ws, row_number, len(headers))
    _finish_sheet(ws, {1: 36, 3: 30, 6: 36, 9: 30})

    activities = PlanificacionActividadDocente.objects.select_related(
        'id_docente', 'id_periodo', 'id_actividad'
    ).order_by('id_docente__nombres_completos', 'id_actividad__nombre_actividad')
    if periodo_id:
        activities = activities.filter(id_periodo_id=periodo_id)
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
    ws = wb.create_sheet('Matriz F4')
    headers = [
        'Docente', 'Cédula', 'Carrera', 'Período', 'Tipo', 'Detalle',
        'Nivel', 'Horas', 'Paralelos', 'Total', 'Observaciones',
    ]
    ws.append(headers)
    _style_header(ws, 1, len(headers))
    for row_number, item in enumerate(f4_rows.iterator(), start=2):
        total = (item.horas_actividad or 0) * (item.numero_paralelos_actividad or 1)
        ws.append([
            item.id_docente.nombres_completos, item.id_docente.cedula_docente,
            item.id_carrera.nombre_carrera, item.id_periodo.nombre_periodo,
            item.tipo_actividad, item.nombre_asignatura_actividad or '',
            item.nivel_semestre_actividad or '', item.horas_actividad,
            item.numero_paralelos_actividad, total, item.observaciones or '',
        ])
        _style_data(ws, row_number, len(headers))
    _finish_sheet(ws, {1: 36, 3: 30, 5: 24, 6: 38, 11: 45})

    return _excel_response(wb, 'planificacion_detallada')
