from django.contrib import admin
from django import forms
from django.db import ProgrammingError, OperationalError
from django.shortcuts import render
from django.contrib import messages
from .models import (
    CatalogoCarrera, CatalogoModalidadContratacion,
    CatalogoDedicacionHoraria, CatalogoTipoDocente,
    CatalogoTipoLicencia, CatalogoPais, CatalogoTituloPosgrado,
    CatalogoCampoConocimiento, CatalogoGradoAfinidad,
    CatalogoTipoPublicacion, CatalogoTipoCursoCapacitacion,
    CatalogoPeriodoAcademico, RelacionCarreraPeriodo,
)


class SafeCatalogoAdmin(admin.ModelAdmin):
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


@admin.register(CatalogoCarrera)
class CatalogoCarreraAdmin(SafeCatalogoAdmin):
    list_display = ['codigo_carrera', 'nombre_carrera', 'carrera_activa']
    list_filter = ['carrera_activa']
    search_fields = ['codigo_carrera', 'nombre_carrera']
    ordering = ['codigo_carrera']


@admin.register(CatalogoModalidadContratacion)
class CatalogoModalidadContratacionAdmin(SafeCatalogoAdmin):
    list_display = ['codigo_modalidad', 'nombre_modalidad']
    search_fields = ['nombre_modalidad']


@admin.register(CatalogoDedicacionHoraria)
class CatalogoDedicacionHorariaAdmin(SafeCatalogoAdmin):
    list_display = ['codigo_dedicacion', 'nombre_dedicacion']
    search_fields = ['nombre_dedicacion']


@admin.register(CatalogoTipoDocente)
class CatalogoTipoDocenteAdmin(SafeCatalogoAdmin):
    list_display = ['codigo_tipo_docente', 'nombre_tipo_docente']
    search_fields = ['nombre_tipo_docente']


@admin.register(CatalogoTipoLicencia)
class CatalogoTipoLicenciaAdmin(SafeCatalogoAdmin):
    list_display = ['codigo_licencia', 'nombre_licencia']
    search_fields = ['nombre_licencia']


@admin.register(CatalogoPais)
class CatalogoPaisAdmin(SafeCatalogoAdmin):
    list_display = ['codigo_iso_pais', 'nombre_pais', 'nombre_nacionalidad']
    search_fields = ['nombre_pais', 'nombre_nacionalidad']
    ordering = ['nombre_pais']


@admin.register(CatalogoTituloPosgrado)
class CatalogoTituloPosgradoAdmin(SafeCatalogoAdmin):
    list_display = ['codigo_posgrado', 'nombre_titulo_posgrado']
    search_fields = ['nombre_titulo_posgrado']


@admin.register(CatalogoCampoConocimiento)
class CatalogoCampoConocimientoAdmin(SafeCatalogoAdmin):
    list_display = ['codigo_campo', 'nombre_campo_conocimiento']
    search_fields = ['nombre_campo_conocimiento']


@admin.register(CatalogoGradoAfinidad)
class CatalogoGradoAfinidadAdmin(SafeCatalogoAdmin):
    list_display = ['codigo_grado_afinidad', 'nombre_grado_afinidad', 'nivel_prioridad']
    list_filter = ['nivel_prioridad']


@admin.register(CatalogoTipoPublicacion)
class CatalogoTipoPublicacionAdmin(SafeCatalogoAdmin):
    list_display = ['codigo_tipo_publicacion', 'nombre_tipo_publicacion']
    search_fields = ['nombre_tipo_publicacion']


@admin.register(CatalogoTipoCursoCapacitacion)
class CatalogoTipoCursoCapacitacionAdmin(SafeCatalogoAdmin):
    list_display = ['codigo_tipo_curso', 'nombre_tipo_curso']
    search_fields = ['nombre_tipo_curso']


@admin.register(CatalogoPeriodoAcademico)
class CatalogoPeriodoAcademicoAdmin(SafeCatalogoAdmin):
    list_display = ['codigo_periodo', 'nombre_periodo', 'periodo_activo', 'fecha_inicio_periodo', 'fecha_fin_periodo']
    list_filter = ['periodo_activo']
    search_fields = ['codigo_periodo', 'nombre_periodo']
    date_hierarchy = 'fecha_inicio_periodo'


@admin.register(RelacionCarreraPeriodo)
class RelacionCarreraPeriodoAdmin(SafeCatalogoAdmin):
    list_display = ['id_carrera', 'id_periodo']
    list_filter = ['id_carrera', 'id_periodo']
