from django.contrib import admin

from .models import CertificadoEmitido, FirmanteCertificado


@admin.register(FirmanteCertificado)
class FirmanteCertificadoAdmin(admin.ModelAdmin):
    list_display = ('nombres_completos', 'cargo', 'activo', 'orden')
    list_filter = ('activo',)


@admin.register(CertificadoEmitido)
class CertificadoEmitidoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'tipo', 'docente', 'firmante_nombre', 'fecha_emision')
    list_filter = ('tipo', 'fecha_emision')
    search_fields = ('codigo', 'docente__cedula_docente', 'docente__nombres_completos')
    readonly_fields = ('codigo', 'datos_certificados', 'creado_el')
