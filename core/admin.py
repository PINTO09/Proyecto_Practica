from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.core.validators import RegexValidator
from django.db import ProgrammingError, OperationalError
from django.shortcuts import render
from django.contrib import messages
from .models import (
    # App existente
    Usuario, Docente, Carrera, Dedicacion, Licencia,
    Modalidad, Periodo, TipoPublicacion, Curso, Titulo,
    Pais, Publicacion, DocenteTransaccional, CursoDocente,
    # M1 · Catálogos
    CatalogoCarrera, CatalogoModalidadContratacion,
    CatalogoDedicacionHoraria, CatalogoTipoDocente,
    CatalogoTipoLicencia, CatalogoPais, CatalogoTituloPosgrado,
    CatalogoCampoConocimiento, CatalogoGradoAfinidad,
    CatalogoTipoPublicacion, CatalogoTipoCursoCapacitacion,
    CatalogoPeriodoAcademico, RelacionCarreraPeriodo,
    # M2 · Docentes
    DocenteFcacc, DocenteTituloAcademico, DocenteCampoAfinidad,
    DocenteAsignacionCarreraPeriodo, DocenteCursoCapacitacion,
    DocenteParticipacionCurso, DocentePublicacionAcademica,
    # M3 · Seguridad
    SeguridadRol, SeguridadUsuario, SeguridadUsuarioRol,
    # M4 · Currículo
    CurriculoAsignatura, CurriculoAsignaturaCampo, RelacionPosgradoCampo,
    # M5 · Planificación
    PlanificacionDemandaAcademica, PlanificacionAsignacionDocente,
    PlanificacionRepartoHoras, PlanificacionMatrizF4, PlanificacionAulaHorario,
    # M6 · Auditoría
    AuditoriaRegistroCambios,
    # M7 · Limitaciones
    Limitacion, HistorialLimitacion, Cabecera, Cuerpo,
)

class SafeBaseAdmin(admin.ModelAdmin):
    def _is_unmanaged(self):
        return not getattr(self.model._meta, 'managed', True)

    def _table_exists(self):
        try:
            self.model.objects.count()
            return True
        except (ProgrammingError, OperationalError):
            return False

    def changelist_view(self, request, extra_context=None):
        if self._is_unmanaged() and not self._table_exists():
            extra = extra_context or {}
            extra.update({
                'title': self.model._meta.verbose_name_plural,
                'table_name': self.model._meta.db_table,
            })
            return render(request, 'admin/table_not_ready.html', extra)
        return super().changelist_view(request, extra_context)

    def add_view(self, request, form_url='', extra_context=None):
        if self._is_unmanaged() and not self._table_exists():
            messages.error(request, f'La tabla {self.model._meta.db_table} no existe en la base de datos.')
            return self.changelist_view(request)
        return super().add_view(request, form_url, extra_context)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        if self._is_unmanaged() and not self._table_exists():
            messages.error(request, f'La tabla {self.model._meta.db_table} no existe en la base de datos.')
            return self.changelist_view(request)
        return super().change_view(request, object_id, form_url, extra_context)


validate_10_digits_admin = RegexValidator(
    r'^\d{10}$', 'Este campo debe tener exactamente 10 dígitos numéricos.'
)

widget_10_digits = forms.TextInput(attrs={
    'maxlength': '10',
    'oninput': "this.value = this.value.replace(/\\D/g, '')",
})


class UsuarioAdminForm(forms.ModelForm):
    cedula = forms.CharField(
        max_length=10, min_length=10,
        validators=[validate_10_digits_admin],
        widget=widget_10_digits,
    )

    class Meta:
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


# --- INLINES (modelos existentes) ---

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


# --- INLINES (modelos PostgreSQL) ---

class DocenteTituloAcademicoInline(admin.TabularInline):
    model = DocenteTituloAcademico
    extra = 0
    fields = ['nombre_titulo', 'id_pais', 'nivel_titulo', 'fecha_obtencion_titulo', 'numero_registro_senescyt']


