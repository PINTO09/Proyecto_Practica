from core.crud_base import CrudListView, CrudCreateView, CrudUpdateView, CrudDeleteView

from .models import SeguridadUsuario, SeguridadUsuarioRol


class SeguridadUsuarioListView(CrudListView):
    model = SeguridadUsuario


class SeguridadUsuarioCreateView(CrudCreateView):
    model = SeguridadUsuario


class SeguridadUsuarioUpdateView(CrudUpdateView):
    model = SeguridadUsuario


class SeguridadUsuarioDeleteView(CrudDeleteView):
    model = SeguridadUsuario


class SeguridadUsuarioRolListView(CrudListView):
    model = SeguridadUsuarioRol


class SeguridadUsuarioRolCreateView(CrudCreateView):
    model = SeguridadUsuarioRol


class SeguridadUsuarioRolUpdateView(CrudUpdateView):
    model = SeguridadUsuarioRol


class SeguridadUsuarioRolDeleteView(CrudDeleteView):
    model = SeguridadUsuarioRol
