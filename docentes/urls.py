from django.urls import path
from . import views

app_name = 'docentes'

urlpatterns = [
    path('api/docente-por-documento/', views.api_docente_por_documento, name='api_docente_por_documento'),
    path('docentes/', views.DocenteFcaccListView.as_view(), name='docentefcacc_list'),
    path('docentes/crear/', views.DocenteFcaccCreateView.as_view(), name='docentefcacc_create'),
    path('docentes/<int:pk>/editar/', views.DocenteFcaccUpdateView.as_view(), name='docentefcacc_update'),
    path('docentes/<int:pk>/eliminar/', views.DocenteFcaccDeleteView.as_view(), name='docentefcacc_delete'),
    path('titulos/', views.DocenteTituloAcademicoListView.as_view(), name='docentetituloacademico_list'),
    path('titulos/crear/', views.DocenteTituloAcademicoCreateView.as_view(), name='docentetituloacademico_create'),
    path('titulos/<int:pk>/editar/', views.DocenteTituloAcademicoUpdateView.as_view(), name='docentetituloacademico_update'),
    path('titulos/<int:pk>/eliminar/', views.DocenteTituloAcademicoDeleteView.as_view(), name='docentetituloacademico_delete'),
    path('campos/', views.DocenteCampoAfinidadListView.as_view(), name='docentecampoafinidad_list'),
    path('campos/crear/', views.DocenteCampoAfinidadCreateView.as_view(), name='docentecampoafinidad_create'),
    path('campos/<int:pk>/editar/', views.DocenteCampoAfinidadUpdateView.as_view(), name='docentecampoafinidad_update'),
    path('campos/<int:pk>/eliminar/', views.DocenteCampoAfinidadDeleteView.as_view(), name='docentecampoafinidad_delete'),
    path('asignaciones/', views.DocenteAsignacionCarreraPeriodoListView.as_view(), name='docenteasignacioncarreraperiodo_list'),
    path('asignaciones/crear/', views.DocenteAsignacionCarreraPeriodoCreateView.as_view(), name='docenteasignacioncarreraperiodo_create'),
    path('asignaciones/<int:pk>/editar/', views.DocenteAsignacionCarreraPeriodoUpdateView.as_view(), name='docenteasignacioncarreraperiodo_update'),
    path('asignaciones/<int:pk>/eliminar/', views.DocenteAsignacionCarreraPeriodoDeleteView.as_view(), name='docenteasignacioncarreraperiodo_delete'),
    path('cursos/', views.DocenteCursoCapacitacionListView.as_view(), name='docentecursocapacitacion_list'),
    path('cursos/crear/', views.DocenteCursoCapacitacionCreateView.as_view(), name='docentecursocapacitacion_create'),
    path('cursos/<int:pk>/editar/', views.DocenteCursoCapacitacionUpdateView.as_view(), name='docentecursocapacitacion_update'),
    path('cursos/<int:pk>/eliminar/', views.DocenteCursoCapacitacionDeleteView.as_view(), name='docentecursocapacitacion_delete'),
    path('participaciones/', views.DocenteParticipacionCursoListView.as_view(), name='docenteparticipacioncurso_list'),
    path('participaciones/crear/', views.DocenteParticipacionCursoCreateView.as_view(), name='docenteparticipacioncurso_create'),
    path('participaciones/<int:pk>/editar/', views.DocenteParticipacionCursoUpdateView.as_view(), name='docenteparticipacioncurso_update'),
    path('participaciones/<int:pk>/eliminar/', views.DocenteParticipacionCursoDeleteView.as_view(), name='docenteparticipacioncurso_delete'),
    path('publicaciones/', views.DocentePublicacionAcademicaListView.as_view(), name='docentepublicacionacademica_list'),
    path('publicaciones/crear/', views.DocentePublicacionAcademicaCreateView.as_view(), name='docentepublicacionacademica_create'),
    path('publicaciones/<int:pk>/editar/', views.DocentePublicacionAcademicaUpdateView.as_view(), name='docentepublicacionacademica_update'),
    path('publicaciones/<int:pk>/eliminar/', views.DocentePublicacionAcademicaDeleteView.as_view(), name='docentepublicacionacademica_delete'),
]
