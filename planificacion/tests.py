from django.core.exceptions import PermissionDenied, ValidationError
from django.test import RequestFactory, SimpleTestCase
from django.urls import reverse
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from catalogos.models import CatalogoPeriodoAcademico
from core.crud_base import CrudListView
from .forms import (
    PlanificacionActividadDocenteForm, PlanificacionAsignacionDocenteForm,
    PlanificacionAulaHorarioForm, PlanificacionCapacidadEspecialForm,
)
from .management.commands.import_complete_fcacc import _normalize_phone, _valid_email
from .views import (
    PlanificacionCapacidadEspecialListView, _build_parallel_labels,
    reporte_horas_docentes,
)
from .models import PlanificacionAsignacionDocente, PlanificacionCapacidadEspecial
from .services import activity_workload_key, normalize_parallel, periodo_es_editable


def _special_capacity_form_without_database():
    with patch('django.db.models.query.QuerySet.first', return_value=None):
        return PlanificacionCapacidadEspecialForm()


class PlanificacionRulesTests(SimpleTestCase):
    def test_activity_form_does_not_request_a_career(self):
        self.assertNotIn('id_carrera', PlanificacionActividadDocenteForm().fields)

    def test_planning_forms_follow_the_workflow_order(self):
        assignment_fields = list(PlanificacionAsignacionDocenteForm().fields)
        self.assertLess(
            assignment_fields.index('nivel_semestre_asignado'),
            assignment_fields.index('id_asignatura'),
        )
        self.assertEqual(
            list(PlanificacionActividadDocenteForm().fields)[:3],
            ['id_periodo', 'id_docente', 'id_actividad'],
        )
        self.assertEqual(
            list(PlanificacionAulaHorarioForm().fields)[:5],
            ['id_periodo', 'id_asignacion', 'dia_semana', 'hora_inicio', 'hora_fin'],
        )

    def test_assignment_id_is_automatic_and_field_is_textual(self):
        form = PlanificacionAsignacionDocenteForm()
        self.assertNotIn('id_asignacion', form.fields)
        self.assertTrue(form.fields['campo_conocimiento'].widget.attrs.get('readonly'))
        self.assertEqual(
            form.fields['id_campo'].widget.input_type,
            'hidden',
        )

    def test_assignment_allows_optional_affinity_only_before_level_four(self):
        form = PlanificacionAsignacionDocenteForm()
        self.assertIn('requiere_afinidad', form.fields)
        self.assertEqual(
            [value for value, _ in form.fields['requiere_afinidad'].choices],
            ['AUTO', 'SI', 'NO'],
        )

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
        first = activity_workload_key(1, 2, 'AD4 Preparación de Clases', 3)
        second = activity_workload_key(1, 2, 'ad4 preparacion de clases', 3)
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

    def test_special_capacity_form_follows_workflow_order(self):
        self.assertEqual(
            list(_special_capacity_form_without_database().fields),
            [
                'id_periodo', 'id_carrera', 'estudiante_nombre', 'condicion',
                'nivel_asignado', 'paralelo_asignado', 'informes_adjuntos',
            ],
        )

    def test_special_capacity_form_normalizes_parallel(self):
        form = _special_capacity_form_without_database()
        form.cleaned_data = {'paralelo_asignado': ' b '}
        self.assertEqual(form.clean_paralelo_asignado(), 'B')


