from collections import OrderedDict

from docentes.models import DocenteAsignacionCarreraPeriodo
from planificacion.models import PlanificacionActividadDocente, PlanificacionAsignacionDocente


def _date_value(value):
    return value.strftime('%d/%m/%Y') if value else None


def build_certificate_snapshot(certificate_type, teacher):
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
        activities = PlanificacionActividadDocente.objects.filter(
            id_docente=teacher, id_actividad__tipo_actividad__in=('GESTION', 'VINCULACION')
        ).select_related('id_actividad', 'id_periodo').order_by(
            'id_periodo__fecha_inicio_periodo', 'id_actividad__nombre_actividad'
        )
        common['filas'] = [{
            'descripcion': activity.id_actividad.nombre_actividad,
            'unidad': teacher.unidad_organica or 'Facultad de Ciencias Administrativas, Contables y Comercio',
            'desde': _date_value(activity.id_periodo.fecha_inicio_periodo),
            'hasta': _date_value(activity.id_periodo.fecha_fin_periodo),
            'periodo': activity.id_periodo.nombre_periodo,
        } for activity in activities]
    return common
