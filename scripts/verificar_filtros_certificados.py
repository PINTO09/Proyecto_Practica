"""Regresión con ORM real y SQLite en memoria; no accede a la base del proyecto.

Ejecutar: venv/Scripts/python.exe scripts/verificar_filtros_certificados.py
"""
import itertools
from pathlib import Path
import sys
import unittest
from datetime import date

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from django.conf import settings

settings.configure(
    SECRET_KEY='isolated-tests',
    INSTALLED_APPS=[
        'django.contrib.auth', 'django.contrib.contenttypes', 'catalogos',
        'docentes', 'curriculo', 'planificacion', 'certificados',
    ],
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    USE_TZ=True,
)

import django
django.setup()

from django.db import connection, models, transaction
from catalogos.models import CatalogoPeriodoAcademico
from certificados.forms import GenerarCertificadoForm
from certificados.models import FirmanteCertificado
from certificados.services import activity_choices, build_certificate_snapshot, docentes_con_datos
from curriculo.models import CurriculoAsignatura
from docentes.models import DocenteAsignacionCarreraPeriodo, DocenteFcacc
from planificacion.models import CatalogoActividadComplementaria, PlanificacionActividadDocente, PlanificacionAsignacionDocente


counter = itertools.count(1)


def fixture(model, **values):
    """Rellena los catálogos obligatorios de las tablas heredadas."""
    for field in model._meta.concrete_fields:
        if field.name in values or field.attname in values or field.primary_key or field.has_default() or field.null:
            continue
        if isinstance(field, models.ForeignKey):
            values[field.name] = fixture(field.remote_field.model)
        elif isinstance(field, models.BooleanField):
            values[field.name] = True
        elif isinstance(field, (models.IntegerField, models.DecimalField)):
            values[field.name] = 2
        elif isinstance(field, models.DateTimeField):
            continue
        elif isinstance(field, models.DateField):
            values[field.name] = date(2026, 1, 1)
        else:
            values[field.name] = str(next(counter))
    return model.objects.create(**values)


class CertificateSelectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        created = set()

        def create(model, editor):
            if model in created:
                return
            created.add(model)
            for field in model._meta.concrete_fields:
                if isinstance(field, models.ForeignKey):
                    create(field.remote_field.model, editor)
            editor.create_model(model)

        with connection.schema_editor() as editor:
            for model in (PlanificacionActividadDocente, PlanificacionAsignacionDocente,
                          DocenteAsignacionCarreraPeriodo, FirmanteCertificado):
                create(model, editor)

    def setUp(self):
        self.atomic = transaction.atomic()
        self.atomic.__enter__()
        self.addCleanup(self.rollback)
        self.teacher = fixture(DocenteFcacc)
        self.other_teacher = fixture(DocenteFcacc)
        self.period = fixture(CatalogoPeriodoAcademico, nombre_periodo='2026-1')
        self.other_period = fixture(CatalogoPeriodoAcademico, nombre_periodo='2026-2')
        self.activity = fixture(CatalogoActividadComplementaria, nombre_actividad='Tutoría', peso=1)
        self.excluded = fixture(CatalogoActividadComplementaria, nombre_actividad='Clase de docencia', peso=0)
        for period, activity in ((self.period, self.activity), (self.period, self.excluded),
                                 (self.other_period, self.activity)):
            fixture(PlanificacionActividadDocente, id_docente=self.teacher,
                    id_periodo=period, id_actividad=activity, horas_asignadas=2)
        self.subject = fixture(CurriculoAsignatura, nombre_asignatura='Investigación', es_actividad=True)
        self.assignment = fixture(PlanificacionAsignacionDocente, id_docente=self.teacher,
                                  id_periodo=self.period, id_asignatura=self.subject,
                                  comision_servicio='')

    def rollback(self):
        transaction.set_rollback(True)
        self.atomic.__exit__(None, None, None)

    def snapshot(self, **kwargs):
        return build_certificate_snapshot('FUNCIONES', self.teacher, 'ACTIVIDADES', **kwargs)

    def test_default_includes_both_sources_and_excludes_zero(self):
        rows = self.snapshot(periodo=self.period)['filas']
        self.assertEqual({r['descripcion'] for r in rows}, {'Tutoría', 'Investigación'})

    def test_all_periods_and_specific_period(self):
        self.assertEqual(len(self.snapshot()['filas']), 3)
        self.assertEqual(len(self.snapshot(periodo=self.other_period)['filas']), 1)

    def test_selection_limits_both_sources_and_is_saved(self):
        for key, expected in ((f'complementaria:{self.activity.pk}', 'Tutoría'),
                              (f'curricular:{self.subject.pk}', 'Investigación')):
            result = self.snapshot(periodo=self.period, activity_keys=[key])
            self.assertEqual([r['descripcion'] for r in result['filas']], [expected])
            self.assertEqual(result['actividades_seleccionadas'], [key])

    def test_disabled_curricular_activity_disappears_from_choices_and_docentes(self):
        self.subject.importante_certificado = False
        self.subject.save()
        PlanificacionActividadDocente.objects.filter(id_docente=self.teacher).update(id_docente=self.other_teacher)
        self.assertEqual(activity_choices(self.teacher), [])
        self.assertFalse(docentes_con_datos('FUNCIONES', 'ACTIVIDADES').filter(pk=self.teacher.pk).exists())

    def test_curricular_activity_alone_makes_teacher_eligible(self):
        PlanificacionActividadDocente.objects.filter(id_docente=self.teacher).update(id_docente=self.other_teacher)
        self.assertTrue(docentes_con_datos('FUNCIONES', 'ACTIVIDADES', self.period).filter(pk=self.teacher.pk).exists())
        self.assertFalse(docentes_con_datos('FUNCIONES', 'ACTIVIDADES', self.other_period).filter(pk=self.teacher.pk).exists())

    def test_form_rejects_excluded_foreign_and_out_of_period_options(self):
        foreign = fixture(CatalogoActividadComplementaria)
        fixture(PlanificacionActividadDocente, id_docente=self.other_teacher,
                id_periodo=self.period, id_actividad=foreign, horas_asignadas=2)
        signer = fixture(FirmanteCertificado)
        for teacher, period, key in (
            (self.teacher, self.period, f'complementaria:{self.excluded.pk}'),
            (self.teacher, self.period, f'complementaria:{foreign.pk}'),
            (self.teacher, self.other_period, f'curricular:{self.subject.pk}'),
        ):
            form = GenerarCertificadoForm(data={
                'tipo': 'FUNCIONES', 'filtro_funciones': 'ACTIVIDADES',
                'docente': teacher.pk, 'periodo': period.pk, 'firmante': signer.pk,
                'fecha_emision': '2026-09-17', 'ciudad': 'Manta', 'actividades': [key],
            })
            self.assertFalse(form.is_valid())
            self.assertIn('actividades', form.errors)

    def test_valid_form_accepts_multiple_activities_and_all_periods(self):
        signer = fixture(FirmanteCertificado)
        form = GenerarCertificadoForm(data={
            'tipo': 'FUNCIONES', 'filtro_funciones': 'ACTIVIDADES',
            'docente': self.teacher.pk, 'periodo': '', 'firmante': signer.pk,
            'fecha_emision': '2026-09-17', 'ciudad': 'Manta',
            'actividades': [f'complementaria:{self.activity.pk}', f'curricular:{self.subject.pk}'],
        })
        self.assertTrue(form.is_valid(), form.errors)
        self.assertIsNone(form.cleaned_data['periodo'])

    def test_no_duplicate_curricular_activity_in_all_categories(self):
        rows = build_certificate_snapshot('FUNCIONES', self.teacher, periodo=self.period)['filas']
        self.assertEqual(sum(r['descripcion'] == 'Investigación' for r in rows), 1)
        self.assertFalse(any(r['categoria'] == 'ASIGNACIONES' for r in rows))

    def test_subject_valuation_does_not_remove_catedras_or_commissions(self):
        self.subject.es_actividad = False
        self.subject.importante_certificado = False
        self.subject.save()
        self.assignment.comision_servicio = 'Comisión académica'
        self.assignment.save()
        self.assertEqual(build_certificate_snapshot('FUNCIONES', self.teacher, 'ASIGNACIONES')['filas'], [])
        self.assertEqual(len(build_certificate_snapshot('CATEDRAS', self.teacher)['filas']), 1)
        self.assertEqual(len(build_certificate_snapshot('FUNCIONES', self.teacher, 'COMISIONES')['filas']), 1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
