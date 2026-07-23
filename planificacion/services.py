import re

from django.core.exceptions import ValidationError


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
    if asignatura and docente and nivel >= 4 and not docente_tiene_afinidad(docente, asignatura):
        errors['id_docente'] = 'Desde cuarto nivel solo se permiten docentes con afinidad registrada.'
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
