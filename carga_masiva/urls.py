from django.urls import path
from . import views

app_name = 'carga_masiva'

urlpatterns = [
    path('subir/', views.subir_archivos, name='subir'),
    path('previsualizar/', views.previsualizar, name='previsualizar'),
    path('confirmar/', views.confirmar, name='confirmar'),
    path('confirmado/', views.confirmado, name='confirmado'),
]
