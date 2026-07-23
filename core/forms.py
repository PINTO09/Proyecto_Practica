import re

from django import forms
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.forms import SetPasswordForm
from .models import (
    Docente, Titulo, Publicacion, DocenteTransaccional, Pais, TipoPublicacion,
    Modalidad, Dedicacion, Carrera, Periodo, Licencia,
    UsuarioAlcanceCarrera,
)
from docentes.models import DocenteFcacc
from catalogos.models import (
    CatalogoTipoDocente, CatalogoModalidadContratacion, CatalogoDedicacionHoraria,
    CatalogoCarrera, CatalogoPeriodoAcademico, CatalogoPais, CatalogoTipoLicencia,
    CatalogoTipoPublicacion,
)
from accounts.decorators import ADMIN, AUTORIDAD, COORDINADOR, FUNCIONARIO, DOCENTE
from PIL import Image, UnidentifiedImageError

Usuario = get_user_model()


class LoginForm(forms.Form):
    cedula = forms.CharField(
        label='Cédula',
        max_length=10,
        min_length=10,
        validators=[RegexValidator(r'^\d{10}$', 'La cédula debe tener exactamente 10 dígitos numéricos.')],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese su cédula',
            'autocomplete': 'username',
            'maxlength': '10',
            'oninput': "this.value = this.value.replace(/\\D/g, '')",
        })
    )
    password = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese su contraseña',
            'autocomplete': 'current-password',
        })
    )


class DocenteFcaccForm(forms.ModelForm):
    class Meta:
        model = DocenteFcacc
        fields = [
            'nombres_completos', 'fecha_nacimiento', 'foto', 'unidad_organica',
            'correo_institucional', 'numero_celular', 'tipo_sangre',
        ]
        widgets = {
            'nombres_completos': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellidos y nombres'}),
            'fecha_nacimiento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'foto': forms.ClearableFileInput(attrs={
                'class': 'form-control', 'accept': 'image/jpeg,image/png,image/webp',
            }),
            'unidad_organica': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Unidad orgánica'}),
            'correo_institucional': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'correo@uleam.edu.ec'}),
            'numero_celular': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '0999999999', 'maxlength': '15'}),
            'tipo_sangre': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.local_docente = kwargs.pop('local_docente', None)
        super().__init__(*args, **kwargs)
        for field_name in ['fecha_nacimiento', 'foto', 'unidad_organica', 'correo_institucional', 'numero_celular', 'tipo_sangre']:
            self.fields[field_name].required = False
        self.fields['tipo_sangre'].empty_label = 'Seleccione el tipo de sangre'

    def clean_numero_celular(self):
        value = (self.cleaned_data.get('numero_celular') or '').replace(' ', '').replace('-', '')
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
        if not image or not hasattr(image, 'size'):
            return image
        if image.size > 5 * 1024 * 1024:
            raise ValidationError('La fotografía no puede superar 5 MB.')
        content_type = getattr(image, 'content_type', '')
        if content_type not in {'image/jpeg', 'image/png', 'image/webp'}:
            raise ValidationError('Utilice una imagen JPG, PNG o WEBP.')
        try:
            parsed = Image.open(image)
            width, height = parsed.size
            if parsed.format not in {'JPEG', 'PNG', 'WEBP'}:
                raise ValidationError('El archivo no contiene una imagen admitida.')
            if width > 4096 or height > 4096:
                raise ValidationError('La imagen no puede superar 4096 × 4096 píxeles.')
            parsed.verify()
            image.seek(0)
        except (UnidentifiedImageError, OSError):
            raise ValidationError('El archivo de fotografía está dañado o no es una imagen válida.')
        return image

    def save(self, commit=True):
        instance = super().save(commit=False)
        if not instance.pk:
            instance.cedula_docente = self.user.cedula if self.user else instance.cedula_docente
            if not instance.id_tipo_docente_id:
                instance.id_tipo_docente = CatalogoTipoDocente.objects.order_by('id_tipo_docente').first()
            if not instance.id_modalidad_id:
                instance.id_modalidad = CatalogoModalidadContratacion.objects.order_by('id_modalidad').first()
            if not instance.id_dedicacion_id:
                instance.id_dedicacion = CatalogoDedicacionHoraria.objects.order_by('id_dedicacion').first()
            if self.local_docente and not instance.nombres_completos:
                instance.nombres_completos = self.local_docente.apellidos_nombres or f'Usuario {self.user.cedula}'
            if self.local_docente and not instance.correo_institucional:
                instance.correo_institucional = self.local_docente.correo
            if self.local_docente and not instance.numero_celular:
                instance.numero_celular = self.local_docente.telefono
        if commit:
            instance.save()
        return instance


