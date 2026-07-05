import json
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages


class CrudListView(LoginRequiredMixin, ListView):
    paginate_by = 25
    template_name = 'generic_crud/list.html'
    select_related_fields = None

    def get_queryset(self):
        qs = super().get_queryset()
        pk_field = self.model._meta.pk
        if pk_field:
            qs = qs.order_by(pk_field.column)
        if self.select_related_fields:
            qs = qs.select_related(*self.select_related_fields)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        model = self.model
        app = model._meta.app_label
        name = model._meta.model_name
        fields = [f for f in model._meta.get_fields() if f.concrete and not f.auto_created]
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
        return ctx


class CrudCreateView(LoginRequiredMixin, CreateView):
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
        messages.success(self.request, 'Registro creado correctamente.')
        return super().form_valid(form)


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
        messages.success(self.request, 'Registro actualizado correctamente.')
        return super().form_valid(form)


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
