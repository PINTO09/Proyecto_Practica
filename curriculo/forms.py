from django import forms
from .models import CurriculoAsignatura
from catalogos.models import CatalogoCarrera


class CurriculoAsignaturaForm(forms.ModelForm):
    class Meta:
        model = CurriculoAsignatura
        fields = '__all__'
        widgets = {
            'nivel_semestre': forms.Select(choices=[('', '--- Seleccione ---')] + [(i, f'Nivel {i}') for i in range(1, 11)]),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['id_carrera'].queryset = CatalogoCarrera.objects.all().order_by('nombre_carrera')
        self.fields['id_carrera'].label_from_instance = lambda obj: f"{'[ACT] ' if obj.es_actividad else ''}{obj.codigo_carrera} - {obj.nombre_carrera}"
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-select' if isinstance(field.widget, forms.Select) else 'form-control'
        if self.instance.pk and self.instance.es_actividad:
            self.fields['nivel_semestre'].required = False
            self.fields['nivel_semestre'].widget.attrs['disabled'] = True

    def clean(self):
        cleaned = super().clean()
        es_actividad = cleaned.get('es_actividad', False)
        carrera = cleaned.get('id_carrera')
        if carrera and carrera.es_actividad:
            es_actividad = True
            cleaned['es_actividad'] = True
        if es_actividad:
            cleaned['nivel_semestre'] = 0
        return cleaned
