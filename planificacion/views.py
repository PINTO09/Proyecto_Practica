import json
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Sum, Q, Prefetch
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from core.crud_base import CrudListView, CrudCreateView, CrudUpdateView, CrudDeleteView
from .models import PlanificacionDemandaAcademica, PlanificacionAsignacionDocente, PlanificacionRepartoHoras, PlanificacionMatrizF4, PlanificacionAulaHorario
from docentes.models import DocenteFcacc, DocenteCampoAfinidad
from curriculo.models import CurriculoAsignatura, CurriculoAsignaturaCampo, RelacionPosgradoCampo
from catalogos.models import CatalogoCampoConocimiento, LimiteHorario


class PlanificacionDemandaAcademicaListView(CrudListView):
    model = PlanificacionDemandaAcademica


class PlanificacionDemandaAcademicaCreateView(CrudCreateView):
    model = PlanificacionDemandaAcademica
    autofill_rules = {
        'id_asignatura': {
            'app': 'curriculo',
            'model': 'CurriculoAsignatura',
            'fields': {
                'id_carrera': 'id_carrera_id',
            },
        },
    }

class PlanificacionDemandaAcademicaUpdateView(CrudUpdateView):
    model = PlanificacionDemandaAcademica

class PlanificacionDemandaAcademicaDeleteView(CrudDeleteView):
    model = PlanificacionDemandaAcademica


class PlanificacionAsignacionDocenteListView(CrudListView):
    model = PlanificacionAsignacionDocente
    template_name = 'planificacion/planificacionasignaciondocente_list.html'


class PlanificacionAsignacionDocenteCreateView(CrudCreateView):
    model = PlanificacionAsignacionDocente
    template_name = 'planificacion/asignaciondocente_form.html'
    autofill_rules = {
        'id_asignatura': {
            'app': 'curriculo',
            'model': 'CurriculoAsignatura',
            'fields': {
                'id_carrera': 'id_carrera_id',
                'nivel_semestre_asignado': 'nivel_semestre',
                'horas_clase': 'horas_semanales_asignatura',
            },
        },
    }

    def get_initial(self):
        initial = super().get_initial()
        # FK fields: doc/id maps to id_docente, etc.
        fk_map = {'docente': 'id_docente', 'asignatura': 'id_asignatura', 'carrera': 'id_carrera', 'periodo': 'id_periodo', 'campo': 'id_campo'}
        for param, field in fk_map.items():
            val = self.request.GET.get(param)
            if val is not None:
                try:
                    initial[field] = int(val)
                except (ValueError, TypeError):
                    pass
        # Direct fields
        direct_map = {'nivel': 'nivel_semestre_asignado', 'horas': 'horas_clase', 'complementarias': 'horas_complementarias', 'paralelo': 'paralelo_asignado'}
        for param, field in direct_map.items():
            val = self.request.GET.get(param)
            if val is not None:
                initial[field] = int(val) if field != 'paralelo_asignado' else val
        # If subject is in GET param, pre-fill derived fields
        subj_id = self.request.GET.get('asignatura')
        if subj_id:
            try:
                subj = CurriculoAsignatura.objects.get(id_asignatura=subj_id)
                initial['id_asignatura'] = subj
                initial['id_carrera'] = subj.id_carrera
                initial['nivel_semestre_asignado'] = subj.nivel_semestre
                if 'id_periodo' not in initial:
                    from catalogos.models import CatalogoPeriodoAcademico
                    periodo_activo = CatalogoPeriodoAcademico.objects.filter(periodo_activo=True).first()
                    if periodo_activo:
                        initial['id_periodo'] = periodo_activo
            except CurriculoAsignatura.DoesNotExist:
                pass
        return initial

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        subj_id = self.request.GET.get('asignatura') or self.request.POST.get('id_asignatura')
        if subj_id:
            try:
                subj = CurriculoAsignatura.objects.get(id_asignatura=subj_id)
                recommendations = _compute_teacher_scores(subj)
                ctx['teacher_recommendations'] = recommendations[:10]
                ctx['selected_subject'] = subj
                from catalogos.models import CatalogoPeriodoAcademico
                periodo_activo = CatalogoPeriodoAcademico.objects.filter(periodo_activo=True).first()
                existing = _get_existing_assignment(subj.id_asignatura, getattr(periodo_activo, 'id_periodo', None))
                if existing:
                    ctx['existing_assignment'] = existing
            except CurriculoAsignatura.DoesNotExist:
                pass
        return ctx


