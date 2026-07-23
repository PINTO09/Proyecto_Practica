from django.shortcuts import redirect
from django.urls import reverse


class ForcePasswordChangeMiddleware:
    """Impide usar el sistema mientras se conserve la clave temporal."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, 'user', None)
        if user and user.is_authenticated and user.debe_cambiar_password:
            allowed = {
                reverse('core:cambiar_password_obligatorio'),
                reverse('core:logout'),
            }
            if request.path not in allowed and not request.path.startswith('/static/'):
                return redirect('core:cambiar_password_obligatorio')
        return self.get_response(request)
