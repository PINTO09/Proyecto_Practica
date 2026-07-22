import re

from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Sum

from curriculo.models import CurriculoAsignatura, CurriculoAsignaturaCampo
from docentes.models import DocenteCampoAfinidad
from catalogos.models import LimiteHorario, CatalogoCarrera, CatalogoPeriodoAcademico

from .models import (
    PlanificacionAsignacionDocente, PlanificacionActividadDocente,
    PlanificacionDemandaAcademica,
)


def _parallel_labels(total):
    labels = []
    for index in range(max(total, 0)):
        label = ''
        current = index
        while current >= 0:
            label = chr(65 + (current % 26)) + label
            current = (current // 26) - 1
        labels.append(label)
    return labels


def docente_tiene_afinidad(docente, asignatura):
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

    from docentes.models import DocenteTituloAcademico
    from curriculo.models import RelacionPosgradoCampo

    posgrados = DocenteTituloAcademico.objects.filter(
        id_docente=docente, id_posgrado__isnull=False,
    ).values_list('id_posgrado_id', flat=True)
    return RelacionPosgradoCampo.objects.filter(
        id_posgrado_id__in=posgrados,
        id_campo_id__in=campos_asignatura,
    ).exists()


class PlanificacionAsignacionDocenteForm(forms.ModelForm):
    paralelo_asignado = forms.ChoiceField(
        label='Paralelo', choices=[],
        help_text='Seleccione el paralelo según la demanda académica.',
    )

    class Meta:
        model = PlanificacionAsignacionDocente
        fields = (
            'id_periodo', 'id_carrera', 'nivel_semestre_asignado',
            'id_asignatura', 'paralelo_asignado', 'id_campo',
            'id_docente', 'horas_clase', 'comision_servicio',
        )
        widgets = {
            'comision_servicio': forms.Textarea(attrs={'rows': 2}),
            'nivel_semestre_asignado': forms.Select(choices=[('', '--- Seleccione ---')]),
            'horas_clase': forms.NumberInput(attrs={'min': 0}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-select' if isinstance(field.widget, forms.Select) else 'form-control'
        self.fields['id_docente'].queryset = self.fields['id_docente'].queryset.filter(docente_activo=True).order_by('nombres_completos')
        self.fields['id_asignatura'].queryset = CurriculoAsignatura.objects.select_related('id_carrera').order_by(
            'id_carrera__nombre_carrera', 'nivel_semestre', 'nombre_asignatura'
        )
        asignatura = None
        carrera = None
        periodo = None
        paralelo_actual = None
        es_actividad = False
        if self.instance and self.instance.pk:
            asignatura = self.instance.id_asignatura
            carrera = self.instance.id_carrera
            periodo = self.instance.id_periodo
            paralelo_actual = self.instance.paralelo_asignado
            es_actividad = getattr(asignatura, 'es_actividad', False) or getattr(carrera, 'es_actividad', False)
        else:
            raw_subj = self.initial.get('id_asignatura')
            carr_id = self.initial.get('id_carrera')
            per_id = self.initial.get('id_periodo')
            if carr_id and per_id:
                subj_id = raw_subj.pk if hasattr(raw_subj, 'pk') else raw_subj
                carr_id_v = carr_id.pk if hasattr(carr_id, 'pk') else carr_id
                per_id_v = per_id.pk if hasattr(per_id, 'pk') else per_id
                if subj_id and carr_id_v and per_id_v:
                    try:
                        asignatura = CurriculoAsignatura.objects.get(pk=subj_id)
                        carrera = CatalogoCarrera.objects.get(pk=carr_id_v)
                        periodo = CatalogoPeriodoAcademico.objects.get(pk=per_id_v)
                        es_actividad = asignatura.es_actividad or carrera.es_actividad
                    except (CurriculoAsignatura.DoesNotExist, CatalogoCarrera.DoesNotExist, CatalogoPeriodoAcademico.DoesNotExist):
                        pass
            paralelo_actual = self.initial.get('paralelo_asignado', '')

        # Populate nivel choices based on career's actual levels
        if carrera:
            niveles = CurriculoAsignatura.objects.filter(
                id_carrera=carrera, es_actividad=False
            ).values_list('nivel_semestre', flat=True).distinct().order_by('nivel_semestre')
            nivel_choices = [('', '--- Seleccione ---')] + [(n, f'Nivel {n}') for n in niveles]
            self.fields['nivel_semestre_asignado'].widget = forms.Select(choices=nivel_choices)

        # Populate paralelo choices from demanda for the current subject+carrera+periodo
        choices = self.fields['paralelo_asignado'].choices or []
        if paralelo_actual:
            choices.append((paralelo_actual, paralelo_actual))
        if asignatura and carrera and periodo:
            demanda = PlanificacionDemandaAcademica.objects.filter(
                id_asignatura=asignatura, id_carrera=carrera, id_periodo=periodo,
            ).first()
            if demanda:
                labels = _parallel_labels(demanda.numero_paralelos)
                choices = [(l, l) for l in labels]
                if paralelo_actual and paralelo_actual not in labels:
                    choices.append((paralelo_actual, paralelo_actual))
        self.fields['paralelo_asignado'].choices = choices

    def clean_paralelo_asignado(self):
        value = self.cleaned_data.get('paralelo_asignado', '').strip().upper()
        valid = [k for k, v in self.fields['paralelo_asignado'].choices]
        if valid and value and value not in valid:
            raise ValidationError(f'Paralelo no válido. Opciones: {", ".join(valid)}.')
        if not valid and not re.fullmatch(r'[A-Z]{1,3}', value):
            raise ValidationError('El paralelo debe contener 1 a 3 letras mayúsculas.')
        return value if value else ''

    def clean(self):
        cleaned = super().clean()
        asignatura = cleaned.get('id_asignatura')
        carrera = cleaned.get('id_carrera')
        nivel = cleaned.get('nivel_semestre_asignado')
        docente = cleaned.get('id_docente')
        periodo = cleaned.get('id_periodo')
        paralelo = cleaned.get('paralelo_asignado')
        campo = cleaned.get('id_campo')

        es_actividad = False
        if asignatura:
            es_actividad = asignatura.es_actividad
        if carrera and not es_actividad:
            es_actividad = carrera.es_actividad

        if asignatura and carrera and asignatura.id_carrera_id != carrera.id_carrera:
            self.add_error('id_carrera', 'La carrera no corresponde a la asignatura seleccionada.')
        if asignatura and nivel and asignatura.nivel_semestre != nivel:
            self.add_error('nivel_semestre_asignado', 'El nivel debe coincidir con el nivel de la asignatura.')
        if not es_actividad and asignatura and campo and not CurriculoAsignaturaCampo.objects.filter(
            id_asignatura=asignatura, id_campo=campo
        ).exists():
            self.add_error('id_campo', 'El campo seleccionado no corresponde a esta asignatura.')

        if not es_actividad and asignatura and carrera and periodo:
            if not PlanificacionDemandaAcademica.objects.filter(
                id_asignatura=asignatura, id_carrera=carrera, id_periodo=periodo,
            ).exists():
                self.add_error(
                    'id_asignatura',
                    'Esta asignatura no está registrada en la demanda académica del período y carrera seleccionados.',
                )

        if not es_actividad and asignatura and docente and (nivel or asignatura.nivel_semestre) >= 4:
            if not docente_tiene_afinidad(docente, asignatura):
                self.add_error(
                    'id_docente',
                    'Desde cuarto nivel solo se permiten docentes con afinidad registrada para la asignatura.',
                )

        if not es_actividad and asignatura and docente and periodo and asignatura.id_asignatura:
            otras_asignaciones = PlanificacionAsignacionDocente.objects.filter(
                id_docente=docente,
                id_periodo=periodo,
            ).exclude(
                id_asignatura__in=PlanificacionAsignacionDocente.objects.filter(
                    id_asignatura__es_actividad=True
                ).values('id_asignatura')
            )
            if self.instance.pk:
                otras_asignaciones = otras_asignaciones.exclude(pk=self.instance.pk)
            otras_ids = set(otras_asignaciones.values_list('id_asignatura_id', flat=True))
            otras_ids.discard(asignatura.id_asignatura)
            if otras_ids:
                self.add_error(
                    'id_docente',
                    'El docente ya tiene asignada otra asignatura en este período. '
                    'Solo puede tener una asignatura distinta (se permiten varios paralelos de la misma).',
                )

        if not es_actividad and asignatura and carrera and periodo and paralelo:
            duplicate = PlanificacionAsignacionDocente.objects.filter(
                id_asignatura=asignatura, id_carrera=carrera,
                id_periodo=periodo, paralelo_asignado__iexact=paralelo,
            )
            if self.instance.pk:
                duplicate = duplicate.exclude(pk=self.instance.pk)
            if duplicate.exists():
                self.add_error('paralelo_asignado', 'Este nivel, asignatura y paralelo ya tienen un docente asignado.')
        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.horas_complementarias = 0
        if commit:
            instance.save()
            self.save_m2m()
        return instance


class PlanificacionActividadDocenteForm(forms.ModelForm):
    class Meta:
        model = PlanificacionActividadDocente
        fields = '__all__'
        widgets = {'observaciones': forms.Textarea(attrs={'rows': 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['id_docente'].queryset = self.fields['id_docente'].queryset.filter(docente_activo=True).order_by('nombres_completos')
        self.fields['id_actividad'].queryset = self.fields['id_actividad'].queryset.filter(actividad_activa=True)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-select' if isinstance(field.widget, forms.Select) else 'form-control'

    def clean(self):
        cleaned = super().clean()
        docente = cleaned.get('id_docente')
        periodo = cleaned.get('id_periodo')
        horas = cleaned.get('horas_asignadas') or 0
        if not docente or not periodo:
            return cleaned
        limite = LimiteHorario.objects.filter(id_modalidad=docente.id_modalidad, activo=True).first()
        if not limite:
            raise ValidationError('La modalidad del docente no tiene límites horarios configurados.')
        previas = PlanificacionActividadDocente.objects.filter(
            id_docente=docente, id_periodo=periodo,
        )
        if self.instance.pk:
            previas = previas.exclude(pk=self.instance.pk)
        legacy = PlanificacionAsignacionDocente.objects.filter(
            id_docente=docente, id_periodo=periodo,
        ).aggregate(total=Sum('horas_complementarias'))['total'] or 0
        total = legacy + (previas.aggregate(total=Sum('horas_asignadas'))['total'] or 0) + horas
        if total > limite.horas_complementarias_maximas:
            self.add_error(
                'horas_asignadas',
                f'La carga complementaria sería {total}h y supera el límite de {limite.horas_complementarias_maximas}h.',
            )
        return cleaned
