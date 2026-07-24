import re
import unicodedata

from django.core.exceptions import ValidationError
from django.db.models import Sum


def normalize_workload_text(value):
    text = re.sub(r'\s+', ' ', str(value or '').replace('\xa0', ' ')).strip()
    text = unicodedata.normalize('NFKD', text)
    text = ''.join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r'\s+', ' ', text).strip().upper()


def classify_f4_activity(tipo_actividad):
    activity = (tipo_actividad or '').strip().lower()
    if 'invest' in activity:
        return 'investigacion'
    if 'gesti' in activity:
        return 'gestion'
    if 'vincul' in activity:
        return 'vinculacion'
    return 'actividad'


def empty_workload():
    return {
        'horas_afinidad': 0,
        'horas_no_afinidad': 0,
        'horas_unidad_basica': 0,
        'horas_clase': 0,
        'total_horas_clase': 0,
        'horas_complementarias': 0,
        'horas_investigacion': 0,
        'horas_gestion': 0,
        'horas_vinculacion': 0,
        'horas_actividad': 0,
        'horas_actividades_total': 0,
        'total_horas': 0,
    }


def knowledge_field_maps():
    from curriculo.models import CurriculoAsignaturaCampo, RelacionPosgradoCampo
    from docentes.models import DocenteCampoAfinidad, DocenteTituloAcademico

    subject_fields = {}
    for subject_id, field_id in CurriculoAsignaturaCampo.objects.values_list(
        'id_asignatura_id', 'id_campo_id'
    ):
        subject_fields.setdefault(subject_id, set()).add(field_id)

    teacher_fields = {}
    for teacher_id, field_id in DocenteCampoAfinidad.objects.values_list(
        'id_docente_id', 'id_campo_id'
    ):
        teacher_fields.setdefault(teacher_id, set()).add(field_id)

    postgraduate_fields = {}
    for postgraduate_id, field_id in RelacionPosgradoCampo.objects.values_list(
        'id_posgrado_id', 'id_campo_id'
    ):
        postgraduate_fields.setdefault(postgraduate_id, set()).add(field_id)
    for teacher_id, postgraduate_id in DocenteTituloAcademico.objects.exclude(
        id_posgrado__isnull=True
    ).values_list('id_docente_id', 'id_posgrado_id'):
        teacher_fields.setdefault(teacher_id, set()).update(
            postgraduate_fields.get(postgraduate_id, set())
        )
    return subject_fields, teacher_fields


def assignment_hour_category(
    docente_id, asignatura_id, field_name, subject_fields=None, teacher_fields=None
):
    """Clasifica las horas de clase como afinidad, no afinidad o unidad básica."""
    if normalize_workload_text(field_name) == 'UNIDAD BASICA':
        return 'unidad_basica'
    if subject_fields is None or teacher_fields is None:
        subject_fields, teacher_fields = knowledge_field_maps()
    if subject_fields.get(asignatura_id, set()) & teacher_fields.get(docente_id, set()):
        return 'afinidad'
    return 'no_afinidad'


def activity_workload_key(docente_id, periodo_id, name, hours):
    return (
        docente_id,
        periodo_id,
        normalize_workload_text(name),
        int(hours or 0),
    )


def registered_activity_keys(periodo_id=None):
    from .models import PlanificacionActividadDocente

    qs = PlanificacionActividadDocente.objects.all()
    if periodo_id:
        qs = qs.filter(id_periodo_id=periodo_id)
    return {
        activity_workload_key(
            row['id_docente_id'], row['id_periodo_id'],
            row['id_actividad__nombre_actividad'], row['horas_asignadas'],
        )
        for row in qs.values(
            'id_docente_id', 'id_periodo_id',
            'id_actividad__nombre_actividad', 'horas_asignadas',
        )
    }


