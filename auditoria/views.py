from django.apps import apps

from core.crud_base import (
    ReadOnlyCrudListView,
    DisabledCrudMutationMixin,
    CrudCreateView,
    CrudUpdateView,
    CrudDeleteView,
)

from .models import AuditoriaRegistroCambios


_MODEL_BY_TABLE = None


def _model_by_table(db_table):
    global _MODEL_BY_TABLE
    if _MODEL_BY_TABLE is None:
        _MODEL_BY_TABLE = {
            model._meta.db_table: model for model in apps.get_models()
        }
    return _MODEL_BY_TABLE.get(db_table)


def _field_verbose(model, attname):
    if model is not None:
        for field in model._meta.get_fields():
            if field.concrete and field.attname == attname:
                return str(field.verbose_name)
    return attname.replace('_', ' ').title()


def _format_value(value):
    if value is None:
        return '—'
    if isinstance(value, bool):
        return 'Sí' if value else 'No'
    text = str(value)
    if len(text) > 120:
        return text[:120] + '…'
    return text


def _resolve_related(model, attname, value):
    """Intenta mostrar el registro relacionado (por su __str__) en lugar del
    id crudo para los campos FK. Devuelve None si no se puede resolver."""
    if value is None or model is None:
        return None
    field = None
    for f in model._meta.get_fields():
        if (
            f.concrete and f.attname == attname
            and getattr(f, 'is_relation', False) and f.related_model is not None
        ):
            field = f
            break
    if field is None:
        return None
    try:
        obj = field.related_model.objects.filter(pk=value).first()
        if obj is not None:
            return str(obj)
    except Exception:
        pass
    return None


def _record_changes(record):
    """Devuelve una lista de dicts {campo, anterior, nuevo} con SOLO los
    campos que cambiaron, usando etiquetas legibles y valores resueltos."""
    old = record.valor_anterior or {}
    new = record.valor_nuevo or {}
    model = _model_by_table(record.nombre_tabla_afectada)
    NOISE_FIELDS = {'observaciones', 'observacion'}

    def render_old(k, v):
        display = _resolve_related(model, k, v)
        return display or _format_value(v)

    def render_new(k, v):
        display = _resolve_related(model, k, v)
        return display or _format_value(v)

    def clean(items):
        return [(k, v) for k, v in items if k.lower() not in NOISE_FIELDS]

    if record.tipo_accion == 'INSERT':
        return [
            {'campo': _field_verbose(model, k), 'anterior': None, 'nuevo': render_new(k, v)}
            for k, v in clean(new.items())
        ]
    if record.tipo_accion == 'DELETE':
        return [
            {'campo': _field_verbose(model, k), 'anterior': render_old(k, v), 'nuevo': None}
            for k, v in clean(old.items())
        ]
    # UPDATE: solo los campos que efectivamente cambiaron
    changes = []
    for k, v in clean(new.items()):
        if old.get(k) != v:
            changes.append({
                'campo': _field_verbose(model, k),
                'anterior': render_old(k, old.get(k)),
                'nuevo': render_new(k, v),
            })
    return changes


class AuditoriaRegistroCambiosListView(ReadOnlyCrudListView):
    model = AuditoriaRegistroCambios
    template_name = 'auditoria/auditoriaregistrocambios_list.html'
    paginate_by = 25

    def get_queryset(self):
        qs = super().get_queryset()
        tipo = (self.request.GET.get('tipo') or '').strip()
        desde = (self.request.GET.get('desde') or '').strip()
        hasta = (self.request.GET.get('hasta') or '').strip()
        if tipo:
            qs = qs.filter(tipo_accion__startswith=tipo)
        if desde:
            qs = qs.filter(fecha_hora_cambio__date__gte=desde)
        if hasta:
            qs = qs.filter(fecha_hora_cambio__date__lte=hasta)
        return qs.order_by('-fecha_hora_cambio', '-pk')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['tipo_filter'] = (self.request.GET.get('tipo') or '').strip()
        ctx['desde'] = self.request.GET.get('desde', '')
        ctx['hasta'] = self.request.GET.get('hasta', '')
        ctx['tipos'] = [
            t.strip() for t in AuditoriaRegistroCambios.objects.values_list(
                'tipo_accion', flat=True
            ).distinct().order_by('tipo_accion')
        ]
        for obj in ctx['object_list']:
            obj.tipo_label = obj.tipo_accion.strip()
            obj.cambios = _record_changes(obj)
            u = obj.id_usuario
            if u is not None:
                nombre = f"{u.first_name} {u.last_name}".strip()
                obj.usuario_label = f"{nombre} ({u.cedula})" if nombre else u.cedula
            else:
                obj.usuario_label = '—'
        return ctx


class AuditoriaRegistroCambiosCreateView(DisabledCrudMutationMixin, CrudCreateView):
    model = AuditoriaRegistroCambios


class AuditoriaRegistroCambiosUpdateView(DisabledCrudMutationMixin, CrudUpdateView):
    model = AuditoriaRegistroCambios


class AuditoriaRegistroCambiosDeleteView(DisabledCrudMutationMixin, CrudDeleteView):
    model = AuditoriaRegistroCambios
