from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from .forms import PlanificacionAsignacionDocenteForm
from .views import _build_parallel_labels


class PlanificacionRulesTests(SimpleTestCase):
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
