from django.test import SimpleTestCase
from django.core.exceptions import ValidationError
from unittest.mock import patch

from .forms import CurriculoAsignaturaForm


class CurriculoAsignaturaFormTests(SimpleTestCase):
    def test_subject_form_includes_knowledge_fields(self):
        form = CurriculoAsignaturaForm()
        self.assertIn('campos_conocimiento', form.fields)
        self.assertFalse(form.fields['campos_conocimiento'].required)

    def test_form_includes_space_distribution(self):
        form = CurriculoAsignaturaForm()
        self.assertIn('horas_aula', form.fields)
        self.assertIn('horas_centro_computo', form.fields)

    def test_space_distribution_must_total_one_hundred(self):
        form = CurriculoAsignaturaForm()
        cleaned = {
            'es_actividad': False,
            'modalidad_espacio': 'AULA_CENTRO',
            'horas_semanales_asignatura': 5,
            'horas_aula': 3,
            'horas_centro_computo': 1,
            'campos_conocimiento': [object()],
        }
        with patch(
            'django.forms.models.BaseModelForm.clean',
            return_value=cleaned,
        ):
            with self.assertRaisesMessage(
                ValidationError,
                'Para usar aula y centro de cómputo, ambas cantidades '
                'deben ser mayores que 0 y sumar las horas semanales.',
            ):
                form.clean()

    def test_only_classroom_forces_full_classroom_distribution(self):
        form = CurriculoAsignaturaForm()
        cleaned = {
            'es_actividad': False,
            'modalidad_espacio': 'SOLO_AULA',
            'horas_semanales_asignatura': 5,
            'horas_aula': 2,
            'horas_centro_computo': 3,
            'campos_conocimiento': [object()],
        }
        with patch(
            'django.forms.models.BaseModelForm.clean',
            return_value=cleaned,
        ):
            result = form.clean()
        self.assertEqual(result['horas_aula'], 5)
        self.assertEqual(result['horas_centro_computo'], 0)

    def test_only_computer_center_forces_full_laboratory_distribution(self):
        form = CurriculoAsignaturaForm()
        cleaned = {
            'es_actividad': False,
            'modalidad_espacio': 'SOLO_CENTRO',
            'horas_semanales_asignatura': 6,
            'horas_aula': 4,
            'horas_centro_computo': 2,
            'campos_conocimiento': [object()],
        }
        with patch(
            'django.forms.models.BaseModelForm.clean',
            return_value=cleaned,
        ):
            result = form.clean()
        self.assertEqual(result['horas_aula'], 0)
        self.assertEqual(result['horas_centro_computo'], 6)

    def test_weekly_hours_follow_distribution(self):
        subject = CurriculoAsignaturaForm._meta.model(
            horas_semanales_asignatura=5,
            horas_aula=3,
            horas_centro_computo=2,
        )
        self.assertEqual(subject.porcentaje_aula, 60)
        self.assertEqual(subject.porcentaje_centro_computo, 40)
