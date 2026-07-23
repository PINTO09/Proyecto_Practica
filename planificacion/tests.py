from django.core.exceptions import ValidationError
from django.test import RequestFactory, SimpleTestCase
from types import SimpleNamespace

from .forms import PlanificacionActividadDocenteForm, PlanificacionAsignacionDocenteForm
from .management.commands.import_complete_fcacc import _normalize_phone, _valid_email
from .views import _activity_workload_key, _build_parallel_labels, reporte_horas_docentes
from .models import PlanificacionAsignacionDocente
from .services import normalize_parallel, periodo_es_editable


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

    def test_activity_keys_normalize_names_for_deduplication(self):
        first = _activity_workload_key(1, 2, 'AD4 Preparación de Clases', 3)
        second = _activity_workload_key(1, 2, 'ad4 preparacion de clases', 3)
        self.assertEqual(first, second)

    def test_old_hours_report_redirects_to_consolidated_view(self):
        request = RequestFactory().get('/', {'periodo': '6', 'carrera': '3'})
        response = reporte_horas_docentes.__wrapped__(request)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/planificacion/consolidado-docentes/', response['Location'])
        self.assertIn('periodo=6', response['Location'])

    def test_normalize_parallel_for_all_entry_points(self):
        self.assertEqual(normalize_parallel('  ab  '), 'AB')

    def test_draft_and_review_periods_are_editable(self):
        self.assertTrue(periodo_es_editable(SimpleNamespace(estado_planificacion='BORRADOR')))
        self.assertTrue(periodo_es_editable(SimpleNamespace(estado_planificacion='EN_REVISION')))

    def test_approved_and_closed_periods_are_locked(self):
        self.assertFalse(periodo_es_editable(SimpleNamespace(estado_planificacion='APROBADO')))
        self.assertFalse(periodo_es_editable(SimpleNamespace(estado_planificacion='CERRADO')))

    def test_period_class_hours_are_traceable(self):
        assignment = SimpleNamespace(horas_clase=6, semanas_planificadas=16)
        self.assertEqual(
            PlanificacionAsignacionDocente.horas_clase_periodo.fget(assignment),
            96,
        )
