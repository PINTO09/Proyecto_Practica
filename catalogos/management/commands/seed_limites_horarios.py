from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from catalogos.models import CatalogoModalidadContratacion, LimiteHorario


DEFAULT_LIMITS = {
    "NOMBRAMIENTO": {"horas_maximas": 20, "horas_complementarias_maximas": 20},
    "CONTRATOS OCASIONALES": {"horas_maximas": 10, "horas_complementarias_maximas": 10},
    "NOMBRAMIENTO PROVISIONAL": {"horas_maximas": 10, "horas_complementarias_maximas": 10},
    "NOMBRAMIENTO AUTORIDAD UNIVERSITARIA": {"horas_maximas": 8, "horas_complementarias_maximas": 0},
}


class Command(BaseCommand):
    help = "Carga limites horarios base por modalidad de contratacion."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Muestra que haria sin guardar cambios.",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Actualiza tambien registros existentes.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        force = options["force"]

        modalidades = {
            obj.nombre_modalidad: obj
            for obj in CatalogoModalidadContratacion.objects.all()
        }

        missing_codes = [code for code in DEFAULT_LIMITS if code not in modalidades]
        if missing_codes:
            raise CommandError(
                "Faltan modalidades requeridas en catalogo_modalidad_contratacion: "
                + ", ".join(missing_codes)
            )

        created_count = 0
        updated_count = 0
        skipped_count = 0

        with transaction.atomic():
            for nombre, values in DEFAULT_LIMITS.items():
                modalidad = modalidades[nombre]
                existing = LimiteHorario.objects.filter(id_modalidad=modalidad).first()

                if existing:
                    if force:
                        existing.horas_maximas = values["horas_maximas"]
                        existing.horas_complementarias_maximas = values["horas_complementarias_maximas"]
                        existing.activo = True
                        existing.save(
                            update_fields=[
                                "horas_maximas",
                                "horas_complementarias_maximas",
                                "activo",
                            ]
                        )
                        updated_count += 1
                        self.stdout.write(
                            f"Actualizado {nombre}: clase={existing.horas_maximas}, comp={existing.horas_complementarias_maximas}"
                        )
                    else:
                        skipped_count += 1
                        self.stdout.write(
                            f"Omitido {nombre}: ya existe (clase={existing.horas_maximas}, comp={existing.horas_complementarias_maximas})"
                        )
                    continue

                LimiteHorario.objects.create(
                    id_modalidad=modalidad,
                    horas_maximas=values["horas_maximas"],
                    horas_complementarias_maximas=values["horas_complementarias_maximas"],
                    activo=True,
                )
                created_count += 1
                self.stdout.write(
                    f"Creado {nombre}: clase={values['horas_maximas']}, comp={values['horas_complementarias_maximas']}"
                )

            if dry_run:
                transaction.set_rollback(True)

        if dry_run:
            self.stdout.write(self.style.WARNING("Dry run completado sin guardar cambios"))
        else:
            self.stdout.write(self.style.SUCCESS("Carga de limites horarios completada"))

        self.stdout.write(
            f"Resumen: creados={created_count}, actualizados={updated_count}, omitidos={skipped_count}"
        )