class PlanificacionAsignacionDocenteUpdateView(CrudUpdateView):
    model = PlanificacionAsignacionDocente

class PlanificacionAsignacionDocenteDeleteView(CrudDeleteView):
    model = PlanificacionAsignacionDocente


class PlanificacionRepartoHorasListView(CrudListView):
    model = PlanificacionRepartoHoras


class PlanificacionRepartoHorasCreateView(CrudCreateView):
    model = PlanificacionRepartoHoras

class PlanificacionRepartoHorasUpdateView(CrudUpdateView):
    model = PlanificacionRepartoHoras

class PlanificacionRepartoHorasDeleteView(CrudDeleteView):
    model = PlanificacionRepartoHoras


class PlanificacionMatrizF4ListView(CrudListView):
    model = PlanificacionMatrizF4


class PlanificacionMatrizF4CreateView(CrudCreateView):
    model = PlanificacionMatrizF4

class PlanificacionMatrizF4UpdateView(CrudUpdateView):
    model = PlanificacionMatrizF4

class PlanificacionMatrizF4DeleteView(CrudDeleteView):
    model = PlanificacionMatrizF4


class PlanificacionAulaHorarioListView(CrudListView):
    model = PlanificacionAulaHorario


class PlanificacionAulaHorarioCreateView(CrudCreateView):
    model = PlanificacionAulaHorario

class PlanificacionAulaHorarioUpdateView(CrudUpdateView):
    model = PlanificacionAulaHorario

class PlanificacionAulaHorarioDeleteView(CrudDeleteView):
    model = PlanificacionAulaHorario


# ——— Reporte: Horas por Docente ———————————————————————————————

@login_required
def reporte_horas_docentes(request):
    periodo_id = request.GET.get('periodo')

    docentes = DocenteFcacc.objects.filter(docente_activo=True).select_related('id_dedicacion')

    limites = {l.id_dedicacion_id: l for l in LimiteHorario.objects.filter(activo=True).select_related('id_dedicacion')}

    rows = []
    for d in docentes:
        asignaciones = PlanificacionAsignacionDocente.objects.filter(id_docente=d)
        if periodo_id:
            asignaciones = asignaciones.filter(id_periodo_id=periodo_id)

        total_horas = asignaciones.aggregate(
            total_clase=Sum('horas_clase'),
            total_complementarias=Sum('horas_complementarias'),
        )
        h_clase = total_horas['total_clase'] or 0
        h_comp = total_horas['total_complementarias'] or 0
        h_total = h_clase + h_comp

        limite = limites.get(d.id_dedicacion_id)
        max_horas = limite.horas_maximas if limite else 0
        pct = round((h_total / max_horas) * 100, 1) if max_horas > 0 else 0

        if pct >= 100:
            status = 'danger'
        elif pct >= 80:
            status = 'warning'
        else:
            status = 'success'

        rows.append({
            'docente': d,
            'horas_clase': h_clase,
            'horas_complementarias': h_comp,
            'total_horas': h_total,
            'max_horas': max_horas,
            'porcentaje': pct,
            'status': status,
        })

    rows.sort(key=lambda r: r['total_horas'], reverse=True)

    total = len(rows)
    sobrecargados = sum(1 for r in rows if r['porcentaje'] >= 100)
    alerta = sum(1 for r in rows if 80 <= r['porcentaje'] < 100)
    disponibles = total - sobrecargados - alerta

    context = {
        'active_section': 'reporte_horas_docentes',
        'rows': rows,
        'limites_config': limites,
        'total_docentes': total,
        'sobrecargados': sobrecargados,
        'en_alerta': alerta,
        'disponibles': disponibles,
    }
    return render(request, 'planificacion/reporte_horas_docentes.html', context)


