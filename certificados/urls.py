from django.urls import path

from . import views

app_name = 'certificados'

urlpatterns = [
    path('', views.generar_certificado, name='generar'),
    path('emitidos/', views.emisiones, name='emisiones'),
    path('emitidos/<int:pk>/', views.previsualizar, name='previsualizar'),
    path('firmantes/', views.firmantes, name='firmantes'),
    path('firmantes/<int:pk>/editar/', views.firmantes, name='firmante_editar'),
]