def _seed_core_lookup_tables():
    if Pais.objects.exists():
        return
    for cp in CatalogoPais.objects.all():
        Pais.objects.get_or_create(
            pk=cp.id_pais,
            defaults={'nombre_pais': cp.nombre_pais or ''}
        )
    if not Pais.objects.exists():
        for i, nombre in enumerate([
            'Ecuador', 'Colombia', 'Perú', 'Bolivia', 'Chile', 'Argentina',
        ], start=1):
            Pais.objects.get_or_create(pk=i, defaults={'nombre_pais': nombre})
    for tp in CatalogoTipoPublicacion.objects.all():
        TipoPublicacion.objects.get_or_create(
            pk=tp.id_tipo_publicacion,
            defaults={'nombre': tp.nombre_tipo_publicacion or tp.codigo_tipo_publicacion or ''}
        )
    if not TipoPublicacion.objects.exists():
        for i, nombre in enumerate([
            'Artículo científico', 'Libro', 'Capítulo de libro',
            'Ponencia / Conferencia', 'Tesis', 'Informe técnico',
        ], start=1):
            TipoPublicacion.objects.get_or_create(pk=i, defaults={'nombre': nombre})
    for cl in CatalogoTipoLicencia.objects.all():
        Licencia.objects.get_or_create(
            pk=cl.id_licencia,
            defaults={'nombre_licencia': cl.nombre_licencia or ''}
        )
    if not Licencia.objects.exists():
        for i, nombre in enumerate([
            'Ninguna', 'Copyright', 'Creative Commons', 'Licencia institucional',
        ], start=1):
            Licencia.objects.get_or_create(pk=i, defaults={'nombre_licencia': nombre})
    for m in CatalogoModalidadContratacion.objects.all():
        Modalidad.objects.get_or_create(
            pk=m.id_modalidad,
            defaults={'nombre_modalidad': m.nombre_modalidad or ''}
        )
    for d in CatalogoDedicacionHoraria.objects.all():
        Dedicacion.objects.get_or_create(
            pk=d.id_dedicacion,
            defaults={'nombre_dedicacion': d.nombre_dedicacion or ''}
        )
    for c in CatalogoCarrera.objects.all():
        Carrera.objects.get_or_create(
            pk=c.id_carrera,
            defaults={'nombre_carrera': c.nombre_carrera or ''}
        )
    first_carrera = Carrera.objects.first()
    if first_carrera:
        for p in CatalogoPeriodoAcademico.objects.all():
            Periodo.objects.get_or_create(
                pk=p.id_periodo,
                defaults={'nombre_periodo': str(p), 'id_carrera': first_carrera}
            )


class TituloForm(forms.ModelForm):
    class Meta:
        model = Titulo
        fields = [
            'nombre', 'id_pais', 'fecha_titulo',
            'registro_titulo', 'fecha_senecyt', 'registro_senecyt'
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Nombre del título'
            }),
            'id_pais': forms.Select(attrs={'class': 'form-select'}),
            'fecha_titulo': forms.DateInput(attrs={
                'class': 'form-control', 'type': 'date'
            }),
            'registro_titulo': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Número de registro'
            }),
            'fecha_senecyt': forms.DateInput(attrs={
                'class': 'form-control', 'type': 'date'
            }),
            'registro_senecyt': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Registro Senescyt'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['id_pais'].queryset = Pais.objects.all()
        self.fields['id_pais'].empty_label = 'Seleccione un país'
        self.fields['fecha_titulo'].required = False
        self.fields['fecha_senecyt'].required = False


