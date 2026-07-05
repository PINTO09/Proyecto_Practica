from django.contrib import admin
from django.db import ProgrammingError, OperationalError
from django.shortcuts import render
from .models import AuditoriaRegistroCambios


class SafeAuditoriaAdmin(admin.ModelAdmin):
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


@admin.register(AuditoriaRegistroCambios)
class AuditoriaRegistroCambiosAdmin(SafeAuditoriaAdmin):
    list_display = ['fecha_hora_cambio', 'tipo_accion', 'nombre_tabla_afectada', 'id_registro_afectado', 'id_usuario', 'direccion_ip_origen']
    list_filter = ['tipo_accion', 'nombre_tabla_afectada']
    search_fields = ['nombre_tabla_afectada']
    date_hierarchy = 'fecha_hora_cambio'
    readonly_fields = ['id_registro_auditoria', 'fecha_hora_cambio', 'valor_anterior', 'valor_nuevo']
