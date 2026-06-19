from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.login_view, name='login'),
    path('login/docente/', views.login_view, name='login_docente'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('logout/', views.logout_view, name='logout'),
    path('perfil/', views.mi_perfil_view, name='mi_perfil'),
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
]