class PublicacionForm(forms.ModelForm):
    class Meta:
        model = Publicacion
        fields = [
            'nombre_publicacion', 'id_tipo_publicacion',
            'fecha', 'codigo', 'funcion'
        ]
        widgets = {
            'nombre_publicacion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de la publicación'
            }),
            'id_tipo_publicacion': forms.Select(attrs={
                'class': 'form-select'
            }),
            'fecha': forms.DateInput(attrs={
                'class': 'form-control', 'type': 'date'
            }),
            'codigo': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Código ISBN/ISSN'
            }),
            'funcion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Autor, Coautor, Editor'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['id_tipo_publicacion'].queryset = TipoPublicacion.objects.all()
        self.fields['id_tipo_publicacion'].empty_label = 'Seleccione un tipo'
        self.fields['fecha'].required = False
        if not self.instance.pk and not self.is_bound:
            self.fields['fecha'].initial = timezone.now().date()


class DocumentoForm(forms.ModelForm):
    class Meta:
        model = DocenteTransaccional
        fields = [
            'id_modalidad', 'id_dedicacion', 'id_carrera',
            'id_periodo', 'id_licencia', 'observacion', 'adj_archivo'
        ]
        widgets = {
            'id_modalidad': forms.Select(attrs={'class': 'form-select'}),
            'id_dedicacion': forms.Select(attrs={'class': 'form-select'}),
            'id_carrera': forms.Select(attrs={'class': 'form-select'}),
            'id_periodo': forms.Select(attrs={'class': 'form-select'}),
            'id_licencia': forms.Select(attrs={'class': 'form-select'}),
            'observacion': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3,
                'placeholder': 'Observaciones (opcional)'
            }),
            'adj_archivo': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        _seed_core_lookup_tables()
        docente_fcacc = kwargs.pop('docente_fcacc', None)
        cedula_docente = kwargs.pop('cedula_docente', None)
        super().__init__(*args, **kwargs)
        self.fields['id_modalidad'].queryset = Modalidad.objects.all()
        self.fields['id_modalidad'].empty_label = 'Seleccione modalidad'
        self.fields['id_dedicacion'].queryset = Dedicacion.objects.all()
        self.fields['id_dedicacion'].empty_label = 'Seleccione dedicación'
        self.fields['id_carrera'].queryset = Carrera.objects.all()
        self.fields['id_carrera'].empty_label = 'Seleccione carrera'
        self.fields['id_periodo'].queryset = Periodo.objects.all()
        self.fields['id_periodo'].empty_label = 'Seleccione período'
        self.fields['id_licencia'].queryset = Licencia.objects.all()
        self.fields['id_licencia'].empty_label = 'Seleccione licencia'
        for field in self.fields:
            self.fields[field].required = False
        self.fields['adj_archivo'].required = False
        if not self.instance.pk and not self.is_bound and docente_fcacc:
            from docentes.models import DocenteFcacc
            if isinstance(docente_fcacc, DocenteFcacc):
                modalidad = Modalidad.objects.filter(
                    nombre_modalidad__icontains=str(docente_fcacc.id_modalidad or '')
                ).first()
                if modalidad:
                    self.fields['id_modalidad'].initial = modalidad.pk
                dedicacion = Dedicacion.objects.filter(
                    nombre_dedicacion__icontains=str(docente_fcacc.id_dedicacion or '')
                ).first()
                if dedicacion:
                    self.fields['id_dedicacion'].initial = dedicacion.pk
                if cedula_docente:
                    from docentes.models import DocenteAsignacionCarreraPeriodo
                    asignacion = DocenteAsignacionCarreraPeriodo.objects.filter(
                        id_docente=docente_fcacc,
                    ).select_related('id_licencia').first()
                    if asignacion and asignacion.id_licencia:
                        lic = Licencia.objects.filter(
                            pk=asignacion.id_licencia_id
                        ).first()
                        if lic:
                            self.fields['id_licencia'].initial = lic.pk