class DocenteCampoAfinidadInline(admin.TabularInline):
    model = DocenteCampoAfinidad
    extra = 0


class DocenteAsignacionCarreraPeriodoInline(admin.TabularInline):
    model = DocenteAsignacionCarreraPeriodo
    extra = 0
    fields = ['id_carrera', 'id_periodo', 'id_licencia', 'horas_otras_unidades_academicas']


class DocentePublicacionAcademicaInline(admin.TabularInline):
    model = DocentePublicacionAcademica
    extra = 0
    fields = ['nombre_publicacion', 'id_tipo_publicacion', 'fecha_publicacion']


class DocenteParticipacionCursoInline(admin.TabularInline):
    model = DocenteParticipacionCurso
    extra = 0


# =============================================================================
#  APP EXISTENTE
# =============================================================================

@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    model = Usuario
    form = UsuarioAdminForm
    add_form = UsuarioAdminForm
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
class DocenteAdmin(SafeBaseAdmin):
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
class CarreraAdmin(SafeBaseAdmin):
    list_display = ['nombre_carrera', 'get_docentes_count']
    search_fields = ['nombre_carrera']
    ordering = ['nombre_carrera']

    def get_docentes_count(self, obj):
        return obj.docentetransaccional_set.values('id_docente').distinct().count()
    get_docentes_count.short_description = 'Docentes'


@admin.register(Dedicacion)
class DedicacionAdmin(SafeBaseAdmin):
    list_display = ['nombre_dedicacion']
    search_fields = ['nombre_dedicacion']


@admin.register(Licencia)
class LicenciaAdmin(SafeBaseAdmin):
    list_display = ['nombre_licencia']
    search_fields = ['nombre_licencia']


@admin.register(Modalidad)
class ModalidadAdmin(SafeBaseAdmin):
    list_display = ['nombre_modalidad']
    search_fields = ['nombre_modalidad']


@admin.register(Periodo)
class PeriodoAdmin(SafeBaseAdmin):
    list_display = ['nombre_periodo', 'id_carrera', 'get_docentes_count']
    list_filter = ['id_carrera']
    search_fields = ['nombre_periodo']

    def get_docentes_count(self, obj):
        return obj.docentetransaccional_set.count()
    get_docentes_count.short_description = 'Asignaciones'


@admin.register(TipoPublicacion)
class TipoPublicacionAdmin(SafeBaseAdmin):
    list_display = ['nombre', 'get_publicaciones_count']
    search_fields = ['nombre']

    def get_publicaciones_count(self, obj):
        return obj.publicacion_set.count()
    get_publicaciones_count.short_description = 'Publicaciones'


@admin.register(Curso)
class CursoAdmin(SafeBaseAdmin):
    list_display = ['nombre_curso', 'id_tipo_curso', 'fecha_inicio', 'fecha_final', 'hora_total']
    list_filter = ['id_tipo_curso']
    search_fields = ['nombre_curso']
    date_hierarchy = 'fecha_inicio'
    inlines = [CursoDocenteInline]


@admin.register(Titulo)
class TituloAdmin(SafeBaseAdmin):
    list_display = ['nombre', 'id_cedula', 'id_pais', 'fecha_titulo', 'registro_senecyt']
    list_filter = ['id_pais']
    search_fields = ['nombre', 'registro_senecyt', 'id_cedula__apellidos_nombres']
    date_hierarchy = 'fecha_titulo'
    raw_id_fields = ['id_cedula']


@admin.register(Pais)
class PaisAdmin(SafeBaseAdmin):
    list_display = ['nombre_pais', 'nacionalidad']
    search_fields = ['nombre_pais', 'nacionalidad']
    ordering = ['nombre_pais']


