from unittest.mock import MagicMock, Mock, patch

from django.test import SimpleTestCase
from django.contrib import messages
from django.test import RequestFactory
from django.core.exceptions import PermissionDenied

from accounts.decorators import (
    DOCENTE, DECANO, ADMIN, AUTORIDAD, COORDINADOR, FUNCIONARIO,
    allowed_career_ids, can_access_module,
)


class DecanoPermissionTests(SimpleTestCase):
    @patch('accounts.decorators._modulos_efectivos', return_value={
        'catalogos': ['view', 'change'], 'docentes': ['view', 'change'],
        'certificados': ['view', 'change'], 'curriculo': ['view', 'change'],
        'planificacion': ['view', 'change'], 'reportes': ['view'],
        'restricciones': ['view', 'change'], 'auditoria': ['view'],
        'self_service': ['view', 'change'], 'seguridad': ['view', 'change'],
    })
    @patch('accounts.decorators.get_user_roles', return_value=[DECANO])
    def test_decano_conserva_estructura_base_docente(self, _roles, _modulos):
        user = MagicMock(is_authenticated=True, is_superuser=False)
        # El flujo base del docente (self_service) queda dentro de la matriz de Decano
        self.assertTrue(can_access_module(user, 'self_service', 'view'))
        self.assertTrue(can_access_module(user, 'self_service', 'change'))

    @patch('accounts.decorators._modulos_efectivos', return_value={
        'catalogos': ['view', 'change'], 'docentes': ['view', 'change'],
        'certificados': ['view', 'change'], 'curriculo': ['view', 'change'],
        'planificacion': ['view', 'change'], 'reportes': ['view'],
        'restricciones': ['view', 'change'], 'auditoria': ['view'],
        'self_service': ['view', 'change'], 'seguridad': ['view', 'change'],
    })
    @patch('accounts.decorators.get_user_roles', return_value=[DECANO])
    def test_decano_tiene_permisos_elevados(self, _roles, _modulos):
        user = MagicMock(is_authenticated=True, is_superuser=False)
        for module in ('catalogos', 'docentes', 'certificados', 'curriculo',
                       'planificacion', 'seguridad'):
            self.assertTrue(can_access_module(user, module, 'change'), module)
            self.assertTrue(can_access_module(user, module, 'view'), module)

    @patch('accounts.decorators._alcance_rol', return_value='global')
    @patch('accounts.decorators.get_user_roles', return_value=[DECANO])
    def test_decano_tiene_alcance_global_en_toda_la_facultad(self, _roles, _alcance):
        user = MagicMock(is_authenticated=True, is_superuser=False)
        # El Decano administra su decanato entero: alcance global (None)
        self.assertIsNone(allowed_career_ids(user))


class RoleTransitionTests(SimpleTestCase):
    def _grupo(self, name):
        g = Mock()
        g.name = name
        return g

    def _fake_user(self, active_groups):
        """Simula un usuario con grupos activos sin tocar la base de datos."""
        groups = type('GroupsM2M', (), {})()
        groups.active = set(active_groups)

        def remove(*targets):
            names = {
                t.name if hasattr(t, 'name') else t
                for t in targets
            }
            groups.active -= {g for g in groups.active if g in names}

        def add(*targets):
            groups.active.update(t.name if hasattr(t, 'name') else t for t in targets)

        groups.remove = remove
        groups.add = add

        user = MagicMock()
        user.groups = groups
        user.alcances_carrera = MagicMock()
        user.alcances_carrera.update = MagicMock(return_value=0)
        user.alcances_carrera.get_or_create = MagicMock(
            return_value=(MagicMock(), True)
        )

        return user

    @patch('accounts.role_service.Rol.objects.get_or_create')
    @patch('accounts.role_service.Group.objects.get_or_create')
    @patch('accounts.role_service.Group.objects.filter')
    def test_promover_docente_a_decano_quita_docente_y_pone_decano(
        self, filter_mock, get_or_create_mock, rol_mock
    ):
        from accounts.role_service import asignar_rol

        user = self._fake_user({DOCENTE})
        filter_mock.return_value = [self._grupo(DOCENTE)]
        get_or_create_mock.return_value = (self._grupo(DECANO), False)
        rol_mock.return_value = (Mock(), False)

        asignar_rol(user, DECANO, [], user)

        self.assertNotIn(DOCENTE, user.groups.active)
        self.assertIn(DECANO, user.groups.active)

    @patch('accounts.role_service.Rol.objects.get_or_create')
    @patch('accounts.role_service.Group.objects.get_or_create')
    @patch('accounts.role_service.Group.objects.filter')
    def test_rol_unico_promocion_reemplaza_todo_cargo_anterior(
        self, filter_mock, get_or_create_mock, rol_mock
    ):
        from accounts.role_service import asignar_rol

        user = self._fake_user({AUTORIDAD, COORDINADOR})
        filter_mock.return_value = [self._grupo(AUTORIDAD), self._grupo(COORDINADOR)]
        get_or_create_mock.return_value = (self._grupo(DECANO), False)
        rol_mock.return_value = (Mock(), False)

        asignar_rol(user, DECANO, [], user)

        self.assertEqual(user.groups.active, {DECANO})

    @patch('accounts.role_service.Rol.objects.get_or_create')
    @patch('accounts.role_service.Group.objects.get_or_create')
    @patch('accounts.role_service.Group.objects.filter')
    def test_coordinador_almacena_carreras_en_alcance(self, filter_mock, get_or_create_mock, rol_mock):
        from accounts.role_service import asignar_rol

        user = self._fake_user({COORDINADOR})
        filter_mock.return_value = [self._grupo(COORDINADOR)]
        get_or_create_mock.return_value = (self._grupo(COORDINADOR), False)
        rol_mock.return_value = (Mock(), False)
        careers = [Mock(pk=1), Mock(pk=2)]

        asignar_rol(user, COORDINADOR, careers, user)

        user.alcances_carrera.get_or_create.assert_called()
        user.alcances_carrera.update.assert_called_once()