def build_docente_workload_map(periodo_id=None, carrera_id=None):
    """Calcula en un único lugar la carga completa de cada docente."""
    from .models import (
        PlanificacionActividadDocente, PlanificacionAsignacionDocente,
        PlanificacionMatrizF4,
    )

    workload = {}
    subject_fields, teacher_fields = knowledge_field_maps()

    asignaciones_qs = PlanificacionAsignacionDocente.objects.select_related('id_campo')
    if periodo_id:
        asignaciones_qs = asignaciones_qs.filter(id_periodo_id=periodo_id)
    if carrera_id:
        asignaciones_qs = asignaciones_qs.filter(id_carrera_id=carrera_id)
    for row in asignaciones_qs.values(
        'id_docente_id', 'id_asignatura_id', 'id_campo__nombre_campo_conocimiento',
        'horas_clase', 'horas_complementarias',
    ):
        docente_workload = workload.setdefault(row['id_docente_id'], empty_workload())
        hours = row['horas_clase'] or 0
        category = assignment_hour_category(
            row['id_docente_id'], row['id_asignatura_id'],
            row['id_campo__nombre_campo_conocimiento'], subject_fields, teacher_fields,
        )
        docente_workload[f'horas_{category}'] += hours
        docente_workload['horas_clase'] += hours
        docente_workload['horas_complementarias'] += row['horas_complementarias'] or 0

    actividades_qs = PlanificacionActividadDocente.objects.select_related('id_actividad')
    if periodo_id:
        actividades_qs = actividades_qs.filter(id_periodo_id=periodo_id)
    activity_keys = registered_activity_keys(periodo_id)

    f4_qs = PlanificacionMatrizF4.objects.all()
    if periodo_id:
        f4_qs = f4_qs.filter(id_periodo_id=periodo_id)
    if carrera_id:
        f4_qs = f4_qs.filter(id_carrera_id=carrera_id)
    seen_f4 = set()
    f4_totals = {}
    for row in f4_qs.values(
        'id_docente_id', 'id_periodo_id', 'tipo_actividad',
        'nombre_asignatura_actividad', 'horas_actividad',
        'numero_paralelos_actividad',
    ):
        total = (row['horas_actividad'] or 0) * (row['numero_paralelos_actividad'] or 1)
        activity_key = activity_workload_key(
            row['id_docente_id'], row['id_periodo_id'],
            row['nombre_asignatura_actividad'], total,
        )
        if activity_key in activity_keys:
            continue
        dedupe_key = (
            row['id_docente_id'], row['id_periodo_id'], row['tipo_actividad'],
            normalize_workload_text(row['nombre_asignatura_actividad']),
            row['horas_actividad'], row['numero_paralelos_actividad'],
        )
        if not carrera_id and dedupe_key in seen_f4:
            continue
        seen_f4.add(dedupe_key)
        key = (row['id_docente_id'], row['tipo_actividad'])
        f4_totals[key] = f4_totals.get(key, 0) + total

    for (docente_id, tipo_actividad), total in f4_totals.items():
        docente_workload = workload.setdefault(docente_id, empty_workload())
        bucket = classify_f4_activity(tipo_actividad)
        docente_workload[f'horas_{bucket}'] += total

    for row in actividades_qs.values(
        'id_docente_id', 'id_actividad__tipo_actividad'
    ).annotate(total_horas=Sum('horas_asignadas')):
        docente_workload = workload.setdefault(row['id_docente_id'], empty_workload())
        activity_type = row['id_actividad__tipo_actividad']
        if activity_type == 'INVESTIGACION':
            docente_workload['horas_investigacion'] += row['total_horas'] or 0
        elif activity_type == 'GESTION':
            docente_workload['horas_gestion'] += row['total_horas'] or 0
        elif activity_type == 'VINCULACION':
            docente_workload['horas_vinculacion'] += row['total_horas'] or 0
        else:
            docente_workload['horas_complementarias'] += row['total_horas'] or 0

    for docente_workload in workload.values():
        docente_workload['total_horas_clase'] = docente_workload['horas_clase']
        docente_workload['horas_actividades_total'] = (
            docente_workload['horas_complementarias'] +
            docente_workload['horas_investigacion'] +
            docente_workload['horas_gestion'] +
            docente_workload['horas_vinculacion'] +
            docente_workload['horas_actividad']
        )
        docente_workload['total_horas'] = (
            docente_workload['horas_clase'] + docente_workload['horas_actividades_total']
        )
    return workload


def normalize_parallel(value):
    return re.sub(r'\s+', ' ', str(value or '')).strip().upper()[:3]