@admin.register(Publicacion)
class PublicacionAdmin(SafeBaseAdmin):
    list_display = ['nombre_publicacion', 'id_tipo_publicacion', 'fecha', 'id_docente']
    list_filter = ['id_tipo_publicacion']
    search_fields = ['nombre_publicacion', 'id_docente__apellidos_nombres']
    date_hierarchy = 'fecha'
    raw_id_fields = ['id_docente']


@admin.register(DocenteTransaccional)
class DocenteTransaccionalAdmin(SafeBaseAdmin):
    list_display = ['id_docente', 'id_periodo', 'id_carrera', 'id_modalidad', 'id_dedicacion', 'id_licencia']
    list_filter = ['id_periodo', 'id_carrera', 'id_modalidad', 'id_dedicacion', 'id_licencia']
    search_fields = ['id_docente__apellidos_nombres', 'id_docente__cedula']
    raw_id_fields = ['id_docente']


@admin.register(CursoDocente)
class CursoDocenteAdmin(SafeBaseAdmin):
    list_display = ['id_curso', 'id_docente']
    list_filter = ['id_curso']
    search_fields = ['id_docente__apellidos_nombres', 'id_curso__nombre_curso']
    raw_id_fields = ['id_docente', 'id_curso']


# =============================================================================
#  MÓDULO 1 · CATÁLOGOS BASE
# =============================================================================

@admin.register(CatalogoCarrera)
class CatalogoCarreraAdmin(SafeBaseAdmin):
    list_display = ['codigo_carrera', 'nombre_carrera', 'carrera_activa']
    list_filter = ['carrera_activa']
    search_fields = ['codigo_carrera', 'nombre_carrera']
    ordering = ['codigo_carrera']


@admin.register(CatalogoModalidadContratacion)
class CatalogoModalidadContratacionAdmin(SafeBaseAdmin):
    list_display = ['codigo_modalidad', 'nombre_modalidad']
    search_fields = ['nombre_modalidad']


@admin.register(CatalogoDedicacionHoraria)
class CatalogoDedicacionHorariaAdmin(SafeBaseAdmin):
    list_display = ['codigo_dedicacion', 'nombre_dedicacion']
    search_fields = ['nombre_dedicacion']


@admin.register(CatalogoTipoDocente)
class CatalogoTipoDocenteAdmin(SafeBaseAdmin):
    list_display = ['codigo_tipo_docente', 'nombre_tipo_docente']
    search_fields = ['nombre_tipo_docente']


@admin.register(CatalogoTipoLicencia)
class CatalogoTipoLicenciaAdmin(SafeBaseAdmin):
    list_display = ['codigo_licencia', 'nombre_licencia']
    search_fields = ['nombre_licencia']


@admin.register(CatalogoPais)
class CatalogoPaisAdmin(SafeBaseAdmin):
    list_display = ['codigo_iso_pais', 'nombre_pais', 'nombre_nacionalidad']
    search_fields = ['nombre_pais', 'nombre_nacionalidad']
    ordering = ['nombre_pais']


@admin.register(CatalogoTituloPosgrado)
class CatalogoTituloPosgradoAdmin(SafeBaseAdmin):
    list_display = ['codigo_posgrado', 'nombre_titulo_posgrado']
    search_fields = ['nombre_titulo_posgrado']


@admin.register(CatalogoCampoConocimiento)
class CatalogoCampoConocimientoAdmin(SafeBaseAdmin):
    list_display = ['codigo_campo', 'nombre_campo_conocimiento']
    search_fields = ['nombre_campo_conocimiento']


@admin.register(CatalogoGradoAfinidad)
class CatalogoGradoAfinidadAdmin(SafeBaseAdmin):
    list_display = ['codigo_grado_afinidad', 'nombre_grado_afinidad', 'nivel_prioridad']
    list_filter = ['nivel_prioridad']


@admin.register(CatalogoTipoPublicacion)
class CatalogoTipoPublicacionAdmin(SafeBaseAdmin):
    list_display = ['codigo_tipo_publicacion', 'nombre_tipo_publicacion']
    search_fields = ['nombre_tipo_publicacion']


