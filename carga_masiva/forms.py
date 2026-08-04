from django import forms

_VALID_EXTENSIONS = ('.xlsx', '.xls')


class CargaMasivaUploadForm(forms.Form):
    archivo = forms.FileField(
        label='Archivo Excel',
        help_text='Sube cualquiera de los Excel de planificación FCACC (docentes, carreras, '
                   'asignaturas, planificación, etc.). El sistema detecta automáticamente qué '
                   'información trae.',
        widget=forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': '.xlsx,.xls'}),
    )
    periodo_codigo = forms.CharField(
        label='Código del período', max_length=20, initial='2026-2',
        widget=forms.TextInput(attrs={'class': 'form-control', 'data-uppercase': 'false'}),
    )
    periodo_nombre = forms.CharField(
        label='Nombre del período', max_length=100, initial='2026-2',
        widget=forms.TextInput(attrs={'class': 'form-control', 'data-uppercase': 'false'}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from catalogos.models import CatalogoPeriodoAcademico
        activo = CatalogoPeriodoAcademico.objects.filter(periodo_activo=True).first()
        if activo:
            self.fields['periodo_codigo'].initial = activo.codigo_periodo
            self.fields['periodo_nombre'].initial = activo.nombre_periodo

    def clean_archivo(self):
        archivo = self.cleaned_data['archivo']
        if not archivo.name.lower().endswith(_VALID_EXTENSIONS):
            raise forms.ValidationError('El archivo debe ser .xlsx o .xls.')
        return archivo
