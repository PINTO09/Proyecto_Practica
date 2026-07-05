from django.urls import path
from . import views

app_name = 'restricciones'

urlpatterns = [
    path('limitaciones/', views.LimitacionListView.as_view(), name='limitacion_list'),
    path('limitaciones/crear/', views.LimitacionCreateView.as_view(), name='limitacion_create'),
    path('limitaciones/<int:pk>/editar/', views.LimitacionUpdateView.as_view(), name='limitacion_update'),
    path('limitaciones/<int:pk>/eliminar/', views.LimitacionDeleteView.as_view(), name='limitacion_delete'),
    path('historial/', views.HistorialLimitacionListView.as_view(), name='historiallimitacion_list'),
    path('historial/crear/', views.HistorialLimitacionCreateView.as_view(), name='historiallimitacion_create'),
    path('historial/<int:pk>/editar/', views.HistorialLimitacionUpdateView.as_view(), name='historiallimitacion_update'),
    path('historial/<int:pk>/eliminar/', views.HistorialLimitacionDeleteView.as_view(), name='historiallimitacion_delete'),
    path('cabeceras/', views.CabeceraListView.as_view(), name='cabecera_list'),
    path('cabeceras/crear/', views.CabeceraCreateView.as_view(), name='cabecera_create'),
    path('cabeceras/<int:pk>/editar/', views.CabeceraUpdateView.as_view(), name='cabecera_update'),
    path('cabeceras/<int:pk>/eliminar/', views.CabeceraDeleteView.as_view(), name='cabecera_delete'),
    path('cuerpos/', views.CuerpoListView.as_view(), name='cuerpo_list'),
    path('cuerpos/crear/', views.CuerpoCreateView.as_view(), name='cuerpo_create'),
    path('cuerpos/<int:pk>/editar/', views.CuerpoUpdateView.as_view(), name='cuerpo_update'),
    path('cuerpos/<int:pk>/eliminar/', views.CuerpoDeleteView.as_view(), name='cuerpo_delete'),
]
