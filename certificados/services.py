from collections import OrderedDict

from docentes.models import DocenteAsignacionCarreraPeriodo
from planificacion.models import PlanificacionActividadDocente, PlanificacionAsignacionDocente


FUNCTION_FILTERS = (
    ('TODOS', 'Actividades, asignaciones y comisiones'),
    ('ACTIVIDADES', 'Solo actividades'),
    ('ASIGNACIONES', 'Solo asignaciones'),
    ('COMISIONES', 'Solo comisiones'),
)
FUNCTION_FILTER_LABELS = dict(FUNCTION_FILTERS)


def _date_value(value):
    return value.strftime('%d/%m/%Y') if value else None


def normalize_function_filter(value):
    value = (value or 'TODOS').strip().upper()
    return value if value in FUNCTION_FILTER_LABELS else 'TODOS'


def build_certificate_snapshot(certificate_type, teacher, function_filter='TODOS'):
    common = {
        'docente': {
            'id': teacher.id_docente,
            'cedula': teacher.cedula_docente,
            'nombres': teacher.nombres_completos,
            'unidad': teacher.unidad_organica or '',
        },
        'filas': [],
        'advertencias': [],
    }
    if certificate_type == 'DEDICACION':
        assignments = DocenteAsignacionCarreraPeriodo.objects.filter(
            id_docente=teacher
        ).select_related(
            'id_periodo', 'id_carrera', 'id_licencia'
        ).order_by('id_periodo__fecha_inicio_periodo', 'id_carrera__nombre_carrera')
        periods = OrderedDict()
        for assignment in assignments:
            period = assignment.id_periodo
            row = periods.setdefault(period.id_periodo, {
                'periodo': period.nombre_periodo,
                'desde': _date_value(period.fecha_inicio_periodo),
                'hasta': _date_value(period.fecha_fin_periodo),
                'dedicacion': str(teacher.id_dedicacion),
                'unidad': [],
            })
            career_name = assignment.id_carrera.nombre_carrera
            if career_name not in row['unidad']:
                row['unidad'].append(career_name)
            if getattr(assignment.id_licencia, 'codigo_licencia', '') != 'NINGUNA':
                row['dedicacion'] = assignment.id_licencia.nombre_licencia
        common['filas'] = [
            {**row, 'unidad': ', '.join(row['unidad'])} for row in periods.values()
        ]
        if common['filas']:
            common['advertencias'].append(
                'La base actual no conserva cambios históricos de dedicación; '
                'se aplicó la dedicación vigente, salvo períodos con licencia.'
            )
    elif certificate_type == 'CATEDRAS':
        assignments = PlanificacionAsignacionDocente.objects.filter(
            id_docente=teacher
        ).select_related(
            'id_asignatura', 'id_carrera', 'id_periodo'
        ).order_by('id_periodo__fecha_inicio_periodo', 'id_asignatura__nombre_asignatura')
        common['filas'] = [{
            'descripcion': assignment.id_asignatura.nombre_asignatura,
            'unidad': assignment.id_carrera.nombre_carrera,
            'dedicacion': str(teacher.id_dedicacion),
            'desde': _date_value(assignment.id_periodo.fecha_inicio_periodo),
            'hasta': _date_value(assignment.id_periodo.fecha_fin_periodo),
            'periodo': assignment.id_periodo.nombre_periodo,
        } for assignment in assignments]
        if common['filas']:
            common['advertencias'].append(
                'La dedicación mostrada corresponde al registro vigente del docente.'
            )
    elif certificate_type == 'FUNCIONES':
        selected_filter = normalize_function_filter(function_filter)
        common['filtro_funciones'] = selected_filter
        common['filtro_funciones_label'] = FUNCTION_FILTER_LABELS[selected_filter]
        rows = []

        if selected_filter in ('TODOS', 'ACTIVIDADES'):
            activities = PlanificacionActividadDocente.objects.filter(
                id_docente=teacher
            ).select_related('id_actividad', 'id_periodo').order_by(
                'id_periodo__fecha_inicio_periodo',
                'id_actividad__nombre_actividad',
            )
            rows.extend({
                'categoria': 'ACTIVIDADES',
                'categoria_label': 'Actividad',
                'descripcion': (
                    activity.observaciones.strip()
                    if activity.observaciones and activity.observaciones.strip()
                    else activity.id_actividad.nombre_actividad
                ),
                'unidad': (
                    teacher.unidad_organica
                    or 'Facultad de Ciencias Administrativas, Contables y Comercio'
                ),
                'desde': _date_value(activity.id_periodo.fecha_inicio_periodo),
                'hasta': _date_value(activity.id_periodo.fecha_fin_periodo),
                'periodo': activity.id_periodo.nombre_periodo,
            } for activity in activities)

        assignments = None
        if selected_filter in ('TODOS', 'ASIGNACIONES', 'COMISIONES'):
            assignments = PlanificacionAsignacionDocente.objects.filter(
                id_docente=teacher
            ).select_related(
                'id_asignatura', 'id_carrera', 'id_periodo'
            ).order_by(
                'id_periodo__fecha_inicio_periodo',
                'id_asignatura__nombre_asignatura',
            )

        if selected_filter in ('TODOS', 'ASIGNACIONES'):
            rows.extend({
                'categoria': 'ASIGNACIONES',
                'categoria_label': 'Asignación',
                'descripcion': (
                    f'{assignment.id_asignatura.nombre_asignatura} · '
                    f'Paralelo {assignment.paralelo_asignado}'
                ),
                'unidad': assignment.id_carrera.nombre_carrera,
                'desde': _date_value(assignment.id_periodo.fecha_inicio_periodo),
                'hasta': _date_value(assignment.id_periodo.fecha_fin_periodo),
                'periodo': assignment.id_periodo.nombre_periodo,
            } for assignment in assignments)

        if selected_filter in ('TODOS', 'COMISIONES'):
            commissions = OrderedDict()
            for assignment in assignments:
                description = (assignment.comision_servicio or '').strip()
                if not description:
                    continue
                key = (
                    description.casefold(),
                    assignment.id_periodo_id,
                    assignment.id_carrera_id,
                )
                commissions.setdefault(key, {
                    'categoria': 'COMISIONES',
                    'categoria_label': 'Comisión',
                    'descripcion': description,
                    'unidad': assignment.id_carrera.nombre_carrera,
                    'desde': _date_value(assignment.id_periodo.fecha_inicio_periodo),
                    'hasta': _date_value(assignment.id_periodo.fecha_fin_periodo),
                    'periodo': assignment.id_periodo.nombre_periodo,
                })
            rows.extend(commissions.values())

        common['filas'] = rows
    return common
