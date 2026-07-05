from django.contrib import admin
from django.db import ProgrammingError, OperationalError
from django.shortcuts import render
from .models import (
    DocenteFcacc, DocenteTituloAcademico, DocenteCampoAfinidad,
    DocenteAsignacionCarreraPeriodo, DocenteCursoCapacitacion,
    DocenteParticipacionCurso, DocentePublicacionAcademica,
)


class SafeDocenteAdmin(admin.ModelAdmin):
    def _table_exists(self):
        try:
            self.model.objects.count()
            return True
        except (ProgrammingError, OperationalError):
            return False

    def changelist_view(self, request, extra_context=None):
        if not self._table_exists():
            extra = extra_context or {}
            extra.update({
                'title': self.model._meta.verbose_name_plural,
                'table_name': self.model._meta.db_table,
            })
            return render(request, 'admin/table_not_ready.html', extra)
        return super().changelist_view(request, extra_context)


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


@admin.register(DocenteFcacc)
class DocenteFcaccAdmin(SafeDocenteAdmin):
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
class DocenteTituloAcademicoAdmin(SafeDocenteAdmin):
    list_display = ['nombre_titulo', 'id_docente', 'id_pais', 'nivel_titulo', 'fecha_obtencion_titulo', 'numero_registro_senescyt']
    list_filter = ['nivel_titulo', 'id_pais']
    search_fields = ['nombre_titulo', 'numero_registro_senescyt', 'id_docente__nombres_completos']
    date_hierarchy = 'fecha_obtencion_titulo'
    raw_id_fields = ['id_docente']


@admin.register(DocenteCampoAfinidad)
class DocenteCampoAfinidadAdmin(SafeDocenteAdmin):
    list_display = ['id_docente', 'id_campo']
    list_filter = ['id_campo']
    search_fields = ['id_docente__nombres_completos']
    raw_id_fields = ['id_docente', 'id_campo']


@admin.register(DocenteAsignacionCarreraPeriodo)
class DocenteAsignacionCarreraPeriodoAdmin(SafeDocenteAdmin):
    list_display = ['id_docente', 'id_carrera', 'id_periodo', 'id_licencia', 'horas_otras_unidades_academicas']
    list_filter = ['id_carrera', 'id_periodo', 'id_licencia']
    search_fields = ['id_docente__nombres_completos']
    raw_id_fields = ['id_docente']


@admin.register(DocenteCursoCapacitacion)
class DocenteCursoCapacitacionAdmin(SafeDocenteAdmin):
    list_display = ['nombre_curso_capacitacion', 'id_tipo_curso', 'fecha_inicio_curso', 'fecha_fin_curso', 'horas_totales_curso']
    list_filter = ['id_tipo_curso']
    search_fields = ['nombre_curso_capacitacion']
    date_hierarchy = 'fecha_inicio_curso'


@admin.register(DocenteParticipacionCurso)
class DocenteParticipacionCursoAdmin(SafeDocenteAdmin):
    list_display = ['id_docente', 'id_curso', 'fecha_participacion']
    list_filter = ['fecha_participacion']
    search_fields = ['id_docente__nombres_completos', 'id_curso__nombre_curso_capacitacion']
    raw_id_fields = ['id_docente', 'id_curso']


@admin.register(DocentePublicacionAcademica)
class DocentePublicacionAcademicaAdmin(SafeDocenteAdmin):
    list_display = ['nombre_publicacion', 'id_docente', 'id_tipo_publicacion', 'fecha_publicacion']
    list_filter = ['id_tipo_publicacion']
    search_fields = ['nombre_publicacion', 'id_docente__nombres_completos']
    date_hierarchy = 'fecha_publicacion'
    raw_id_fields = ['id_docente']
