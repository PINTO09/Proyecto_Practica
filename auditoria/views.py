import datetime

from django.apps import apps
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from accounts.decorators import module_permission_required
from core.crud_base import (
    ReadOnlyCrudListView,
    DisabledCrudMutationMixin,
    CrudCreateView,
    CrudUpdateView,
    CrudDeleteView,
)

from .models import AuditoriaRegistroCambios

# Nombre de tabla "virtual" que usa carga_masiva.services.apply_audit_log
# para el movimiento único que agrupa una carga completa.
CARGA_MASIVA_TABLA = 'carga_masiva'

# Tope de filas de detalle mostradas en "ver más" de una carga masiva, para
# no inflar la página con cargas de miles de filas.
_CARGA_MASIVA_DETALLE_LIMITE = 500

_MODEL_BY_TABLE = None


def _model_by_table(db_table):
    global _MODEL_BY_TABLE
    if _MODEL_BY_TABLE is None:
        _MODEL_BY_TABLE = {
            model._meta.db_table.lower(): model for model in apps.get_models()
        }
    if not db_table:
        return None
    return _MODEL_BY_TABLE.get(str(db_table).lower())


def _clean_label(label):
    """Limpia etiquetas verbosas: quita prefijos '[...]' y sufijos '(...)'
    que algunos verbose_name incluyen, dejando solo el nombre base."""
    import re
    if not label:
        return label
    text = re.sub(r'^\s*\[[^\]]*\]\s*', '', str(label))
    text = re.sub(r'\s*\([^)]*\)\s*$', '', text)
    return text.strip() or str(label).strip()


def _field_verbose(model, attname):
    key = str(attname).lower()
    if model is not None:
        for field in model._meta.get_fields():
            if (field.concrete and (field.attname.lower() == key or field.name.lower() == key)):
                label = str(field.verbose_name)
                # Para relaciones (p. ej. "id docente") mostrar solo el nombre
                # real del recurso al que pertenece ("Docente").
                if getattr(field, 'is_relation', False) and getattr(field, 'related_model', None) is not None:
                    label = str(field.related_model._meta.verbose_name) or label
                return _clean_label(label)
    return _clean_label(attname.replace('_', ' ').title())


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
    key = str(attname).lower()
    field = None
    for f in model._meta.get_fields():
        if not (f.concrete and getattr(f, 'is_relation', False)
                and f.related_model is not None):
            continue
        if f.name.lower() == key or f.attname.lower() == key:
            field = f
            break
    if field is None:
        return None
    try:
        obj = field.related_model.objects.filter(pk=value).first()
        if obj is not None:
            # Para las actividades complementarias mostrar solo la descripción
            # (nombre) sin el código.
            if hasattr(obj, 'nombre_actividad'):
                return str(obj.nombre_actividad)
            return str(obj)
    except Exception:
        pass
    return None


def _resolve_registro(model, registro_pk):
    """Devuelve el texto legible del registro auditado: su __str__ y el tipo de
    recurso. Devuelve None si el modelo o el registro no se pueden resolver."""
    if model is None or registro_pk is None:
        return None
    try:
        obj = model.objects.filter(pk=registro_pk).first()
        if obj is None:
            return None
        return {
            'modelo_label': str(model._meta.verbose_name),
            'texto': str(obj),
        }
    except Exception:
        return None


def _record_changes(tipo_accion, tabla, valor_anterior, valor_nuevo):
    """Devuelve una lista de dicts {campo, anterior, nuevo} con SOLO los
    campos que cambiaron, usando etiquetas legibles y valores resueltos."""
    old = valor_anterior or {}
    new = valor_nuevo or {}
    model = _model_by_table(tabla)

    # El campo PK (identificador interno del registro) no es relevante para el
    # detalle, así que se omite.
    pk_attname = model._meta.pk.attname.lower() if model is not None else None

    # Normaliza las claves (pueden venir en mayúsculas según el origen) para
    # poder resolver el campo correcto.
    old = {k.strip().lower(): v for k, v in old.items()}
    new = {k.strip().lower(): v for k, v in new.items()}

    def skip(k):
        return pk_attname is not None and k == pk_attname

    def render_old(k, v):
        display = _resolve_related(model, k, v)
        return display or _format_value(v)

    def render_new(k, v):
        display = _resolve_related(model, k, v)
        return display or _format_value(v)

    if tipo_accion == 'INSERT':
        return [
            {'campo': _field_verbose(model, k), 'anterior': None, 'nuevo': render_new(k, v)}
            for k, v in new.items() if not skip(k)
        ]
    if tipo_accion == 'DELETE':
        return [
            {'campo': _field_verbose(model, k), 'anterior': render_old(k, v), 'nuevo': None}
            for k, v in old.items() if not skip(k)
        ]
    # UPDATE: lista todos los campos (igual que INSERT), mostrando el
    # valor anterior y el nuevo de cada uno.
    changes = []
    for k, v in new.items():
        if skip(k):
            continue
        changes.append({
            'campo': _field_verbose(model, k),
            'anterior': render_old(k, old.get(k)),
            'nuevo': render_new(k, v),
        })
    return changes


