from django.test import SimpleTestCase
from django.urls import reverse

from .models import CertificadoEmitido


class CertificateModuleTests(SimpleTestCase):
    def test_certificate_routes_are_available(self):
        self.assertEqual(reverse('certificados:generar'), '/certificados/')
        self.assertEqual(reverse('certificados:emisiones'), '/certificados/emitidos/')
        self.assertEqual(reverse('certificados:firmantes'), '/certificados/firmantes/')

    def test_supported_certificate_types_match_official_samples(self):
        self.assertEqual(
            {key for key, _ in CertificadoEmitido.TIPOS},
            {'DEDICACION', 'CATEDRAS', 'FUNCIONES'},
        )
