import json
import re
import unicodedata
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django import forms
from accounts.decorators import can_access_module, allowed_career_ids


def _scope_queryset_by_career(queryset, user):
    career_ids = allowed_career_ids(user)
    if career_ids is None:
        return queryset
    field_names = {field.name for field in queryset.model._meta.get_fields()}
    for candidate in ('id_carrera', 'carrera'):
        if candidate in field_names:
            return queryset.filter(**{f'{candidate}_id__in': career_ids})
    return queryset


def _limit_career_form_fields(form, user):
    career_ids = allowed_career_ids(user)
    if career_ids is None:
        return
    for field in form.fields.values():
        queryset = getattr(field, 'queryset', None)
        if queryset is not None and queryset.model._meta.label_lower == 'catalogos.catalogocarrera':
            field.queryset = queryset.filter(pk__in=career_ids)


def _prepare_crud_form(view, form):
    """Uniforma orden, etiquetas y controles de los formularios CRUD."""
    order = getattr(view, 'form_field_order', None)
    if order:
        form.order_fields(order)
    label_overrides = getattr(view, 'form_field_labels', {}) or {}
    for name, field in form.fields.items():
        try:
            model_field = view.model._meta.get_field(name)
        except Exception:
            model_field = None

        if name in label_overrides:
            field.label = label_overrides[name]
        elif model_field is not None and model_field.is_relation and name.startswith('id_'):
            label = str(model_field.related_model._meta.verbose_name)
            label = re.sub(r'^\[[^]]+\]\s*', '', label)
            field.label = re.sub(r'\s*\([^)]*\)\s*$', '', label)

        widget = field.widget
        current_class = widget.attrs.get('class', '')
        if isinstance(widget, forms.CheckboxInput):
            desired_class = 'form-check-input'
        elif isinstance(widget, (forms.Select, forms.SelectMultiple)):
            desired_class = 'form-select'
            if hasattr(field, 'empty_label') and field.empty_label == '---------':
                field.empty_label = f'Seleccione {str(field.label).lower()}'
        else:
            desired_class = 'form-control'
        widget.attrs['class'] = ' '.join(dict.fromkeys(
            part for part in f'{current_class} {desired_class}'.split() if part
        ))
        if (
            isinstance(widget, forms.Select)
            and not isinstance(widget, forms.SelectMultiple)
            and getattr(field, 'queryset', None) is not None
        ):
            related_label = field.queryset.model._meta.label_lower
            if related_label in {
                'catalogos.catalogocarrera',
                'catalogos.catalogocampoconocimiento',
                'catalogos.catalogoperiodoacademico',
                'curriculo.curriculoasignatura',
                'docentes.docentefcacc',
                'planificacion.planificacionasignaciondocente',
            }:
                widget.attrs.setdefault('data-searchable-select', 'true')
                widget.attrs.setdefault(
                    'data-search-placeholder',
                    f'Buscar {str(field.label).lower()}...',
                )

        if model_field is not None:
            internal_type = model_field.get_internal_type()
            if internal_type == 'DateField':
                widget.attrs.setdefault('type', 'date')
            elif internal_type == 'DateTimeField':
                widget.attrs.setdefault('type', 'datetime-local')
            elif internal_type == 'TimeField':
                widget.attrs.setdefault('type', 'time')
        if isinstance(widget, forms.Textarea):
            widget.attrs.setdefault('rows', 3)
    return form


def _get_seguridad_user(user):
    if not user or not user.is_authenticated:
        return None
    from seguridad.models import SeguridadUsuario
    for field in ('cedula', 'username', 'email'):
        val = getattr(user, field, None)
        if val:
            try:
                return SeguridadUsuario.objects.get(nombre_usuario=val)
            except SeguridadUsuario.DoesNotExist:
                continue
    return None


def _get_client_ip(request):
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def _model_to_dict(instance):
    result = {}
    for field in instance._meta.get_fields():
        if field.concrete and not field.auto_created:
            try:
                val = getattr(instance, field.attname)
                if val is not None and hasattr(val, 'pk'):
                    val = val.pk
                elif val is not None and hasattr(val, 'isoformat'):
                    val = val.isoformat()
                result[field.attname] = val
            except Exception:
                result[field.attname] = None
    return result


def _find_codigo_nombre_fields(model):
    codigo_field = None
    nombre_field = None
    for field in model._meta.get_fields():
        if not field.concrete or field.auto_created:
            continue
        if field.name.startswith('codigo_') or field.name == 'codigo':
            from django.db.models import CharField
            if isinstance(field, CharField):
                codigo_field = field
        if field.name.startswith('nombre_'):
            nombre_field = field
    return codigo_field, nombre_field


