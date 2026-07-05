from django.contrib import admin
from django.db import ProgrammingError, OperationalError
from django.shortcuts import render
from .models import (
    CurriculoAsignatura, CurriculoAsignaturaCampo, RelacionPosgradoCampo,
)


class SafeCurriculoAdmin(admin.ModelAdmin):
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


@admin.register(CurriculoAsignatura)
class CurriculoAsignaturaAdmin(SafeCurriculoAdmin):
    list_display = ['codigo_asignatura', 'nombre_asignatura', 'id_carrera', 'horas_semanales_asignatura', 'nivel_semestre']
    list_filter = ['id_carrera', 'nivel_semestre']
    search_fields = ['codigo_asignatura', 'nombre_asignatura']
    ordering = ['codigo_asignatura']


@admin.register(CurriculoAsignaturaCampo)
class CurriculoAsignaturaCampoAdmin(SafeCurriculoAdmin):
    list_display = ['id_asignatura', 'id_campo']
    list_filter = ['id_campo']
    raw_id_fields = ['id_asignatura', 'id_campo']


@admin.register(RelacionPosgradoCampo)
class RelacionPosgradoCampoAdmin(SafeCurriculoAdmin):
    list_display = ['id_posgrado', 'id_campo']
    list_filter = ['id_campo']
    raw_id_fields = ['id_posgrado', 'id_campo']
