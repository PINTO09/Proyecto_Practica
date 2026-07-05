from django.contrib import admin
from django.db import ProgrammingError, OperationalError
from django.shortcuts import render
from .models import Limitacion, HistorialLimitacion, Cabecera, Cuerpo


class SafeRestriccionesAdmin(admin.ModelAdmin):
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


@admin.register(Limitacion)
class LimitacionAdmin(SafeRestriccionesAdmin):
    list_display = ['codigo_limitacion', 'nombre_limitacion', 'hora_minima', 'hora_maxima']
    search_fields = ['codigo_limitacion', 'nombre_limitacion']


@admin.register(HistorialLimitacion)
class HistorialLimitacionAdmin(SafeRestriccionesAdmin):
    list_display = ['id_docente', 'id_limitacion', 'fecha_inicio_vigencia', 'fecha_fin_vigencia']
    list_filter = ['id_limitacion']
    search_fields = ['id_docente__nombres_completos']
    date_hierarchy = 'fecha_inicio_vigencia'
    raw_id_fields = ['id_docente', 'id_limitacion']


@admin.register(Cabecera)
class CabeceraAdmin(SafeRestriccionesAdmin):
    list_display = ['descripcion_periodo']
    search_fields = ['descripcion_periodo']


@admin.register(Cuerpo)
class CuerpoAdmin(SafeRestriccionesAdmin):
    list_display = ['id_cabecera', 'id_docente', 'horas']
    list_filter = ['id_cabecera']
    search_fields = ['id_docente__nombres_completos']
    raw_id_fields = ['id_docente', 'id_cabecera']
