from django.urls import path
from . import views

app_name = 'auditoria'

urlpatterns = [
    path('registros/', views.AuditoriaRegistroCambiosListView.as_view(), name='auditoriaregistrocambios_list'),
    path('registros/crear/', views.AuditoriaRegistroCambiosCreateView.as_view(), name='auditoriaregistrocambios_create'),
    path('registros/<int:pk>/editar/', views.AuditoriaRegistroCambiosUpdateView.as_view(), name='auditoriaregistrocambios_update'),
    path('registros/<int:pk>/eliminar/', views.AuditoriaRegistroCambiosDeleteView.as_view(), name='auditoriaregistrocambios_delete'),
]