def parallel_labels(total):
    labels = []
    for index in range(max(int(total or 0), 0)):
        label = ''
        current = index
        while current >= 0:
            label = chr(65 + (current % 26)) + label
            current = (current // 26) - 1
        labels.append(label)
    return labels


def docente_tiene_afinidad(docente, asignatura):
    from curriculo.models import CurriculoAsignaturaCampo, RelacionPosgradoCampo
    from docentes.models import DocenteCampoAfinidad, DocenteTituloAcademico

    campos_asignatura = set(
        CurriculoAsignaturaCampo.objects.filter(id_asignatura=asignatura)
        .values_list('id_campo_id', flat=True)
    )
    if not campos_asignatura:
        return False
    campos_docente = set(
        DocenteCampoAfinidad.objects.filter(id_docente=docente)
        .values_list('id_campo_id', flat=True)
    )
    if campos_asignatura & campos_docente:
        return True
    posgrados = DocenteTituloAcademico.objects.filter(
        id_docente=docente, id_posgrado__isnull=False,
    ).values_list('id_posgrado_id', flat=True)
    return RelacionPosgradoCampo.objects.filter(
        id_posgrado_id__in=posgrados,
        id_campo_id__in=campos_asignatura,
    ).exists()


def periodo_es_editable(periodo):
    estado = getattr(periodo, 'estado_planificacion', 'BORRADOR') or 'BORRADOR'
    return estado in {'BORRADOR', 'EN_REVISION'}


def assert_periodo_editable(periodo):
    if periodo and not periodo_es_editable(periodo):
        display = getattr(periodo, 'get_estado_planificacion_display', lambda: 'cerrado')()
        raise ValidationError(
            f'El periodo {periodo} está {display.lower()} y ya no admite cambios de planificación.'
        )


def validate_assignment_business_rules(
    *, docente, asignatura, carrera, periodo, campo, nivel, paralelo,
    horas_clase, instance=None, require_editable=True,
):
    """Reglas únicas para formulario, operativa, API e importadores."""
    from curriculo.models import CurriculoAsignaturaCampo
    from .models import PlanificacionAsignacionDocente, PlanificacionDemandaAcademica

    errors = {}
    paralelo = normalize_parallel(paralelo)
    nivel = int(nivel or 0)
    horas_clase = int(horas_clase or 0)

    if require_editable:
        try:
            assert_periodo_editable(periodo)
        except ValidationError as exc:
            errors['id_periodo'] = exc.messages[0]
    if asignatura and carrera and asignatura.id_carrera_id != carrera.id_carrera:
        errors['id_carrera'] = 'La carrera no corresponde a la asignatura seleccionada.'
    if asignatura and nivel != asignatura.nivel_semestre:
        errors['nivel_semestre_asignado'] = 'El nivel debe coincidir con el nivel de la asignatura.'
    if not re.fullmatch(r'[A-Z]{1,3}', paralelo):
        errors['paralelo_asignado'] = 'El paralelo debe contener entre 1 y 3 letras.'

    if asignatura and carrera and periodo:
        demanda = PlanificacionDemandaAcademica.objects.filter(
            id_asignatura=asignatura, id_carrera=carrera, id_periodo=periodo,
        ).first()
        if not demanda:
            errors['id_asignatura'] = 'La asignatura no está registrada en la demanda académica.'
        elif paralelo not in parallel_labels(demanda.numero_paralelos):
            errors['paralelo_asignado'] = (
                f'El paralelo {paralelo or "indicado"} no existe en la demanda. '
                f'Opciones: {", ".join(parallel_labels(demanda.numero_paralelos))}.'
            )
    if asignatura and campo and not CurriculoAsignaturaCampo.objects.filter(
        id_asignatura=asignatura, id_campo=campo,
    ).exists():
        errors['id_campo'] = 'El campo seleccionado no corresponde a esta asignatura.'
   ## if asignatura and docente and nivel >= 4 and not docente_tiene_afinidad(docente, asignatura):
     ##   errors['id_docente'] = 'Desde cuarto nivel solo se permiten docentes con afinidad registrada.'
    expected_hours = asignatura.horas_semanales_asignatura or 0 if asignatura else 0
    if asignatura and horas_clase <= 0:
        errors['horas_clase'] = 'Las horas de clase deben ser mayores que cero.'
    elif asignatura and horas_clase != expected_hours:
        errors['horas_clase'] = f'Las horas deben coincidir con la malla: {expected_hours}h.'

    if asignatura and carrera and periodo and paralelo:
        duplicate = PlanificacionAsignacionDocente.objects.filter(
            id_asignatura=asignatura, id_carrera=carrera, id_periodo=periodo,
            paralelo_asignado__iexact=paralelo,
        )
        if instance and instance.pk:
            duplicate = duplicate.exclude(pk=instance.pk)
        if duplicate.exists():
            errors['paralelo_asignado'] = 'Este paralelo ya tiene un docente asignado.'
    return errors


def add_form_errors(form, errors):
    for field, message in errors.items():
        form.add_error(field if field in form.fields else None, message)
