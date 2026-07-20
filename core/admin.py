from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.core.validators import RegexValidator
from .models import (
    Usuario, Docente, Carrera, Dedicacion, Licencia,
    Modalidad, Periodo, TipoPublicacion, Curso, Titulo,
    Pais, Publicacion, DocenteTransaccional, CursoDocente,
)


validate_10_digits_admin = RegexValidator(
    r'^\d{10}$', 'Este campo debe tener exactamente 10 dígitos numéricos.'
)

widget_10_digits = forms.TextInput(attrs={
    'maxlength': '10',
    'oninput': "this.value = this.value.replace(/\\D/g, '')",
})


class UsuarioChangeForm(UserChangeForm):
    cedula = forms.CharField(
        max_length=10, min_length=10,
        validators=[validate_10_digits_admin],
        widget=widget_10_digits,
    )

    class Meta(UserChangeForm.Meta):
        model = Usuario
        fields = '__all__'


class UsuarioCreationForm(UserCreationForm):
    cedula = forms.CharField(
        max_length=10, min_length=10,
        validators=[validate_10_digits_admin],
        widget=widget_10_digits,
    )

    class Meta(UserCreationForm.Meta):
        model = Usuario
        fields = '__all__'


class DocenteAdminForm(forms.ModelForm):
    cedula = forms.CharField(
        max_length=10, min_length=10,
        validators=[validate_10_digits_admin],
        widget=widget_10_digits,
    )
    telefono = forms.CharField(
        max_length=10, min_length=10,
        validators=[validate_10_digits_admin],
        widget=widget_10_digits,
        required=False,
    )

    class Meta:
        model = Docente
        fields = '__all__'


class TituloInline(admin.TabularInline):
    model = Titulo
    extra = 1
    fields = ['nombre', 'id_pais', 'fecha_titulo', 'registro_titulo', 'registro_senecyt']


class PublicacionInline(admin.TabularInline):
    model = Publicacion
    extra = 1
    fields = ['nombre_publicacion', 'id_tipo_publicacion', 'fecha', 'codigo']


class CursoDocenteInline(admin.TabularInline):
    model = CursoDocente
    extra = 1


class DocenteTransaccionalInline(admin.TabularInline):
    model = DocenteTransaccional
    extra = 0
    fields = ['id_periodo', 'id_carrera', 'id_modalidad', 'id_dedicacion', 'id_licencia']


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    model = Usuario
    form = UsuarioChangeForm
    add_form = UsuarioCreationForm
    list_display = ['cedula', 'is_staff', 'is_superuser', 'is_active', 'last_login']
    list_filter = ['is_staff', 'is_superuser', 'is_active', 'groups']
    fieldsets = (
        (None, {'fields': ('cedula', 'password')}),
        ('Permisos', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Fechas', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('cedula', 'password1', 'password2',
                       'is_staff', 'is_superuser', 'groups'),
        }),
    )
    search_fields = ('cedula',)
    ordering = ('cedula',)
    filter_horizontal = ('groups', 'user_permissions')
    date_hierarchy = 'date_joined'


@admin.register(Docente)
class DocenteAdmin(admin.ModelAdmin):
    form = DocenteAdminForm
    list_display = ['cedula', 'apellidos_nombres', 'telefono', 'correo', 'get_titulos_count']
    list_filter = ['titulo__id_pais']
    search_fields = ['cedula', 'apellidos_nombres', 'correo']
    ordering = ['apellidos_nombres']
    inlines = [TituloInline, PublicacionInline, DocenteTransaccionalInline, CursoDocenteInline]

    def get_titulos_count(self, obj):
        return f'{obj.titulo_set.count()} título(s)'
    get_titulos_count.short_description = 'Títulos'


