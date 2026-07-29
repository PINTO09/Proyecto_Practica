from collections import OrderedDict

from django import forms
from core.crud_base import CrudListView, ReadOnlyCrudListView, CrudCreateView, CrudUpdateView, CrudDeleteView, DisabledCrudMutationMixin
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin

from accounts.decorators import ADMIN, has_role, module_permission_required
from core.crud_base import RoleAccessMixin

from catalogos.models import CatalogoTituloPosgrado, CatalogoCampoConocimiento
from curriculo.models import RelacionPosgradoCampo

from .forms import DocenteFcaccForm
from .models import DocenteFcacc, DocenteTituloAcademico, DocenteCampoAfinidad, DocenteAsignacionCarreraPeriodo, DocenteCursoCapacitacion, DocenteParticipacionCurso, DocentePublicacionAcademica
from .services import unique_postgraduate_titles


@module_permission_required('certificados', 'view')
def reporte_historial_docente(request):
    # Compatibilidad con enlaces anteriores: el reporte oficial ahora vive en M3.
    from certificados.views import reporte_base
    return reporte_base(request, 'dedicacion')


@module_permission_required('certificados', 'view')
def reporte_dedicacion_formacion_docente(request):
    from django.db.models import Prefetch, Q

    estado = (request.GET.get('estado') or 'activos').strip()
    dedicacion_id = (request.GET.get('dedicacion') or '').strip()
    formacion = (request.GET.get('formacion') or 'todos').strip()
    search = (request.GET.get('q') or '').strip()

    teachers = DocenteFcacc.objects.select_related(
        'id_dedicacion', 'id_modalidad', 'id_tipo_docente'
    ).prefetch_related(Prefetch(
        'docentetituloacademico_set',
        queryset=DocenteTituloAcademico.objects.select_related('id_posgrado'),
    ))
    if estado == 'activos':
        teachers = teachers.filter(docente_activo=True)
    elif estado == 'inactivos':
        teachers = teachers.filter(docente_activo=False)
    else:
        estado = 'todos'
    if dedicacion_id.isdigit():
        teachers = teachers.filter(id_dedicacion_id=int(dedicacion_id))
    else:
        dedicacion_id = ''
    if search:
        teachers = teachers.filter(
            Q(nombres_completos__icontains=search) |
            Q(cedula_docente__icontains=search)
        )

    teacher_rows = []
    category_totals = {
        'masters': 0, 'doctorates': 0, 'specializations': 0, 'other': 0,
    }
    dedication_totals = OrderedDict()
    teachers_with_postgraduate = 0

    for teacher in teachers.order_by('id_dedicacion__nombre_dedicacion', 'nombres_completos'):
        postgraduate_titles = unique_postgraduate_titles(
            teacher.docentetituloacademico_set.all()
        )
        counts = {key: 0 for key in category_totals}
        title_names = []
        for title, category in postgraduate_titles:
            counts[category] += 1
            category_totals[category] += 1
            title_names.append(
                title.id_posgrado.nombre_titulo_posgrado
                if title.id_posgrado_id else title.nombre_titulo
            )
        has_postgraduate = bool(postgraduate_titles)
        if formacion == 'con' and not has_postgraduate:
            for category, value in counts.items():
                category_totals[category] -= value
            continue
        if formacion == 'maestria' and counts['masters'] == 0:
            for category, value in counts.items():
                category_totals[category] -= value
            continue
        if formacion == 'sin' and has_postgraduate:
            for category, value in counts.items():
                category_totals[category] -= value
            continue
        if has_postgraduate:
            teachers_with_postgraduate += 1

        dedication = teacher.id_dedicacion
        dedication_row = dedication_totals.setdefault(dedication.id_dedicacion, {
            'dedication': dedication, 'count': 0,
        })
        dedication_row['count'] += 1
        teacher_rows.append({
            'teacher': teacher,
            'counts': counts,
            'postgraduate_count': len(postgraduate_titles),
            'title_names': title_names,
        })

    teacher_count = len(teacher_rows)
    dedication_rows = list(dedication_totals.values())
    for row in dedication_rows:
        row['percentage'] = round(row['count'] * 100 / teacher_count, 1) if teacher_count else 0
    total_postgraduate_titles = sum(category_totals.values())

    from catalogos.models import CatalogoDedicacionHoraria
    context = {
        'active_section': 'reporte_dedicacion_formacion_docente',
        'estado': estado,
        'dedicacion_filter': dedicacion_id,
        'formacion': formacion,
        'search_value': search,
        'dedicaciones': CatalogoDedicacionHoraria.objects.all().order_by('nombre_dedicacion'),
        'teacher_rows': teacher_rows,
        'dedication_rows': dedication_rows,
        'summary': {
            'teacher_count': teacher_count,
            'teachers_with_postgraduate': teachers_with_postgraduate,
            'total_postgraduate_titles': total_postgraduate_titles,
            **category_totals,
        },
    }
    return render(request, 'docentes/reporte_dedicacion_formacion.html', context)


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

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        for field_name in ('fecha_obtencion_titulo', 'fecha_registro_senescyt'):
            if field_name in form.fields:
                form.fields[field_name].widget = forms.DateInput(
                    attrs={'class': 'form-control', 'type': 'date'}
                )
        return form

class DocenteTituloAcademicoUpdateView(CrudUpdateView):
    model = DocenteTituloAcademico
    form_field_order = DocenteTituloAcademicoCreateView.form_field_order

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        for field_name in ('fecha_obtencion_titulo', 'fecha_registro_senescyt'):
            if field_name in form.fields:
                form.fields[field_name].widget = forms.DateInput(
                    attrs={'class': 'form-control', 'type': 'date'}
                )
        return form