def _fill_carga_masiva_summary(obj):
    """Arma SOLO el resumen (archivo + contadores) de un movimiento de carga
    masiva a partir del JSON ya cargado con la fila -sin ninguna consulta
    extra a la BD-, para que listar la página de auditoría no dependa de
    cuántas filas tocó cada carga. El detalle itemizado ('ver más') se
    calcula aparte, bajo demanda, en carga_masiva_detalle()."""
    payload = obj.valor_nuevo or {}
    obj.cm_archivo = payload.get('archivo') or 'archivo sin nombre'
    resumen = payload.get('resumen') or {}
    obj.cm_nuevas = resumen.get('nuevas', 0)
    obj.cm_modificadas = resumen.get('modificadas', 0)
    obj.cm_retiradas = resumen.get('retiradas', 0)
    obj.cambios_count = obj.cm_nuevas + obj.cm_modificadas + obj.cm_retiradas
    obj.registro = None


def _build_carga_masiva_detalle(payload):
    """Resuelve el detalle itemizado (registro afectado, campos con su valor
    anterior y nuevo) de una carga masiva. Hace una consulta por fila de
    detalle -por eso se calcula solo bajo demanda ('ver más'), no al listar."""
    detalle_crudo = payload.get('detalle') or []
    items = []
    for raw in detalle_crudo[:_CARGA_MASIVA_DETALLE_LIMITE]:
        model = _model_by_table(raw.get('tabla'))
        registro = _resolve_registro(model, raw.get('pk'))
        items.append({
            'accion': raw.get('accion'),
            'label': registro['modelo_label'] if registro else _clean_label(raw.get('tabla')),
            'registro_texto': registro['texto'] if registro else f"#{raw.get('pk')}",
            'cambios': _record_changes(
                raw.get('accion'), raw.get('tabla'), raw.get('anterior'), raw.get('nuevo'),
            ),
        })
    return items, len(detalle_crudo)


class AuditoriaRegistroCambiosListView(ReadOnlyCrudListView):
    model = AuditoriaRegistroCambios
    template_name = 'auditoria/auditoriaregistrocambios_list.html'
    paginate_by = 25

    def _filtros_activos(self):
        return bool(
            (self.request.GET.get('tipo') or '').strip()
            or (self.request.GET.get('desde') or '').strip()
            or (self.request.GET.get('hasta') or '').strip()
            or (self.request.GET.get('q') or '').strip()
        )

    def _ver_todos(self):
        return self.request.GET.get('todos') == '1' or self._filtros_activos()

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
        # Por defecto solo se muestran las cargas masivas (un movimiento por
        # carga); el resto de la auditoría -cambio por cambio- solo aparece
        # si el usuario pide verlo explícitamente ("ver más") o si empieza a
        # filtrar (tipo, fechas o búsqueda), ya que ahí sí necesita ver el
        # detalle fila por fila para encontrar lo que busca.
        if not self._ver_todos():
            qs = qs.filter(nombre_tabla_afectada=CARGA_MASIVA_TABLA)
        return qs.select_related('id_usuario').order_by('-fecha_hora_cambio', '-pk')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['tipo_filter'] = (self.request.GET.get('tipo') or '').strip()
        ctx['desde'] = self.request.GET.get('desde', '')
        ctx['hasta'] = self.request.GET.get('hasta', '')
        ctx['ver_todos'] = self._ver_todos()
        ctx['filtros_activos'] = self._filtros_activos()
        ctx['tipos'] = [
            t.strip() for t in AuditoriaRegistroCambios.objects.values_list(
                'tipo_accion', flat=True
            ).distinct().order_by('tipo_accion')
        ]
        for obj in ctx['object_list']:
            # fecha_hora_cambio vive en una columna "timestamp" (sin zona
            # horaria) de una tabla managed=False; psycopg2 la devuelve
            # naive, así que Django no la reconvierte de UTC a la zona local
            # (America/Guayaquil) y el filtro `date` del template terminaba
            # mostrando la hora UTC tal cual, como si fuera la hora local.
            # Se guardó como UTC (auto_now_add con USE_TZ=True), así que
            # basta con marcarla aware en UTC para que la conversión a hora
            # local funcione en las plantillas.
            if obj.fecha_hora_cambio and timezone.is_naive(obj.fecha_hora_cambio):
                obj.fecha_hora_cambio = timezone.make_aware(obj.fecha_hora_cambio, datetime.timezone.utc)
            obj.tipo_label = obj.tipo_accion.strip()
            obj.es_carga_masiva = obj.nombre_tabla_afectada == CARGA_MASIVA_TABLA
            if obj.es_carga_masiva:
                _fill_carga_masiva_summary(obj)
            else:
                obj.cambios = _record_changes(
                    obj.tipo_accion, obj.nombre_tabla_afectada,
                    obj.valor_anterior, obj.valor_nuevo,
                )
                obj.cambios_count = len(obj.cambios)
                obj.registro = _resolve_registro(
                    _model_by_table(obj.nombre_tabla_afectada), obj.id_registro_afectado
                )
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


@login_required
@module_permission_required('auditoria', 'view')
def carga_masiva_detalle(request, pk):
    """Detalle itemizado de un movimiento de carga masiva, cargado bajo
    demanda (fetch) cuando se abre 'ver más' -no al listar auditoría-, ya
    que resolver cada fila afectada cuesta una consulta por fila."""
    obj = get_object_or_404(AuditoriaRegistroCambios, pk=pk, nombre_tabla_afectada=CARGA_MASIVA_TABLA)
    detalle, total = _build_carga_masiva_detalle(obj.valor_nuevo or {})
    return render(request, 'auditoria/_carga_masiva_detalle.html', {
        'detalle': detalle,
        'detalle_total': total,
        'detalle_mostrado': len(detalle),
    })
