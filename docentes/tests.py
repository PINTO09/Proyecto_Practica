from django.core.exceptions import ValidationError
from django.test import SimpleTestCase
from datetime import date

from .forms import DocenteFcaccForm
from .services import (
    classify_postgraduate_title, humanize_duration, inclusive_days,
    merge_date_ranges, unique_postgraduate_titles,
)


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


class TeacherHistoryDurationTests(SimpleTestCase):
    def test_merges_overlapping_periods_to_avoid_double_counting(self):
        ranges = [
            (date(2025, 1, 1), date(2025, 1, 31)),
            (date(2025, 1, 1), date(2025, 1, 31)),
            (date(2025, 1, 20), date(2025, 2, 10)),
        ]
        self.assertEqual(
            merge_date_ranges(ranges),
            [(date(2025, 1, 1), date(2025, 2, 10))],
        )
        self.assertEqual(inclusive_days(ranges), 41)

    def test_merges_consecutive_periods_but_not_separated_periods(self):
        ranges = [
            (date(2025, 1, 1), date(2025, 1, 10)),
            (date(2025, 1, 11), date(2025, 1, 20)),
            (date(2025, 2, 1), date(2025, 2, 5)),
        ]
        self.assertEqual(len(merge_date_ranges(ranges)), 2)
        self.assertEqual(inclusive_days(ranges), 25)

    def test_duration_label_keeps_exact_days_available(self):
        self.assertEqual(humanize_duration(395), '1 año, 1 mes')


class PostgraduateClassificationTests(SimpleTestCase):
    class Title:
        def __init__(self, name, level=4):
            self.nombre_titulo = name
            self.nivel_titulo = level
            self.id_posgrado_id = None
            self.id_posgrado = None

    def test_classifies_common_postgraduate_degrees(self):
        self.assertEqual(
            classify_postgraduate_title(self.Title('Maestría en Educación')),
            'masters',
        )
        self.assertEqual(
            classify_postgraduate_title(self.Title('Doctorado PhD en Administración')),
            'doctorates',
        )
        self.assertEqual(
            classify_postgraduate_title(self.Title('Especialización en Tributación')),
            'specializations',
        )

    def test_does_not_count_third_level_title_as_postgraduate(self):
        self.assertIsNone(
            classify_postgraduate_title(self.Title('Ingeniería Comercial', level=3))
        )

    def test_deduplicates_same_title_for_one_teacher(self):
        titles = [
            self.Title('Maestría en Educación'),
            self.Title('MAESTRIA EN EDUCACION'),
        ]
        self.assertEqual(len(unique_postgraduate_titles(titles)), 1)
