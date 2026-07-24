from core.crud_base import CrudListView, CrudCreateView, CrudUpdateView, CrudDeleteView
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.urls import reverse

from .forms import DocenteFcaccForm
from .models import DocenteFcacc, DocenteTituloAcademico, DocenteCampoAfinidad, DocenteAsignacionCarreraPeriodo, DocenteCursoCapacitacion, DocenteParticipacionCurso, DocentePublicacionAcademica


class DocenteFcaccListView(CrudListView):
    model = DocenteFcacc


class DocenteFcaccCreateView(CrudCreateView):
    model = DocenteFcacc
    fields = None
    form_class = DocenteFcaccForm
    template_name = 'docentes/docente_form.html'

class DocenteFcaccUpdateView(CrudUpdateView):
    model = DocenteFcacc
    fields = None
    form_class = DocenteFcaccForm
    template_name = 'docentes/docente_form.html'

class DocenteFcaccDeleteView(CrudDeleteView):
    model = DocenteFcacc


class DocenteTituloAcademicoListView(CrudListView):
    model = DocenteTituloAcademico


class DocenteTituloAcademicoCreateView(CrudCreateView):
    model = DocenteTituloAcademico
    form_field_order = (
        'id_docente', 'nombre_titulo', 'nivel_titulo', 'id_posgrado',
        'id_pais', 'fecha_obtencion_titulo', 'numero_registro_titulo',
        'numero_registro_senescyt', 'fecha_registro_senescyt',
    )

class DocenteTituloAcademicoUpdateView(CrudUpdateView):
    model = DocenteTituloAcademico
    form_field_order = DocenteTituloAcademicoCreateView.form_field_order

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
    form_field_order = (
        'id_periodo', 'id_carrera', 'id_docente', 'id_licencia',
        'horas_otras_unidades_academicas', 'observacion_periodo',
    )

class DocenteAsignacionCarreraPeriodoUpdateView(CrudUpdateView):
    model = DocenteAsignacionCarreraPeriodo
    form_field_order = DocenteAsignacionCarreraPeriodoCreateView.form_field_order

class DocenteAsignacionCarreraPeriodoDeleteView(CrudDeleteView):
    model = DocenteAsignacionCarreraPeriodo


class DocenteCursoCapacitacionListView(CrudListView):
    model = DocenteCursoCapacitacion


class DocenteCursoCapacitacionCreateView(CrudCreateView):
    model = DocenteCursoCapacitacion
    form_field_order = (
        'nombre_curso_capacitacion', 'id_tipo_curso',
        'fecha_inicio_curso', 'fecha_fin_curso', 'horas_totales_curso',
    )

class DocenteCursoCapacitacionUpdateView(CrudUpdateView):
    model = DocenteCursoCapacitacion
    form_field_order = DocenteCursoCapacitacionCreateView.form_field_order

class DocenteCursoCapacitacionDeleteView(CrudDeleteView):
    model = DocenteCursoCapacitacion


class DocenteParticipacionCursoListView(CrudListView):
    model = DocenteParticipacionCurso


class DocenteParticipacionCursoCreateView(CrudCreateView):
    model = DocenteParticipacionCurso
    form_field_order = ('id_docente', 'id_curso', 'fecha_participacion')

class DocenteParticipacionCursoUpdateView(CrudUpdateView):
    model = DocenteParticipacionCurso
    form_field_order = DocenteParticipacionCursoCreateView.form_field_order

class DocenteParticipacionCursoDeleteView(CrudDeleteView):
    model = DocenteParticipacionCurso


class DocentePublicacionAcademicaListView(CrudListView):
    model = DocentePublicacionAcademica


class DocentePublicacionAcademicaCreateView(CrudCreateView):
    model = DocentePublicacionAcademica
    form_field_order = (
        'id_docente', 'nombre_publicacion', 'id_tipo_publicacion',
        'fecha_publicacion', 'detalle_publicacion',
    )

class DocentePublicacionAcademicaUpdateView(CrudUpdateView):
    model = DocentePublicacionAcademica
    form_field_order = DocentePublicacionAcademicaCreateView.form_field_order

class DocentePublicacionAcademicaDeleteView(CrudDeleteView):
    model = DocentePublicacionAcademica


@login_required
def api_docente_por_documento(request):
    documento = (request.GET.get('documento') or '').strip().upper()
    if not documento:
        return JsonResponse({'error': 'Documento requerido.'}, status=400)
    try:
        docente = DocenteFcacc.objects.select_related(
            'id_tipo_docente', 'id_modalidad', 'id_dedicacion'
        ).get(cedula_docente=documento)
    except DocenteFcacc.DoesNotExist:
        if len(documento) == 10 and documento.startswith('0'):
            docente = DocenteFcacc.objects.select_related(
                'id_tipo_docente', 'id_modalidad', 'id_dedicacion'
            ).filter(cedula_docente=documento[1:]).first()
        else:
            docente = None
        if docente is None:
            return JsonResponse({'exists': False})
    return JsonResponse({
        'exists': True,
        'id_docente': docente.id_docente,
        'tipo_documento': docente.tipo_documento,
        'cedula_docente': docente.cedula_docente,
        'nombres_completos': docente.nombres_completos,
        'fecha_nacimiento': docente.fecha_nacimiento.isoformat() if docente.fecha_nacimiento else '',
        'foto_url': docente.foto.url if docente.foto else '',
        'id_tipo_docente': docente.id_tipo_docente_id,
        'id_modalidad': docente.id_modalidad_id,
        'id_dedicacion': docente.id_dedicacion_id,
        'unidad_organica': docente.unidad_organica or '',
        'correo_institucional': docente.correo_institucional or '',
        'numero_celular': docente.numero_celular or '',
        'tipo_sangre': (docente.tipo_sangre or '').strip(),
        'docente_activo': docente.docente_activo,
        'edit_url': reverse('docentes:docentefcacc_update', kwargs={'pk': docente.id_docente}),
    })
