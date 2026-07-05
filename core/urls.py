from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('api/modelo-info/', views.api_modelo_info, name='api_modelo_info'),
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login_docente'),
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
    path('usuarios/autoridad/', views.usuarios_por_rol_view, {'rol': 'Autoridad'}, name='usuarios_autoridad'),
    path('usuarios/coordinador/', views.usuarios_por_rol_view, {'rol': 'Coordinador'}, name='usuarios_coordinador'),
    path('usuarios/funcionario/', views.usuarios_por_rol_view, {'rol': 'Funcionario'}, name='usuarios_funcionario'),
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
]
