from django import forms
from django.db import transaction

from .models import CatalogoModalidadContratacion, LimiteHorario


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
