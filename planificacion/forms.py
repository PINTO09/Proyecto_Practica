import re
from datetime import timedelta

from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Exists, OuterRef, Q, Sum

from curriculo.models import CurriculoAsignatura, CurriculoAsignaturaCampo
from catalogos.models import LimiteHorario, CatalogoCarrera, CatalogoPeriodoAcademico

from .models import (
    BitacoraUsoLaboratorio, CatalogoEspacioAcademico,
    PlanificacionAsignacionDocente, PlanificacionActividadDocente,
    PlanificacionAulaHorario, PlanificacionCapacidadEspecial,
    PlanificacionDemandaAcademica,
)
from .services import (
    add_form_errors, bloques_entre, build_docente_workload_map, docente_tiene_afinidad,
    generar_bloques_horarios, parallel_labels, sumar_bloques,
    validate_assignment_business_rules,
)


def _parallel_labels(total):
    return parallel_labels(total)


class BitacoraUsoLaboratorioForm(forms.ModelForm):
    origen_planificacion = forms.ChoiceField(
        label='Asignatura o actividad complementaria',
        choices=(),
        help_text='Solo se muestran registros asignados al docente que inició sesión.',
    )

    class Meta:
        model = BitacoraUsoLaboratorio
        fields = (
            'origen_planificacion', 'semana', 'fecha_uso', 'id_espacio',
            'horas_uso', 'actividad_realizada', 'observaciones',
        )
        labels = {
            'semana': 'Semana',
            'fecha_uso': 'Fecha de uso',
            'id_espacio': 'Aula o centro de cómputo',
            'horas_uso': 'Horas utilizadas',
            'actividad_realizada': 'Actividad realizada',
            'observaciones': 'Observaciones',
        }
        widgets = {
            'semana': forms.Select(),
            'fecha_uso': forms.DateInput(attrs={'type': 'date'}),
            'horas_uso': forms.NumberInput(attrs={'min': '0.25', 'step': '0.25'}),
            'actividad_realizada': forms.Textarea(attrs={'rows': 3}),
            'observaciones': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, docente=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.docente = docente
        asignaciones = PlanificacionAsignacionDocente.objects.none()
        actividades = PlanificacionActividadDocente.objects.none()
        if docente:
            assignment_filter = Q(id_periodo__periodo_activo=True)
            activity_filter = Q(id_periodo__periodo_activo=True)
            if self.instance.pk:
                if self.instance.id_asignacion_id:
                    assignment_filter |= Q(pk=self.instance.id_asignacion_id)
                if self.instance.id_actividad_docente_id:
                    activity_filter |= Q(pk=self.instance.id_actividad_docente_id)
            asignaciones = PlanificacionAsignacionDocente.objects.filter(
                assignment_filter,
                id_docente=docente,
                id_asignatura__horas_centro_computo__gt=0,
            ).select_related('id_asignatura', 'id_periodo').order_by(
                '-id_periodo__fecha_inicio_periodo', 'id_asignatura__nombre_asignatura'
            )
            actividades = PlanificacionActividadDocente.objects.filter(
                activity_filter, id_docente=docente
            ).select_related('id_actividad', 'id_periodo').order_by(
                '-id_periodo__fecha_inicio_periodo', 'id_actividad__nombre_actividad'
            )
        choices = [('', '--- Seleccione ---')]
        choices.extend(
            (
                f'ASIGNACION:{item.pk}',
                f'Asignatura · {item.id_asignatura.nombre_asignatura} · '
                f'{item.paralelo_asignado} · {item.id_periodo} · '
                f'{item.id_asignatura.horas_centro_computo} h en centro de cómputo',
            )
            for item in asignaciones
        )
        choices.extend(
            (
                f'ACTIVIDAD:{item.pk}',
                f'Actividad · {item.id_actividad.nombre_actividad} · {item.id_periodo}',
            )
            for item in actividades
        )
        self.fields['origen_planificacion'].choices = choices

        max_weeks = 30
        selected = self.data.get('origen_planificacion') if self.is_bound else None
        if not selected and self.instance.pk:
            selected = (
                f'ASIGNACION:{self.instance.id_asignacion_id}'
                if self.instance.id_asignacion_id
                else f'ACTIVIDAD:{self.instance.id_actividad_docente_id}'
            )
            self.fields['origen_planificacion'].initial = selected
        if selected and selected.startswith('ASIGNACION:'):
            assignment_id = selected.partition(':')[2]
            assignment = asignaciones.filter(pk=assignment_id).first()
            if assignment:
                max_weeks = assignment.semanas_planificadas
        elif selected and selected.startswith('ACTIVIDAD:'):
            activity_id = selected.partition(':')[2]
            activity = actividades.filter(pk=activity_id).first()
            if activity:
                temporary = BitacoraUsoLaboratorio(id_actividad_docente=activity)
                max_weeks = temporary.semanas_disponibles
        origin = assignment if selected and selected.startswith('ASIGNACION:') else (
            activity if selected and selected.startswith('ACTIVIDAD:') else None
        )
        period = origin.id_periodo if origin else None
        week_choices = [('', '--- Seleccione ---')]
        for number in range(1, max_weeks + 1):
            label = f'Semana {number}'
            if period and period.fecha_inicio_periodo:
                start = period.fecha_inicio_periodo + timedelta(days=(number - 1) * 7)
                end = start + timedelta(days=6)
                if period.fecha_fin_periodo:
                    end = min(end, period.fecha_fin_periodo)
                label += f' · {start:%d/%m/%Y} al {end:%d/%m/%Y}'
            week_choices.append((number, label))
        self.fields['semana'].widget.choices = week_choices
        self.fields['horas_uso'].help_text = (
            'Registre las horas realmente utilizadas. El sistema las comparará '
            'con las horas semanales planificadas.'
        )
        spaces = CatalogoEspacioAcademico.objects.filter(
            espacio_activo=True
        )
        if self.instance.pk and self.instance.id_espacio_id:
            spaces = CatalogoEspacioAcademico.objects.filter(
                Q(espacio_activo=True) | Q(pk=self.instance.id_espacio_id)
            )
        self.fields['id_espacio'].queryset = spaces.order_by(
            'tipo_espacio', 'nombre_espacio'
        )
        self.fields['id_espacio'].required = True
        self.fields['id_espacio'].empty_label = '--- Seleccione un espacio registrado ---'
        for field in self.fields.values():
            field.widget.attrs['class'] = (
                'form-select' if isinstance(field.widget, forms.Select) else 'form-control'
            )

    def clean(self):
        cleaned = super().clean()
        selected = cleaned.get('origen_planificacion', '')
        self.instance.id_docente = self.docente
        self.instance.id_asignacion = None
        self.instance.id_actividad_docente = None
        try:
            kind, raw_pk = selected.split(':', 1)
            if kind == 'ASIGNACION':
                self.instance.id_asignacion = PlanificacionAsignacionDocente.objects.get(
                    pk=raw_pk, id_docente=self.docente
                )
                max_weeks = self.instance.id_asignacion.semanas_planificadas
            elif kind == 'ACTIVIDAD':
                self.instance.id_actividad_docente = PlanificacionActividadDocente.objects.get(
                    pk=raw_pk, id_docente=self.docente
                )
                max_weeks = self.instance.semanas_disponibles
            else:
                raise ValueError
        except (ValueError, PlanificacionAsignacionDocente.DoesNotExist,
                PlanificacionActividadDocente.DoesNotExist):
            self.add_error(
                'origen_planificacion',
                'Seleccione una planificación válida asignada a su usuario.',
            )
            return cleaned
        week = cleaned.get('semana')
        if week and week > max_weeks:
            self.add_error('semana', f'Seleccione una semana entre 1 y {max_weeks}.')
        space = cleaned.get('id_espacio')
        if space:
            self.instance.tipo_espacio = space.tipo_espacio
            self.instance.nombre_espacio = space.nombre_espacio
        return cleaned


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
    carrera = forms.ModelChoiceField(
        queryset=CatalogoCarrera.objects.filter(carrera_activa=True),
        label='Carrera',
        required=True,
        empty_label='Seleccione la carrera',
        help_text='Filtro inicial: las opciones de nivel y asignatura se adaptan a la carrera.',
    )
    nivel_asignado = forms.ChoiceField(
        label='Nivel',
        required=False,
        choices=[('', 'Seleccione el nivel')],
        help_text='Se adapta a la carrera seleccionada.',
    )
    id_asignatura = forms.ModelChoiceField(
        queryset=CurriculoAsignatura.objects.none(),
        label='Asignatura',
        required=False,
        empty_label='Seleccione la asignatura',
        help_text='Solo se listan asignaturas con docente asignado para la carrera y el nivel elegidos en el período.',
    )
    nombre_aula = forms.ChoiceField(
        label='Aula o espacio',
        required=True,
        help_text='Seleccione un espacio del catálogo de espacios académicos.',
    )
    docente = forms.CharField(
        label='Docente asignado',
        required=False,
        disabled=True,
        widget=forms.TextInput(attrs={'readonly': True, 'placeholder': 'Se cargará automáticamente'}),
    )
    horas_bloques = forms.IntegerField(
        label='Cantidad de horas (cada hora = bloque de 45 minutos)',
        min_value=1,
        max_value=10,
        initial=2,
        help_text='Defina cuántos bloques de 45 minutos dura la clase.',
    )

    class Meta:
        model = PlanificacionAulaHorario
        fields = (
            'id_periodo', 'id_asignacion', 'dia_semana',
            'hora_inicio', 'hora_fin', 'turno_horario',
            'nombre_aula', 'nivel_asignado',
        )
        widgets = {
            'hora_inicio': forms.Select(choices=generar_bloques_horarios()),
            'hora_fin': forms.TimeInput(
                attrs={'type': 'time', 'readonly': 'readonly', 'tabindex': '-1'}
            ),
            'id_asignacion': forms.HiddenInput(),
        }
        labels = {
            'id_asignacion': 'Asignación',
            'dia_semana': 'Día',
            'hora_inicio': 'Hora de inicio (bloque de 45 min)',
            'hora_fin': 'Hora de finalización (calculada)',
            'turno_horario': 'Jornada',
            'nombre_aula': 'Aula o espacio',
            'nivel_asignado': 'Nivel',
        }
        help_texts = {
            'hora_inicio': 'Solo bloques de 45 minutos configurados en la jornada.',
            'hora_fin': 'Se calcula automáticamente según la hora de inicio y los bloques seleccionados.',
        }

    def __init__(self, *args, allowed_career_ids=None, **kwargs):
        super().__init__(*args, **kwargs)
        editable_periods = Q(estado_planificacion__in=('BORRADOR', 'EN_REVISION'))
        if self.instance.pk and self.instance.id_periodo_id:
            editable_periods |= Q(pk=self.instance.id_periodo_id)
        self.fields['id_periodo'].queryset = CatalogoPeriodoAcademico.objects.filter(
            editable_periods
        ).order_by('-fecha_inicio_periodo', '-id_periodo')

        periodo_id = self.data.get('id_periodo') or getattr(self.instance, 'id_periodo_id', None)

        asignaciones = PlanificacionAsignacionDocente.objects.select_related(
            'id_docente', 'id_asignatura', 'id_carrera',
        ).order_by('id_carrera__nombre_carrera', 'id_asignatura__nombre_asignatura', 'paralelo_asignado')
        if periodo_id:
            asignaciones = asignaciones.filter(id_periodo_id=periodo_id)
        if allowed_career_ids is not None:
            asignaciones = asignaciones.filter(id_carrera_id__in=allowed_career_ids)
        self.fields['id_asignacion'].queryset = asignaciones

        # Carrera y nivel efectivos según el estado del formulario (POST o instancia)
        editing = bool(self.instance.pk)
        carrera_id = (self.data.get('carrera') or '').strip()
        nivel = (self.data.get('nivel_asignado') or '').strip()
        if not carrera_id and editing and self.instance.id_asignacion_id:
            carrera_id = str(self.instance.id_asignacion.id_carrera_id)
        if not carrera_id and self.fields['carrera'].initial:
            carrera_id = str(self.fields['carrera'].initial)
        if not nivel and editing and self.instance.nivel_asignado:
            nivel = str(self.instance.nivel_asignado)

        # Niveles disponibles para la carrera (con docente asignado en el período)
        if carrera_id:
            niveles_qs = PlanificacionAsignacionDocente.objects.filter(id_carrera_id=carrera_id)
            if periodo_id:
                niveles_qs = niveles_qs.filter(id_periodo_id=periodo_id)
            if allowed_career_ids is not None:
                niveles_qs = niveles_qs.filter(id_carrera_id__in=allowed_career_ids)
            niveles = list(
                niveles_qs.filter(nivel_semestre_asignado__gt=0)
                .values_list('nivel_semestre_asignado', flat=True)
                .distinct().order_by('nivel_semestre_asignado')
            )
            opciones = [('', 'Seleccione el nivel')] + [(str(n), f'Nivel {n}') for n in niveles]
        else:
            opciones = [('', 'Seleccione el nivel')]
        if nivel and not any(value == nivel for value, _ in opciones):
            opciones.append((nivel, f'Nivel {nivel}'))
        self.fields['nivel_asignado'].choices = opciones

        # Asignaturas con docente asignado en período, carrera y nivel
        con_docente = PlanificacionAsignacionDocente.objects.filter(
            id_asignatura=OuterRef('pk')
        )
        if periodo_id:
            con_docente = con_docente.filter(id_periodo_id=periodo_id)
        if allowed_career_ids is not None:
            con_docente = con_docente.filter(id_carrera_id__in=allowed_career_ids)
        if carrera_id:
            con_docente = con_docente.filter(id_carrera_id=carrera_id)
        if nivel:
            con_docente = con_docente.filter(nivel_semestre_asignado=nivel)
        if carrera_id or nivel:
            asignaturas = CurriculoAsignatura.objects.filter(Exists(con_docente)).select_related(
                'id_carrera'
            ).order_by('id_carrera__nombre_carrera', 'nombre_asignatura')
        else:
            asignaturas = CurriculoAsignatura.objects.none()
        self.fields['id_asignatura'].queryset = asignaturas

        self.order_fields([
            'id_periodo', 'carrera', 'nivel_asignado', 'id_asignatura', 'nombre_aula', 'docente',
            'dia_semana', 'hora_inicio', 'horas_bloques', 'hora_fin',
            'turno_horario', 'id_asignacion',
        ])

        if self.instance.pk:
            asignacion = getattr(self.instance, 'id_asignacion', None)
            if asignacion:
                self.fields['id_asignatura'].initial = asignacion.id_asignatura_id
                self.fields['carrera'].initial = asignacion.id_carrera_id
                self.fields['nivel_asignado'].initial = str(asignacion.nivel_semestre_asignado)
                self.fields['docente'].initial = asignacion.id_docente.nombres_completos
            if self.instance.hora_inicio and self.instance.hora_fin:
                bloques = bloques_entre(self.instance.hora_inicio, self.instance.hora_fin)
                if bloques is not None:
                    self.fields['horas_bloques'].initial = bloques

    def clean(self):
        cleaned = super().clean()
        hora_inicio = cleaned.get('hora_inicio')
        horas_bloques = cleaned.get('horas_bloques')
        id_asignatura = cleaned.get('id_asignatura')
        id_asignacion = cleaned.get('id_asignacion')
        periodo = cleaned.get('id_periodo')
        carrera = cleaned.get('carrera')
        nivel = cleaned.get('nivel_asignado')

        if hora_inicio and horas_bloques:
            try:
                cleaned['hora_fin'] = sumar_bloques(hora_inicio, horas_bloques)
            except ValueError:
                self.add_error('horas_bloques', 'Indique una cantidad de horas válida.')

        hora_fin = cleaned.get('hora_fin')
        if hora_inicio and hora_fin and hora_fin <= hora_inicio:
            self.add_error('hora_fin', 'La hora final calculada debe ser posterior a la inicial.')

        if id_asignatura:
            if not carrera:
                self.add_error('carrera', 'Seleccione la carrera antes de elegir la asignatura.')
            if not nivel:
                self.add_error('nivel_asignado', 'Seleccione el nivel antes de elegir la asignatura.')

        if id_asignacion:
            if carrera and id_asignacion.id_carrera_id != carrera.id_carrera:
                self.add_error('carrera', 'La asignación no pertenece a la carrera seleccionada.')
            elif nivel and str(id_asignacion.nivel_semestre_asignado) != str(nivel):
                self.add_error(
                    'nivel_asignado',
                    'El nivel de la asignación no coincide con el nivel seleccionado.',
                )
            elif id_asignatura and id_asignacion.id_asignatura_id != id_asignatura.id_asignatura:
                self.add_error('id_asignatura', 'La asignación no corresponde a la asignatura seleccionada.')
            elif periodo and id_asignacion.id_periodo_id != periodo.id_periodo:
                self.add_error('id_asignatura', 'La asignación pertenece a otro período académico.')
            else:
                cleaned['nivel_asignado'] = str(id_asignacion.nivel_semestre_asignado)
        elif id_asignatura:
            self.add_error(
                'id_asignatura',
                'La asignatura seleccionada no tiene un docente asignado en el período seleccionado.',
            )
        return cleaned
