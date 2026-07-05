from core.crud_base import CrudListView, CrudCreateView, CrudUpdateView, CrudDeleteView
from .models import SeguridadRol, SeguridadUsuario, SeguridadUsuarioRol


class SeguridadRolListView(CrudListView):
    model = SeguridadRol


class SeguridadRolCreateView(CrudCreateView):
    model = SeguridadRol

class SeguridadRolUpdateView(CrudUpdateView):
    model = SeguridadRol

class SeguridadRolDeleteView(CrudDeleteView):
    model = SeguridadRol


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