@admin.register(Carrera)
class CarreraAdmin(admin.ModelAdmin):
    list_display = ['nombre_carrera', 'get_docentes_count']
    search_fields = ['nombre_carrera']
    ordering = ['nombre_carrera']

    def get_docentes_count(self, obj):
        return obj.docentetransaccional_set.values('id_docente').distinct().count()
    get_docentes_count.short_description = 'Docentes'


@admin.register(Dedicacion)
class DedicacionAdmin(admin.ModelAdmin):
    list_display = ['nombre_dedicacion']
    search_fields = ['nombre_dedicacion']


@admin.register(Licencia)
class LicenciaAdmin(admin.ModelAdmin):
    list_display = ['nombre_licencia']
    search_fields = ['nombre_licencia']


@admin.register(Modalidad)
class ModalidadAdmin(admin.ModelAdmin):
    list_display = ['nombre_modalidad']
    search_fields = ['nombre_modalidad']


@admin.register(Periodo)
class PeriodoAdmin(admin.ModelAdmin):
    list_display = ['nombre_periodo', 'id_carrera', 'get_docentes_count']
    list_filter = ['id_carrera']
    search_fields = ['nombre_periodo']

    def get_docentes_count(self, obj):
        return obj.docentetransaccional_set.count()
    get_docentes_count.short_description = 'Asignaciones'


@admin.register(TipoPublicacion)
class TipoPublicacionAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'get_publicaciones_count']
    search_fields = ['nombre']

    def get_publicaciones_count(self, obj):
        return obj.publicacion_set.count()
    get_publicaciones_count.short_description = 'Publicaciones'


@admin.register(Curso)
class CursoAdmin(admin.ModelAdmin):
    list_display = ['nombre_curso', 'id_tipo_curso', 'fecha_inicio', 'fecha_final', 'hora_total']
    list_filter = ['id_tipo_curso']
    search_fields = ['nombre_curso']
    date_hierarchy = 'fecha_inicio'
    inlines = [CursoDocenteInline]


@admin.register(Titulo)
class TituloAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'id_cedula', 'id_pais', 'fecha_titulo', 'registro_senecyt']
    list_filter = ['id_pais']
    search_fields = ['nombre', 'registro_senecyt', 'id_cedula__apellidos_nombres']
    date_hierarchy = 'fecha_titulo'
    raw_id_fields = ['id_cedula']


@admin.register(Pais)
class PaisAdmin(admin.ModelAdmin):
    list_display = ['nombre_pais', 'nacionalidad']
    search_fields = ['nombre_pais', 'nacionalidad']
    ordering = ['nombre_pais']


@admin.register(Publicacion)
class PublicacionAdmin(admin.ModelAdmin):
    list_display = ['nombre_publicacion', 'id_tipo_publicacion', 'fecha', 'id_docente']
    list_filter = ['id_tipo_publicacion']
    search_fields = ['nombre_publicacion', 'id_docente__apellidos_nombres']
    date_hierarchy = 'fecha'
    raw_id_fields = ['id_docente']


@admin.register(DocenteTransaccional)
class DocenteTransaccionalAdmin(admin.ModelAdmin):
    list_display = ['id_docente', 'id_periodo', 'id_carrera', 'id_modalidad', 'id_dedicacion', 'id_licencia']
    list_filter = ['id_periodo', 'id_carrera', 'id_modalidad', 'id_dedicacion', 'id_licencia']
    search_fields = ['id_docente__apellidos_nombres', 'id_docente__cedula']
    raw_id_fields = ['id_docente']


@admin.register(CursoDocente)
class CursoDocenteAdmin(admin.ModelAdmin):
    list_display = ['id_curso', 'id_docente']
    list_filter = ['id_curso']
    search_fields = ['id_docente__apellidos_nombres', 'id_curso__nombre_curso']
    raw_id_fields = ['id_docente', 'id_curso']


admin.site.site_header = 'Gestión Docente - FCACC · ULEAM'
admin.site.site_title = 'Gestión Docente'
admin.site.index_title = 'Panel de Administración Académica'
admin.site.site_url = None
