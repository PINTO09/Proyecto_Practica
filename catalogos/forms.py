from django import forms
from django.db import transaction

from .models import CatalogoModalidadContratacion, CatalogoPeriodoAcademico, LimiteHorario


class CatalogoPeriodoAcademicoForm(forms.ModelForm):
    class Meta:
        model = CatalogoPeriodoAcademico
        fields = (
            'codigo_periodo', 'nombre_periodo',
            'fecha_inicio_periodo', 'fecha_fin_periodo', 'periodo_activo',
        )
        widgets = {
            'fecha_inicio_periodo': forms.DateInput(attrs={'type': 'date'}),
            'fecha_fin_periodo': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean(self):
        cleaned = super().clean()
        inicio = cleaned.get('fecha_inicio_periodo')
        fin = cleaned.get('fecha_fin_periodo')
        if inicio and fin and fin < inicio:
            self.add_error(
                'fecha_fin_periodo',
                'La fecha final debe ser posterior a la fecha de inicio.',
            )
        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=commit)
        if commit and instance.periodo_activo:
            CatalogoPeriodoAcademico.objects.exclude(pk=instance.pk).update(
                periodo_activo=False
            )
        return instance


class ModalidadContratacionForm(forms.ModelForm):
    horas_maximas = forms.IntegerField(label='Horas máximas de clase', min_value=0)
    horas_complementarias_maximas = forms.IntegerField(
        label='Horas máximas complementarias', min_value=0, initial=0,
    )

    class Meta:
        model = CatalogoModalidadContratacion
        fields = ('codigo_modalidad', 'nombre_modalidad')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['codigo_modalidad'].required = False
        self.fields['codigo_modalidad'].help_text = 'Opcional: se genera automáticamente.'
        if self.instance and self.instance.pk:
            limite = LimiteHorario.objects.filter(id_modalidad=self.instance).first()
            if limite:
                self.fields['horas_maximas'].initial = limite.horas_maximas
                self.fields['horas_complementarias_maximas'].initial = limite.horas_complementarias_maximas
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

    @transaction.atomic
    def save(self, commit=True):
        instance = super().save(commit=commit)
        if commit:
            LimiteHorario.objects.update_or_create(
                id_modalidad=instance,
                defaults={
                    'horas_maximas': self.cleaned_data['horas_maximas'],
                    'horas_complementarias_maximas': self.cleaned_data['horas_complementarias_maximas'],
                    'activo': True,
                },
            )
        return instance