@admin.register(CatalogoTipoCursoCapacitacion)
class CatalogoTipoCursoCapacitacionAdmin(SafeBaseAdmin):
    list_display = ['codigo_tipo_curso', 'nombre_tipo_curso']
    search_fields = ['nombre_tipo_curso']


@admin.register(CatalogoPeriodoAcademico)
class CatalogoPeriodoAcademicoAdmin(SafeBaseAdmin):
    list_display = ['codigo_periodo', 'nombre_periodo', 'periodo_activo', 'fecha_inicio_periodo', 'fecha_fin_periodo']
    list_filter = ['periodo_activo']
    search_fields = ['codigo_periodo', 'nombre_periodo']
    date_hierarchy = 'fecha_inicio_periodo'


@admin.register(RelacionCarreraPeriodo)
class RelacionCarreraPeriodoAdmin(SafeBaseAdmin):
    list_display = ['id_carrera', 'id_periodo']
    list_filter = ['id_carrera', 'id_periodo']


# =============================================================================
#  MÓDULO 2 · DOCENTES
# =============================================================================

@admin.register(DocenteFcacc)
class DocenteFcaccAdmin(SafeBaseAdmin):
    list_display = ['cedula_docente', 'nombres_completos', 'id_tipo_docente', 'id_modalidad', 'id_dedicacion', 'docente_activo']
    list_filter = ['docente_activo', 'id_tipo_docente', 'id_modalidad', 'id_dedicacion']
    search_fields = ['cedula_docente', 'nombres_completos', 'correo_institucional']
    ordering = ['nombres_completos']
    inlines = [
        DocenteTituloAcademicoInline, DocenteCampoAfinidadInline,
        DocenteAsignacionCarreraPeriodoInline, DocentePublicacionAcademicaInline,
        DocenteParticipacionCursoInline,
    ]


@admin.register(DocenteTituloAcademico)
class DocenteTituloAcademicoAdmin(SafeBaseAdmin):
    list_display = ['nombre_titulo', 'id_docente', 'id_pais', 'nivel_titulo', 'fecha_obtencion_titulo', 'numero_registro_senescyt']
    list_filter = ['nivel_titulo', 'id_pais']
    search_fields = ['nombre_titulo', 'numero_registro_senescyt', 'id_docente__nombres_completos']
    date_hierarchy = 'fecha_obtencion_titulo'
    raw_id_fields = ['id_docente']


@admin.register(DocenteCampoAfinidad)
class DocenteCampoAfinidadAdmin(SafeBaseAdmin):
    list_display = ['id_docente', 'id_campo']
    list_filter = ['id_campo']
    search_fields = ['id_docente__nombres_completos']
    raw_id_fields = ['id_docente', 'id_campo']


@admin.register(DocenteAsignacionCarreraPeriodo)
class DocenteAsignacionCarreraPeriodoAdmin(SafeBaseAdmin):
    list_display = ['id_docente', 'id_carrera', 'id_periodo', 'id_licencia', 'horas_otras_unidades_academicas']
    list_filter = ['id_carrera', 'id_periodo', 'id_licencia']
    search_fields = ['id_docente__nombres_completos']
    raw_id_fields = ['id_docente']


@admin.register(DocenteCursoCapacitacion)
class DocenteCursoCapacitacionAdmin(SafeBaseAdmin):
    list_display = ['nombre_curso_capacitacion', 'id_tipo_curso', 'fecha_inicio_curso', 'fecha_fin_curso', 'horas_totales_curso']
    list_filter = ['id_tipo_curso']
    search_fields = ['nombre_curso_capacitacion']
    date_hierarchy = 'fecha_inicio_curso'


@admin.register(DocenteParticipacionCurso)
class DocenteParticipacionCursoAdmin(SafeBaseAdmin):
    list_display = ['id_docente', 'id_curso', 'fecha_participacion']
    list_filter = ['fecha_participacion']
    search_fields = ['id_docente__nombres_completos', 'id_curso__nombre_curso_capacitacion']
    raw_id_fields = ['id_docente', 'id_curso']


