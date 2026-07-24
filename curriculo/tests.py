from django.test import SimpleTestCase

from .forms import CurriculoAsignaturaForm


class CurriculoAsignaturaFormTests(SimpleTestCase):
    def test_subject_form_includes_knowledge_fields(self):
        form = CurriculoAsignaturaForm()
        self.assertIn('campos_conocimiento', form.fields)
        self.assertFalse(form.fields['campos_conocimiento'].required)
