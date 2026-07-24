from core.crud_base import (
    ReadOnlyCrudListView,
    DisabledCrudMutationMixin,
    CrudCreateView,
    CrudUpdateView,
    CrudDeleteView,
)

from .models import AuditoriaRegistroCambios


class AuditoriaRegistroCambiosListView(ReadOnlyCrudListView):
    model = AuditoriaRegistroCambios


class AuditoriaRegistroCambiosCreateView(DisabledCrudMutationMixin, CrudCreateView):
    model = AuditoriaRegistroCambios


class AuditoriaRegistroCambiosUpdateView(DisabledCrudMutationMixin, CrudUpdateView):
    model = AuditoriaRegistroCambios


class AuditoriaRegistroCambiosDeleteView(DisabledCrudMutationMixin, CrudDeleteView):
    model = AuditoriaRegistroCambios
