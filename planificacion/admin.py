from django.contrib import admin
from django.db import ProgrammingError, OperationalError
from django.shortcuts import render
from .models import (
    PlanificacionDemandaAcademica, PlanificacionAsignacionDocente,
    PlanificacionRepartoHoras, PlanificacionMatrizF4, PlanificacionAulaHorario,
)


class SafePlanificacionAdmin(admin.ModelAdmin):
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


@admin.register(PlanificacionDemandaAcademica)
class PlanificacionDemandaAcademicaAdmin(SafePlanificacionAdmin):
    list_display = ['id_asignatura', 'id_carrera', 'id_periodo', 'proyeccion_estudiantes', 'numero_paralelos']
    list_filter = ['id_carrera', 'id_periodo']
    search_fields = ['id_asignatura__nombre_asignatura']
    raw_id_fields = ['id_asignatura', 'id_carrera', 'id_periodo']


@admin.register(PlanificacionAsignacionDocente)
class PlanificacionAsignacionDocenteAdmin(SafePlanificacionAdmin):
    list_display = ['id_docente', 'id_asignatura', 'id_carrera', 'id_periodo', 'paralelo_asignado', 'horas_clase', 'horas_complementarias']
    list_filter = ['id_carrera', 'id_periodo', 'nivel_semestre_asignado']
    search_fields = ['id_docente__nombres_completos', 'id_asignatura__nombre_asignatura']
    raw_id_fields = ['id_docente', 'id_asignatura', 'id_carrera', 'id_periodo', 'id_campo']


@admin.register(PlanificacionRepartoHoras)
class PlanificacionRepartoHorasAdmin(SafePlanificacionAdmin):
    list_display = ['id_docente', 'id_asignatura', 'id_periodo', 'nivel_paralelo', 'horas_presenciales_asignadas']
    list_filter = ['id_periodo']
    raw_id_fields = ['id_docente', 'id_asignatura', 'id_periodo']


@admin.register(PlanificacionMatrizF4)
class PlanificacionMatrizF4Admin(SafePlanificacionAdmin):
    list_display = ['id_docente', 'id_carrera', 'id_periodo', 'tipo_actividad', 'horas_actividad', 'numero_paralelos_actividad']
    list_filter = ['id_carrera', 'id_periodo', 'tipo_actividad', 'id_grado_afinidad']
    search_fields = ['id_docente__nombres_completos']
    raw_id_fields = ['id_docente', 'id_carrera', 'id_periodo', 'id_grado_afinidad']


@admin.register(PlanificacionAulaHorario)
class PlanificacionAulaHorarioAdmin(SafePlanificacionAdmin):
    list_display = ['nombre_aula', 'turno_horario', 'id_periodo', 'nivel_asignado']
    list_filter = ['turno_horario', 'id_periodo']
    search_fields = ['nombre_aula']
