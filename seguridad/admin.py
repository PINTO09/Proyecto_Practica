from django.contrib import admin
from django.db import ProgrammingError, OperationalError
from django.shortcuts import render
from .models import SeguridadRol, SeguridadUsuario, SeguridadUsuarioRol


class SafeSeguridadAdmin(admin.ModelAdmin):
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


@admin.register(SeguridadRol)
class SeguridadRolAdmin(SafeSeguridadAdmin):
    list_display = ['codigo_rol', 'nombre_rol', 'rol_activo']
    list_filter = ['rol_activo']
    search_fields = ['codigo_rol', 'nombre_rol']


@admin.register(SeguridadUsuario)
class SeguridadUsuarioAdmin(SafeSeguridadAdmin):
    list_display = ['nombre_usuario', 'id_docente', 'usuario_activo', 'fecha_ultimo_acceso', 'fecha_creacion_usuario']
    list_filter = ['usuario_activo']
    search_fields = ['nombre_usuario', 'id_docente__nombres_completos']
    date_hierarchy = 'fecha_creacion_usuario'
    readonly_fields = ['contrasena_hash']


@admin.register(SeguridadUsuarioRol)
class SeguridadUsuarioRolAdmin(SafeSeguridadAdmin):
    list_display = ['id_usuario', 'id_rol', 'id_carrera', 'fecha_asignacion_rol']
    list_filter = ['id_rol', 'id_carrera']
    search_fields = ['id_usuario__nombre_usuario']
    date_hierarchy = 'fecha_asignacion_rol'
