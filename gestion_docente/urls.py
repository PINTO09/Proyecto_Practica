from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render


def handler404(request, exception):
    return render(request, '404.html', status=404)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('catalogos/', include('catalogos.urls')),
    path('docentes/', include('docentes.urls')),
    path('curriculo/', include('curriculo.urls')),
    path('planificacion/', include('planificacion.urls')),
    path('auditoria/', include('auditoria.urls')),
    path('restricciones/', include('restricciones.urls')),
    path('reportes/', include('reportes.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
