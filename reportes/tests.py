from unittest.mock import MagicMock, call, patch, sentinel
from pathlib import Path

from django.test import RequestFactory, SimpleTestCase
from django.urls import reverse
from openpyxl import load_workbook

from .views import (
    F4_TEMPLATE_PATH,
    _export_filters,
    _filter_teacher_activity_scope,
    export_resumen_horas_excel,
)


class ExportFilterTests(SimpleTestCase):
    def test_accepts_numeric_filters(self):
        request = RequestFactory().get('/', {'periodo': '12', 'carrera': '4'})
        self.assertEqual(_export_filters(request), ('12', '4'))

    def test_ignores_invalid_filters(self):
        request = RequestFactory().get('/', {'periodo': 'x', 'carrera': '-1'})
        self.assertEqual(_export_filters(request), (None, None))

    def test_report_center_has_a_dedicated_route(self):
        self.assertEqual(reverse('reportes:centro_reportes'), '/reportes/')

    @patch('reportes.views.export_planificacion_general_excel')
    def test_legacy_hours_export_uses_canonical_general_report(self, general_export):
        general_export.return_value = sentinel.response
        request = RequestFactory().get('/', {'periodo': '12'})

        result = export_resumen_horas_excel.__wrapped__(request)

        self.assertIs(result, sentinel.response)
        general_export.assert_called_once_with(request)


class ActivityExportScopeTests(SimpleTestCase):
    def test_filters_activities_by_period_and_scoped_teachers(self):
        queryset = MagicMock()
        period_queryset = MagicMock()
        final_queryset = MagicMock()
        queryset.filter.return_value = period_queryset
        period_queryset.filter.return_value = final_queryset

        result = _filter_teacher_activity_scope(
            queryset, periodo_id='2', teacher_ids={4, 9}
        )

        self.assertIs(result, final_queryset)
        queryset.filter.assert_called_once_with(id_periodo_id='2')
        period_queryset.filter.assert_called_once_with(
            id_docente_id__in={4, 9}
        )

    def test_does_not_filter_activities_by_pseudo_career(self):
        queryset = MagicMock()
        queryset.filter.return_value = queryset

        _filter_teacher_activity_scope(
            queryset, periodo_id='2', teacher_ids={4}
        )

        self.assertEqual(
            queryset.filter.call_args_list,
            [
                call(id_periodo_id='2'),
                call(id_docente_id__in={4}),
            ],
        )
        for recorded_call in queryset.filter.call_args_list:
            self.assertNotIn('id_carrera_id', recorded_call.kwargs)


class InstitutionalF4TemplateTests(SimpleTestCase):
    def test_official_template_is_packaged_with_required_sheet_and_logos(self):
        self.assertTrue(Path(F4_TEMPLATE_PATH).is_file())
        workbook = load_workbook(F4_TEMPLATE_PATH)
        self.assertIn('MATRIZ F4 V1', workbook.sheetnames)
        worksheet = workbook['MATRIZ F4 V1']
        self.assertGreaterEqual(len(worksheet._images), 1)
        self.assertTrue(any(
            cell.data_type == 'f'
            for row in worksheet.iter_rows()
            for cell in row
        ))