class PlanificacionCapacidadEspecialUnitTests(SimpleTestCase):
    def test_sensitive_list_requires_change_permission(self):
        self.assertEqual(
            PlanificacionCapacidadEspecialListView.access_action,
            'change',
        )

    def test_list_searches_relevant_fields(self):
        self.assertIn(
            'estudiante_nombre',
            PlanificacionCapacidadEspecialListView.search_fields,
        )
        self.assertIn(
            'condicion',
            PlanificacionCapacidadEspecialListView.search_fields,
        )
        self.assertIn(
            'id_carrera__nombre_carrera',
            PlanificacionCapacidadEspecialListView.search_fields,
        )

    def test_invalid_parallel_is_rejected(self):
        form = _special_capacity_form_without_database()
        form.cleaned_data = {'paralelo_asignado': '2A'}
        with self.assertRaises(ValidationError):
            form.clean_paralelo_asignado()

    def test_student_name_collapses_extra_spaces(self):
        form = _special_capacity_form_without_database()
        form.cleaned_data = {'estudiante_nombre': '  Ana   Pérez  '}
        self.assertEqual(form.clean_estudiante_nombre(), 'Ana Pérez')

    def test_level_selector_offers_ten_levels(self):
        choices = list(
            _special_capacity_form_without_database().fields[
                'nivel_asignado'
            ].widget.choices
        )
        self.assertEqual(choices[0], ('', 'Sin especificar'))
        self.assertEqual(choices[-1], ('10', 'Nivel 10'))

    def test_form_explains_minimal_sensitive_data(self):
        help_text = _special_capacity_form_without_database().fields[
            'condicion'
        ].help_text
        self.assertIn('únicamente', help_text)

    def test_all_crud_routes_are_registered(self):
        self.assertEqual(
            reverse('planificacion:planificacioncapacidadespecial_list'),
            '/planificacion/capacidades-especiales/',
        )
        self.assertEqual(
            reverse('planificacion:planificacioncapacidadespecial_create'),
            '/planificacion/capacidades-especiales/crear/',
        )
        self.assertIn(
            '/editar/',
            reverse(
                'planificacion:planificacioncapacidadespecial_update',
                kwargs={'pk': 7},
            ),
        )
        self.assertIn(
            '/eliminar/',
            reverse(
                'planificacion:planificacioncapacidadespecial_delete',
                kwargs={'pk': 7},
            ),
        )

    @patch('planificacion.views._ensure_career_access', return_value={4})
    @patch.object(CrudListView, 'get_queryset')
    def test_list_scopes_coordinator_careers(self, get_base_queryset, _ensure):
        queryset = MagicMock()
        queryset.select_related.return_value = queryset
        queryset.filter.return_value = queryset
        queryset.order_by.return_value = queryset
        get_base_queryset.return_value = queryset
        view = PlanificacionCapacidadEspecialListView()
        view.request = RequestFactory().get('/capacidades-especiales/')

        self.assertIs(view.get_queryset(), queryset)
        queryset.filter.assert_called_with(id_carrera_id__in={4})

    @patch(
        'planificacion.views._ensure_career_access',
        side_effect=PermissionDenied,
    )
    @patch.object(CrudListView, 'get_queryset')
    def test_unauthorized_career_filter_is_rejected(
        self, get_base_queryset, _ensure
    ):
        queryset = MagicMock()
        queryset.select_related.return_value = queryset
        get_base_queryset.return_value = queryset
        view = PlanificacionCapacidadEspecialListView()
        view.request = RequestFactory().get(
            '/capacidades-especiales/', {'carrera': '99'}
        )
        with self.assertRaises(PermissionDenied):
            view.get_queryset()

    @patch('planificacion.models.PlanificacionCapacidadEspecial.objects')
    def test_model_rejects_duplicate_in_same_slot(self, manager):
        duplicate = manager.filter.return_value
        duplicate.exists.return_value = True
        periodo = CatalogoPeriodoAcademico(
            id_periodo=2,
            estado_planificacion='BORRADOR',
        )
        record = PlanificacionCapacidadEspecial(
            id_capacidad=9,
            id_periodo=periodo,
            id_carrera_id=3,
            estudiante_nombre='Estudiante Duplicado',
            nivel_asignado='2',
            paralelo_asignado='a',
        )
        duplicate.exclude.return_value = duplicate
        with self.assertRaises(ValidationError):
            record.clean()

    def test_closed_period_is_not_editable(self):
        periodo = CatalogoPeriodoAcademico(
            id_periodo=2,
            estado_planificacion='CERRADO',
        )
        record = PlanificacionCapacidadEspecial(
            id_periodo=periodo,
            estudiante_nombre='Estudiante',
        )
        with self.assertRaises(ValidationError):
            record.clean()
