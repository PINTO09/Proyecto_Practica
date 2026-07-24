from django.urls import path
from . import views

app_name = 'reportes'

urlpatterns = [
    path('', views.centro_reportes, name='centro_reportes'),
    path('carga-docente/', views.reporte_carga_docente, name='reporte_carga_docente'),
    path('resumen-horas/', views.reporte_resumen_horas, name='reporte_resumen_horas'),
    path('malla-curricular/', views.reporte_malla_curricular, name='reporte_malla_curricular'),
    path('docentes-formacion/', views.reporte_docentes_formacion, name='reporte_docentes_formacion'),
    path('docentes-campos/', views.reporte_docentes_campos, name='reporte_docentes_campos'),
    path('exportar/carga-docente/', views.export_carga_docente_excel, name='export_carga_docente'),
    path('exportar/malla/', views.export_malla_excel, name='export_malla'),
    path('exportar/resumen-horas/', views.export_resumen_horas_excel, name='export_resumen_horas'),
    path('exportar/planificacion-general/', views.export_planificacion_general_excel, name='export_planificacion_general'),
    path('exportar/planificacion-detallada/', views.export_planificacion_detallada_excel, name='export_planificacion_detallada'),
    path('exportar/matriz-f4-mkt/', views.export_matriz_f4_mkt_excel, name='export_matriz_f4_mkt'),
    path('descargar/planificacion-original/', views.descargar_planificacion_original, name='descargar_planificacion_original'),

]
