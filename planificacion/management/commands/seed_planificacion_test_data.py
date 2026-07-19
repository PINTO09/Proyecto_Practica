from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from catalogos.models import (
    CatalogoPeriodoAcademico, CatalogoCarrera, CatalogoCampoConocimiento,
    CatalogoDedicacionHoraria, CatalogoModalidadContratacion, LimiteHorario,
    CatalogoTipoDocente,
)
from curriculo.models import CurriculoAsignatura, CurriculoAsignaturaCampo
from docentes.models import DocenteFcacc, DocenteCampoAfinidad
from planificacion.models import (
    PlanificacionDemandaAcademica, PlanificacionAsignacionDocente,
    PlanificacionActividadDocente, PlanificacionMatrizF4,
    CatalogoActividadComplementaria,
)


def _get_or_none(model, **kwargs):
    try:
        return model.objects.get(**kwargs)
    except model.DoesNotExist:
        return None


class Command(BaseCommand):
    help = 'Siembra datos de prueba para la sección de planificación (demandas, asignaciones, paralelos).'

    def handle(self, *args, **options):
        self.stdout.write('Sembrando datos de prueba para planificación...')

        # ——— 1. Periodo activo ———
        periodo, created = CatalogoPeriodoAcademico.objects.get_or_create(
            periodo_activo=True,
            defaults={
                'nombre_periodo': 'Periodo 2026-2027',
                'fecha_inicio_periodo': timezone.now().date(),
                'fecha_fin_periodo': timezone.now().date() + timezone.timedelta(days=365),
            },
        )
        if created:
            self.stdout.write(f'  + Periodo creado: {periodo.nombre_periodo}')
        else:
            self.stdout.write(f'  ~ Periodo existente: {periodo.nombre_periodo}')

        # ——— 2. Carreras ———
        carrera_contabilidad, _ = CatalogoCarrera.objects.get_or_create(
            codigo_carrera='CONT-01', defaults={
                'nombre_carrera': 'Contabilidad y Auditoría',
                'carrera_activa': True,
            }
        )
        carrera_administracion, _ = CatalogoCarrera.objects.get_or_create(
            codigo_carrera='ADM-01', defaults={
                'nombre_carrera': 'Administración de Empresas',
                'carrera_activa': True,
            }
        )
        carreras = [carrera_contabilidad, carrera_administracion]
        for c in carreras:
            self.stdout.write(f'  + Carrera: {c.nombre_carrera}')

        # ——— 3. Modalidad y dedicación ———
        modalidad_tc, _ = CatalogoModalidadContratacion.objects.get_or_create(
            codigo_modalidad='TC',
            defaults={'nombre_modalidad': 'Tiempo Completo'},
        )
        modalidad_mt, _ = CatalogoModalidadContratacion.objects.get_or_create(
            codigo_modalidad='MT',
            defaults={'nombre_modalidad': 'Medio Tiempo'},
        )
        dedicacion_tc, _ = CatalogoDedicacionHoraria.objects.get_or_create(
            codigo_dedicacion='TC',
            defaults={'nombre_dedicacion': 'Tiempo Completo'},
        )

        # ——— 4. Límites horarios ———
        for modalidad, h_max, h_comp in [
            (modalidad_tc, 40, 20),
            (modalidad_mt, 20, 10),
        ]:
            obj, created = LimiteHorario.objects.get_or_create(
                id_modalidad=modalidad,
                defaults={
                    'horas_maximas': h_max,
                    'horas_complementarias_maximas': h_comp,
                    'activo': True,
                },
            )
            if not created and obj.activo:
                obj.horas_maximas = h_max
                obj.horas_complementarias_maximas = h_comp
                obj.save()

        # ——— 5. Campos de conocimiento ———
        campo_contabilidad, _ = CatalogoCampoConocimiento.objects.get_or_create(
            codigo_campo='CONT',
            defaults={'nombre_campo_conocimiento': 'Contabilidad'},
        )
        campo_auditoria, _ = CatalogoCampoConocimiento.objects.get_or_create(
            codigo_campo='AUDI',
            defaults={'nombre_campo_conocimiento': 'Auditoría'},
        )
        campo_admin, _ = CatalogoCampoConocimiento.objects.get_or_create(
            codigo_campo='ADMIN',
            defaults={'nombre_campo_conocimiento': 'Administración'},
        )
        campo_finanzas, _ = CatalogoCampoConocimiento.objects.get_or_create(
            codigo_campo='FIN',
            defaults={'nombre_campo_conocimiento': 'Finanzas'},
        )

        # ——— 6. Asignaturas ———
        subjects_data = [
            {'codigo': 'CONT-101', 'nombre': 'Contabilidad Básica', 'nivel': 1, 'carrera': carrera_contabilidad, 'horas': 4, 'campo': campo_contabilidad},
            {'codigo': 'CONT-201', 'nombre': 'Contabilidad Intermedia', 'nivel': 3, 'carrera': carrera_contabilidad, 'horas': 5, 'campo': campo_contabilidad},
            {'codigo': 'CONT-301', 'nombre': 'Contabilidad Avanzada', 'nivel': 5, 'carrera': carrera_contabilidad, 'horas': 5, 'campo': campo_contabilidad},
            {'codigo': 'CONT-401', 'nombre': 'Auditoría Financiera', 'nivel': 7, 'carrera': carrera_contabilidad, 'horas': 4, 'campo': campo_auditoria},
            {'codigo': 'CONT-501', 'nombre': 'Matemática Financiera', 'nivel': 2, 'carrera': carrera_contabilidad, 'horas': 3, 'campo': campo_finanzas},
            {'codigo': 'CONT-601', 'nombre': 'Legislación Tributaria', 'nivel': 6, 'carrera': carrera_contabilidad, 'horas': 3, 'campo': campo_auditoria},
            {'codigo': 'ADM-101', 'nombre': 'Introducción a la Administración', 'nivel': 1, 'carrera': carrera_administracion, 'horas': 4, 'campo': campo_admin},
            {'codigo': 'ADM-201', 'nombre': 'Gestión Empresarial', 'nivel': 3, 'carrera': carrera_administracion, 'horas': 5, 'campo': campo_admin},
            {'codigo': 'ADM-301', 'nombre': 'Planificación Estratégica', 'nivel': 5, 'carrera': carrera_administracion, 'horas': 4, 'campo': campo_admin},
            {'codigo': 'ADM-401', 'nombre': 'Finanzas Corporativas', 'nivel': 7, 'carrera': carrera_administracion, 'horas': 5, 'campo': campo_finanzas},
        ]
        subjects = []
        for sd in subjects_data:
            subj, created = CurriculoAsignatura.objects.get_or_create(
                codigo_asignatura=sd['codigo'],
                defaults={
                    'nombre_asignatura': sd['nombre'],
                    'nivel_semestre': sd['nivel'],
                    'id_carrera': sd['carrera'],
                    'horas_semanales_asignatura': sd['horas'],
                    'es_actividad': False,
                },
            )
            subjects.append(subj)
            # Campo
            CurriculoAsignaturaCampo.objects.get_or_create(
                id_asignatura=subj, id_campo=sd['campo'],
            )
            if created:
                self.stdout.write(f'  + Asignatura: {subj.codigo_asignatura} - {subj.nombre_asignatura}')

        # ——— 7. Tipo docente ———
        tipo_profesor, _ = CatalogoTipoDocente.objects.get_or_create(
            codigo_tipo_docente='PROF',
            defaults={'nombre_tipo_docente': 'Profesor'},
        )

        # ——— 8. Docentes ———
        teachers_data = [
            {'cedula': '1000000001', 'nombres': 'Dr. Carlos Martínez', 'modalidad': modalidad_tc, 'dedicacion': dedicacion_tc},
            {'cedula': '1000000002', 'nombres': 'MSc. Ana López', 'modalidad': modalidad_tc, 'dedicacion': dedicacion_tc},
            {'cedula': '1000000003', 'nombres': 'Ing. Pedro Sánchez', 'modalidad': modalidad_mt, 'dedicacion': dedicacion_tc},
            {'cedula': '1000000004', 'nombres': 'PhD. María García', 'modalidad': modalidad_tc, 'dedicacion': dedicacion_tc},
            {'cedula': '1000000005', 'nombres': 'Econ. Luis Ramírez', 'modalidad': modalidad_mt, 'dedicacion': dedicacion_tc},
        ]
        teachers = []
        for td in teachers_data:
            t, created = DocenteFcacc.objects.get_or_create(
                cedula_docente=td['cedula'],
                defaults={
                    'nombres_completos': td['nombres'],
                    'docente_activo': True,
                    'id_modalidad': td['modalidad'],
                    'id_tipo_docente': tipo_profesor,
                    'id_dedicacion': td['dedicacion'],
                    'tipo_documento': 'CEDULA',
                },
            )
            teachers.append(t)
            if created:
                self.stdout.write(f'  + Docente: {t.nombres_completos}')

        # Asignar afinidades
        afinidades = [
            (teachers[0], campo_contabilidad),
            (teachers[0], campo_auditoria),
            (teachers[1], campo_contabilidad),
            (teachers[2], campo_admin),
            (teachers[3], campo_auditoria),
            (teachers[3], campo_finanzas),
            (teachers[4], campo_admin),
            (teachers[4], campo_finanzas),
        ]
        for t, c in afinidades:
            DocenteCampoAfinidad.objects.get_or_create(id_docente=t, id_campo=c)

        # ——— 8. Demandas académicas ———
        demandas_data = [
            (subjects[0], carrera_contabilidad, 2),  # Cont Básica → 2 paralelos
            (subjects[1], carrera_contabilidad, 1),  # Cont Intermedia → 1 paralelo
            (subjects[2], carrera_contabilidad, 2),  # Cont Avanzada → 2 paralelos
            (subjects[3], carrera_contabilidad, 1),  # Auditoría → 1 paralelo
            (subjects[4], carrera_contabilidad, 2),  # Mat Financiera → 2 paralelos
            (subjects[5], carrera_contabilidad, 2),  # Legislación → 2 paralelos
            (subjects[6], carrera_administracion, 1),  # Intro Admin → 1 paralelo
            (subjects[7], carrera_administracion, 2),  # Gestión → 2 paralelos
            (subjects[8], carrera_administracion, 1),  # Planif Estrat → 1 paralelo
            (subjects[9], carrera_administracion, 2),  # Finanzas Corp → 2 paralelos
        ]
        for s, carrera, num_par in demandas_data:
            PlanificacionDemandaAcademica.objects.get_or_create(
                id_asignatura=s,
                id_carrera=carrera,
                id_periodo=periodo,
                defaults={
                    'numero_paralelos': num_par,
                    'proyeccion_estudiantes': num_par * 30,
                },
            )

        self.stdout.write(f'  + {len(demandas_data)} demandas creadas')

        # ——— 9. Asignaciones docentes ———
        from planificacion.forms import docente_tiene_afinidad, _parallel_labels
        import random

        def _assign_teacher(subject, paralelo_label, carrera, teacher):
            if subject.nivel_semestre >= 4 and not docente_tiene_afinidad(teacher, subject):
                return False
            if PlanificacionAsignacionDocente.objects.filter(
                id_asignatura=subject,
                id_carrera=carrera,
                id_periodo=periodo,
                paralelo_asignado=paralelo_label,
            ).exists():
                return False
            PlanificacionAsignacionDocente.objects.create(
                id_docente=teacher,
                id_asignatura=subject,
                id_carrera=carrera,
                id_periodo=periodo,
                id_campo=CurriculoAsignaturaCampo.objects.filter(id_asignatura=subject).first().id_campo,
                nivel_semestre_asignado=subject.nivel_semestre,
                paralelo_asignado=paralelo_label,
                horas_clase=subject.horas_semanales_asignatura,
                horas_complementarias=0,
            )
            return True

        assigned_count = 0
        for s, carrera, num_par in demandas_data:
            labels = _parallel_labels(num_par)
            for label in labels:
                eligible = [t for t in teachers if docente_tiene_afinidad(t, s) or s.nivel_semestre < 4]
                if eligible:
                    teacher = random.choice(eligible)
                    if _assign_teacher(s, label, carrera, teacher):
                        assigned_count += 1

        self.stdout.write(f'  + {assigned_count} asignaciones creadas')

        # ——— 10. Actividad complementaria (catálogo) ———
        CatalogoActividadComplementaria.objects.get_or_create(
            codigo_actividad='TUT-01',
            defaults={
                'nombre_actividad': 'Tutorías Académicas',
                'tipo_actividad': 'DOCENCIA',
                'actividad_activa': True,
            },
        )

        self.stdout.write(self.style.SUCCESS('\n[OK] Datos de prueba sembrados correctamente.'))
        self.stdout.write(f'   - {len(subjects)} asignaturas')
        self.stdout.write(f'   - {len(teachers)} docentes')
        self.stdout.write(f'   - {len(demandas_data)} demandas')
        self.stdout.write(f'   - {assigned_count} asignaciones')
