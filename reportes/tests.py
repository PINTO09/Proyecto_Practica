from unittest.mock import MagicMock, call, patch, sentinel
from pathlib import Path

from django.test import RequestFactory, SimpleTestCase
from django.urls import reverse
from openpyxl import Workbook, load_workbook

from .views import (
    F4_TEMPLATE_PATH,
    THIN_BORDER,
    _export_filters,
    _filter_teacher_activity_scope,
    _format_f4_identity_block,
    _merge_f4_teacher_cells,
    export_resumen_horas_excel,
)
from planificacion.services import effective_f4_career_filter


class ExportFilterTests(SimpleTestCase):
    def test_accepts_numeric_filters(self):
        request = RequestFactory().get('/', {'periodo': '12', 'carrera': '4'})
        self.assertEqual(_export_filters(request), ('12', '4'))

    def test_ignores_invalid_filters(self):
        request = RequestFactory().get('/', {'periodo': 'x', 'carrera': '-1'})
        self.assertEqual(_export_filters(request), (None, None))

    def test_specific_teacher_overrides_a_stale_career_filter(self):
        self.assertIsNone(effective_f4_career_filter('4', '1040'))

    def test_career_filter_remains_for_general_queries(self):
        self.assertEqual(effective_f4_career_filter('4', None), '4')

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


class F4TeacherGroupingTests(SimpleTestCase):
    def test_identification_is_shown_once_for_multiple_teacher_rows(self):
        worksheet = Workbook().active
        for row in range(8, 11):
            worksheet.cell(row, 2, '1300000000')
            worksheet.cell(row, 3, 'DOCENTE DE PRUEBA')

        _merge_f4_teacher_cells(worksheet, 8, 10)

        merged = {str(item) for item in worksheet.merged_cells.ranges}
        self.assertIn('A8:A10', merged)
        self.assertNotIn('B8:B10', merged)
        self.assertNotIn('C8:C10', merged)

    def test_identity_block_looks_merged_but_keeps_every_value_filterable(self):
        worksheet = Workbook().active
        for row in range(8, 11):
            worksheet.cell(row, 2, '1300000000')
            worksheet.cell(row, 3, 'DOCENTE DE PRUEBA')
            worksheet.cell(row, 2).border = THIN_BORDER
            worksheet.cell(row, 3).border = THIN_BORDER

        _format_f4_identity_block(worksheet, 8, 10)

        self.assertEqual(
            [worksheet.cell(row, 2).value for row in range(8, 11)],
            ['1300000000'] * 3,
        )
        self.assertEqual(
            [worksheet.cell(row, 3).value for row in range(8, 11)],
            ['DOCENTE DE PRUEBA'] * 3,
        )
        self.assertEqual(worksheet['B8'].number_format, ';;;')
        self.assertNotEqual(worksheet['B9'].number_format, ';;;')
        self.assertEqual(worksheet['B10'].number_format, ';;;')
        self.assertIsNone(worksheet['B9'].border.top.style)
        self.assertIsNone(worksheet['B9'].border.bottom.style)

    def test_single_teacher_row_is_not_merged(self):
        worksheet = Workbook().active

        _merge_f4_teacher_cells(worksheet, 8, 8)

        self.assertFalse(worksheet.merged_cells.ranges)


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
