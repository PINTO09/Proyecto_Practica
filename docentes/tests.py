from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from .forms import DocenteFcaccForm


class DocenteFormValidationTests(SimpleTestCase):
    def test_accepts_valid_ecuadorian_identifiers_by_type(self):
        form = DocenteFcaccForm()
        form.cleaned_data = {'tipo_documento': 'CEDULA', 'cedula_docente': '0912345678'}
        self.assertEqual(form.clean_cedula_docente(), '0912345678')

        form.cleaned_data = {'tipo_documento': 'RUC', 'cedula_docente': '0912345678001'}
        self.assertEqual(form.clean_cedula_docente(), '0912345678001')

        form.cleaned_data = {'tipo_documento': 'PASAPORTE', 'cedula_docente': 'ab12345'}
        self.assertEqual(form.clean_cedula_docente(), 'AB12345')

    def test_rejects_invalid_cedula(self):
        form = DocenteFcaccForm()
        form.cleaned_data = {'tipo_documento': 'CEDULA', 'cedula_docente': '1234'}
        with self.assertRaises(ValidationError):
            form.clean_cedula_docente()
