from django import template
from core.models import (
    Carrera, CatalogoPeriodoAcademico,
    DocenteFcacc, DocenteTituloAcademico,
    DocentePublicacionAcademica, DocenteCursoCapacitacion,
    Usuario, CurriculoAsignatura,
    PlanificacionAsignacionDocente, PlanificacionMatrizF4,
    AuditoriaRegistroCambios, Limitacion,
)

register = template.Library()

@register.simple_tag
def admin_stat(module):
    try:
        if module == 'carreras':
            return Carrera.objects.count()
        elif module == 'periodos':
            return CatalogoPeriodoAcademico.objects.count()
        elif module == 'docentes':
            return DocenteFcacc.objects.count()
        elif module == 'titulos':
            return DocenteTituloAcademico.objects.count()
        elif module == 'publicaciones':
            return DocentePublicacionAcademica.objects.count()
        elif module == 'capacitaciones':
            return DocenteCursoCapacitacion.objects.count()
        elif module == 'usuarios':
            return Usuario.objects.count()
        elif module == 'asignaturas':
            return CurriculoAsignatura.objects.count()
        elif module == 'asignaciones':
            return PlanificacionAsignacionDocente.objects.count()
        elif module == 'matriz_f4':
            return PlanificacionMatrizF4.objects.count()
        elif module == 'auditoria':
            return AuditoriaRegistroCambios.objects.count()
        elif module == 'limitaciones':
            return Limitacion.objects.count()
    except Exception:
        return "—"
    return "—"
