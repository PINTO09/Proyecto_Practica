from django.http import HttpResponse, JsonResponse
from django.db.models import Sum, Count, Q
from django.db import ProgrammingError, OperationalError
from django.contrib.auth.decorators import login_required
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from docentes.models import DocenteFcacc, DocenteTituloAcademico, DocenteCampoAfinidad, DocenteAsignacionCarreraPeriodo
from planificacion.models import PlanificacionAsignacionDocente, PlanificacionMatrizF4
from curriculo.models import CurriculoAsignatura
from catalogos.models import CatalogoCarrera, CatalogoPeriodoAcademico, CatalogoCampoConocimiento


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
