import json
import re
import unicodedata
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages


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
        base = words[0][:3]
    else:
        base = ''.join(w[0] for w in words if w)
    if not base:
        return None
    base = base[:max_len]
    qs = model._default_manager.filter(**{codigo_field.name + '__startswith': base})
    existing = set(qs.values_list(codigo_field.name, flat=True))
    if base not in existing:
        return base
    for i in range(1, 999):
        available = max_len - len(base)
        if available >= 4:
            suffix = f'-{i:03d}'
        elif available >= 3:
            suffix = f'-{i:02d}'
        elif available >= 2:
            suffix = f'-{i:d}'
        else:
            for j in range(1, 999):
                alt = base[:max_len - len(str(j))] + str(j)
                if alt not in existing:
                    return alt
            return base[:max_len]
        candidate = base + suffix
        if candidate not in existing:
            return candidate
    return base[:max_len]


def _auto_generate_codigo(form):
    model = form._meta.model
    codigo_field, nombre_field = _find_codigo_nombre_fields(model)
    if not codigo_field or not nombre_field:
        return
    current_val = form.cleaned_data.get(codigo_field.name) or form.initial.get(codigo_field.name)
    if current_val:
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


class CrudListView(LoginRequiredMixin, ListView):
    paginate_by = 25
    template_name = 'generic_crud/list.html'
    select_related_fields = None
    search_fields = None

    def get_paginate_by(self, queryset):
        cant = self.request.GET.get('cant')
        if cant and cant.isdigit():
            return int(cant)
        return self.paginate_by

    def get_queryset(self):
        qs = super().get_queryset()
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
                if f.get_internal_type() in ('CharField', 'TextField'):
                    fields.append(f.name)
        return fields

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        model = self.model
        app = model._meta.app_label
        name = model._meta.model_name
        fields = [f for f in model._meta.get_fields() if f.concrete and not f.auto_created and not f.primary_key]
        bool_types = {'BooleanField', 'NullBooleanField'}
        date_types = {'DateField', 'DateTimeField'}
        ctx['fields'] = fields
        ctx['bool_fields'] = {f.name for f in fields if hasattr(f, 'get_internal_type') and f.get_internal_type() in bool_types}
        ctx['date_fields'] = {f.name for f in fields if hasattr(f, 'get_internal_type') and f.get_internal_type() in date_types}
        ctx['model_name'] = name
        ctx['model_verbose'] = getattr(model._meta, 'verbose_name', name)
        ctx['model_verbose_plural'] = getattr(model._meta, 'verbose_name_plural', name)
        ctx['list_url'] = f'{app}:{name}_list'
        ctx['create_url'] = f'{app}:{name}_create'
        ctx['update_url'] = f'{app}:{name}_update'
        ctx['delete_url'] = f'{app}:{name}_delete'
        ctx['search_value'] = self.request.GET.get('q', '')
        ctx['search_fields'] = self.get_search_fields()
        raw_cant = self.request.GET.get('cant', self.paginate_by)
        try:
            ctx['cant'] = int(raw_cant)
        except (ValueError, TypeError):
            ctx['cant'] = self.paginate_by
        return ctx


class CrudCreateView(LoginRequiredMixin, CreateView):
    fields = '__all__'
    template_name = 'generic_crud/form.html'
    autofill_rules = {}

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        codigo_field, _ = _find_codigo_nombre_fields(self.model)
        if codigo_field and codigo_field.name in form.fields:
            form.fields[codigo_field.name].required = False
            form.fields[codigo_field.name].help_text = 'Opcional: el sistema lo genera automáticamente.'
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


class CrudUpdateView(LoginRequiredMixin, UpdateView):
    fields = '__all__'
    template_name = 'generic_crud/form.html'
    autofill_rules = {}

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


class CrudDeleteView(LoginRequiredMixin, DeleteView):
    template_name = 'generic_crud/confirm_delete.html'

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