class DocenteTituloAcademicoDeleteView(CrudDeleteView):
    model = DocenteTituloAcademico


class DocenteCampoAfinidadListView(LoginRequiredMixin, RoleAccessMixin, ListView):
    model = DocenteTituloAcademico
    template_name = 'docentes/campo_afinidad_list.html'
    paginate_by = 25
    allowed_page_sizes = (10, 25, 50, 100)

    def get_queryset(self):
        qs = DocenteTituloAcademico.objects.select_related('id_docente', 'id_posgrado')

        q = self.request.GET.get('q', '').strip()
        if q:
            from django.db.models import Q as Q_
            qs = qs.filter(
                Q_(id_docente__nombres_completos__icontains=q) |
                Q_(id_docente__cedula_docente__icontains=q) |
                Q_(nombre_titulo__icontains=q) |
                Q_(id_posgrado__nombre_titulo_posgrado__icontains=q)
            )

        campo_filter = self.request.GET.get('campo', '').strip()
        if campo_filter and campo_filter.isdigit():
            posgrado_ids = RelacionPosgradoCampo.objects.filter(
                id_campo_id=int(campo_filter)
            ).values_list('id_posgrado_id', flat=True).distinct()
            qs = qs.filter(id_posgrado_id__in=posgrado_ids)

        posgrado_filter = self.request.GET.get('posgrado', '').strip()
        if posgrado_filter and posgrado_filter.isdigit():
            qs = qs.filter(id_posgrado_id=int(posgrado_filter))

        return qs.order_by('id_docente__nombres_completos', '-nivel_titulo', '-fecha_obtencion_titulo')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['is_admin'] = has_role(getattr(self.request, 'user', None), ADMIN)
        ctx['titulo_create_url'] = 'docentes:docentetituloacademico_create'
        ctx['search_value'] = self.request.GET.get('q', '')
        ctx['campo_filter'] = self.request.GET.get('campo', '')
        ctx['posgrado_filter'] = self.request.GET.get('posgrado', '')

        posgrado_ids = set()
        for obj in ctx.get('object_list', []):
            if obj.id_posgrado_id:
                posgrado_ids.add(obj.id_posgrado_id)

        if posgrado_ids:
            posgrado_campos = {}
            rels = RelacionPosgradoCampo.objects.filter(
                id_posgrado_id__in=posgrado_ids
            ).select_related('id_campo')
            for r in rels:
                posgrado_campos.setdefault(r.id_posgrado_id, []).append(r.id_campo)
            for obj in ctx.get('object_list', []):
                obj.related_campos = posgrado_campos.get(obj.id_posgrado_id, [])
        else:
            for obj in ctx.get('object_list', []):
                obj.related_campos = []

        ctx['campos'] = CatalogoCampoConocimiento.objects.all().order_by('nombre_campo_conocimiento')
        ctx['posgrados'] = CatalogoTituloPosgrado.objects.all().order_by('nombre_titulo_posgrado')

        raw_cant = self.request.GET.get('cant', self.paginate_by)
        try:
            ctx['cant'] = int(raw_cant)
        except (ValueError, TypeError):
            ctx['cant'] = self.paginate_by
        if ctx['cant'] not in self.allowed_page_sizes:
            ctx['cant'] = self.paginate_by
        if ctx.get('paginator') and ctx.get('page_obj'):
            ctx['elided_page_range'] = ctx['paginator'].get_elided_page_range(
                ctx['page_obj'].number, on_each_side=2, on_ends=1,
            )
        return ctx

    def get_paginate_by(self, queryset):
        cant = self.request.GET.get('cant')
        if cant and cant.isdigit() and int(cant) in self.allowed_page_sizes:
            return int(cant)
        return self.paginate_by


class DocenteCampoAfinidadCreateView(DisabledCrudMutationMixin, CrudCreateView):
    model = DocenteCampoAfinidad

class DocenteCampoAfinidadUpdateView(DisabledCrudMutationMixin, CrudUpdateView):
    model = DocenteCampoAfinidad

class DocenteCampoAfinidadDeleteView(DisabledCrudMutationMixin, CrudDeleteView):
    model = DocenteCampoAfinidad


class DocenteAsignacionCarreraPeriodoListView(CrudListView):
    model = DocenteAsignacionCarreraPeriodo


class DocenteAsignacionCarreraPeriodoCreateView(CrudCreateView):
    model = DocenteAsignacionCarreraPeriodo
    form_field_order = (
        'id_docente', 'id_periodo', 'id_carrera', 'id_licencia',
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
        'id_tipo_curso', 'nombre_curso_capacitacion',
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


@login_required
def api_buscar_docentes(request):
    q = (request.GET.get('q') or '').strip()
    if len(q) < 1:
        return JsonResponse({'results': []})
    from django.db.models import Q
    docentes = DocenteFcacc.objects.filter(
        Q(nombres_completos__icontains=q) | Q(cedula_docente__icontains=q)
    ).values('id_docente', 'nombres_completos', 'cedula_docente')[:10]
    return JsonResponse({
        'results': [
            {
                'id': d['id_docente'],
                'nombres': d['nombres_completos'],
                'cedula': d['cedula_docente'],
                'label': f"{d['nombres_completos']} ({d['cedula_docente']})"
            }
            for d in docentes
        ]
    })
