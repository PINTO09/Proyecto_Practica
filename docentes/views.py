from core.crud_base import CrudListView, CrudCreateView, CrudUpdateView, CrudDeleteView
from .models import DocenteFcacc, DocenteTituloAcademico, DocenteCampoAfinidad, DocenteAsignacionCarreraPeriodo, DocenteCursoCapacitacion, DocenteParticipacionCurso, DocentePublicacionAcademica


class DocenteFcaccListView(CrudListView):
    model = DocenteFcacc


class DocenteFcaccCreateView(CrudCreateView):
    model = DocenteFcacc

class DocenteFcaccUpdateView(CrudUpdateView):
    model = DocenteFcacc

class DocenteFcaccDeleteView(CrudDeleteView):
    model = DocenteFcacc


class DocenteTituloAcademicoListView(CrudListView):
    model = DocenteTituloAcademico


class DocenteTituloAcademicoCreateView(CrudCreateView):
    model = DocenteTituloAcademico

class DocenteTituloAcademicoUpdateView(CrudUpdateView):
    model = DocenteTituloAcademico

class DocenteTituloAcademicoDeleteView(CrudDeleteView):
    model = DocenteTituloAcademico


class DocenteCampoAfinidadListView(CrudListView):
    model = DocenteCampoAfinidad


class DocenteCampoAfinidadCreateView(CrudCreateView):
    model = DocenteCampoAfinidad

class DocenteCampoAfinidadUpdateView(CrudUpdateView):
    model = DocenteCampoAfinidad

class DocenteCampoAfinidadDeleteView(CrudDeleteView):
    model = DocenteCampoAfinidad


class DocenteAsignacionCarreraPeriodoListView(CrudListView):
    model = DocenteAsignacionCarreraPeriodo


class DocenteAsignacionCarreraPeriodoCreateView(CrudCreateView):
    model = DocenteAsignacionCarreraPeriodo

class DocenteAsignacionCarreraPeriodoUpdateView(CrudUpdateView):
    model = DocenteAsignacionCarreraPeriodo

class DocenteAsignacionCarreraPeriodoDeleteView(CrudDeleteView):
    model = DocenteAsignacionCarreraPeriodo


class DocenteCursoCapacitacionListView(CrudListView):
    model = DocenteCursoCapacitacion


class DocenteCursoCapacitacionCreateView(CrudCreateView):
    model = DocenteCursoCapacitacion

class DocenteCursoCapacitacionUpdateView(CrudUpdateView):
    model = DocenteCursoCapacitacion

class DocenteCursoCapacitacionDeleteView(CrudDeleteView):
    model = DocenteCursoCapacitacion


class DocenteParticipacionCursoListView(CrudListView):
    model = DocenteParticipacionCurso


class DocenteParticipacionCursoCreateView(CrudCreateView):
    model = DocenteParticipacionCurso

class DocenteParticipacionCursoUpdateView(CrudUpdateView):
    model = DocenteParticipacionCurso

class DocenteParticipacionCursoDeleteView(CrudDeleteView):
    model = DocenteParticipacionCurso


class DocentePublicacionAcademicaListView(CrudListView):
    model = DocentePublicacionAcademica


class DocentePublicacionAcademicaCreateView(CrudCreateView):
    model = DocentePublicacionAcademica

class DocentePublicacionAcademicaUpdateView(CrudUpdateView):
    model = DocentePublicacionAcademica

class DocentePublicacionAcademicaDeleteView(CrudDeleteView):
    model = DocentePublicacionAcademica