@admin.register(DocentePublicacionAcademica)
class DocentePublicacionAcademicaAdmin(SafeBaseAdmin):
    list_display = ['nombre_publicacion', 'id_docente', 'id_tipo_publicacion', 'fecha_publicacion']
    list_filter = ['id_tipo_publicacion']
    search_fields = ['nombre_publicacion', 'id_docente__nombres_completos']
    date_hierarchy = 'fecha_publicacion'
    raw_id_fields = ['id_docente']


# =============================================================================
#  MÓDULO 3 · SEGURIDAD
# =============================================================================

@admin.register(SeguridadRol)
class SeguridadRolAdmin(SafeBaseAdmin):
    list_display = ['codigo_rol', 'nombre_rol', 'rol_activo']
    list_filter = ['rol_activo']
    search_fields = ['codigo_rol', 'nombre_rol']


@admin.register(SeguridadUsuario)
class SeguridadUsuarioAdmin(SafeBaseAdmin):
    list_display = ['nombre_usuario', 'id_docente', 'usuario_activo', 'fecha_ultimo_acceso', 'fecha_creacion_usuario']
    list_filter = ['usuario_activo']
    search_fields = ['nombre_usuario', 'id_docente__nombres_completos']
    date_hierarchy = 'fecha_creacion_usuario'
    readonly_fields = ['contrasena_hash']


@admin.register(SeguridadUsuarioRol)
class SeguridadUsuarioRolAdmin(SafeBaseAdmin):
    list_display = ['id_usuario', 'id_rol', 'id_carrera', 'fecha_asignacion_rol']
    list_filter = ['id_rol', 'id_carrera']
    search_fields = ['id_usuario__nombre_usuario']
    date_hierarchy = 'fecha_asignacion_rol'


# =============================================================================
#  MÓDULO 4 · CURRÍCULO
# =============================================================================

@admin.register(CurriculoAsignatura)
class CurriculoAsignaturaAdmin(SafeBaseAdmin):
    list_display = ['codigo_asignatura', 'nombre_asignatura', 'id_carrera', 'horas_semanales_asignatura', 'nivel_semestre']
    list_filter = ['id_carrera', 'nivel_semestre']
    search_fields = ['codigo_asignatura', 'nombre_asignatura']
    ordering = ['codigo_asignatura']


@admin.register(CurriculoAsignaturaCampo)
class CurriculoAsignaturaCampoAdmin(SafeBaseAdmin):
    list_display = ['id_asignatura', 'id_campo']
    list_filter = ['id_campo']
    raw_id_fields = ['id_asignatura', 'id_campo']


@admin.register(RelacionPosgradoCampo)
class RelacionPosgradoCampoAdmin(SafeBaseAdmin):
    list_display = ['id_posgrado', 'id_campo']
    list_filter = ['id_campo']
    raw_id_fields = ['id_posgrado', 'id_campo']


# =============================================================================
#  MÓDULO 5 · PLANIFICACIÓN
# =============================================================================

@admin.register(PlanificacionDemandaAcademica)
class PlanificacionDemandaAcademicaAdmin(SafeBaseAdmin):
    list_display = ['id_asignatura', 'id_carrera', 'id_periodo', 'proyeccion_estudiantes', 'numero_paralelos']
    list_filter = ['id_carrera', 'id_periodo']
    search_fields = ['id_asignatura__nombre_asignatura']
    raw_id_fields = ['id_asignatura', 'id_carrera', 'id_periodo']


@admin.register(PlanificacionAsignacionDocente)
class PlanificacionAsignacionDocenteAdmin(SafeBaseAdmin):
    list_display = ['id_docente', 'id_asignatura', 'id_carrera', 'id_periodo', 'paralelo_asignado', 'horas_clase', 'horas_complementarias']
    list_filter = ['id_carrera', 'id_periodo', 'nivel_semestre_asignado']
    search_fields = ['id_docente__nombres_completos', 'id_asignatura__nombre_asignatura']
    raw_id_fields = ['id_docente', 'id_asignatura', 'id_carrera', 'id_periodo', 'id_campo']


