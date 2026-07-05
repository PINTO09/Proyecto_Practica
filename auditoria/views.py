from core.crud_base import CrudListView, CrudCreateView, CrudUpdateView, CrudDeleteView
from .models import AuditoriaRegistroCambios


class AuditoriaRegistroCambiosListView(CrudListView):
    model = AuditoriaRegistroCambios


class AuditoriaRegistroCambiosCreateView(CrudCreateView):
    model = AuditoriaRegistroCambios

class AuditoriaRegistroCambiosUpdateView(CrudUpdateView):
    model = AuditoriaRegistroCambios

class AuditoriaRegistroCambiosDeleteView(CrudDeleteView):
    model = AuditoriaRegistroCambios
