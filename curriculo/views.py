from core.crud_base import CrudListView, CrudCreateView, CrudUpdateView, CrudDeleteView
from .models import CurriculoAsignatura, CurriculoAsignaturaCampo, RelacionPosgradoCampo


class CurriculoAsignaturaListView(CrudListView):
    model = CurriculoAsignatura


class CurriculoAsignaturaCreateView(CrudCreateView):
    model = CurriculoAsignatura

class CurriculoAsignaturaUpdateView(CrudUpdateView):
    model = CurriculoAsignatura

class CurriculoAsignaturaDeleteView(CrudDeleteView):
    model = CurriculoAsignatura


class CurriculoAsignaturaCampoListView(CrudListView):
    model = CurriculoAsignaturaCampo


class CurriculoAsignaturaCampoCreateView(CrudCreateView):
    model = CurriculoAsignaturaCampo

class CurriculoAsignaturaCampoUpdateView(CrudUpdateView):
    model = CurriculoAsignaturaCampo

class CurriculoAsignaturaCampoDeleteView(CrudDeleteView):
    model = CurriculoAsignaturaCampo


class RelacionPosgradoCampoListView(CrudListView):
    model = RelacionPosgradoCampo


class RelacionPosgradoCampoCreateView(CrudCreateView):
    model = RelacionPosgradoCampo

class RelacionPosgradoCampoUpdateView(CrudUpdateView):
    model = RelacionPosgradoCampo

class RelacionPosgradoCampoDeleteView(CrudDeleteView):
    model = RelacionPosgradoCampo
