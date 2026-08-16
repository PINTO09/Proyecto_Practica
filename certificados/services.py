from collections import OrderedDict
import re

from django.db.models import Exists, OuterRef

from docentes.models import DocenteAsignacionCarreraPeriodo, DocenteFcacc
from planificacion.models import PlanificacionActividadDocente, PlanificacionAsignacionDocente


def docentes_con_datos(tipo, function_filter='TODOS', periodo=None):
    docentes = DocenteFcacc.objects.all()
    if tipo == 'DEDICACION':
        sub = DocenteAsignacionCarreraPeriodo.objects.filter(id_docente=OuterRef('pk'))
        if periodo is not None:
            sub = sub.filter(id_periodo=periodo)
        docentes = docentes.filter(Exists(sub))
    elif tipo == 'CATEDRAS':
        sub = PlanificacionAsignacionDocente.objects.filter(id_docente=OuterRef('pk'))
        if periodo is not None:
            sub = sub.filter(id_periodo=periodo)
        docentes = docentes.filter(Exists(sub))
    elif tipo == 'FUNCIONES':
        selected = normalize_function_filter(function_filter)
        if selected == 'ACTIVIDADES':
            sub = PlanificacionActividadDocente.objects.filter(
                id_docente=OuterRef('pk'), id_actividad__peso=1,
            )
            if periodo is not None:
                sub = sub.filter(id_periodo=periodo)
            docentes = docentes.filter(Exists(sub))
        elif selected == 'ASIGNACIONES':
            sub = PlanificacionAsignacionDocente.objects.filter(id_docente=OuterRef('pk'))
            if periodo is not None:
                sub = sub.filter(id_periodo=periodo)
            docentes = docentes.filter(Exists(sub))
        elif selected == 'COMISIONES':
            sub = PlanificacionAsignacionDocente.objects.filter(
                id_docente=OuterRef('pk')
            ).exclude(comision_servicio__isnull=True).exclude(comision_servicio='')
            if periodo is not None:
                sub = sub.filter(id_periodo=periodo)
            docentes = docentes.filter(Exists(sub))
        else:
            sub_act = PlanificacionActividadDocente.objects.filter(
                id_docente=OuterRef('pk'), id_actividad__peso=1,
            )
            sub_asig = PlanificacionAsignacionDocente.objects.filter(id_docente=OuterRef('pk'))
            if periodo is not None:
                sub_act = sub_act.filter(id_periodo=periodo)
                sub_asig = sub_asig.filter(id_periodo=periodo)
            docentes = docentes.filter(Exists(sub_act) | Exists(sub_asig))
    return docentes


FUNCTION_FILTERS = (
    ('TODOS', 'Actividades, asignaciones y comisiones'),
    ('ACTIVIDADES', 'Solo actividades'),
    ('ASIGNACIONES', 'Solo asignaciones'),
    ('COMISIONES', 'Solo comisiones'),
)
FUNCTION_FILTER_LABELS = dict(FUNCTION_FILTERS)


def _date_value(value):
    return value.strftime('%d/%m/%Y') if value else None


def clean_function_description(observation, fallback):
    """Evita presentar metadatos del importador como cargo o función."""
    description = (observation or '').strip()
    if not description or re.match(r'^importad[oa]\s+desde(?:\s|$)', description, re.I):
        return fallback
    return description


def normalize_function_filter(value):
    value = (value or 'TODOS').strip().upper()
    return value if value in FUNCTION_FILTER_LABELS else 'TODOS'


def build_certificate_snapshot(certificate_type, teacher, function_filter='TODOS', periodo=None):
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
    if periodo is not None:
        common['periodo'] = periodo.nombre_periodo
    if certificate_type == 'DEDICACION':
        assignments = DocenteAsignacionCarreraPeriodo.objects.filter(
            id_docente=teacher
        ).select_related(
            'id_periodo', 'id_carrera', 'id_licencia'
        ).order_by('id_periodo__fecha_inicio_periodo', 'id_carrera__nombre_carrera')
        if periodo is not None:
            assignments = assignments.filter(id_periodo=periodo)
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
        if periodo is not None:
            assignments = assignments.filter(id_periodo=periodo)
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
                id_docente=teacher, id_actividad__peso=1,
            ).select_related('id_actividad', 'id_periodo').order_by(
                'id_periodo__fecha_inicio_periodo',
                'id_actividad__nombre_actividad',
            )
            if periodo is not None:
                activities = activities.filter(id_periodo=periodo)
            rows.extend({
                'categoria': 'ACTIVIDADES',
                'categoria_label': 'Actividad',
                'descripcion': clean_function_description(
                    activity.observaciones,
                    activity.id_actividad.nombre_actividad,
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
            if periodo is not None:
                assignments = assignments.filter(id_periodo=periodo)

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
                description = clean_function_description(
                    assignment.comision_servicio, ''
                )
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