def _generate_codigo(nombre_value, codigo_field, model):
    if not nombre_value:
        return None
    max_len = getattr(codigo_field, 'max_length', 20)
    raw = unicodedata.normalize('NFKD', str(nombre_value))
    raw = ''.join(ch for ch in raw if not unicodedata.combining(ch))
    raw = re.sub(r'[^A-Za-z0-9\s]', '', raw).upper().strip()
    words = [w for w in raw.split() if w]
    if not words:
        return None
    if len(words) == 1:
        siglas = words[0][:5]
    else:
        siglas = ''.join(w[0] for w in words if w)
    if not siglas:
        return None
    if max_len >= 6:
        suffix_room = 4
    elif max_len >= 4:
        suffix_room = 3
    else:
        suffix_room = 2
    base_max = max_len - suffix_room
    if base_max < 2:
        base_max = 2
        suffix_room = max_len - 2
        if suffix_room < 1:
            suffix_room = 1
    base = siglas[:base_max]
    prefix = base + '-'
    qs = model._default_manager.filter(**{codigo_field.name + '__startswith': prefix})
    existing = set(qs.values_list(codigo_field.name, flat=True))
    for i in range(1, 9999):
        if suffix_room == 4:
            candidate = f'{base}-{i:03d}'
        elif suffix_room == 3:
            candidate = f'{base}-{i:02d}'
        elif suffix_room == 2:
            candidate = f'{base}-{i:d}'
        else:
            candidate = f'{base}{i:d}'
        if len(candidate) > max_len:
            continue
        if candidate not in existing:
            return candidate
    return base


def _auto_generate_codigo(form):
    model = form._meta.model
    codigo_field, nombre_field = _find_codigo_nombre_fields(model)
    if not codigo_field or not nombre_field:
        return
    nombre_val = form.cleaned_data.get(nombre_field.name) or getattr(form.instance, nombre_field.attname, None)
    generated = _generate_codigo(nombre_val, codigo_field, model)
    if generated:
        setattr(form.instance, codigo_field.attname, generated)


def _audit_log(request, instance, action, old_values=None):
    from auditoria.models import AuditoriaRegistroCambios
    if instance._meta.model_name == 'auditoriaregistrocambios':
        return
    seg_user = _get_seguridad_user(request.user)
    new_values = _model_to_dict(instance) if action != 'DELETE' else None
    AuditoriaRegistroCambios.objects.create(
        id_usuario=seg_user,
        nombre_tabla_afectada=instance._meta.db_table,
        id_registro_afectado=instance.pk,
        tipo_accion=action,
        valor_anterior=old_values,
        valor_nuevo=new_values,
        direccion_ip_origen=_get_client_ip(request),
    )


class RoleAccessMixin:
    access_action = 'view'

    def dispatch(self, request, *args, **kwargs):
        module = self.model._meta.app_label
        if not can_access_module(request.user, module, self.access_action):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class CrudListView(LoginRequiredMixin, RoleAccessMixin, ListView):
    paginate_by = 25
    allowed_page_sizes = (10, 25, 50, 100)
    template_name = 'generic_crud/list.html'
    select_related_fields = None
    search_fields = None

    def get_paginate_by(self, queryset):
        cant = self.request.GET.get('cant')
        if cant and cant.isdigit() and int(cant) in self.allowed_page_sizes:
            return int(cant)
        return self.paginate_by

    def get_queryset(self):
        qs = _scope_queryset_by_career(super().get_queryset(), self.request.user)
        pk_field = self.model._meta.pk
        if pk_field:
            qs = qs.order_by(pk_field.column)
        if self.select_related_fields:
            qs = qs.select_related(*self.select_related_fields)
        search = self.request.GET.get('q', '').strip()
        search_fields_list = self.get_search_fields()
        if search and search_fields_list:
            from django.db.models import Q
            query = Q()
            for field_name in search_fields_list:
                query |= Q(**{f'{field_name}__icontains': search})
            qs = qs.filter(query)
        return qs

    def get_search_fields(self):
        if self.search_fields is not None:
            return self.search_fields
        fields = []
        for f in self.model._meta.get_fields():
            if f.concrete and not f.auto_created and hasattr(f, 'get_internal_type'):
                if f.get_internal_type() in ('CharField', 'TextField', 'EmailField'):
                    fields.append(f.name)
                elif f.is_relation and getattr(f, 'many_to_one', False) and f.related_model:
                    # Los listados relacionales deben poder localizarse por el texto
                    # que el usuario ve (docente, carrera, periodo, asignatura, etc.).
                    for related_field in f.related_model._meta.get_fields():
                        if (
                            related_field.concrete
                            and not related_field.auto_created
                            and not related_field.is_relation
                            and hasattr(related_field, 'get_internal_type')
                            and related_field.get_internal_type() in ('CharField', 'TextField', 'EmailField')
                        ):
                            fields.append(f'{f.name}__{related_field.name}')
        return fields

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        model = self.model
        app = model._meta.app_label
        name = model._meta.model_name
        fields = [f for f in model._meta.get_fields() if f.concrete and not f.auto_created and not f.primary_key]
        bool_types = {'BooleanField', 'NullBooleanField'}
        image_types = {'ImageField'}
        ctx['fields'] = fields
        ctx['bool_fields'] = {f.name for f in fields if hasattr(f, 'get_internal_type') and f.get_internal_type() in bool_types}
        ctx['date_fields'] = {
            f.name for f in fields
            if hasattr(f, 'get_internal_type') and f.get_internal_type() == 'DateField'
        }
        ctx['datetime_fields'] = {
            f.name for f in fields
            if hasattr(f, 'get_internal_type') and f.get_internal_type() == 'DateTimeField'
        }
        ctx['image_fields'] = {f.name for f in fields if hasattr(f, 'get_internal_type') and f.get_internal_type() in image_types}
        ctx['model_name'] = name
        ctx['model_verbose'] = getattr(model._meta, 'verbose_name', name)
        ctx['model_verbose_plural'] = getattr(model._meta, 'verbose_name_plural', name)
        ctx['list_url'] = f'{app}:{name}_list'
        ctx['create_url'] = f'{app}:{name}_create'
        ctx['update_url'] = f'{app}:{name}_update'
        ctx['delete_url'] = f'{app}:{name}_delete'
        ctx['search_value'] = self.request.GET.get('q', '')
        ctx['search_fields'] = self.get_search_fields()
        ctx['search_placeholder'] = f'Buscar en {getattr(model._meta, "verbose_name_plural", name).lower()}...'
        ctx['can_change_records'] = can_access_module(
            getattr(self.request, 'user', None), app, 'change'
        )
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


