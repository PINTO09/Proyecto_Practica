from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.core.validators import RegexValidator
from .models import (
    Usuario, Docente, Carrera, Dedicacion, Licencia,
    Modalidad, Periodo, TipoPublicacion, Curso, Titulo,
    Pais, Publicacion, DocenteTransaccional, CursoDocente
)

validate_10_digits_admin = RegexValidator(
    r'^\d{10}$', 'Este campo debe tener exactamente 10 dígitos numéricos.'
)

widget_10_digits = forms.TextInput(attrs={
    'maxlength': '10',
    'oninput': "this.value = this.value.replace(/\\D/g, '')",
})


class UsuarioAdminForm(forms.ModelForm):
    cedula = forms.CharField(
        max_length=10,
        min_length=10,
        validators=[validate_10_digits_admin],
        widget=widget_10_digits,
    )

    class Meta:
        model = Usuario
        fields = '__all__'


class DocenteAdminForm(forms.ModelForm):
    cedula = forms.CharField(
        max_length=10,
        min_length=10,
        validators=[validate_10_digits_admin],
        widget=widget_10_digits,
    )
    telefono = forms.CharField(
        max_length=10,
        min_length=10,
        validators=[validate_10_digits_admin],
        widget=widget_10_digits,
        required=False,
    )

    class Meta:
        model = Docente
        fields = '__all__'


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    model = Usuario
    form = UsuarioAdminForm
    add_form = UsuarioAdminForm
    list_display = ['cedula', 'is_staff', 'is_active']
    fieldsets = (
        (None, {'fields': ('cedula', 'password')}),
        ('Permisos', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups')
        }),
        ('Fechas', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'cedula', 'password1', 'password2',
                'is_staff', 'is_superuser', 'groups'
            ),
        }),
    )
    search_fields = ('cedula',)
    ordering = ('cedula',)
    filter_horizontal = ('groups',)


@admin.register(Docente)
class DocenteAdmin(admin.ModelAdmin):
    form = DocenteAdminForm
    list_display = ['cedula', 'apellidos_nombres', 'telefono', 'correo']
    search_fields = ['cedula', 'apellidos_nombres']


@admin.register(Carrera)
class CarreraAdmin(admin.ModelAdmin):
    list_display = ['nombre_carrera']
    search_fields = ['nombre_carrera']


@admin.register(Dedicacion)
class DedicacionAdmin(admin.ModelAdmin):
    list_display = ['nombre_dedicacion']


@admin.register(Licencia)
class LicenciaAdmin(admin.ModelAdmin):
    list_display = ['nombre_licencia']


@admin.register(Modalidad)
class ModalidadAdmin(admin.ModelAdmin):
    list_display = ['nombre_modalidad']


@admin.register(Periodo)
class PeriodoAdmin(admin.ModelAdmin):
    list_display = ['nombre_periodo', 'id_carrera']
    list_filter = ['id_carrera']


@admin.register(TipoPublicacion)
class TipoPublicacionAdmin(admin.ModelAdmin):
    list_display = ['nombre']


@admin.register(Curso)
class CursoAdmin(admin.ModelAdmin):
    list_display = [
        'nombre_curso', 'fecha_inicio', 'fecha_final', 'hora_total'
    ]


@admin.register(Titulo)
class TituloAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'id_cedula', 'fecha_titulo']


@admin.register(Pais)
class PaisAdmin(admin.ModelAdmin):
    list_display = ['nombre_pais', 'nacionalidad']


@admin.register(Publicacion)
class PublicacionAdmin(admin.ModelAdmin):
    list_display = ['nombre_publicacion', 'fecha', 'id_docente']


@admin.register(DocenteTransaccional)
class DocenteTransaccionalAdmin(admin.ModelAdmin):
    list_display = [
        'id_docente', 'id_periodo', 'id_carrera', 'id_modalidad'
    ]
    list_filter = ['id_periodo', 'id_carrera', 'id_modalidad']


@admin.register(CursoDocente)
class CursoDocenteAdmin(admin.ModelAdmin):
    list_display = ['id_curso', 'id_docente']


admin.site.site_header = 'Gestión Docente - ULEAM'
admin.site.site_title = 'Gestión Docente'
admin.site.index_title = 'Panel de Administración'