@admin.register(PlanificacionRepartoHoras)
class PlanificacionRepartoHorasAdmin(SafeBaseAdmin):
    list_display = ['id_docente', 'id_asignatura', 'id_periodo', 'nivel_paralelo', 'horas_presenciales_asignadas']
    list_filter = ['id_periodo']
    raw_id_fields = ['id_docente', 'id_asignatura', 'id_periodo']


@admin.register(PlanificacionMatrizF4)
class PlanificacionMatrizF4Admin(SafeBaseAdmin):
    list_display = ['id_docente', 'id_carrera', 'id_periodo', 'tipo_actividad', 'horas_actividad', 'numero_paralelos_actividad']
    list_filter = ['id_carrera', 'id_periodo', 'tipo_actividad', 'id_grado_afinidad']
    search_fields = ['id_docente__nombres_completos']
    raw_id_fields = ['id_docente', 'id_carrera', 'id_periodo', 'id_grado_afinidad']


@admin.register(PlanificacionAulaHorario)
class PlanificacionAulaHorarioAdmin(SafeBaseAdmin):
    list_display = ['nombre_aula', 'turno_horario', 'id_periodo', 'nivel_asignado']
    list_filter = ['turno_horario', 'id_periodo']
    search_fields = ['nombre_aula']


# =============================================================================
#  MÓDULO 6 · AUDITORÍA
# =============================================================================

@admin.register(AuditoriaRegistroCambios)
class AuditoriaRegistroCambiosAdmin(SafeBaseAdmin):
    list_display = ['fecha_hora_cambio', 'tipo_accion', 'nombre_tabla_afectada', 'id_registro_afectado', 'id_usuario', 'direccion_ip_origen']
    list_filter = ['tipo_accion', 'nombre_tabla_afectada']
    search_fields = ['nombre_tabla_afectada']
    date_hierarchy = 'fecha_hora_cambio'
    readonly_fields = ['id_registro_auditoria', 'fecha_hora_cambio', 'valor_anterior', 'valor_nuevo']


# =============================================================================
#  MÓDULO 7 · LIMITACIONES Y PLANIFICACIÓN COMPLEMENTARIA
# =============================================================================

@admin.register(Limitacion)
class LimitacionAdmin(SafeBaseAdmin):
    list_display = ['codigo_limitacion', 'nombre_limitacion', 'hora_minima', 'hora_maxima']
    search_fields = ['codigo_limitacion', 'nombre_limitacion']


@admin.register(HistorialLimitacion)
class HistorialLimitacionAdmin(SafeBaseAdmin):
    list_display = ['id_docente', 'id_limitacion', 'fecha_inicio_vigencia', 'fecha_fin_vigencia']
    list_filter = ['id_limitacion']
    search_fields = ['id_docente__nombres_completos']
    date_hierarchy = 'fecha_inicio_vigencia'
    raw_id_fields = ['id_docente', 'id_limitacion']


@admin.register(Cabecera)
class CabeceraAdmin(SafeBaseAdmin):
    list_display = ['descripcion_periodo']
    search_fields = ['descripcion_periodo']


@admin.register(Cuerpo)
class CuerpoAdmin(SafeBaseAdmin):
    list_display = ['id_cabecera', 'id_docente', 'horas']
    list_filter = ['id_cabecera']
    search_fields = ['id_docente__nombres_completos']
    raw_id_fields = ['id_docente', 'id_cabecera']


admin.site.site_header = 'Gestión Docente - FCACC · ULEAM'
admin.site.site_title = 'Gestión Docente'
admin.site.index_title = 'Panel de Administración Académica'
admin.site.site_url = None
