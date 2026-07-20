from core.crud_base import CrudListView, CrudCreateView, CrudUpdateView, CrudDeleteView
from .models import CurriculoAsignatura, CurriculoAsignaturaCampo, RelacionPosgradoCampo


class CurriculoAsignaturaListView(CrudListView):
    model = CurriculoAsignatura
    template_name = 'curriculo/curriculoasignatura_list.html'

    def get_queryset(self):
        qs = super().get_queryset()
        tipo = self.request.GET.get('tipo', '')
        if tipo == 'subjects':
            qs = qs.filter(es_actividad=False)
        elif tipo == 'activities':
            qs = qs.filter(es_actividad=True)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['tipo_filter'] = self.request.GET.get('tipo', 'all')
        return ctx

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