class ReadOnlyCrudListView(CrudListView):
    """Listado informativo sin acciones de creación, edición o eliminación."""

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['can_change_records'] = False
        return ctx


class DisabledCrudMutationMixin:
    """Bloquea formularios heredados que ya no deben modificar datos."""

    def dispatch(self, request, *args, **kwargs):
        raise PermissionDenied


class CrudCreateView(LoginRequiredMixin, RoleAccessMixin, CreateView):
    access_action = 'change'
    fields = '__all__'
    template_name = 'generic_crud/form.html'
    autofill_rules = {}
    form_field_order = None
    form_field_labels = {}

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        _limit_career_form_fields(form, self.request.user)
        _prepare_crud_form(self, form)
        codigo_field, _ = _find_codigo_nombre_fields(self.model)
        if codigo_field and codigo_field.name in form.fields:
            form.fields[codigo_field.name].required = False
            form.fields[codigo_field.name].help_text = 'El sistema lo genera automáticamente.'
            form.fields[codigo_field.name].widget.attrs['readonly'] = True
            form.fields[codigo_field.name].widget.attrs['class'] = 'form-control bg-light'
        return form

    def get_success_url(self):
        return reverse_lazy(f'{self.model._meta.app_label}:{self.model._meta.model_name}_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        model = self.model
        app = model._meta.app_label
        name = model._meta.model_name
        ctx['model_name'] = name
        ctx['model_verbose'] = getattr(model._meta, 'verbose_name', name)
        ctx['list_url'] = f'{app}:{name}_list'
        ctx['autofill_rules_json'] = json.dumps(self.autofill_rules, default=str)
        return ctx

    def form_valid(self, form):
        _auto_generate_codigo(form)
        response = super().form_valid(form)
        _audit_log(self.request, self.object, 'INSERT')
        messages.success(self.request, 'Registro creado correctamente.')
        return response


class CrudUpdateView(LoginRequiredMixin, RoleAccessMixin, UpdateView):
    access_action = 'change'
    fields = '__all__'
    template_name = 'generic_crud/form.html'
    autofill_rules = {}
    form_field_order = None
    form_field_labels = {}

    def get_queryset(self):
        return _scope_queryset_by_career(super().get_queryset(), self.request.user)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        _limit_career_form_fields(form, self.request.user)
        _prepare_crud_form(self, form)
        return form

    def get_success_url(self):
        return reverse_lazy(f'{self.model._meta.app_label}:{self.model._meta.model_name}_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        model = self.model
        app = model._meta.app_label
        name = model._meta.model_name
        ctx['model_name'] = name
        ctx['model_verbose'] = getattr(model._meta, 'verbose_name', name)
        ctx['list_url'] = f'{app}:{name}_list'
        ctx['autofill_rules_json'] = json.dumps(self.autofill_rules, default=str)
        return ctx

    def form_valid(self, form):
        old_values = _model_to_dict(self.get_object())
        _auto_generate_codigo(form)
        response = super().form_valid(form)
        _audit_log(self.request, self.object, 'UPDATE', old_values=old_values)
        messages.success(self.request, 'Registro actualizado correctamente.')
        return response


class CrudDeleteView(LoginRequiredMixin, RoleAccessMixin, DeleteView):
    access_action = 'change'
    template_name = 'generic_crud/confirm_delete.html'

    def get_queryset(self):
        return _scope_queryset_by_career(super().get_queryset(), self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        model = self.model
        app = model._meta.app_label
        name = model._meta.model_name
        ctx['model_name'] = name
        ctx['model_verbose'] = getattr(model._meta, 'verbose_name', name)
        ctx['list_url'] = f'{app}:{name}_list'
        return ctx

    def get_success_url(self):
        messages.success(self.request, 'Registro eliminado correctamente.')
        return reverse_lazy(f'{self.model._meta.app_label}:{self.model._meta.model_name}_list')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        old_values = _model_to_dict(self.object)
        _audit_log(request, self.object, 'DELETE', old_values=old_values)
        return super().delete(request, *args, **kwargs)
