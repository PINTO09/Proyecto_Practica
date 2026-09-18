from core.crud_base import CrudListView, CrudCreateView, CrudUpdateView, CrudDeleteView
from .forms import CatalogoPeriodoAcademicoForm, ModalidadContratacionForm
from core.crud_base import ReadOnlyCrudListView, DisabledCrudMutationMixin
from .models import (
    CatalogoCarrera, CatalogoModalidadContratacion, CatalogoDedicacionHoraria,
    CatalogoTipoDocente, CatalogoTipoLicencia, CatalogoPais, CatalogoTituloPosgrado,
    CatalogoCampoConocimiento, CatalogoGradoAfinidad, CatalogoTipoPublicacion,
    CatalogoTipoCursoCapacitacion, CatalogoPeriodoAcademico, RelacionCarreraPeriodo,
    LimiteHorario,
)

# â”€â”€â”€ CatalogoCarrera â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
class CatalogoCarreraListView(CrudListView):
    model = CatalogoCarrera

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['model_verbose_plural'] = 'Carreras y actividades'
        return context

class CatalogoCarreraCreateView(CrudCreateView):
    model = CatalogoCarrera

class CatalogoCarreraUpdateView(CrudUpdateView):
    model = CatalogoCarrera

class CatalogoCarreraDeleteView(CrudDeleteView):
    model = CatalogoCarrera

# â”€â”€â”€ CatalogoModalidadContratacion â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
class CatalogoModalidadContratacionListView(CrudListView):
    model = CatalogoModalidadContratacion

class CatalogoModalidadContratacionCreateView(CrudCreateView):
    model = CatalogoModalidadContratacion
    fields = None
    form_class = ModalidadContratacionForm

class CatalogoModalidadContratacionUpdateView(CrudUpdateView):
    model = CatalogoModalidadContratacion
    fields = None
    form_class = ModalidadContratacionForm

class CatalogoModalidadContratacionDeleteView(CrudDeleteView):
    model = CatalogoModalidadContratacion

# â”€â”€â”€ CatalogoDedicacionHoraria â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
class CatalogoDedicacionHorariaListView(CrudListView):
    model = CatalogoDedicacionHoraria

class CatalogoDedicacionHorariaCreateView(CrudCreateView):
    model = CatalogoDedicacionHoraria

class CatalogoDedicacionHorariaUpdateView(CrudUpdateView):
    model = CatalogoDedicacionHoraria

class CatalogoDedicacionHorariaDeleteView(CrudDeleteView):
    model = CatalogoDedicacionHoraria

# â”€â”€â”€ CatalogoTipoDocente â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
class CatalogoTipoDocenteListView(CrudListView):
    model = CatalogoTipoDocente

class CatalogoTipoDocenteCreateView(CrudCreateView):
    model = CatalogoTipoDocente

class CatalogoTipoDocenteUpdateView(CrudUpdateView):
    model = CatalogoTipoDocente

class CatalogoTipoDocenteDeleteView(CrudDeleteView):
    model = CatalogoTipoDocente

# â”€â”€â”€ CatalogoTipoLicencia â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
class CatalogoTipoLicenciaListView(CrudListView):
    model = CatalogoTipoLicencia

class CatalogoTipoLicenciaCreateView(CrudCreateView):
    model = CatalogoTipoLicencia

class CatalogoTipoLicenciaUpdateView(CrudUpdateView):
    model = CatalogoTipoLicencia

class CatalogoTipoLicenciaDeleteView(CrudDeleteView):
    model = CatalogoTipoLicencia

# â”€â”€â”€ CatalogoPais â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
class CatalogoPaisListView(CrudListView):
    model = CatalogoPais

class CatalogoPaisCreateView(CrudCreateView):
    model = CatalogoPais

class CatalogoPaisUpdateView(CrudUpdateView):
    model = CatalogoPais

class CatalogoPaisDeleteView(CrudDeleteView):
    model = CatalogoPais

# â”€â”€â”€ CatalogoTituloPosgrado â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
class CatalogoTituloPosgradoListView(CrudListView):
    model = CatalogoTituloPosgrado

class CatalogoTituloPosgradoCreateView(CrudCreateView):
    model = CatalogoTituloPosgrado

