from django.urls import path
from . import views

app_name = 'curriculo'

urlpatterns = [
    path('asignaturas/', views.CurriculoAsignaturaListView.as_view(), name='curriculoasignatura_list'),
    path('asignaturas/crear/', views.CurriculoAsignaturaCreateView.as_view(), name='curriculoasignatura_create'),
    path('asignaturas/<int:pk>/editar/', views.CurriculoAsignaturaUpdateView.as_view(), name='curriculoasignatura_update'),
    path('asignaturas/<int:pk>/eliminar/', views.CurriculoAsignaturaDeleteView.as_view(), name='curriculoasignatura_delete'),
    path('campos/', views.CurriculoAsignaturaCampoListView.as_view(), name='curriculoasignaturacampo_list'),
    path('campos/crear/', views.CurriculoAsignaturaCampoCreateView.as_view(), name='curriculoasignaturacampo_create'),
    path('campos/<int:pk>/editar/', views.CurriculoAsignaturaCampoUpdateView.as_view(), name='curriculoasignaturacampo_update'),
    path('campos/<int:pk>/eliminar/', views.CurriculoAsignaturaCampoDeleteView.as_view(), name='curriculoasignaturacampo_delete'),
    path('posgrados/', views.RelacionPosgradoCampoListView.as_view(), name='relacionposgradocampo_list'),
    path('posgrados/crear/', views.RelacionPosgradoCampoCreateView.as_view(), name='relacionposgradocampo_create'),
    path('posgrados/<int:pk>/editar/', views.RelacionPosgradoCampoUpdateView.as_view(), name='relacionposgradocampo_update'),
    path('posgrados/<int:pk>/eliminar/', views.RelacionPosgradoCampoDeleteView.as_view(), name='relacionposgradocampo_delete'),
]
