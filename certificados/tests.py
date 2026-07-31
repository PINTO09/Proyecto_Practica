from django.test import SimpleTestCase
from django.urls import reverse

from .models import CertificadoEmitido
from .services import (
    FUNCTION_FILTER_LABELS,
    clean_function_description,
    normalize_function_filter,
)


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

    def test_import_source_is_not_used_as_function_description(self):
        self.assertEqual(
            clean_function_description(
                'Importado desde COOR_CEXT/planificacion.xlsx',
                'Gestión académica',
            ),
            'Gestión académica',
        )
        self.assertEqual(
            clean_function_description(
                'Coordinación de prácticas preprofesionales',
                'Gestión académica',
            ),
            'Coordinación de prácticas preprofesionales',
        )
