from django import forms
from django.core.validators import RegexValidator
from django.contrib.auth import get_user_model
from .models import (
    Docente, Titulo, Publicacion, DocenteTransaccional, Pais, TipoPublicacion,
)
from docentes.models import DocenteFcacc
from catalogos.models import (
    CatalogoTipoDocente, CatalogoModalidadContratacion, CatalogoDedicacionHoraria,
)

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
            'autocomplete': 'off',
            'maxlength': '10',
            'oninput': "this.value = this.value.replace(/\\D/g, '')",
        })
    )
    password = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese su contraseña',
        })
    )


class DocentePerfilForm(forms.ModelForm):
    class Meta:
        model = Docente
        fields = ['telefono', 'correo']
        widgets = {
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 0999999999',
                'maxlength': '10',
                'oninput': "this.value = this.value.replace(/\\D/g, '')",
            }),
            'correo': forms.EmailInput(attrs={
                'class': 'form-control', 'placeholder': 'correo@uleam.edu.ec'
            }),
        }


class DocenteFcaccForm(forms.ModelForm):
    class Meta:
        model = DocenteFcacc
        fields = ['nombres_completos', 'unidad_organica', 'correo_institucional', 'numero_celular', 'tipo_sangre', 'docente_activo']
        widgets = {
            'nombres_completos': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellidos y nombres'}),
            'unidad_organica': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Unidad orgánica'}),
            'correo_institucional': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'correo@uleam.edu.ec'}),
            'numero_celular': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '0999999999', 'maxlength': '15'}),
            'tipo_sangre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'O+', 'maxlength': '5'}),
            'docente_activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.local_docente = kwargs.pop('local_docente', None)
        super().__init__(*args, **kwargs)
        for field_name in ['unidad_organica', 'correo_institucional', 'numero_celular', 'tipo_sangre']:
            self.fields[field_name].required = False

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
        super().__init__(*args, **kwargs)
        self.fields['id_modalidad'].empty_label = 'Seleccione'
        self.fields['id_dedicacion'].empty_label = 'Seleccione'
        self.fields['id_carrera'].empty_label = 'Seleccione'
        self.fields['id_periodo'].empty_label = 'Seleccione'
        self.fields['id_licencia'].empty_label = 'Seleccione'
        for field in self.fields:
            self.fields[field].required = False
        self.fields['adj_archivo'].required = False


class UsuarioCreateForm(forms.ModelForm):
    password1 = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control', 'placeholder': 'Contraseña'
        }),
    )
    password2 = forms.CharField(
        label='Confirmar contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control', 'placeholder': 'Repetir contraseña'
        }),
    )
    rol = forms.ChoiceField(
        label='Rol',
        choices=[
            ('', 'Seleccione un rol'),
            ('Administrador', 'Administrador'),
            ('Autoridad', 'Autoridad'),
            ('Coordinador', 'Coordinador'),
            ('Usuario', 'Usuario'),
            ('Funcionario', 'Funcionario'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True,
    )

    class Meta:
        model = Usuario
        fields = ['cedula']
        widgets = {
            'cedula': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '10 dígitos',
                'maxlength': '10',
                'oninput': "this.value = this.value.replace(/\\D/g, '')",
            }),
        }

    def clean_password2(self):
        p1 = self.cleaned_data.get('password1')
        p2 = self.cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('Las contraseñas no coinciden.')
        return p2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


class UsuarioEditForm(forms.ModelForm):
    password1 = forms.CharField(
        label='Nueva contraseña (dejar vacío para no cambiar)',
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control', 'placeholder': 'Dejar vacío si no cambia'
        }),
    )
    password2 = forms.CharField(
        label='Confirmar nueva contraseña',
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control', 'placeholder': 'Repetir contraseña'
        }),
    )
    rol = forms.ChoiceField(
        label='Rol',
        choices=[
            ('', 'Seleccione un rol'),
            ('Administrador', 'Administrador'),
            ('Autoridad', 'Autoridad'),
            ('Coordinador', 'Coordinador'),
            ('Usuario', 'Usuario'),
            ('Funcionario', 'Funcionario'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False,
    )

    class Meta:
        model = Usuario
        fields = ['cedula', 'is_active']
        widgets = {
            'cedula': forms.TextInput(attrs={
                'class': 'form-control',
                'maxlength': '10',
                'oninput': "this.value = this.value.replace(/\\D/g, '')",
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            grupos = list(self.instance.groups.filter(
                name__in=['Administrador', 'Autoridad', 'Coordinador', 'Usuario', 'Funcionario']
            ).values_list('name', flat=True))
            if grupos:
                self.fields['rol'].initial = grupos[0]

    def clean_password2(self):
        p1 = self.cleaned_data.get('password1')
        p2 = self.cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('Las contraseñas no coinciden.')
        if p1 and not p2:
            raise forms.ValidationError('Confirma la nueva contraseña.')
        return p2

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password1')
        if password:
            user.set_password(password)
        if commit:
            user.save()
        return user
