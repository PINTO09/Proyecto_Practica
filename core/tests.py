from unittest.mock import patch

from django.test import RequestFactory, SimpleTestCase
from django.core.exceptions import PermissionDenied
from types import SimpleNamespace

from catalogos.models import CatalogoPeriodoAcademico
from core.crud_base import CrudListView
from core.forms import UsuarioCreateForm, DocenteFcaccForm
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from datetime import timedelta
from accounts.decorators import can_access_module, module_permission_required
from accounts.middleware import ForcePasswordChangeMiddleware
from core.management.commands.load_schema import split_sql_statements


class SqlSplitterTests(SimpleTestCase):
    def test_split_sql_statements_respects_dollar_quoted_blocks(self):
        sql = """
        CREATE FUNCTION ejemplo() RETURNS void AS $$
        BEGIN
            INSERT INTO tabla VALUES (1);
        END;
        $$ LANGUAGE plpgsql;

        CREATE TABLE otro(id INT);
        """

        statements = split_sql_statements(sql)

        self.assertEqual(len(statements), 2)
        self.assertIn('CREATE FUNCTION ejemplo()', statements[0])
        self.assertIn('CREATE TABLE otro(id INT);', statements[1])


class UsuarioFormTests(SimpleTestCase):
    @patch('core.forms.Usuario.objects.filter')
    def test_rejects_duplicate_identity_with_clear_message(self, filter_mock):
        filter_mock.return_value.exists.return_value = True
        form = UsuarioCreateForm()
        form.cleaned_data = {'cedula': '1300000003'}

        with self.assertRaisesMessage(Exception, 'Ya existe un usuario registrado con esta cédula.'):
            form.clean_cedula()


class UnifiedProfileFormTests(SimpleTestCase):
    def test_rejects_photo_larger_than_five_megabytes(self):
        photo = SimpleNamespace(size=5 * 1024 * 1024 + 1, content_type='image/jpeg')
        form = DocenteFcaccForm()
        form.cleaned_data = {'foto': photo}
        with self.assertRaisesMessage(Exception, 'La fotografía no puede superar 5 MB.'):
            form.clean_foto()

    def test_rejects_non_image_upload(self):
        photo = SimpleUploadedFile('archivo.txt', b'no es una imagen', content_type='text/plain')
        form = DocenteFcaccForm()
        form.cleaned_data = {'foto': photo}
        with self.assertRaisesMessage(Exception, 'Utilice una imagen JPG, PNG o WEBP.'):
            form.clean_foto()

    def test_rejects_future_birth_date(self):
        form = DocenteFcaccForm()
        form.cleaned_data = {'fecha_nacimiento': timezone.localdate() + timedelta(days=1)}
        with self.assertRaisesMessage(Exception, 'La fecha de nacimiento debe ser anterior a hoy.'):
            form.clean_fecha_nacimiento()

class CrudPaginationTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def _page_size(self, value):
        view = CrudListView()
        view.request = self.factory.get('/', {'cant': value})
        return view.get_paginate_by(queryset=None)

    def test_accepts_supported_page_size(self):
        self.assertEqual(self._page_size('100'), 100)

    def test_rejects_unbounded_page_size(self):
        self.assertEqual(self._page_size('999999'), 25)

    def test_rejects_invalid_page_size(self):
        self.assertEqual(self._page_size('texto'), 25)


class CrudFieldTypeTests(SimpleTestCase):
    def test_date_fields_are_not_treated_as_datetimes(self):
        view = CrudListView()
        view.model = CatalogoPeriodoAcademico
        view.request = RequestFactory().get('/')
        view.object_list = []
        view.kwargs = {}

        context = view.get_context_data(object_list=[])

        self.assertIn('fecha_inicio_periodo', context['date_fields'])
        self.assertNotIn('fecha_inicio_periodo', context['datetime_fields'])


class RolePermissionTests(SimpleTestCase):
    @patch('accounts.decorators.get_user_roles', return_value=['Coordinador'])
    def test_coordinator_can_change_planning_but_not_catalogs(self, _roles):
        user = SimpleNamespace(is_authenticated=True, is_superuser=False)
        self.assertTrue(can_access_module(user, 'planificacion', 'change'))
        self.assertFalse(can_access_module(user, 'catalogos', 'change'))

    @patch('accounts.decorators.get_user_roles', return_value=['Funcionario'])
    def test_funcionario_is_read_only(self, _roles):
        user = SimpleNamespace(is_authenticated=True, is_superuser=False)
        self.assertTrue(can_access_module(user, 'planificacion', 'view'))
        self.assertFalse(can_access_module(user, 'planificacion', 'change'))

    @patch('accounts.decorators.can_access_module', return_value=False)
    def test_docente_cannot_open_reports(self, _access):
        request = RequestFactory().get('/reportes/')
        request.user = SimpleNamespace(is_authenticated=True)
        protected = module_permission_required('reportes')(
            lambda request: None
        )
        with self.assertRaises(PermissionDenied):
            protected(request)

    def test_temporary_password_forces_change(self):
        request = RequestFactory().get('/dashboard/')
        request.user = SimpleNamespace(is_authenticated=True, debe_cambiar_password=True)
        response = ForcePasswordChangeMiddleware(lambda request: None)(request)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/cambiar-password/', response.url)
