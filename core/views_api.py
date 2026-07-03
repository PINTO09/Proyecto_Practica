import json
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.db import ProgrammingError, OperationalError
from django.db.models import Q
from django.forms.models import model_to_dict


def _get_model(model_name):
    import core.models as m
    return getattr(m, model_name, None)


def _field_meta(field):
    info = {
        'name': field.name,
        'verbose_name': field.verbose_name or field.name.title(),
        'type': field.get_internal_type(),
        'required': not (field.null or field.blank or getattr(field, 'auto_created', False)),
        'max_length': getattr(field, 'max_length', None),
        'help_text': field.help_text or '',
    }
    if field.is_relation and field.many_to_one and field.related_model:
        info['fk_model'] = field.related_model._meta.model_name
        info['fk_verbose'] = getattr(field.related_model._meta, 'verbose_name', field.related_model._meta.model_name)
    if field.primary_key:
        info['auto_pk'] = True
    return info


def _get_searchable_fields(model):
    return [f for f in model._meta.fields if f.get_internal_type() in ('CharField', 'TextField', 'IntegerField')]


def _serialize(obj):
    d = model_to_dict(obj)
    d['id'] = obj.pk
    for f in obj._meta.fields:
        if f.is_relation and f.many_to_one:
            fk_val = getattr(obj, f.name, None)
            if fk_val is not None:
                d[f.name + '_display'] = str(fk_val)
    return d


# ─── API: Field metadata ─────────────────────────────────────────────────────

@csrf_exempt
@require_http_methods(['GET'])
def api_fields(request, model_name):
    model = _get_model(model_name)
    if not model:
        return JsonResponse({'error': 'Modelo no encontrado'}, status=404)
    try:
        fields = [_field_meta(f) for f in model._meta.fields if not getattr(f, 'auto_pk', False)]
        return JsonResponse({'fields': fields, 'model_name': model_name, 'verbose_name_plural': model._meta.verbose_name_plural or model_name})
    except (ProgrammingError, OperationalError) as e:
        return JsonResponse({'error': str(e)}, status=500)


# ─── API: List with pagination & search ──────────────────────────────────────

@csrf_exempt
@require_http_methods(['GET'])
def api_list(request, model_name):
    model = _get_model(model_name)
    if not model:
        return JsonResponse({'error': 'Modelo no encontrado'}, status=404)
    try:
        search = request.GET.get('search', '').strip()
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))

        pk_name = model._meta.pk.name if model._meta.pk else 'id'
        qs = model.objects.all().order_by(pk_name)
        if search:
            q = Q()
            for f in _get_searchable_fields(model):
                q |= Q(**{f'{f.name}__icontains': search})
            qs = qs.filter(q)

        paginator = Paginator(qs, page_size)
        page_obj = paginator.get_page(page)

        results = [_serialize(o) for o in page_obj]

        return JsonResponse({
            'count': paginator.count,
            'page': page_obj.number,
            'num_pages': paginator.num_pages,
            'page_size': page_size,
            'results': results,
        })
    except (ProgrammingError, OperationalError) as e:
        return JsonResponse({'error': str(e)}, status=500)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


# ─── API: Create ──────────────────────────────────────────────────────────────

@csrf_exempt
@require_http_methods(['POST'])
def api_create(request, model_name):
    model = _get_model(model_name)
    if not model:
        return JsonResponse({'error': 'Modelo no encontrado'}, status=404)
    try:
        data = json.loads(request.body)
        obj = model(**data)
        obj.save()
        return JsonResponse({'success': True, 'data': _serialize(obj)}, status=201)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


# ─── API: Update ──────────────────────────────────────────────────────────────

@csrf_exempt
@require_http_methods(['PUT'])
def api_update(request, model_name, pk):
    model = _get_model(model_name)
    if not model:
        return JsonResponse({'error': 'Modelo no encontrado'}, status=404)
    try:
        obj = model.objects.get(pk=pk)
        data = json.loads(request.body)
        for key, value in data.items():
            setattr(obj, key, value)
        obj.save()
        return JsonResponse({'success': True, 'data': _serialize(obj)})
    except model.DoesNotExist:
        return JsonResponse({'error': 'Registro no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


# ─── API: Delete ──────────────────────────────────────────────────────────────

@csrf_exempt
@require_http_methods(['DELETE'])
def api_delete(request, model_name, pk):
    model = _get_model(model_name)
    if not model:
        return JsonResponse({'error': 'Modelo no encontrado'}, status=404)
    try:
        obj = model.objects.get(pk=pk)
        pk_val = obj.pk
        obj.delete()
        return JsonResponse({'success': True, 'deleted_id': pk_val})
    except model.DoesNotExist:
        return JsonResponse({'error': 'Registro no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
