from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from .forms import PlanificacionActividadDocenteForm, PlanificacionAsignacionDocenteForm
from .management.commands.import_complete_fcacc import _normalize_phone, _valid_email
from .views import _build_parallel_labels


class PlanificacionRulesTests(SimpleTestCase):
    def test_activity_form_does_not_request_a_career(self):
        self.assertNotIn('id_carrera', PlanificacionActividadDocenteForm().fields)

    def test_builds_parallel_labels(self):
        self.assertEqual(_build_parallel_labels(4), ['A', 'B', 'C', 'D'])
        self.assertEqual(_build_parallel_labels(28)[-2:], ['AA', 'AB'])

    def test_normalizes_parallel(self):
        form = PlanificacionAsignacionDocenteForm()
        form.cleaned_data = {'paralelo_asignado': ' b '}
        self.assertEqual(form.clean_paralelo_asignado(), 'B')

    def test_rejects_numeric_parallel(self):
        form = PlanificacionAsignacionDocenteForm()
        form.cleaned_data = {'paralelo_asignado': '01'}
        with self.assertRaises(ValidationError):
            form.clean_paralelo_asignado()

    def test_normalizes_nine_digit_ecuadorian_phone(self):
        self.assertEqual(_normalize_phone(993841367), '0993841367')

    def test_rejects_incomplete_phone(self):
        self.assertIsNone(_normalize_phone('0'))
        self.assertIsNone(_normalize_phone('95490040'))

    def test_repairs_known_uleam_email_typo(self):
        self.assertEqual(
            _valid_email('avelino.carrillo@uleam.eud.ec'),
            'avelino.carrillo@uleam.edu.ec',
        )
