from django.urls import path
from . import views

app_name = 'seguridad'

urlpatterns = [
    path('roles/', views.SeguridadRolListView.as_view(), name='seguridadrol_list'),
    path('roles/crear/', views.SeguridadRolCreateView.as_view(), name='seguridadrol_create'),
    path('roles/<int:pk>/editar/', views.SeguridadRolUpdateView.as_view(), name='seguridadrol_update'),
    path('roles/<int:pk>/eliminar/', views.SeguridadRolDeleteView.as_view(), name='seguridadrol_delete'),
    path('usuarios/', views.SeguridadUsuarioListView.as_view(), name='seguridadusuario_list'),
    path('usuarios/crear/', views.SeguridadUsuarioCreateView.as_view(), name='seguridadusuario_create'),
    path('usuarios/<int:pk>/editar/', views.SeguridadUsuarioUpdateView.as_view(), name='seguridadusuario_update'),
    path('usuarios/<int:pk>/eliminar/', views.SeguridadUsuarioDeleteView.as_view(), name='seguridadusuario_delete'),
    path('usuarios-roles/', views.SeguridadUsuarioRolListView.as_view(), name='seguridadusuariorol_list'),
    path('usuarios-roles/crear/', views.SeguridadUsuarioRolCreateView.as_view(), name='seguridadusuariorol_create'),
    path('usuarios-roles/<int:pk>/editar/', views.SeguridadUsuarioRolUpdateView.as_view(), name='seguridadusuariorol_update'),
    path('usuarios-roles/<int:pk>/eliminar/', views.SeguridadUsuarioRolDeleteView.as_view(), name='seguridadusuariorol_delete'),
]
