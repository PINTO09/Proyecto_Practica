from django import forms
from .models import CurriculoAsignatura, CurriculoAsignaturaCampo
from catalogos.models import CatalogoCampoConocimiento, CatalogoCarrera


class CurriculoAsignaturaForm(forms.ModelForm):
    modalidad_espacio = forms.ChoiceField(
        label='Uso de espacios',
        choices=(
            ('SOLO_AULA', 'Únicamente aula de clases'),
            (
                'AULA_CENTRO',
                'Aula de clases y centro de cómputo',
            ),
            (
                'SOLO_CENTRO',
                'Únicamente centro de cómputo',
            ),
        ),
        initial='SOLO_AULA',
        help_text=(
            'Seleccione si todas las horas se imparten en aula o si una parte '
            'requiere un centro de cómputo.'
        ),
    )
    campos_conocimiento = forms.ModelMultipleChoiceField(
        label='Campos de conocimiento',
        queryset=CatalogoCampoConocimiento.objects.none(),
        required=False,
        help_text=(
            'Seleccione al menos un campo para que el sistema pueda calcular '
            'la afinidad y completar automáticamente las asignaciones.'
        ),
        widget=forms.SelectMultiple(attrs={'size': 6}),
    )

    class Meta:
        model = CurriculoAsignatura
        fields = (
            'id_carrera', 'codigo_asignatura', 'nombre_asignatura',
            'es_actividad', 'nivel_semestre', 'horas_semanales_asignatura',
            'modalidad_espacio',
            'horas_aula', 'horas_centro_computo',
            'campos_conocimiento',
        )
        widgets = {
            'nivel_semestre': forms.Select(choices=[('', '--- Seleccione ---')] + [(i, f'Nivel {i}') for i in range(1, 11)]),
            'horas_aula': forms.NumberInput(attrs={'min': 0, 'step': '0.25'}),
            'horas_centro_computo': forms.NumberInput(attrs={'min': 0, 'step': '0.25'}),
        }
        labels = {
            'horas_aula': 'Horas semanales en aula',
            'horas_centro_computo': 'Horas semanales en centro de cómputo',
        }
        help_texts = {
            'horas_aula': 'La suma debe coincidir con las horas semanales de la asignatura.',
            'horas_centro_computo': 'Horas que requieren equipos del centro de cómputo.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        bound_activity = self.is_bound and str(
            self.data.get('es_actividad', '')
        ).lower() in ('1', 'true', 'on', 'yes')
        if bound_activity:
            self.fields['nivel_semestre'].required = False
            self.fields['modalidad_espacio'].required = False
            self.fields['horas_aula'].required = False
            self.fields['horas_centro_computo'].required = False
        self.fields['id_carrera'].queryset = CatalogoCarrera.objects.all().order_by('nombre_carrera')
        self.fields['campos_conocimiento'].queryset = (
            CatalogoCampoConocimiento.objects.order_by(
                'nombre_campo_conocimiento'
            )
        )
        self.fields['id_carrera'].label_from_instance = lambda obj: f"{'[ACT] ' if obj.es_actividad else ''}{obj.codigo_carrera} - {obj.nombre_carrera}"
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-check-input'
            else:
                field.widget.attrs['class'] = 'form-select' if isinstance(field.widget, forms.Select) else 'form-control'
        if self.instance.pk and self.instance.es_actividad:
            self.fields['nivel_semestre'].required = False
            self.fields['modalidad_espacio'].required = False
            self.fields['horas_aula'].required = False
            self.fields['horas_centro_computo'].required = False
            self.fields['nivel_semestre'].widget.attrs['disabled'] = True
        if self.instance.pk and not self.is_bound:
            if self.instance.horas_centro_computo <= 0:
                modalidad_inicial = 'SOLO_AULA'
            elif self.instance.horas_aula <= 0:
                modalidad_inicial = 'SOLO_CENTRO'
            else:
                modalidad_inicial = 'AULA_CENTRO'
            self.fields['modalidad_espacio'].initial = modalidad_inicial
        if self.instance.pk:
            self.fields['campos_conocimiento'].initial = (
                CurriculoAsignaturaCampo.objects.filter(
                    id_asignatura=self.instance
                ).values_list('id_campo_id', flat=True)
            )

    def clean(self):
        cleaned = super().clean()
        es_actividad = cleaned.get('es_actividad', False)
        carrera = cleaned.get('id_carrera')
        if carrera and carrera.es_actividad:
            es_actividad = True
            cleaned['es_actividad'] = True
        if es_actividad:
            cleaned['nivel_semestre'] = 0
            cleaned['horas_aula'] = cleaned.get('horas_semanales_asignatura') or 0
            cleaned['horas_centro_computo'] = 0
            cleaned['campos_conocimiento'] = (
                CatalogoCampoConocimiento.objects.none()
            )
        else:
            modalidad = cleaned.get('modalidad_espacio')
            total = cleaned.get('horas_semanales_asignatura')
            aula = cleaned.get('horas_aula')
            centro = cleaned.get('horas_centro_computo')
            if modalidad == 'SOLO_AULA':
                aula = total or 0
                centro = 0
                cleaned['horas_aula'] = aula
                cleaned['horas_centro_computo'] = centro
            elif modalidad == 'SOLO_CENTRO':
                aula = 0
                centro = total or 0
                cleaned['horas_aula'] = aula
                cleaned['horas_centro_computo'] = centro
            elif modalidad == 'AULA_CENTRO' and (
                aula is None or centro is None
                or aula <= 0 or centro <= 0
                or total is None or aula + centro != total
            ):
                raise forms.ValidationError(
                    'Para usar aula y centro de cómputo, ambas cantidades '
                    'deben ser mayores que 0 y sumar las horas semanales.'
                )
            if not cleaned.get('campos_conocimiento'):
                self.add_error(
                    'campos_conocimiento',
                    'Seleccione al menos un campo de conocimiento.',
                )
        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=commit)
        if commit:
            selected_ids = set(
                self.cleaned_data.get(
                    'campos_conocimiento',
                    CatalogoCampoConocimiento.objects.none(),
                ).values_list('id_campo', flat=True)
            )
            current = CurriculoAsignaturaCampo.objects.filter(
                id_asignatura=instance
            )
            current.exclude(id_campo_id__in=selected_ids).delete()
            existing_ids = set(
                current.values_list('id_campo_id', flat=True)
            )
            CurriculoAsignaturaCampo.objects.bulk_create([
                CurriculoAsignaturaCampo(
                    id_asignatura=instance,
                    id_campo_id=field_id,
                )
                for field_id in selected_ids - existing_ids
            ])
        return instance
