import re

from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Sum

from curriculo.models import CurriculoAsignatura, CurriculoAsignaturaCampo
from docentes.models import DocenteCampoAfinidad
from catalogos.models import LimiteHorario

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
    paralelo_asignado = forms.CharField(
        label='Paralelo', max_length=3,
        help_text='Use A, B, C… según los paralelos solicitados en la demanda.',
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
            'nivel_semestre_asignado': forms.NumberInput(attrs={'min': 1, 'max': 10}),
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

    def clean_paralelo_asignado(self):
        value = re.sub(r'\s+', '', self.cleaned_data['paralelo_asignado']).upper()
        if not re.fullmatch(r'[A-Z]{1,3}', value):
            raise ValidationError('El paralelo debe contener únicamente letras, por ejemplo A o B.')
        return value

    def clean(self):
        cleaned = super().clean()
        asignatura = cleaned.get('id_asignatura')
        carrera = cleaned.get('id_carrera')
        nivel = cleaned.get('nivel_semestre_asignado')
        docente = cleaned.get('id_docente')
        periodo = cleaned.get('id_periodo')
        paralelo = cleaned.get('paralelo_asignado')
        campo = cleaned.get('id_campo')

        if asignatura and carrera and asignatura.id_carrera_id != carrera.id_carrera:
            self.add_error('id_carrera', 'La carrera no corresponde a la asignatura seleccionada.')
        if asignatura and nivel and asignatura.nivel_semestre != nivel:
            self.add_error('nivel_semestre_asignado', 'El nivel debe coincidir con el nivel de la asignatura.')
        if asignatura and campo and not CurriculoAsignaturaCampo.objects.filter(
            id_asignatura=asignatura, id_campo=campo
        ).exists():
            self.add_error('id_campo', 'El campo seleccionado no corresponde a esta asignatura.')
        if asignatura and docente and (nivel or asignatura.nivel_semestre) >= 4:
            if not docente_tiene_afinidad(docente, asignatura):
                self.add_error(
                    'id_docente',
                    'Desde cuarto nivel solo se permiten docentes con afinidad registrada para la asignatura.',
                )

        if asignatura and carrera and periodo and paralelo:
            demanda = PlanificacionDemandaAcademica.objects.filter(
                id_asignatura=asignatura, id_carrera=carrera, id_periodo=periodo,
            ).first()
            if demanda:
                allowed = _parallel_labels(demanda.numero_paralelos)
                if paralelo not in allowed:
                    self.add_error(
                        'paralelo_asignado',
                        f'El paralelo debe ser uno de los solicitados: {", ".join(allowed)}.',
                    )
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
