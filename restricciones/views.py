from core.crud_base import CrudListView, CrudCreateView, CrudUpdateView, CrudDeleteView
from .models import Limitacion, HistorialLimitacion, Cabecera, Cuerpo


class LimitacionListView(CrudListView):
    model = Limitacion


class LimitacionCreateView(CrudCreateView):
    model = Limitacion

class LimitacionUpdateView(CrudUpdateView):
    model = Limitacion

class LimitacionDeleteView(CrudDeleteView):
    model = Limitacion


class HistorialLimitacionListView(CrudListView):
    model = HistorialLimitacion


class HistorialLimitacionCreateView(CrudCreateView):
    model = HistorialLimitacion

class HistorialLimitacionUpdateView(CrudUpdateView):
    model = HistorialLimitacion

class HistorialLimitacionDeleteView(CrudDeleteView):
    model = HistorialLimitacion


class CabeceraListView(CrudListView):
    model = Cabecera


class CabeceraCreateView(CrudCreateView):
    model = Cabecera

class CabeceraUpdateView(CrudUpdateView):
    model = Cabecera

class CabeceraDeleteView(CrudDeleteView):
    model = Cabecera


class CuerpoListView(CrudListView):
    model = Cuerpo


class CuerpoCreateView(CrudCreateView):
    model = Cuerpo

class CuerpoUpdateView(CrudUpdateView):
    model = Cuerpo

class CuerpoDeleteView(CrudDeleteView):
    model = Cuerpo