class UsuarioAccessFormMixin(forms.Form):
    ROLE_CHOICES = [
        (AUTORIDAD, 'Autoridad'),
        (COORDINADOR, 'Coordinador'),
        (FUNCIONARIO, 'Funcionario'),
        (DOCENTE, 'Docente'),
    ]
    rol = forms.ChoiceField(
        label='Rol',
        choices=[],
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True,
    )
    carreras = forms.ModelMultipleChoiceField(
        label='Carreras autorizadas',
        queryset=CatalogoCarrera.objects.none(), required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text='Es obligatorio para coordinadores. Los demás roles tienen el alcance definido por su rol.',
    )

    def __init__(self, *args, actor=None, **kwargs):
        self.actor = actor
        super().__init__(*args, **kwargs)
        role_choices = list(self.ROLE_CHOICES)
        if actor and (actor.is_superuser or actor.groups.filter(name=ADMIN).exists()):
            role_choices.insert(0, (ADMIN, 'Administrador'))
        self.fields['rol'].choices = [('', 'Seleccione un rol'), *role_choices]
        self.fields['carreras'].queryset = CatalogoCarrera.objects.filter(
            carrera_activa=True
        ).order_by('nombre_carrera')

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('rol') == COORDINADOR and not cleaned.get('carreras'):
            self.add_error('carreras', 'Seleccione al menos una carrera para el coordinador.')
        return cleaned


class UsuarioCreateForm(UsuarioAccessFormMixin, forms.ModelForm):

    class Meta:
        model = Usuario
        fields = ['cedula', 'email']
        widgets = {
            'cedula': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '10 dígitos',
                'maxlength': '10',
                'oninput': "this.value = this.value.replace(/\\D/g, '')",
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control', 'placeholder': 'correo@uleam.edu.ec',
            }),
        }

    def clean_cedula(self):
        cedula = (self.cleaned_data.get('cedula') or '').strip()
        if Usuario.objects.filter(cedula=cedula).exists():
            raise forms.ValidationError('Ya existe un usuario registrado con esta cédula.')
        return cedula

    def clean(self):
        cleaned = super().clean()
        role = cleaned.get('rol')
        cedula = cleaned.get('cedula')
        if role in {DOCENTE, COORDINADOR} and cedula:
            if not DocenteFcacc.objects.filter(cedula_docente=cedula).exists():
                self.add_error('cedula', 'La cédula no corresponde a un docente registrado.')
        return cleaned


class UsuarioEditForm(UsuarioAccessFormMixin, forms.ModelForm):

    class Meta:
        model = Usuario
        fields = ['cedula', 'email', 'is_active']
        widgets = {
            'cedula': forms.TextInput(attrs={
                'class': 'form-control',
                'maxlength': '10',
                'oninput': "this.value = this.value.replace(/\\D/g, '')",
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            grupos = list(self.instance.groups.filter(
                name__in=[ADMIN, AUTORIDAD, COORDINADOR, FUNCIONARIO, DOCENTE]
            ).values_list('name', flat=True))
            if grupos:
                self.fields['rol'].initial = grupos[0]
            self.fields['carreras'].initial = self.instance.alcances_carrera.filter(
                activo=True
            ).values_list('carrera_id', flat=True)


class CambioPasswordObligatorioForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['new_password1'].widget.attrs.update({
            'class': 'form-control', 'autocomplete': 'new-password',
        })
        self.fields['new_password2'].widget.attrs.update({
            'class': 'form-control', 'autocomplete': 'new-password',
        })
