from django.urls import path, re_path
from . import views
from . import views_api

app_name = 'core'

urlpatterns = [
    path('', views.login_view, name='login'),
    path('login/docente/', views.login_view, name='login_docente'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('logout/', views.logout_view, name='logout'),
    path('perfil/', views.mi_perfil_view, name='mi_perfil'),
    path('mi-docente/', views.mi_docente_view, name='mi_docente'),
    path('titulos/', views.mis_titulos_view, name='mis_titulos'),
    path('titulos/crear/', views.crear_titulo_view, name='crear_titulo'),
    path('publicaciones/', views.mis_publicaciones_view, name='mis_publicaciones'),
    path('publicaciones/crear/', views.crear_publicacion_view, name='crear_publicacion'),
    path('documentos/', views.mis_documentos_view, name='mis_documentos'),
    path('documentos/crear/', views.subir_documento_view, name='subir_documento'),
    path('cursos/', views.mis_cursos_view, name='mis_cursos'),
    path('usuarios/', views.usuarios_list_view, name='usuarios_list'),
    path('usuarios/crear/', views.usuario_crear_view, name='usuario_crear'),
    path('usuarios/<int:usuario_id>/editar/', views.usuario_editar_view, name='usuario_editar'),

    # Módulos CRUD (7 módulos)
    path('modulo/catalogos/', views.modulo_view, {'slug': 'catalogos'}, name='modulo_catalogos'),
    path('modulo/docentes/', views.modulo_view, {'slug': 'docentes'}, name='modulo_docentes'),
    path('modulo/seguridad/', views.modulo_view, {'slug': 'seguridad'}, name='modulo_seguridad'),
    path('modulo/curriculo/', views.modulo_view, {'slug': 'curriculo'}, name='modulo_curriculo'),
    path('modulo/planificacion/', views.modulo_view, {'slug': 'planificacion'}, name='modulo_planificacion'),
    path('modulo/auditoria/', views.modulo_view, {'slug': 'auditoria'}, name='modulo_auditoria'),
    path('modulo/restricciones/', views.modulo_view, {'slug': 'restricciones'}, name='modulo_restricciones'),

    # API CRUD genérica para SPA
    path('api/<str:model_name>/fields/', views_api.api_fields, name='api_fields'),
    path('api/<str:model_name>/list/', views_api.api_list, name='api_list'),
    path('api/<str:model_name>/create/', views_api.api_create, name='api_create'),
    path('api/<str:model_name>/<int:pk>/update/', views_api.api_update, name='api_update'),
    path('api/<str:model_name>/<int:pk>/delete/', views_api.api_delete, name='api_delete'),
    # Vista SPA para CRUD de un modelo específico
    path('crud/<str:model_name>/', views.crud_spa_view, name='crud_spa'),
]