# ——— Helper: verificar si una asignatura ya tiene docente ————————

def _get_existing_assignment(asignatura_id, periodo_id=None):
    from catalogos.models import CatalogoPeriodoAcademico
    if not periodo_id:
        periodo_activo = CatalogoPeriodoAcademico.objects.filter(periodo_activo=True).first()
        if periodo_activo:
            periodo_id = periodo_activo.id_periodo
    if not periodo_id:
        return None
    asignaciones = PlanificacionAsignacionDocente.objects.select_related('id_docente').filter(
        id_asignatura_id=asignatura_id, id_periodo_id=periodo_id
    )
    if not asignaciones.exists():
        return None
    docentes = list(set(
        (a.id_docente_id, a.id_docente.nombres_completos) for a in asignaciones
    ))
    return {
        'id_docente': docentes[0][0],
        'docente_nombre': docentes[0][1],
        'total_docentes': len(docentes),
        'docente_label': docentes[0][1] if len(docentes) == 1 else f'{docentes[0][1]} (+{len(docentes)-1} m&aacute;s)',
    }


# ——— Scoring reutilizable: compatibilidad docente ↔ asignatura ————

def _compute_teacher_scores(subject):
    """Return list of teacher dicts with compatibility score for a given subject."""
    from docentes.models import DocenteTituloAcademico

    # Subject campos
    subj_campos = list(CurriculoAsignaturaCampo.objects.filter(id_asignatura=subject).select_related('id_campo'))
    req_campo_ids = {c.id_campo_id for c in subj_campos}

    # All active teachers
    docentes = list(DocenteFcacc.objects.filter(docente_activo=True).select_related('id_dedicacion'))
    if not docentes:
        return []

    # Teacher → campos
    afinidad_rels = list(DocenteCampoAfinidad.objects.all())
    doc_campos = {}
    for ar in afinidad_rels:
        doc_campos.setdefault(ar.id_docente_id, set()).add(ar.id_campo_id)

    # Posgrado → campos
    posgrado_campos = {}
    for rpc in RelacionPosgradoCampo.objects.all():
        posgrado_campos.setdefault(rpc.id_posgrado_id, set()).add(rpc.id_campo_id)

    # Teacher → previous subjects
    prev_dict = {}
    for p in PlanificacionAsignacionDocente.objects.filter(id_asignatura=subject).values('id_docente_id'):
        prev_dict[p['id_docente_id']] = True

    # Teacher titles with posgrado
    doc_titulos = {}
    for t in DocenteTituloAcademico.objects.filter(id_posgrado__isnull=False).values('id_docente_id', 'id_posgrado_id'):
        doc_titulos.setdefault(t['id_docente_id'], []).append(t['id_posgrado_id'])

    # Teacher current hours
    hour_qs = PlanificacionAsignacionDocente.objects.values('id_docente_id').annotate(
        total=Sum('horas_clase') + Sum('horas_complementarias')
    )
    doc_hours = {h['id_docente_id']: h['total'] or 0 for h in hour_qs}
    limites = {l.id_dedicacion_id: l for l in LimiteHorario.objects.filter(activo=True)}

    results = []
    for d in docentes:
        score = 0
        reasons = []

        # 1. Direct campo affinity (+50)
        teacher_campo_ids = doc_campos.get(d.id_docente, set())
        match_ids = req_campo_ids & teacher_campo_ids
        if match_ids:
            score += 50
            camp_names = [str(c) for c in subj_campos if c.id_campo_id in match_ids]
            reasons.append(f'Campo afinidad: {", ".join(camp_names)}')

        # 2. Title/Posgrado match (+25)
        for posgrado_id in doc_titulos.get(d.id_docente, []):
            if posgrado_campos.get(posgrado_id, set()) & req_campo_ids:
                score += 25
                reasons.append('Posgrado afín')
                break

        # 3. Previous experience (+20)
        if prev_dict.get(d.id_docente):
            score += 20
            reasons.append('Experiencia previa')

        # 4. Available hours (+10)
        limite = limites.get(d.id_dedicacion_id)
        max_h = limite.horas_maximas if limite else 0
        used_h = doc_hours.get(d.id_docente, 0)
        available = max_h - used_h
        if available > 0:
            score += 10

        if score > 0:
            results.append({
                'docente': d,
                'id': d.id_docente,
                'score': score,
                'reasons': reasons,
                'available': max(0, available),
                'used': used_h,
                'max': max_h,
                'status': 'excelente' if score >= 50 else 'bueno' if score >= 25 else 'regular',
            })

    results.sort(key=lambda r: (-r['score'], -r['available']))
    return results


