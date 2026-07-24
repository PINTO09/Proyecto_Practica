from django import forms
from .models import CurriculoAsignatura, CurriculoAsignaturaCampo
from catalogos.models import CatalogoCampoConocimiento, CatalogoCarrera


class CurriculoAsignaturaForm(forms.ModelForm):
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
            'campos_conocimiento',
        )
        widgets = {
            'nivel_semestre': forms.Select(choices=[('', '--- Seleccione ---')] + [(i, f'Nivel {i}') for i in range(1, 11)]),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
            self.fields['nivel_semestre'].widget.attrs['disabled'] = True
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
            cleaned['campos_conocimiento'] = (
                CatalogoCampoConocimiento.objects.none()
            )
        elif not cleaned.get('campos_conocimiento'):
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
