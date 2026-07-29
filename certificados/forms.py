from django import forms
from django.utils import timezone

from docentes.models import DocenteFcacc

from .models import CertificadoEmitido, FirmanteCertificado


class GenerarCertificadoForm(forms.Form):
    tipo = forms.ChoiceField(choices=CertificadoEmitido.TIPOS, label='Tipo de certificado')
    docente = forms.ModelChoiceField(
        queryset=DocenteFcacc.objects.none(), label='Docente',
    )
    firmante = forms.ModelChoiceField(
        queryset=FirmanteCertificado.objects.none(), label='Firmante',
    )
    fecha_emision = forms.DateField(
        initial=timezone.localdate, label='Fecha de emisión',
        widget=forms.DateInput(attrs={'type': 'date'}),
    )
    ciudad = forms.CharField(initial='Manta', max_length=80)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['docente'].queryset = DocenteFcacc.objects.select_related(
            'id_dedicacion'
        ).order_by('nombres_completos')
        self.fields['firmante'].queryset = FirmanteCertificado.objects.filter(
            activo=True
        ).order_by('orden', 'nombres_completos')
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-select' if isinstance(
                field.widget, forms.Select
            ) else 'form-control'
        self.fields['docente'].widget.attrs.update({
            'data-searchable-select': 'true',
            'data-search-placeholder': 'Buscar docente por nombre o cédula...',
        })


class FirmanteCertificadoForm(forms.ModelForm):
    class Meta:
        model = FirmanteCertificado
        fields = ('nombres_completos', 'cargo', 'activo', 'orden')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = (
                'form-check-input' if isinstance(field.widget, forms.CheckboxInput)
                else 'form-control'
            )
