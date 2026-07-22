from django.test import RequestFactory, SimpleTestCase

from .views import _export_filters


class ExportFilterTests(SimpleTestCase):
    def test_accepts_numeric_filters(self):
        request = RequestFactory().get('/', {'periodo': '12', 'carrera': '4'})
        self.assertEqual(_export_filters(request), ('12', '4'))

    def test_ignores_invalid_filters(self):
        request = RequestFactory().get('/', {'periodo': 'x', 'carrera': '-1'})
        self.assertEqual(_export_filters(request), (None, None))
