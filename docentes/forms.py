import re

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import DocenteFcacc


class DocenteFcaccForm(forms.ModelForm):
    class Meta:
        model = DocenteFcacc
        fields = (
            'tipo_documento', 'cedula_docente', 'nombres_completos',
            'fecha_nacimiento', 'tipo_sangre', 'numero_celular',
            'correo_institucional', 'foto', 'id_tipo_docente', 'id_modalidad',
            'id_dedicacion', 'unidad_organica', 'docente_activo',
        )
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date'}),
            'foto': forms.ClearableFileInput(attrs={'accept': 'image/*'}),
            'cedula_docente': forms.TextInput(attrs={
                'maxlength': '13', 'inputmode': 'numeric', 'autocomplete': 'off',
            }),
            'numero_celular': forms.TextInput(attrs={'maxlength': '15', 'inputmode': 'tel'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-check-input'
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = 'form-select'
            else:
                field.widget.attrs['class'] = 'form-control'
        self.fields['tipo_sangre'].empty_label = 'Seleccione el tipo de sangre'
        self.fields['fecha_nacimiento'].required = False
        self.fields['foto'].required = False

    def clean_cedula_docente(self):
        value = re.sub(r'\s+', '', self.cleaned_data['cedula_docente']).upper()
        tipo = self.cleaned_data.get('tipo_documento')
        if tipo == 'CEDULA' and re.fullmatch(r'\d{9}', value):
            value = '0' + value
        if tipo == 'CEDULA' and not re.fullmatch(r'\d{10}', value):
            raise ValidationError('La cédula debe contener exactamente 10 dígitos.')
        if tipo == 'RUC' and not re.fullmatch(r'\d{13}', value):
            raise ValidationError('El RUC debe contener exactamente 13 dígitos.')
        if tipo == 'PASAPORTE' and not re.fullmatch(r'[A-Z0-9]{5,13}', value):
            raise ValidationError('El pasaporte debe tener entre 5 y 13 letras o números.')
        return value

    def clean_numero_celular(self):
        value = re.sub(r'[\s-]+', '', self.cleaned_data.get('numero_celular') or '')
        if value and not re.fullmatch(r'\+?\d{7,15}', value):
            raise ValidationError('Ingrese un teléfono válido de 7 a 15 dígitos.')
        return value or None

    def clean_fecha_nacimiento(self):
        value = self.cleaned_data.get('fecha_nacimiento')
        if value and value >= timezone.localdate():
            raise ValidationError('La fecha de nacimiento debe ser anterior a hoy.')
        return value

    def clean_foto(self):
        image = self.cleaned_data.get('foto')
        if image and getattr(image, 'size', 0) > 5 * 1024 * 1024:
            raise ValidationError('La fotografía no puede superar 5 MB.')
        return image
