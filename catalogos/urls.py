from django.urls import path
from . import views

app_name = 'catalogos'

urlpatterns = [
    path('carreras/', views.CatalogoCarreraListView.as_view(), name='catalogocarrera_list'),
    path('carreras/crear/', views.CatalogoCarreraCreateView.as_view(), name='catalogocarrera_create'),
    path('carreras/<int:pk>/editar/', views.CatalogoCarreraUpdateView.as_view(), name='catalogocarrera_update'),
    path('carreras/<int:pk>/eliminar/', views.CatalogoCarreraDeleteView.as_view(), name='catalogocarrera_delete'),

    path('modalidades/', views.CatalogoModalidadContratacionListView.as_view(), name='catalogomodalidadcontratacion_list'),
    path('modalidades/crear/', views.CatalogoModalidadContratacionCreateView.as_view(), name='catalogomodalidadcontratacion_create'),
    path('modalidades/<int:pk>/editar/', views.CatalogoModalidadContratacionUpdateView.as_view(), name='catalogomodalidadcontratacion_update'),
    path('modalidades/<int:pk>/eliminar/', views.CatalogoModalidadContratacionDeleteView.as_view(), name='catalogomodalidadcontratacion_delete'),

    path('dedicaciones/', views.CatalogoDedicacionHorariaListView.as_view(), name='catalogodedicacionhoraria_list'),
    path('dedicaciones/crear/', views.CatalogoDedicacionHorariaCreateView.as_view(), name='catalogodedicacionhoraria_create'),
    path('dedicaciones/<int:pk>/editar/', views.CatalogoDedicacionHorariaUpdateView.as_view(), name='catalogodedicacionhoraria_update'),
    path('dedicaciones/<int:pk>/eliminar/', views.CatalogoDedicacionHorariaDeleteView.as_view(), name='catalogodedicacionhoraria_delete'),

    path('tipos-docente/', views.CatalogoTipoDocenteListView.as_view(), name='catalogotipodocente_list'),
    path('tipos-docente/crear/', views.CatalogoTipoDocenteCreateView.as_view(), name='catalogotipodocente_create'),
    path('tipos-docente/<int:pk>/editar/', views.CatalogoTipoDocenteUpdateView.as_view(), name='catalogotipodocente_update'),
    path('tipos-docente/<int:pk>/eliminar/', views.CatalogoTipoDocenteDeleteView.as_view(), name='catalogotipodocente_delete'),

    path('licencias/', views.CatalogoTipoLicenciaListView.as_view(), name='catalogotipolicencia_list'),
    path('licencias/crear/', views.CatalogoTipoLicenciaCreateView.as_view(), name='catalogotipolicencia_create'),
    path('licencias/<int:pk>/editar/', views.CatalogoTipoLicenciaUpdateView.as_view(), name='catalogotipolicencia_update'),
    path('licencias/<int:pk>/eliminar/', views.CatalogoTipoLicenciaDeleteView.as_view(), name='catalogotipolicencia_delete'),

    path('paises/', views.CatalogoPaisListView.as_view(), name='catalogopais_list'),
    path('paises/crear/', views.CatalogoPaisCreateView.as_view(), name='catalogopais_create'),
    path('paises/<int:pk>/editar/', views.CatalogoPaisUpdateView.as_view(), name='catalogopais_update'),
    path('paises/<int:pk>/eliminar/', views.CatalogoPaisDeleteView.as_view(), name='catalogopais_delete'),

    path('titulos-posgrado/', views.CatalogoTituloPosgradoListView.as_view(), name='catalogotituloposgrado_list'),
    path('titulos-posgrado/crear/', views.CatalogoTituloPosgradoCreateView.as_view(), name='catalogotituloposgrado_create'),
    path('titulos-posgrado/<int:pk>/editar/', views.CatalogoTituloPosgradoUpdateView.as_view(), name='catalogotituloposgrado_update'),
    path('titulos-posgrado/<int:pk>/eliminar/', views.CatalogoTituloPosgradoDeleteView.as_view(), name='catalogotituloposgrado_delete'),

    path('campos/', views.CatalogoCampoConocimientoListView.as_view(), name='catalogocampoconocimiento_list'),
    path('campos/crear/', views.CatalogoCampoConocimientoCreateView.as_view(), name='catalogocampoconocimiento_create'),
    path('campos/<int:pk>/editar/', views.CatalogoCampoConocimientoUpdateView.as_view(), name='catalogocampoconocimiento_update'),
    path('campos/<int:pk>/eliminar/', views.CatalogoCampoConocimientoDeleteView.as_view(), name='catalogocampoconocimiento_delete'),

    path('grados-afinidad/', views.CatalogoGradoAfinidadListView.as_view(), name='catalogogradoafinidad_list'),
    path('grados-afinidad/crear/', views.CatalogoGradoAfinidadCreateView.as_view(), name='catalogogradoafinidad_create'),
    path('grados-afinidad/<int:pk>/editar/', views.CatalogoGradoAfinidadUpdateView.as_view(), name='catalogogradoafinidad_update'),
    path('grados-afinidad/<int:pk>/eliminar/', views.CatalogoGradoAfinidadDeleteView.as_view(), name='catalogogradoafinidad_delete'),

    path('tipos-publicacion/', views.CatalogoTipoPublicacionListView.as_view(), name='catalogotipopublicacion_list'),
    path('tipos-publicacion/crear/', views.CatalogoTipoPublicacionCreateView.as_view(), name='catalogotipopublicacion_create'),
    path('tipos-publicacion/<int:pk>/editar/', views.CatalogoTipoPublicacionUpdateView.as_view(), name='catalogotipopublicacion_update'),
    path('tipos-publicacion/<int:pk>/eliminar/', views.CatalogoTipoPublicacionDeleteView.as_view(), name='catalogotipopublicacion_delete'),

    path('tipos-curso/', views.CatalogoTipoCursoCapacitacionListView.as_view(), name='catalogotipocursocapacitacion_list'),
    path('tipos-curso/crear/', views.CatalogoTipoCursoCapacitacionCreateView.as_view(), name='catalogotipocursocapacitacion_create'),
    path('tipos-curso/<int:pk>/editar/', views.CatalogoTipoCursoCapacitacionUpdateView.as_view(), name='catalogotipocursocapacitacion_update'),
    path('tipos-curso/<int:pk>/eliminar/', views.CatalogoTipoCursoCapacitacionDeleteView.as_view(), name='catalogotipocursocapacitacion_delete'),

    path('periodos/', views.CatalogoPeriodoAcademicoListView.as_view(), name='catalogoperiodoacademico_list'),
    path('periodos/crear/', views.CatalogoPeriodoAcademicoCreateView.as_view(), name='catalogoperiodoacademico_create'),
    path('periodos/<int:pk>/editar/', views.CatalogoPeriodoAcademicoUpdateView.as_view(), name='catalogoperiodoacademico_update'),
    path('periodos/<int:pk>/eliminar/', views.CatalogoPeriodoAcademicoDeleteView.as_view(), name='catalogoperiodoacademico_delete'),

    path('relaciones-carrera-periodo/', views.RelacionCarreraPeriodoListView.as_view(), name='relacioncarreraperiodo_list'),
    path('relaciones-carrera-periodo/crear/', views.RelacionCarreraPeriodoCreateView.as_view(), name='relacioncarreraperiodo_create'),
    path('relaciones-carrera-periodo/<int:pk>/editar/', views.RelacionCarreraPeriodoUpdateView.as_view(), name='relacioncarreraperiodo_update'),
    path('relaciones-carrera-periodo/<int:pk>/eliminar/', views.RelacionCarreraPeriodoDeleteView.as_view(), name='relacioncarreraperiodo_delete'),

    path('limites/', views.LimiteHorarioListView.as_view(), name='limitehorario_list'),
    path('limites/crear/', views.LimiteHorarioCreateView.as_view(), name='limitehorario_create'),
    path('limites/<int:pk>/editar/', views.LimiteHorarioUpdateView.as_view(), name='limitehorario_update'),
    path('limites/<int:pk>/eliminar/', views.LimiteHorarioDeleteView.as_view(), name='limitehorario_delete'),
]
