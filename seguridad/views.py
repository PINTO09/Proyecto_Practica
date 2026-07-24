from core.crud_base import (
    ReadOnlyCrudListView,
    DisabledCrudMutationMixin,
    CrudCreateView,
    CrudUpdateView,
    CrudDeleteView,
)

from .models import SeguridadRol, SeguridadUsuario, SeguridadUsuarioRol


class SeguridadRolListView(ReadOnlyCrudListView):
    model = SeguridadRol


class SeguridadRolCreateView(DisabledCrudMutationMixin, CrudCreateView):
    model = SeguridadRol


class SeguridadRolUpdateView(DisabledCrudMutationMixin, CrudUpdateView):
    model = SeguridadRol


class SeguridadRolDeleteView(DisabledCrudMutationMixin, CrudDeleteView):
    model = SeguridadRol


class SeguridadUsuarioListView(ReadOnlyCrudListView):
    model = SeguridadUsuario


class SeguridadUsuarioCreateView(DisabledCrudMutationMixin, CrudCreateView):
    model = SeguridadUsuario


class SeguridadUsuarioUpdateView(DisabledCrudMutationMixin, CrudUpdateView):
    model = SeguridadUsuario


class SeguridadUsuarioDeleteView(DisabledCrudMutationMixin, CrudDeleteView):
    model = SeguridadUsuario


class SeguridadUsuarioRolListView(ReadOnlyCrudListView):
    model = SeguridadUsuarioRol


class SeguridadUsuarioRolCreateView(DisabledCrudMutationMixin, CrudCreateView):
    model = SeguridadUsuarioRol


class SeguridadUsuarioRolUpdateView(DisabledCrudMutationMixin, CrudUpdateView):
    model = SeguridadUsuarioRol


class SeguridadUsuarioRolDeleteView(DisabledCrudMutationMixin, CrudDeleteView):
    model = SeguridadUsuarioRol
