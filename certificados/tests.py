from django.test import SimpleTestCase
from django.urls import reverse

from .models import CertificadoEmitido
from .services import FUNCTION_FILTER_LABELS, normalize_function_filter


class CertificateModuleTests(SimpleTestCase):
    def test_certificate_routes_are_available(self):
        self.assertEqual(reverse('certificados:generar'), '/certificados/')
        self.assertEqual(reverse('certificados:emisiones'), '/certificados/emitidos/')
        self.assertEqual(reverse('certificados:firmantes'), '/certificados/firmantes/')
        self.assertEqual(
            reverse('certificados:reporte_base', kwargs={'tipo': 'catedras'}),
            '/certificados/reportes/catedras/',
        )

    def test_supported_certificate_types_match_official_samples(self):
        self.assertEqual(
            {key for key, _ in CertificadoEmitido.TIPOS},
            {'DEDICACION', 'CATEDRAS', 'FUNCIONES'},
        )

    def test_function_certificate_supports_requested_filters(self):
        self.assertEqual(
            set(FUNCTION_FILTER_LABELS),
            {'TODOS', 'ACTIVIDADES', 'ASIGNACIONES', 'COMISIONES'},
        )
        self.assertEqual(normalize_function_filter('comisiones'), 'COMISIONES')
        self.assertEqual(normalize_function_filter('desconocido'), 'TODOS')
