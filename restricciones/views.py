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
    form_field_order = (
        'id_docente', 'id_limitacion',
        'fecha_inicio_vigencia', 'fecha_fin_vigencia',
    )

class HistorialLimitacionUpdateView(CrudUpdateView):
    model = HistorialLimitacion
    form_field_order = HistorialLimitacionCreateView.form_field_order

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
