from core.crud_base import CrudListView, CrudCreateView, CrudUpdateView, CrudDeleteView
from .models import CurriculoAsignatura, CurriculoAsignaturaCampo, RelacionPosgradoCampo
from .forms import CurriculoAsignaturaForm
from catalogos.models import CatalogoCampoConocimiento, CatalogoCarrera


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
    fields = None
    form_class = CurriculoAsignaturaForm
    template_name = 'curriculo/curriculoasignatura_form.html'

class CurriculoAsignaturaUpdateView(CrudUpdateView):
    model = CurriculoAsignatura
    fields = None
    form_class = CurriculoAsignaturaForm
    template_name = 'curriculo/curriculoasignatura_form.html'

class CurriculoAsignaturaDeleteView(CrudDeleteView):
    model = CurriculoAsignatura


class CurriculoAsignaturaCampoListView(CrudListView):
    model = CurriculoAsignaturaCampo
    template_name = 'curriculo/curriculoasignaturacampo_list.html'

    def get_queryset(self):
        qs = super().get_queryset().select_related(
            'id_asignatura', 'id_asignatura__id_carrera', 'id_campo',
        )
        carrera_id = self.request.GET.get('carrera')
        campo_id = self.request.GET.get('campo')
        if carrera_id:
            qs = qs.filter(id_asignatura__id_carrera_id=carrera_id)
        if campo_id:
            qs = qs.filter(id_campo_id=campo_id)
        return qs.order_by(
            'id_asignatura__id_carrera__nombre_carrera',
            'id_asignatura__nombre_asignatura',
            'id_campo__nombre_campo_conocimiento',
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({
            'carreras': CatalogoCarrera.objects.filter(
                carrera_activa=True
            ).order_by('nombre_carrera'),
            'campos': CatalogoCampoConocimiento.objects.order_by(
                'nombre_campo_conocimiento'
            ),
            'carrera_id': (
                int(self.request.GET['carrera'])
                if self.request.GET.get('carrera', '').isdigit()
                else None
            ),
            'campo_id': (
                int(self.request.GET['campo'])
                if self.request.GET.get('campo', '').isdigit()
                else None
            ),
        })
        return ctx


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
