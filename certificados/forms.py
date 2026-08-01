from django import forms
from django.utils import timezone

from catalogos.models import CatalogoPeriodoAcademico
from docentes.models import DocenteFcacc

from .models import CertificadoEmitido, FirmanteCertificado
from .services import FUNCTION_FILTERS, docentes_con_datos, normalize_function_filter


class GenerarCertificadoForm(forms.Form):
    tipo = forms.ChoiceField(choices=CertificadoEmitido.TIPOS, label='Tipo de certificado')
    filtro_funciones = forms.ChoiceField(
        choices=FUNCTION_FILTERS,
        label='Contenido de funciones y comisiones',
        initial='TODOS',
        required=False,
        help_text='Este filtro se aplica únicamente al certificado de funciones y comisiones.',
    )
    periodo = forms.ModelChoiceField(
        queryset=CatalogoPeriodoAcademico.objects.none(),
        label='Período académico',
        required=False,
        help_text='Opcional. Si se selecciona, el certificado incluirá únicamente la información de ese período.',
    )
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

    def __init__(self, *args, allowed_career_ids=None, **kwargs):
        super().__init__(*args, **kwargs)
        selected_tipo = (self.data.get('tipo') if self.data else None) or self.initial.get('tipo')
        selected_filtro = (self.data.get('filtro_funciones') if self.data else None) or self.initial.get('filtro_funciones')
        periodo_pk = (self.data.get('periodo') if self.data else None) or self.initial.get('periodo')
        periodo = None
        if periodo_pk:
            try:
                periodo = CatalogoPeriodoAcademico.objects.get(pk=periodo_pk)
            except (CatalogoPeriodoAcademico.DoesNotExist, ValueError):
                periodo = None
        self.fields['periodo'].queryset = CatalogoPeriodoAcademico.objects.all().order_by(
            '-fecha_inicio_periodo', '-codigo_periodo'
        )
        docentes_qs = DocenteFcacc.objects.select_related('id_dedicacion')
        if selected_tipo:
            docentes_qs = docentes_con_datos(selected_tipo, selected_filtro, periodo)
        if allowed_career_ids is not None:
            docentes_qs = docentes_qs.filter(
                docenteasignacioncarreraperiodo__id_carrera_id__in=allowed_career_ids
            ).distinct()
        self.fields['docente'].queryset = docentes_qs.order_by('nombres_completos')
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
        self.fields['periodo'].widget.attrs.update({'data-searchable-select': 'true'})

    def clean(self):
        cleaned = super().clean()
        cleaned['filtro_funciones'] = (
            normalize_function_filter(cleaned.get('filtro_funciones'))
            if cleaned.get('tipo') == 'FUNCIONES'
            else 'TODOS'
        )
        return cleaned


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
