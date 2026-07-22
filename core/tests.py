from unittest.mock import patch

from django.test import RequestFactory, SimpleTestCase

from catalogos.models import CatalogoPeriodoAcademico
from core.crud_base import CrudListView
from core.forms import UsuarioCreateForm
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

    def test_rejects_different_password_confirmation(self):
        form = UsuarioCreateForm()
        form.cleaned_data = {
            'password1': 'ClaveSegura2026!',
            'password2': 'OtraClave2026!',
        }

        with self.assertRaisesMessage(Exception, 'Las contraseñas no coinciden.'):
            form.clean_password2()


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