class CatalogoTituloPosgradoUpdateView(CrudUpdateView):
    model = CatalogoTituloPosgrado

class CatalogoTituloPosgradoDeleteView(CrudDeleteView):
    model = CatalogoTituloPosgrado

# â”€â”€â”€ CatalogoCampoConocimiento â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
class CatalogoCampoConocimientoListView(CrudListView):
    model = CatalogoCampoConocimiento

class CatalogoCampoConocimientoCreateView(CrudCreateView):
    model = CatalogoCampoConocimiento

class CatalogoCampoConocimientoUpdateView(CrudUpdateView):
    model = CatalogoCampoConocimiento

class CatalogoCampoConocimientoDeleteView(CrudDeleteView):
    model = CatalogoCampoConocimiento

# â”€â”€â”€ CatalogoGradoAfinidad â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
class CatalogoGradoAfinidadListView(CrudListView):
    model = CatalogoGradoAfinidad

class CatalogoGradoAfinidadCreateView(CrudCreateView):
    model = CatalogoGradoAfinidad

class CatalogoGradoAfinidadUpdateView(CrudUpdateView):
    model = CatalogoGradoAfinidad

class CatalogoGradoAfinidadDeleteView(CrudDeleteView):
    model = CatalogoGradoAfinidad

# â”€â”€â”€ CatalogoTipoPublicacion â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
class CatalogoTipoPublicacionListView(CrudListView):
    model = CatalogoTipoPublicacion

class CatalogoTipoPublicacionCreateView(CrudCreateView):
    model = CatalogoTipoPublicacion

class CatalogoTipoPublicacionUpdateView(CrudUpdateView):
    model = CatalogoTipoPublicacion

class CatalogoTipoPublicacionDeleteView(CrudDeleteView):
    model = CatalogoTipoPublicacion

# â”€â”€â”€ CatalogoTipoCursoCapacitacion â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
class CatalogoTipoCursoCapacitacionListView(CrudListView):
    model = CatalogoTipoCursoCapacitacion

class CatalogoTipoCursoCapacitacionCreateView(CrudCreateView):
    model = CatalogoTipoCursoCapacitacion

class CatalogoTipoCursoCapacitacionUpdateView(CrudUpdateView):
    model = CatalogoTipoCursoCapacitacion

class CatalogoTipoCursoCapacitacionDeleteView(CrudDeleteView):
    model = CatalogoTipoCursoCapacitacion

# â”€â”€â”€ CatalogoPeriodoAcademico â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
class CatalogoPeriodoAcademicoListView(CrudListView):
    model = CatalogoPeriodoAcademico

class CatalogoPeriodoAcademicoCreateView(CrudCreateView):
    model = CatalogoPeriodoAcademico
    fields = None
    form_class = CatalogoPeriodoAcademicoForm

class CatalogoPeriodoAcademicoUpdateView(CrudUpdateView):
    model = CatalogoPeriodoAcademico
    fields = None
    form_class = CatalogoPeriodoAcademicoForm

class CatalogoPeriodoAcademicoDeleteView(CrudDeleteView):
    model = CatalogoPeriodoAcademico

# â”€â”€â”€ RelacionCarreraPeriodo â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
class RelacionCarreraPeriodoListView(ReadOnlyCrudListView):
    model = RelacionCarreraPeriodo
    # La tabla heredada de algunas instalaciones solo conserva su clave
    # primaria; no se generan JOIN de búsqueda contra columnas inexistentes.
    search_fields = ()

class RelacionCarreraPeriodoCreateView(DisabledCrudMutationMixin, CrudCreateView):
    model = RelacionCarreraPeriodo

class RelacionCarreraPeriodoUpdateView(DisabledCrudMutationMixin, CrudUpdateView):
    model = RelacionCarreraPeriodo

class RelacionCarreraPeriodoDeleteView(DisabledCrudMutationMixin, CrudDeleteView):
    model = RelacionCarreraPeriodo


class LimiteHorarioListView(CrudListView):
    model = LimiteHorario

class LimiteHorarioCreateView(CrudCreateView):
    model = LimiteHorario

class LimiteHorarioUpdateView(CrudUpdateView):
    model = LimiteHorario

class LimiteHorarioDeleteView(CrudDeleteView):
    model = LimiteHorario
