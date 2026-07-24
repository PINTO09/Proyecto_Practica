import re

from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q, Sum

from curriculo.models import CurriculoAsignatura, CurriculoAsignaturaCampo
from catalogos.models import LimiteHorario, CatalogoCarrera, CatalogoPeriodoAcademico

from .models import (
    PlanificacionAsignacionDocente, PlanificacionActividadDocente,
    PlanificacionAulaHorario, PlanificacionCapacidadEspecial,
    PlanificacionDemandaAcademica,
)
from .services import (
    add_form_errors, build_docente_workload_map, docente_tiene_afinidad, parallel_labels,
    validate_assignment_business_rules,
)


def _parallel_labels(total):
    return parallel_labels(total)


class PlanificacionAsignacionDocenteForm(forms.ModelForm):
    paralelo_asignado = forms.ChoiceField(
        label='Paralelo', choices=[],
        help_text='Seleccione el paralelo según la demanda académica.',
    )
    campo_conocimiento = forms.CharField(
        label='Campo de conocimiento',
        required=False,
        widget=forms.TextInput(attrs={'readonly': 'readonly', 'class': 'form-control-plaintext'}),
        help_text='Campos de conocimiento asociados a la asignatura.',
    )
    requiere_afinidad = forms.ChoiceField(
        label='¿Requiere afinidad?',
        choices=(
            ('AUTO', 'Automático según el nivel'),
            ('SI', 'Sí, exigir docente afín'),
            ('NO', 'No, permitir cualquier docente activo'),
        ),
        initial='AUTO',
        help_text=(
            'Automático: según el nivel. SI: exige docente con afinidad. '
            'NO: permite cualquier docente activo.'
        ),
    )

    class Meta:
        model = PlanificacionAsignacionDocente
        fields = (
            'id_periodo', 'id_carrera', 'nivel_semestre_asignado',
            'id_asignatura', 'paralelo_asignado',
            'campo_conocimiento', 'id_campo', 'requiere_afinidad',
            'id_docente', 'horas_clase', 'semanas_planificadas',
            'comision_servicio',
        )
        widgets = {
            'comision_servicio': forms.Textarea(attrs={'rows': 2}),
            'nivel_semestre_asignado': forms.Select(choices=[('', '--- Seleccione ---')]),
            'horas_clase': forms.NumberInput(attrs={'min': 0}),
            'semanas_planificadas': forms.NumberInput(attrs={'min': 1, 'max': 30}),
        }
        labels = {
            'nivel_semestre_asignado': 'Nivel',
            'id_campo': 'Campo de conocimiento',
            'id_docente': 'Docente',
            'horas_clase': 'Horas semanales de clase',
            'semanas_planificadas': 'Semanas del período',
            'comision_servicio': 'Comisión de servicio u observación',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name == 'campo_conocimiento':
                continue
            field.widget.attrs['class'] = 'form-select' if isinstance(field.widget, forms.Select) else 'form-control'
        self.fields['id_campo'].widget = forms.HiddenInput()
        self.fields['id_campo'].required = False
        self.fields['id_docente'].queryset = self.fields['id_docente'].queryset.filter(docente_activo=True).order_by('nombres_completos')
        subjects = CurriculoAsignatura.objects.select_related('id_carrera').filter(
            es_actividad=False
        )
        if self.instance and self.instance.pk and self.instance.id_asignatura_id:
            subjects = CurriculoAsignatura.objects.select_related('id_carrera').filter(
                Q(es_actividad=False) | Q(pk=self.instance.id_asignatura_id)
            )
        # Filter subjects by Demanda Académica for selected period/carrera
        source = self.data if self.is_bound else self.initial
        demanda_periodo = source.get('id_periodo')
        if demanda_periodo:
            demanda_carrera = source.get('id_carrera')
            demanda_filter = {'id_periodo_id': demanda_periodo.pk if hasattr(demanda_periodo, 'pk') else demanda_periodo}
            if demanda_carrera:
                car_id = demanda_carrera.pk if hasattr(demanda_carrera, 'pk') else demanda_carrera
                demanda_filter['id_carrera_id'] = car_id
            demanda_ids = list(PlanificacionDemandaAcademica.objects.filter(**demanda_filter).values_list('id_asignatura_id', flat=True))
            if demanda_ids:
                subjects = subjects.filter(id_asignatura__in=demanda_ids)
            else:
                subjects = subjects.none()
        else:
            subjects = subjects.none()
        self.fields['id_asignatura'].queryset = subjects.order_by(
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
            source = self.data if self.is_bound else self.initial
            raw_subj = source.get('id_asignatura')
            carr_id = source.get('id_carrera')
            per_id = source.get('id_periodo')
            subj_id = raw_subj.pk if hasattr(raw_subj, 'pk') else raw_subj
            carr_id_v = carr_id.pk if hasattr(carr_id, 'pk') else carr_id
            per_id_v = per_id.pk if hasattr(per_id, 'pk') else per_id
            try:
                if subj_id:
                    asignatura = CurriculoAsignatura.objects.get(pk=subj_id)
                if carr_id_v:
                    carrera = CatalogoCarrera.objects.get(pk=carr_id_v)
                elif asignatura:
                    carrera = asignatura.id_carrera
                if per_id_v:
                    periodo = CatalogoPeriodoAcademico.objects.get(pk=per_id_v)
                es_actividad = (
                    getattr(asignatura, 'es_actividad', False)
                    or getattr(carrera, 'es_actividad', False)
                )
            except (
                CurriculoAsignatura.DoesNotExist,
                CatalogoCarrera.DoesNotExist,
                CatalogoPeriodoAcademico.DoesNotExist,
            ):
                pass
            paralelo_actual = source.get('paralelo_asignado', '')

        if asignatura:
            campos_qs = (
                CurriculoAsignaturaCampo.objects
                .filter(id_asignatura=asignatura)
                .select_related('id_campo')
                .order_by('id_asignatura_campo')
            )
            if campos_qs:
                nombres = [str(rel.id_campo) for rel in campos_qs]
                self.fields['id_campo'].initial = campos_qs[0].id_campo_id
                self.fields['campo_conocimiento'].initial = ' · '.join(nombres)

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
        requiere_afinidad = cleaned.get('requiere_afinidad') or 'AUTO'

        es_actividad = False
        if asignatura:
            es_actividad = asignatura.es_actividad
        if carrera and not es_actividad:
            es_actividad = carrera.es_actividad

        if asignatura and not es_actividad:
            campo_rel = (
                CurriculoAsignaturaCampo.objects
                .filter(id_asignatura=asignatura)
                .select_related('id_campo')
                .order_by('id_asignatura_campo')
                .first()
            )
            if campo_rel:
                campo = campo_rel.id_campo
                cleaned['id_campo'] = campo
                cleaned['campo_conocimiento'] = str(campo)
            else:
                self.add_error(
                    'campo_conocimiento',
                    'La asignatura no tiene un campo de conocimiento configurado.',
                )

        if not es_actividad and all((asignatura, carrera, periodo, docente, campo, nivel, paralelo)):
            errors = validate_assignment_business_rules(
                docente=docente,
                asignatura=asignatura,
                carrera=carrera,
                periodo=periodo,
                campo=campo,
                nivel=nivel,
                paralelo=paralelo,
                horas_clase=cleaned.get('horas_clase'),
                instance=self.instance,
            )
            ##if (
                ##requiere_afinidad == 'SI'
                ##and nivel < 4
              ##  and not docente_tiene_afinidad(docente, asignatura)
            ##):
                ######    'id_docente',
              ########  self.add_error(
                  ####  'Seleccione un docente con afinidad para esta asignatura.',
               ## )
           ## if requiere_afinidad == 'NO' and nivel >= 4:
            ##add_form_errors(self, errors)
              ##  self.add_error(
                 ####   'requiere_afinidad',
                ##    'Desde cuarto nivel la afinidad no puede desactivarse.',
              ##  )
            return cleaned

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
            if requiere_afinidad != 'NO' and not docente_tiene_afinidad(docente, asignatura):
                self.add_error(
                    'id_docente',
                    'Desde cuarto nivel solo se permiten docentes con afinidad registrada para la asignatura.',
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


class PlanificacionDemandaAcademicaForm(forms.ModelForm):
    nivel_semestre = forms.ChoiceField(
        label='Nivel',
        choices=[('', '--- Seleccione ---')] + [(str(i), f'Nivel {i}') for i in range(1, 11)],
        required=False,
    )

    class Meta:
        model = PlanificacionDemandaAcademica
        fields = (
            'id_periodo', 'id_carrera',
            'id_asignatura',
            'proyeccion_estudiantes', 'numero_paralelos',
        )
        widgets = {
            'proyeccion_estudiantes': forms.NumberInput(attrs={'min': 0}),
            'numero_paralelos': forms.NumberInput(attrs={'min': 1}),
        }
        labels = {
            'proyeccion_estudiantes': 'Estudiantes proyectados',
            'numero_paralelos': 'Número de paralelos',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['id_asignatura'].queryset = CurriculoAsignatura.objects.filter(
            es_actividad=False
        ).select_related('id_carrera').order_by(
            'id_carrera__nombre_carrera', 'nivel_semestre', 'nombre_asignatura'
        )
        if not self.is_bound and not self.instance.pk:
            active_period = CatalogoPeriodoAcademico.objects.filter(
                periodo_activo=True
            ).first()
            if active_period:
                self.fields['id_periodo'].initial = active_period

        # Move nivel_semestre so it renders after id_carrera
        nivel_key = 'nivel_semestre'
        self.fields[nivel_key] = self.fields.pop(nivel_key)
        order = ['id_periodo', 'id_carrera', nivel_key, 'id_asignatura', 'proyeccion_estudiantes', 'numero_paralelos']
        self.order_fields(order)

        # Pre-populate nivel_semestre from instance's subject when editing
        if self.instance.pk and self.instance.id_asignatura_id:
            self.fields[nivel_key].initial = str(self.instance.id_asignatura.nivel_semestre)

        for field in self.fields.values():
            field.widget.attrs['class'] = (
                'form-select' if isinstance(field.widget, forms.Select) else 'form-control'
            )

        # Filter subjects when bound
        if self.is_bound:
            carrera_id = self.data.get('id_carrera')
            nivel = self.data.get('nivel_semestre')
            qs = self.fields['id_asignatura'].queryset
            if carrera_id:
                qs = qs.filter(id_carrera_id=carrera_id)
            if nivel:
                qs = qs.filter(nivel_semestre=nivel)
            self.fields['id_asignatura'].queryset = qs

    def clean(self):
        cleaned = super().clean()
        subject = cleaned.get('id_asignatura')
        career = cleaned.get('id_carrera')
        nivel = cleaned.get('nivel_semestre')
        projected = cleaned.get('proyeccion_estudiantes')
        parallels = cleaned.get('numero_paralelos')

        if nivel and not nivel.isdigit():
            self.add_error('nivel_semestre', 'Seleccione un nivel válido.')
            return cleaned

        if subject:
            if career and subject.id_carrera_id != career.id_carrera:
                self.add_error(
                    'id_asignatura',
                    'La asignatura no pertenece a la carrera seleccionada.',
                )
            if nivel and int(nivel) != subject.nivel_semestre:
                self.add_error(
                    'id_asignatura',
                    f'La asignatura pertenece al nivel {subject.nivel_semestre}, no al nivel seleccionado.',
                )
        if projected is not None and projected < 0:
            self.add_error(
                'proyeccion_estudiantes',
                'La proyección de estudiantes no puede ser negativa.',
            )
        if parallels is not None and parallels < 1:
            self.add_error(
                'numero_paralelos',
                'Debe existir al menos un paralelo.',
            )
        return cleaned


class PlanificacionCapacidadEspecialForm(forms.ModelForm):
    class Meta:
        model = PlanificacionCapacidadEspecial
        fields = (
            'id_periodo', 'id_carrera', 'estudiante_nombre', 'condicion',
            'nivel_asignado', 'paralelo_asignado', 'informes_adjuntos',
        )
        labels = {
            'estudiante_nombre': 'Nombres completos del estudiante',
            'condicion': 'Condición o necesidad educativa',
            'nivel_asignado': 'Nivel',
            'paralelo_asignado': 'Paralelo',
            'informes_adjuntos': 'Informes o referencias',
        }
        help_texts = {
            'condicion': 'Registre únicamente la información necesaria para la planificación académica.',
            'informes_adjuntos': (
                'Indique el nombre, código o ubicación institucional del informe. '
                'No incluya información médica innecesaria.'
            ),
        }
        widgets = {
            'condicion': forms.Textarea(attrs={'rows': 3}),
            'informes_adjuntos': forms.Textarea(attrs={'rows': 3}),
            'paralelo_asignado': forms.TextInput(attrs={
                'maxlength': 3,
                'data-uppercase': 'true',
                'placeholder': 'Ej. A',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        current_period_id = self.instance.id_periodo_id if self.instance.pk else None
        editable_periods = Q(estado_planificacion__in=('BORRADOR', 'EN_REVISION'))
        if current_period_id:
            editable_periods |= Q(pk=current_period_id)
        self.fields['id_periodo'].queryset = CatalogoPeriodoAcademico.objects.filter(
            editable_periods
        ).order_by('-fecha_inicio_periodo', '-id_periodo')
        self.fields['id_carrera'].queryset = self.fields['id_carrera'].queryset.filter(
            carrera_activa=True
        ).order_by('nombre_carrera')
        if not self.is_bound and not self.instance.pk:
            active_period = self.fields['id_periodo'].queryset.filter(
                periodo_activo=True
            ).first()
            if active_period:
                self.fields['id_periodo'].initial = active_period

        current_level = (self.instance.nivel_asignado or '').strip() if self.instance.pk else ''
        level_choices = [('', 'Sin especificar')] + [
            (str(level), f'Nivel {level}') for level in range(1, 11)
        ]
        if current_level and current_level not in dict(level_choices):
            level_choices.append((current_level, current_level))
        self.fields['nivel_asignado'].widget = forms.Select(choices=level_choices)

    def clean_estudiante_nombre(self):
        return ' '.join((self.cleaned_data.get('estudiante_nombre') or '').split())

    def clean_paralelo_asignado(self):
        value = (self.cleaned_data.get('paralelo_asignado') or '').strip().upper()
        if value and not re.fullmatch(r'[A-Z]{1,3}', value):
            raise ValidationError('El paralelo debe contener entre 1 y 3 letras.')
        return value


class PlanificacionActividadDocenteForm(forms.ModelForm):
    class Meta:
        model = PlanificacionActividadDocente
        fields = ['id_periodo', 'id_docente', 'id_actividad', 'horas_asignadas', 'observaciones']
        widgets = {'observaciones': forms.Textarea(attrs={'rows': 3})}
        labels = {
            'horas_asignadas': 'Horas semanales',
            'observaciones': 'Observaciones',
        }

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
        workload = build_docente_workload_map(
            periodo_id=periodo.id_periodo
        ).get(docente.id_docente, {})
        actual_total = workload.get('total_horas', 0) or 0
        if self.instance.pk:
            actual_total -= self.instance.horas_asignadas or 0
        nuevo_total = actual_total + horas
        maximo_total = (limite.horas_maximas or 0) + (limite.horas_complementarias_maximas or 0)
        if nuevo_total > maximo_total:
            self.add_error(
                'horas_asignadas',
                f'La carga total sería {nuevo_total}h y supera el límite contractual de {maximo_total}h.',
            )
        return cleaned


class PlanificacionAulaHorarioForm(forms.ModelForm):
    turno_horario = forms.ChoiceField(choices=(
        ('MANANA', 'Mañana'), ('TARDE', 'Tarde'), ('NOCHE', 'Noche'),
    ))

    class Meta:
        model = PlanificacionAulaHorario
        fields = (
            'id_periodo', 'id_asignacion', 'dia_semana',
            'hora_inicio', 'hora_fin', 'turno_horario',
            'nombre_aula', 'nivel_asignado',
        )
        widgets = {
            'hora_inicio': forms.TimeInput(attrs={'type': 'time'}),
            'hora_fin': forms.TimeInput(attrs={'type': 'time'}),
        }
        labels = {
            'id_asignacion': 'Asignatura, paralelo y docente',
            'dia_semana': 'Día',
            'hora_inicio': 'Hora de inicio',
            'hora_fin': 'Hora de finalización',
            'turno_horario': 'Jornada',
            'nombre_aula': 'Aula o espacio',
            'nivel_asignado': 'Nivel',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        periodo_id = self.data.get('id_periodo') or getattr(self.instance, 'id_periodo_id', None)
        asignaciones = PlanificacionAsignacionDocente.objects.select_related(
            'id_docente', 'id_asignatura', 'id_carrera',
        ).order_by('id_carrera__nombre_carrera', 'id_asignatura__nombre_asignatura', 'paralelo_asignado')
        if periodo_id:
            asignaciones = asignaciones.filter(id_periodo_id=periodo_id)
        self.fields['id_asignacion'].queryset = asignaciones
        self.fields['id_asignacion'].label_from_instance = lambda item: (
            f'{item.id_docente.nombres_completos} → '
            f'{item.id_asignatura.codigo_asignatura} - '
            f'{item.id_asignatura.nombre_asignatura} '
            f'({item.paralelo_asignado} · {item.id_periodo.nombre_periodo})'
        )
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-select' if isinstance(field.widget, forms.Select) else 'form-control'