# ——— Asignación Inteligente (página de exploración) ——————————

@login_required
def asignacion_inteligente(request):
    carrera_id = request.GET.get('carrera')
    subject_id = request.GET.get('asignatura')

    from catalogos.models import CatalogoCarrera, CatalogoPeriodoAcademico
    carreras = CatalogoCarrera.objects.filter(carrera_activa=True)
    periodo_activo = CatalogoPeriodoAcademico.objects.filter(periodo_activo=True).first()

    qs = CurriculoAsignatura.objects.select_related('id_carrera').order_by('id_carrera_id', 'nivel_semestre', 'nombre_asignatura')
    if carrera_id:
        qs = qs.filter(id_carrera_id=carrera_id)
    if subject_id:
        qs = qs.filter(id_asignatura=subject_id)

    subj_qs = CurriculoAsignatura.objects.select_related('id_carrera').order_by('id_carrera_id', 'nombre_asignatura')
    if carrera_id:
        subj_qs = subj_qs.filter(id_carrera_id=carrera_id)
    all_subjects_for_select = list(subj_qs.values('id_asignatura', 'nombre_asignatura'))

    paginator = Paginator(qs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    subjects_data = []
    for a in page_obj:
        recs = _compute_teacher_scores(a)
        existing = _get_existing_assignment(a.id_asignatura, getattr(periodo_activo, 'id_periodo', None))
        subjects_data.append({
            'asignatura': a,
            'recomendados': recs[:5],
            'existing_assignment': existing,
        })

    from catalogos.models import CatalogoCampoConocimiento
    campos = CatalogoCampoConocimiento.objects.values('id_campo', 'codigo_campo', 'nombre_campo_conocimiento').order_by('codigo_campo')

    context = {
        'active_section': 'asignacion_inteligente',
        'subjects_data': subjects_data,
        'carreras': carreras,
        'campos': campos,
        'carrera_id': int(carrera_id) if carrera_id else None,
        'subject_id': int(subject_id) if subject_id else None,
        'page_obj': page_obj,
        'paginator': paginator,
        'total_subjects': paginator.count,
        'all_subjects': all_subjects_for_select,
        'periodo_activo': periodo_activo,
    }
    return render(request, 'planificacion/asignacion_inteligente.html', context)


# ——— AJAX: endpoints para auto-fill ————————————————————————

@login_required
def api_asignatura_info(request):
    asignatura_id = request.GET.get('id')
    if not asignatura_id:
        return JsonResponse({'error': 'id requerido'}, status=400)
    try:
        subj = CurriculoAsignatura.objects.select_related('id_carrera').get(id_asignatura=asignatura_id)
        campo = CurriculoAsignaturaCampo.objects.filter(id_asignatura=subj).select_related('id_campo').first()
        existing = _get_existing_assignment(subj.id_asignatura)
        data = {
            'id_asignatura': subj.id_asignatura,
            'id_carrera': subj.id_carrera_id,
            'carrera_nombre': str(subj.id_carrera),
            'nivel_semestre_asignado': subj.nivel_semestre,
            'horas_clase': subj.horas_semanales_asignatura,
            'id_campo': campo.id_campo_id if campo else None,
            'campo_nombre': str(campo.id_campo) if campo else '',
            'existing_assignment': existing,
        }
        return JsonResponse(data)
    except CurriculoAsignatura.DoesNotExist:
        return JsonResponse({'error': 'no encontrada'}, status=404)


@login_required
def api_recommendations(request):
    """Return top teacher recommendations for a subject as JSON."""
    asignatura_id = request.GET.get('asignatura')
    if not asignatura_id:
        return JsonResponse({'error': 'asignatura requerida'}, status=400)
    try:
        subj = CurriculoAsignatura.objects.get(id_asignatura=asignatura_id)
    except CurriculoAsignatura.DoesNotExist:
        return JsonResponse({'error': 'no encontrada'}, status=404)

    recs = _compute_teacher_scores(subj)[:10]
    data = [{
        'id': r['id'],
        'nombre': r['docente'].nombres_completos,
        'dedicacion': r['docente'].id_dedicacion.codigo_dedicacion,
        'score': r['score'],
        'reasons': r['reasons'],
        'available': r['available'],
        'used': r['used'],
        'max': r['max'],
        'status': r['status'],
    } for r in recs]
    return JsonResponse({'recomendados': data})


@login_required
def api_check_affinity(request):
    asignatura_id = request.GET.get('asignatura')
    docente_id = request.GET.get('docente')
    if not asignatura_id or not docente_id:
        return JsonResponse({'error': 'asignatura y docente requeridos'}, status=400)
    subj_campos = set(CurriculoAsignaturaCampo.objects.filter(id_asignatura_id=asignatura_id).values_list('id_campo_id', flat=True))
    doc_campos = set(DocenteCampoAfinidad.objects.filter(id_docente_id=docente_id).values_list('id_campo_id', flat=True))
    has_affinity = bool(subj_campos & doc_campos)
    return JsonResponse({'has_affinity': has_affinity})


@login_required
@csrf_exempt
def api_crear_asignacion(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST requerido'}, status=405)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)

    docente_id = data.get('id_docente')
    asignatura_id = data.get('id_asignatura')
    carrera_id = data.get('id_carrera')
    periodo_id = data.get('id_periodo')
    campo_id = data.get('id_campo')
    nivel = data.get('nivel_semestre_asignado')
    paralelo = data.get('paralelo_asignado', 'A')
    horas_clase = data.get('horas_clase', 0)
    horas_comp = data.get('horas_complementarias', 0)

    from catalogos.models import CatalogoPeriodoAcademico
    if not periodo_id:
        periodo_activo = CatalogoPeriodoAcademico.objects.filter(periodo_activo=True).first()
        periodo_id = periodo_activo.id_periodo if periodo_activo else None

    if not campo_id:
        campo_rel = CurriculoAsignaturaCampo.objects.filter(id_asignatura_id=asignatura_id).first()
        if campo_rel:
            campo_id = campo_rel.id_campo_id

    if not campo_id:
        return JsonResponse({'error': 'La asignatura no tiene un campo de conocimiento asociado. Seleccione uno manualmente.'}, status=400)

    if not all([docente_id, asignatura_id, carrera_id, periodo_id]):
        return JsonResponse({'error': 'Faltan campos obligatorios'}, status=400)

    existing = list(PlanificacionAsignacionDocente.objects.filter(
        id_asignatura_id=asignatura_id, id_periodo_id=periodo_id
    ).select_related('id_docente'))
    if existing:
        return JsonResponse({
            'error': 'Esta asignatura ya tiene un docente asignado en el per\u00edodo actual.',
            'existing': [{'id': e.id_docente_id, 'nombre': e.id_docente.nombres_completos} for e in existing],
        }, status=409)

    from docentes.models import DocenteFcacc
    asignacion = PlanificacionAsignacionDocente.objects.create(
        id_docente_id=docente_id,
        id_asignatura_id=asignatura_id,
        id_carrera_id=carrera_id,
        id_periodo_id=periodo_id,
        id_campo_id=campo_id,
        nivel_semestre_asignado=nivel or 0,
        paralelo_asignado=paralelo or 'A',
        horas_clase=horas_clase,
        horas_complementarias=horas_comp,
    )
    from core.crud_base import _audit_log
    try:
        _audit_log(request, asignacion, 'INSERT')
    except Exception:
        pass

    return JsonResponse({
        'success': True,
        'id_asignacion': asignacion.id_asignacion,
        'message': 'Asignaci\u00f3n creada correctamente.',
    })
