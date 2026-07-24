from django.core.management.base import BaseCommand
from catalogos.models import CatalogoPeriodoAcademico, LimiteHorario
from planificacion.services import build_docente_workload_map
from docentes.models import DocenteFcacc
from planificacion.models import PlanificacionAsignacionDocente
from django.db.models import Sum


class Command(BaseCommand):
    help = 'Debug progress bar calculation: workload, limits, percentages'

    def handle(self, *args, **options):
        # 1. Active period
        active = CatalogoPeriodoAcademico.objects.filter(periodo_activo=True).first()
        if not active:
            self.stdout.write(self.style.ERROR('No active period found'))
            return
        self.stdout.write(f"Active period: {active.nombre_periodo} (id_periodo={active.id_periodo})")

        # 2. Build workload map
        workload_map = build_docente_workload_map(periodo_id=active.id_periodo)
        self.stdout.write(f"\nTeachers with workload data: {len(workload_map)}")
        self.stdout.write("-" * 120)

        # Get all active limit configs
        limites = {l.id_modalidad_id: l for l in LimiteHorario.objects.filter(activo=True).select_related('id_modalidad')}
        self.stdout.write(f"Active LimiteHorario records: {len(limites)}")
        for l in limites.values():
            self.stdout.write(f"  modalidad_id={l.id_modalidad_id}: max_clase={l.horas_maximas}, max_comp={l.horas_complementarias_maximas}")
        self.stdout.write("")

        # 3. For each teacher with workload, print details
        header = f"{'ID':<6} {'Docente':<30} {'Clase':<6} {'Comp':<6} {'Invest':<6} {'Activ':<6} {'Total':<6} {'Modalidad':<12} {'LimClase':<8} {'LimComp':<8} {'MaxTotal':<8} {'%':<6} {'Lim OK?'}"
        self.stdout.write(header)
        self.stdout.write("-" * 120)

        docente_ids = [k for k in workload_map.keys()]
        for docente in DocenteFcacc.objects.filter(id_docente__in=docente_ids, docente_activo=True).order_by('nombres_completos'):
            wl = workload_map.get(docente.id_docente, {})
            limite = limites.get(docente.id_modalidad_id)
            max_total = ((limite.horas_maximas or 0) + (limite.horas_complementarias_maximas or 0)) if limite else 0
            pct = round((wl.get('total_horas', 0) / max_total) * 100, 1) if max_total > 0 else 0
            lim_ok = "YES" if limite else "NO"
            modalidad = str(docente.id_modalidad_id)

            self.stdout.write(
                f"{docente.id_docente:<6} {docente.nombres_completos:<30} "
                f"{wl.get('horas_clase', 0):<6} {wl.get('horas_complementarias', 0):<6} "
                f"{wl.get('horas_investigacion', 0):<6} {wl.get('horas_actividad', 0):<6} "
                f"{wl.get('total_horas', 0):<6} {modalidad:<12} "
                f"{limite.horas_maximas if limite else '-':<8} {limite.horas_complementarias_maximas if limite else '-':<8} "
                f"{max_total:<8} {pct:<6} {lim_ok}"
            )

        # 4. Check PlanificacionAsignacionDocente id_docente_id type
        first_assign = PlanificacionAsignacionDocente.objects.values('id_docente_id').annotate(cnt=Sum('id_asignacion')).order_by('id_docente_id').first()
        if first_assign:
            val = first_assign['id_docente_id']
            self.stdout.write(f"\n--- PlanificacionAsignacionDocente.id_docente_id ---")
            self.stdout.write(f"Sample value: {val!r}, type: {type(val).__name__}")

        # Show a sample DocenteFcacc.id_docente type
        first_doc = DocenteFcacc.objects.first()
        if first_doc:
            self.stdout.write(f"DocenteFcacc.id_docente sample: {first_doc.id_docente!r}, type: {type(first_doc.id_docente).__name__}")

        # Workload map key type
        if workload_map:
            sample_key = list(workload_map.keys())[0]
            self.stdout.write(f"Workload map key sample: {sample_key!r}, type: {type(sample_key).__name__}")

        self.stdout.write(self.style.SUCCESS('\nDone.'))
