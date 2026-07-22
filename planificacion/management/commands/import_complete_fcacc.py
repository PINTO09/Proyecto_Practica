from collections import defaultdict
from datetime import date
import hashlib
from pathlib import Path
import re
import unicodedata

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from openpyxl import load_workbook

from catalogos.models import (
    CatalogoCampoConocimiento,
    CatalogoCarrera,
    CatalogoDedicacionHoraria,
    CatalogoGradoAfinidad,
    CatalogoModalidadContratacion,
    CatalogoPeriodoAcademico,
    CatalogoTipoDocente,
    CatalogoTituloPosgrado,
    CatalogoPais,
)
from curriculo.models import (
    CurriculoAsignatura,
    CurriculoAsignaturaCampo,
    RelacionPosgradoCampo,
)
from docentes.models import (
    DocenteCampoAfinidad,
    DocenteFcacc,
    DocenteTituloAcademico,
)
from planificacion.models import (
    CargaHistorial,
    PlanificacionAsignacionDocente,
    PlanificacionDemandaAcademica,
    PlanificacionMatrizF4,
)


def _normalize_text(value):
    text = str(value or "").replace("\xa0", " ").strip()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"\s+", " ", text)
    return text.upper()


def _clean_text(value):
    return re.sub(r"\s+", " ", str(value or "").replace("\xa0", " ")).strip()


def _fit_code(value, prefix, max_length=20):
    code = _clean_text(value)
    if len(code) <= max_length:
        return code
    digest = hashlib.sha1(code.encode("utf-8")).hexdigest().upper()[: max_length - len(prefix)]
    return f"{prefix}{digest}"


def _sheet_rows(path, sheet_name):
    workbook = load_workbook(path, read_only=True, data_only=True)
    try:
        sheet = workbook[sheet_name]
        rows = list(sheet.iter_rows(values_only=True))
    finally:
        workbook.close()
    return rows


def _valid_level(value):
    try:
        level = int(value or 0)
    except (TypeError, ValueError):
        return None
    return level if 1 <= level <= 8 else None


def _normalize_cedula(value):
    digits = re.sub(r"\D", "", str(value or ""))
    if not digits:
        return None
    if len(digits) > 10:
        digits = digits[:10]
    return digits.zfill(10)


def _normalize_phone(value):
    digits = re.sub(r"\D", "", str(value or ""))
    if not digits:
        return None
    if len(digits) == 9:
        digits = "0" + digits
    return digits[:15]


def _positive_int(value):
    try:
        number = int(float(value or 0))
    except (TypeError, ValueError):
        return 0
    return number if number > 0 else 0


def _valid_email(value):
    email = _clean_text(value)
    if not email or not re.match(r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$', email):
        return None
    return email


def _valid_tipo_sangre(value):
    VALID_BLOOD_TYPES = {"A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"}
    cleaned = _clean_text(value).upper()
    return cleaned if cleaned in VALID_BLOOD_TYPES else None


def _canonical_name(value):
    text = _normalize_text(value)
    text = re.sub(r"^\d+\s+", "", text)
    text = re.sub(r"\s*\([^)]*\)\s*", " ", text)
    text = text.replace(" - ", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


CAREER_ALIASES = {
    "CONTABILIDAD Y ADITORIA 2024": "CONTABILIDAD Y AUDITORIA 2024 NS",
    "CONTABILIDAD Y AUDITORIA": "CONTABILIDAD Y AUDITORIA 2024 NS",
    "AUDITORIA Y CONTROL DE GESTION 2024": "AUDITORIA Y CONTROL DE GESTION 2024 NS",
    "GESTION DE LA INFORMACION GERENCIAL": "GESTION DE LA INFORMACION GERENCIAL 2024 NS",
    "GESTION DE LA INFORMACION GERENCIAL 2024": "GESTION DE LA INFORMACION GERENCIAL 2024 NS",
    "COMERCIO EXTERIOR": "COMERCIO EXTERIOR 2026 NS",
    "COMERCIO EXTERIOR 2026": "COMERCIO EXTERIOR 2026 NS",
    "MARKETING": "MARKETING 2024 NS",
    "ADMINISTRACION DE EMPRESAS": "ADMINISTRACION DE EMPRESAS",
}

FIELD_ALIASES = {
    "ADMINISTRACION": "ADMINISTRACION",
    "COMPUTACION": "CIENCIAS COMPUTACIONALES",
    "CONTABILIDAD": "CONTABILIDAD Y AUDITORIA",
    "DERECHO": "DERECHO",
    "ESTADISTICA": "ECONOMIA MATEMATICA",
    "INFORMATICA": "CIENCIAS COMPUTACIONALES",
    "MATEMATICA": "ECONOMIA MATEMATICA",
    "SOCIALES": "UNIDAD BASICA",
}

F4_ACTIVITY_CAREER_CODES = {
    "FCACC-1-DO-CL",
    "FCACC-4-DO-TU-TI",
    "FCACC-5-DO-PE-IN",
    "FCACC-6-IVN",
    "FCACC-8-VI-SO",
    "FCACC-9-GE_ED",
    "FCACC-8-PRAC",
    "FCACC-8-TITU",
}


def _log_carga(tipo_carga, archivo_origen, total, creados, actualizados, omitidos, errores=None, estado="COMPLETADO"):
    try:
        CargaHistorial.objects.create(
            tipo_carga=tipo_carga,
            archivo_origen=archivo_origen,
            total_registros=total,
            registros_creados=creados,
            registros_actualizados=actualizados,
            registros_omitidos=omitidos,
            detalle_errores=errores,
            estado=estado,
        )
    except Exception:
        pass


class Command(BaseCommand):
    help = "Importacion completa FCACC: 12 pasos desde los 18+ Excel en PLANIFICACION Copiar3"

    def add_arguments(self, parser):
        parser.add_argument(
            "--base-dir",
            default=None,
            help="Directorio base con los archivos Excel (PLANIFICACION Copiar3).",
        )
        parser.add_argument(
            "--periodo-codigo",
            default="2026-2",
            help="Codigo del periodo academico.",
        )
        parser.add_argument(
            "--periodo-nombre",
            default="2026-2",
            help="Nombre del periodo academico.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Analiza y valida sin guardar cambios.",
        )
        parser.add_argument(
            "--sync-asignaciones",
            action="store_true",
            help="Elimina asignaciones del periodo que no aparecen en la carga actual.",
        )
        parser.add_argument(
            "--step",
            type=int,
            default=0,
            help="Ejecutar solo un paso especifico (1-12). 0 = todos.",
        )

    def handle(self, *args, **options):
        base_dir = Path(options["base_dir"] or r"C:\Users\Det-Pc\Documents\Universidad\Semestre 2026(1)\Practicas profesionales\OneDrive_2026-07-22\PLANIFICACION Copiar3")
        dry_run = options["dry_run"]
        sync_assignments = options["sync_asignaciones"]
        only_step = options["step"]

        if not base_dir.exists():
            raise CommandError(f"No se encontro el directorio base: {base_dir}")

        main_book = base_dir / "FCACC-PLANIFICACION.xlsx"
        revision_book = base_dir / "revision" / "REVISIONDocentes.xlsx"
        malla_book = base_dir / "revision" / "MALLA.xlsx"
        nivel_docente_book = base_dir / "NIVEL_DOCENTE.xlsx"
        maestria_book = base_dir / "Maestria.xlsx"
        detallado_book = base_dir / "DETALLADO.xlsx"
        detallado_asig_book = base_dir / "DETALLADO_ASIGNATURA.xlsx"

        for book in [main_book, revision_book, nivel_docente_book, maestria_book]:
            if not book.exists():
                raise CommandError(f"No se encontro: {book}")

        coor_files = []
        coor_dirnames = {
            "COOR_CEXT": "FCACC-PLANIFICACION COM_MAR.xlsx",
            "COOR_CONT": "FCACC-PLANIFICACION CONTABILIDAD.xlsx",
            "COOR_EMPRE": "FCACC-PLANIFICACION EMPRESAS.xlsx",
        }
        for subdir, fname in coor_dirnames.items():
            fp = base_dir / subdir / fname
            if fp.exists():
                coor_files.append((subdir, fp))

        self.stdout.write(f"Leyendo datos desde: {base_dir}")
        self.stdout.write(f"Archivo principal: {main_book.name}")
        self.stdout.write(f"Archivos COOR: {[s for s, _ in coor_files]}")
        self.stdout.write(f"Periodo: {options['periodo_codigo']} | Dry-run: {dry_run}")

        tipo_docente_default = CatalogoTipoDocente.objects.filter(
            nombre_tipo_docente__icontains="TITULAR"
        ).first() or CatalogoTipoDocente.objects.filter(
            codigo_tipo_docente__icontains="TIT"
        ).first() or CatalogoTipoDocente.objects.first()
        if not tipo_docente_default:
            raise CommandError("No existe ningun catalogo de tipo docente.")
        grado_afinidad_default = CatalogoGradoAfinidad.objects.filter(
            nombre_grado_afinidad__icontains="MEDIA"
        ).first() or CatalogoGradoAfinidad.objects.filter(
            codigo_grado_afinidad__icontains="MEDIA"
        ).first() or CatalogoGradoAfinidad.objects.order_by("nivel_prioridad").first()
        if not grado_afinidad_default:
            raise CommandError("No existe ningun catalogo de grado de afinidad.")

        modalidad_map = {}
        for obj in CatalogoModalidadContratacion.objects.all():
            modalidad_map[_normalize_text(obj.codigo_modalidad)] = obj
            modalidad_map[_normalize_text(obj.nombre_modalidad)] = obj
        dedicacion_map = {}
        for obj in CatalogoDedicacionHoraria.objects.all():
            dedicacion_map[_normalize_text(obj.codigo_dedicacion)] = obj
            dedicacion_map[_normalize_text(obj.nombre_dedicacion)] = obj
        modalidad_aliases = {
            "CONTRATOS OCASIONALES": "CONTRATO",
            "CONTRATO OCASIONAL": "CONTRATO",
            "NOMBRAMIENTO PROVISIONAL": "NOMBRAMIENTO",
            "NOMBRAMIENTO AUTORIDAD UNIVERS": "NOMBRAMIENTO",
        }

        pais_default = CatalogoPais.objects.filter(codigo_iso_pais="EC").first()
        if not pais_default:
            pais_default = CatalogoPais.objects.order_by("id_pais").first()

        with transaction.atomic():
            periodo, _ = CatalogoPeriodoAcademico.objects.update_or_create(
                codigo_periodo=options["periodo_codigo"],
                defaults={
                    "nombre_periodo": options["periodo_nombre"],
                    "periodo_activo": True,
                    "fecha_inicio_periodo": date(2026, 5, 1),
                    "fecha_fin_periodo": date(2026, 9, 30),
                },
            )

            steps_results = {}

            # ── STEP 1: CARRERAS ──
            malla_career_by_name = {}
            if only_step in (0, 1):
                malla_career_by_name = self._step1_carreras(main_book, coor_files, malla_book, steps_results)
                self.stdout.write(self.style.SUCCESS(f"  Step 1: {steps_results.get('step1', {}).get('msg', 'OK')}"))

            # ── STEP 2: CAMPOS DE CONOCIMIENTO ──
            if only_step in (0, 2):
                self._step2_campos(main_book, detallado_book, steps_results)
                self.stdout.write(self.style.SUCCESS(f"  Step 2: {steps_results.get('step2', {}).get('msg', 'OK')}"))

            # ── STEP 3: POSGRADOS ──
            if only_step in (0, 3):
                self._step3_posgrados(maestria_book, main_book, steps_results)
                self.stdout.write(self.style.SUCCESS(f"  Step 3: {steps_results.get('step3', {}).get('msg', 'OK')}"))

            # Build lookups needed by subsequent steps
            career_by_code = {obj.codigo_carrera: obj for obj in CatalogoCarrera.objects.all()}
            careers_by_name = {_canonical_name(obj.nombre_carrera): obj for obj in CatalogoCarrera.objects.all()}
            if not malla_career_by_name and malla_book.exists():
                try:
                    for row in _sheet_rows(malla_book, "CARRERAS_FCACC")[1:]:
                        if row and row[0] and row[1]:
                            key = _canonical_name(row[1])
                            code = _clean_text(row[0])
                            if key not in malla_career_by_name and code in career_by_code:
                                malla_career_by_name[key] = code
                except Exception:
                    pass
            field_by_code = {obj.codigo_campo: obj for obj in CatalogoCampoConocimiento.objects.all()}
            field_by_name = {_normalize_text(obj.nombre_campo_conocimiento): obj for obj in CatalogoCampoConocimiento.objects.all()}
            posgrado_by_code = {obj.codigo_posgrado: obj for obj in CatalogoTituloPosgrado.objects.all()}
            posgrado_by_name = {_normalize_text(obj.nombre_titulo_posgrado): obj for obj in CatalogoTituloPosgrado.objects.all()}

            # ── STEP 4: ASIGNATURAS ──
            subject_code_map = {}
            subject_by_code = {}
            subjects_by_lookup = defaultdict(list)
            if only_step in (0, 4):
                self._step4_asignaturas(main_book, coor_files, malla_book, detallado_asig_book, career_by_code, careers_by_name, malla_career_by_name, subject_code_map, subject_by_code, subjects_by_lookup, steps_results)
                self.stdout.write(self.style.SUCCESS(f"  Step 4: {steps_results.get('step4', {}).get('msg', 'OK')}"))

            subject_by_code = {obj.codigo_asignatura: obj for obj in CurriculoAsignatura.objects.select_related("id_carrera")}
            subjects_by_lookup = defaultdict(list)
            for obj in subject_by_code.values():
                key = (
                    _canonical_name(obj.id_carrera.nombre_carrera),
                    int(obj.nivel_semestre or 0),
                    _canonical_name(obj.nombre_asignatura),
                )
                subjects_by_lookup[key].append(obj)

            # ── STEP 5: ASIGNATURA-CAMPO ──
            if only_step in (0, 5):
                self._step5_asignatura_campo(main_book, coor_files, detallado_asig_book, subject_code_map, subject_by_code, field_by_code, steps_results)
                self.stdout.write(self.style.SUCCESS(f"  Step 5: {steps_results.get('step5', {}).get('msg', 'OK')}"))

            # ── STEP 6: POSGRADO-CAMPO ──
            if only_step in (0, 6):
                self._step6_posgrado_campo(main_book, posgrado_by_code, posgrado_by_name, field_by_code, field_by_name, steps_results)
                self.stdout.write(self.style.SUCCESS(f"  Step 6: {steps_results.get('step6', {}).get('msg', 'OK')}"))

            # ── STEP 7: DOCENTES ──
            if only_step in (0, 7):
                self._step7_docentes(main_book, modalidad_map, modalidad_aliases, dedicacion_map, tipo_docente_default, steps_results)
                self.stdout.write(self.style.SUCCESS(f"  Step 7: {steps_results.get('step7', {}).get('msg', 'OK')}"))

            teacher_by_name = {_normalize_text(obj.nombres_completos): obj for obj in DocenteFcacc.objects.all()}
            teacher_by_cedula = {_normalize_cedula(obj.cedula_docente): obj for obj in DocenteFcacc.objects.all() if _normalize_cedula(obj.cedula_docente)}

            # ── STEP 8: TITULOS DOCENTES ──
            if only_step in (0, 8):
                self._step8_titulos(nivel_docente_book, main_book, teacher_by_name, teacher_by_cedula, posgrado_by_code, posgrado_by_name, pais_default, steps_results)
                self.stdout.write(self.style.SUCCESS(f"  Step 8: {steps_results.get('step8', {}).get('msg', 'OK')}"))

            # ── STEP 9: DOCENTE-CAMPO AFINIDAD ──
            if only_step in (0, 9):
                self._step9_afinidad(revision_book, teacher_by_name, field_by_name, steps_results)
                self.stdout.write(self.style.SUCCESS(f"  Step 9: {steps_results.get('step9', {}).get('msg', 'OK')}"))

            # ── STEP 10: DEMANDAS ACADEMICAS ──
            if only_step in (0, 10):
                self._step10_demandas(main_book, careers_by_name, subjects_by_lookup, periodo, steps_results)
                self.stdout.write(self.style.SUCCESS(f"  Step 10: {steps_results.get('step10', {}).get('msg', 'OK')}"))

            subject_field_by_id = {}
            for relation in CurriculoAsignaturaCampo.objects.select_related("id_campo", "id_asignatura"):
                subject_field_by_id.setdefault(relation.id_asignatura_id, relation.id_campo)

            # ── STEP 11: ASIGNACIONES DOCENTES ──
            if only_step in (0, 11):
                self._step11_asignaciones(main_book, coor_files, careers_by_name, subjects_by_lookup, teacher_by_name, teacher_by_cedula, field_by_name, field_by_code, subject_field_by_id, periodo, sync_assignments, steps_results)
                self.stdout.write(self.style.SUCCESS(f"  Step 11: {steps_results.get('step11', {}).get('msg', 'OK')}"))

            # ── STEP 12: MATRIZ F4 ──
            if only_step in (0, 12):
                self._step12_f4(main_book, coor_files, career_by_code, careers_by_name, teacher_by_name, teacher_by_cedula, grado_afinidad_default, periodo, steps_results)
                self.stdout.write(self.style.SUCCESS(f"  Step 12: {steps_results.get('step12', {}).get('msg', 'OK')}"))

            if dry_run:
                transaction.set_rollback(True)
                self.stdout.write(self.style.WARNING("Dry run completado sin guardar cambios"))
            else:
                self.stdout.write(self.style.SUCCESS("Importacion completada"))

        for step_num in sorted(steps_results.keys()):
            r = steps_results[step_num]
            self.stdout.write(f"  {r['label']}: +{r['creados']} ~{r['actualizados']} -{r['omitidos']} (total {r['total']})")

    # ── STEP 1: CARRERAS ──
    def _step1_carreras(self, main_book, coor_files, malla_book, results):
        seen = set()
        creados = 0
        actualizados = 0
        omitidos = 0
        sources = [("MAE_CARRERA", main_book)]
        for _subdir, fp in coor_files:
            sources.append(("MAE_CARRERA", fp))
        malla_career_by_name = {}
        if malla_book.exists():
            try:
                malla_rows = _sheet_rows(malla_book, "CARRERAS_FCACC")
                for row in malla_rows[1:]:
                    if row and row[0] and row[1]:
                        key = _canonical_name(row[1])
                        if key not in malla_career_by_name:
                            malla_career_by_name[key] = _clean_text(row[0])
                sources.append(("CARRERAS_FCACC", malla_book))
            except Exception:
                pass
        for sheet_name, book in sources:
            try:
                rows = _sheet_rows(book, sheet_name)
            except Exception:
                omitidos += 1
                continue
            for row in rows[1:]:
                if not row or not row[0] or not row[1]:
                    omitidos += 1
                    continue
                codigo = _clean_text(row[0])
                if codigo in seen:
                    omitidos += 1
                    continue
                seen.add(codigo)
                nombre = _clean_text(row[1])
                activa = True
                if len(row) > 6:
                    activa = _normalize_text(row[6]) != "NO VIGENTE"
                _, created = CatalogoCarrera.objects.update_or_create(
                    codigo_carrera=codigo,
                    defaults={"nombre_carrera": nombre, "carrera_activa": activa, "es_actividad": codigo in F4_ACTIVITY_CAREER_CODES},
                )
                if created:
                    creados += 1
                else:
                    actualizados += 1
        total = creados + actualizados + omitidos
        _log_carga("CARRERAS", f"FCACC-PLANIFICACION.xlsx + {len(coor_files)} COOR + MALLA.xlsx", total, creados, actualizados, omitidos)
        results["step1"] = {"label": "Carreras", "total": total, "creados": creados, "actualizados": actualizados, "omitidos": omitidos, "msg": f"{creados} creadas, {actualizados} actualizadas, {omitidos} omitidas"}
        return malla_career_by_name

    # ── STEP 2: CAMPOS DE CONOCIMIENTO ──
    def _step2_campos(self, main_book, detallado_book, results):
        seen = set()
        creados = 0
        actualizados = 0
        omitidos = 0
        sources = [("MAE_CONOCIMIENTO", main_book)]
        if detallado_book.exists():
            sources.append(("MAE_CONOCIMIENTO", detallado_book))
        for sheet_name, book in sources:
            rows = _sheet_rows(book, sheet_name)
            for row in rows[1:]:
                if not row or not row[0] or not row[1]:
                    omitidos += 1
                    continue
                codigo = _clean_text(row[0])
                if codigo in seen:
                    continue
                seen.add(codigo)
                nombre = _clean_text(row[1])
                _, created = CatalogoCampoConocimiento.objects.update_or_create(
                    codigo_campo=codigo,
                    defaults={"nombre_campo_conocimiento": nombre},
                )
                if created:
                    creados += 1
                else:
                    actualizados += 1
        total = creados + actualizados + omitidos
        _log_carga("CAMPOS_CONOCIMIENTO", f"{main_book.name}, DETALLADO.xlsx", total, creados, actualizados, omitidos)
        results["step2"] = {"label": "Campos Conocimiento", "total": total, "creados": creados, "actualizados": actualizados, "omitidos": omitidos, "msg": f"{creados} creados, {actualizados} actualizados, {omitidos} omitidos"}

    # ── STEP 3: POSGRADOS ──
    def _step3_posgrados(self, maestria_book, main_book, results):
        seen = set()
        creados = 0
        actualizados = 0
        omitidos = 0
        sources = [("MAESTRIA", maestria_book)]
        for sheet_name, book in sources:
            rows = _sheet_rows(book, sheet_name)
            for row in rows[1:]:
                if not row or not row[1]:
                    omitidos += 1
                    continue
                nombre = _clean_text(row[1])
                codigo = _clean_text(row[0]) if row[0] else _fit_code(nombre, "POS-")
                if codigo in seen:
                    continue
                seen.add(codigo)
                _, created = CatalogoTituloPosgrado.objects.update_or_create(
                    codigo_posgrado=codigo,
                    defaults={"nombre_titulo_posgrado": nombre},
                )
                if created:
                    creados += 1
                else:
                    actualizados += 1
        total = creados + actualizados + omitidos
        _log_carga("POSGRADOS", f"Maestria.xlsx, {main_book.name}", total, creados, actualizados, omitidos)
        results["step3"] = {"label": "Posgrados", "total": total, "creados": creados, "actualizados": actualizados, "omitidos": omitidos, "msg": f"{creados} creados, {actualizados} actualizados, {omitidos} omitidos"}

    # ── STEP 4: ASIGNATURAS ──
    # ---- STEP 4: ASIGNATURAS (desde FCACC + COOR + MALLA + DETALLADO_ASIGNATURA) ----
    def _step4_asignaturas(self, main_book, coor_files, malla_book, detallado_asig_book, career_by_code, careers_by_name, malla_career_by_name, subject_code_map, subject_by_code, subjects_by_lookup, results):
        creados = 0
        actualizados = 0
        omitidos = 0
        seen_codes = set()
        sources = [("MAE_ASIGNATURA", main_book)]
        for _subdir, fp in coor_files:
            sources.append(("MAE_ASIGNATURA", fp))
        if malla_book.exists():
            sources.append(("ASIGNATURAS_FCACC", malla_book))
        if detallado_asig_book.exists():
            sources.append(("MAE_ASIGNATURA", detallado_asig_book))
        for sheet_name, book in sources:
            try:
                rows = _sheet_rows(book, sheet_name)
            except Exception:
                omitidos += 1
                continue
            for row in rows[1:]:
                if not row or not row[0] or not row[1]:
                    omitidos += 1
                    continue
                # MALLA.xlsx: 5 cols [code, name, hours, carrera, nivel]
                # Others: 7 cols [code, name, hours, semanas, carrera, nombre_carrera, nivel]
                is_malla = sheet_name == "ASIGNATURAS_FCACC"
                carrera_code = _clean_text(row[3] if is_malla else row[4]) if len(row) > (3 if is_malla else 4) and (row[3] if is_malla else row[4]) else ""
                if not carrera_code:
                    omitidos += 1
                    continue
                carrera_code_key = _canonical_name(carrera_code)
                malla_code = malla_career_by_name.get(carrera_code_key)
                carrera = career_by_code.get(malla_code) if malla_code else None
                if not carrera:
                    carrera = career_by_code.get(carrera_code) or careers_by_name.get(carrera_code_key)
                if not carrera:
                    omitidos += 1
                    continue
                subject_es_act = carrera.es_actividad if hasattr(carrera, 'es_actividad') else False
                if subject_es_act:
                    level = 0
                else:
                    level = _valid_level(row[6] if not is_malla else row[4]) if len(row) > (6 if not is_malla else 4) else None
                    if level is None:
                        omitidos += 1
                        continue
                source_code = _clean_text(row[0])
                if source_code in seen_codes:
                    continue
                seen_codes.add(source_code)
                compact_code = _fit_code(source_code, "ASG-")
                subject_code_map[source_code] = compact_code
                obj, created = CurriculoAsignatura.objects.update_or_create(
                    codigo_asignatura=compact_code,
                    defaults={
                        "id_carrera": carrera,
                        "nombre_asignatura": _clean_text(row[1]),
                        "horas_semanales_asignatura": int(row[2] or 0),
                        "nivel_semestre": level,
                        "es_actividad": subject_es_act,
                    },
                )
                if created:
                    creados += 1
                else:
                    actualizados += 1
                subject_by_code[compact_code] = obj
                key = (
                    _canonical_name(obj.id_carrera.nombre_carrera),
                    int(obj.nivel_semestre or 0),
                    _canonical_name(obj.nombre_asignatura),
                )
                subjects_by_lookup[key].append(obj)
        total = creados + actualizados + omitidos
        _log_carga("ASIGNATURAS", f"FCACC-PLANIFICACION.xlsx + {len(coor_files)} COOR + MALLA.xlsx + DETALLADO_ASIGNATURA.xlsx", total, creados, actualizados, omitidos)
        results["step4"] = {"label": "Asignaturas", "total": total, "creados": creados, "actualizados": actualizados, "omitidos": omitidos, "msg": f"{creados} creadas, {actualizados} actualizadas, {omitidos} omitidas"}
    # ---- STEP 5: ASIGNATURA-CAMPO (desde FCACC + COOR + DETALLADO_ASIGNATURA) ----
    def _step5_asignatura_campo(self, main_book, coor_files, detallado_asig_book, subject_code_map, subject_by_code, field_by_code, results):
        creados = 0
        ya_existentes = 0
        omitidos = 0
        seen_pairs = set()
        sources = [("DET_ASIG", main_book)]
        for _subdir, fp in coor_files:
            sources.append(("DET_ASIG", fp))
        if detallado_asig_book.exists():
            sources.append(("DET_ASIG", detallado_asig_book))
        for sheet_name, book in sources:
            try:
                rows = _sheet_rows(book, sheet_name)
            except Exception:
                omitidos += 1
                continue
            for row in rows[1:]:
                if not row or len(row) < 8 or not row[5] or not row[7]:
                    omitidos += 1
                    continue
                source_subject_code = _clean_text(row[5])
                compact_subject_code = subject_code_map.get(source_subject_code, _fit_code(source_subject_code, "ASG-"))
                subject = subject_by_code.get(compact_subject_code)
                if not subject:
                    omitidos += 1
                    continue
                field_code = _clean_text(row[7])
                field = field_by_code.get(field_code)
                if not field:
                    omitidos += 1
                    continue
                pair = (compact_subject_code, field_code)
                if pair in seen_pairs:
                    continue
                seen_pairs.add(pair)
                _, created = CurriculoAsignaturaCampo.objects.get_or_create(
                    id_asignatura=subject,
                    id_campo=field,
                )
                if created:
                    creados += 1
                else:
                    ya_existentes += 1
        total = creados + ya_existentes + omitidos
        _log_carga("ASIGNATURA_CAMPO", f"FCACC-PLANIFICACION.xlsx + {len(coor_files)} COOR + DETALLADO_ASIGNATURA.xlsx", total, creados, 0, omitidos)
        results["step5"] = {"label": "Asignatura-Campo", "total": total, "creados": creados, "actualizados": ya_existentes, "omitidos": omitidos, "msg": f"{creados} creadas, {ya_existentes} ya existian, {omitidos} omitidas"}

    # ── STEP 6: POSGRADO-CAMPO ──
    def _step6_posgrado_campo(self, main_book, posgrado_by_code, posgrado_by_name, field_by_code, field_by_name, results):
        rows = _sheet_rows(main_book, "MAESTRIA_DETALLADO")
        creados = 0
        omitidos = 0
        for row in rows[1:]:
            if not row or len(row) < 5 or not row[1] or not row[3]:
                omitidos += 1
                continue
            posgrado_name = _clean_text(row[1])
            posgrado_code = _clean_text(row[2]) if row[2] else None
            posgrado = None
            if posgrado_code:
                posgrado = posgrado_by_code.get(posgrado_code)
            if not posgrado:
                posgrado = posgrado_by_name.get(_normalize_text(posgrado_name))
            if not posgrado:
                omitidos += 1
                continue
            field_code = _clean_text(row[4]) if len(row) > 4 and row[4] else None
            field_name_raw = _clean_text(row[3])
            field = None
            if field_code:
                field = field_by_code.get(field_code)
            if not field:
                alias = FIELD_ALIASES.get(_canonical_name(field_name_raw), field_name_raw)
                field = field_by_name.get(_normalize_text(alias))
            if not field:
                omitidos += 1
                continue
            _, created = RelacionPosgradoCampo.objects.get_or_create(
                id_posgrado=posgrado,
                id_campo=field,
            )
            if created:
                creados += 1
        total = creados + omitidos
        _log_carga("POSGRADO_CAMPO", main_book.name, total, creados, 0, omitidos)
        results["step6"] = {"label": "Posgrado-Campo", "total": total, "creados": creados, "actualizados": 0, "omitidos": omitidos, "msg": f"{creados} creadas, {omitidos} omitidas"}

    # ── STEP 7: DOCENTES ──
    def _step7_docentes(self, main_book, modalidad_map, modalidad_aliases, dedicacion_map, tipo_docente_default, results):
        rows = _sheet_rows(main_book, "MDOCENTES")
        creados = 0
        actualizados = 0
        omitidos = 0
        for row in rows[1:]:
            if not row or not row[0] or not row[1]:
                omitidos += 1
                continue
            cedula = _normalize_cedula(row[0])
            if not cedula:
                omitidos += 1
                continue
            modalidad_key = _normalize_text(row[7]) if len(row) > 7 else ""
            modalidad = modalidad_map.get(modalidad_key) or modalidad_map.get(modalidad_aliases.get(modalidad_key, ""))
            if not modalidad:
                omitidos += 1
                continue
            dedicacion = dedicacion_map.get(_normalize_text(row[6])) if len(row) > 6 else None
            if not dedicacion:
                dedicacion = CatalogoDedicacionHoraria.objects.first()
                if not dedicacion:
                    omitidos += 1
                    continue
            _, created = DocenteFcacc.objects.update_or_create(
                cedula_docente=cedula,
                defaults={
                    "tipo_documento": "CEDULA",
                    "id_tipo_docente": tipo_docente_default,
                    "id_modalidad": modalidad,
                    "id_dedicacion": dedicacion,
                    "nombres_completos": _clean_text(row[1]),
                    "unidad_organica": _clean_text(row[2]) if len(row) > 2 else "",
                    "correo_institucional": _valid_email(row[3]) if len(row) > 3 else None,
                    "numero_celular": _normalize_phone(row[4]) if len(row) > 4 else None,
                    "tipo_sangre": _valid_tipo_sangre(row[8]) if len(row) > 8 else None,
                    "docente_activo": True,
                },
            )
            if created:
                creados += 1
            else:
                actualizados += 1
        total = creados + actualizados + omitidos
        _log_carga("DOCENTES", main_book.name, total, creados, actualizados, omitidos)
        results["step7"] = {"label": "Docentes", "total": total, "creados": creados, "actualizados": actualizados, "omitidos": omitidos, "msg": f"{creados} creados, {actualizados} actualizados, {omitidos} omitidos"}

    # ── STEP 8: TITULOS DOCENTES ──
    def _step8_titulos(self, nivel_docente_book, main_book, teacher_by_name, teacher_by_cedula, posgrado_by_code, posgrado_by_name, pais_default, results):
        creados = 0
        omitidos = 0
        sources = [("EDU_DOCENTE", nivel_docente_book), ("EDU_DOCENTE", main_book)]
        for sheet_name, book in sources:
            rows = _sheet_rows(book, sheet_name)
            for row in rows[1:]:
                if not row or not row[1]:
                    omitidos += 1
                    continue
                teacher_name = _clean_text(row[1])
                if _normalize_text(teacher_name) in {"SELECCIONE DOCENTE", "NO DEFINIDO", "#N/A", ""}:
                    omitidos += 1
                    continue
                docente = teacher_by_name.get(_normalize_text(teacher_name))
                if not docente and len(row) > 2 and row[2]:
                    docente = teacher_by_cedula.get(_normalize_cedula(row[2]))
                if not docente:
                    omitidos += 1
                    continue
                titulo_nombre = _clean_text(row[3]) if len(row) > 3 and row[3] else ""
                if not titulo_nombre:
                    omitidos += 1
                    continue
                posgrado_code = _clean_text(row[5]) if len(row) > 5 and row[5] else ""
                posgrado = None
                if posgrado_code:
                    posgrado = posgrado_by_code.get(posgrado_code)
                if not posgrado:
                    posgrado = posgrado_by_name.get(_normalize_text(titulo_nombre))
                if not pais_default:
                    omitidos += 1
                    continue
                _, created = DocenteTituloAcademico.objects.get_or_create(
                    id_docente=docente,
                    nombre_titulo=titulo_nombre,
                    defaults={
                        "id_pais": pais_default,
                        "id_posgrado": posgrado,
                        "nivel_titulo": 4,
                        "numero_registro_senescyt": None,
                        "fecha_registro_senescyt": None,
                    },
                )
                if created:
                    creados += 1
        total = creados + omitidos
        _log_carga("TITULOS_DOCENTES", f"NIVEL_DOCENTE.xlsx, {main_book.name}", total, creados, 0, omitidos)
        results["step8"] = {"label": "Titulos Docentes", "total": total, "creados": creados, "actualizados": 0, "omitidos": omitidos, "msg": f"{creados} creados, {omitidos} omitidos"}

    # ── STEP 9: DOCENTE-CAMPO AFINIDAD ──
    def _step9_afinidad(self, revision_book, teacher_by_name, field_by_name, results):
        rows = _sheet_rows(revision_book, "DET_DOCENTE")
        creados = 0
        omitidos = 0
        for row in rows[1:]:
            if not row or not row[1] or not row[2]:
                omitidos += 1
                continue
            teacher = teacher_by_name.get(_normalize_text(row[1]))
            if not teacher:
                omitidos += 1
                continue
            field_values = [f.strip() for f in str(row[2]).split(";")]
            for fv in field_values:
                fv = _clean_text(fv)
                if not fv:
                    continue
                alias_name = FIELD_ALIASES.get(_canonical_name(fv), fv)
                field = field_by_name.get(_normalize_text(alias_name))
                if not field:
                    continue
                _, created = DocenteCampoAfinidad.objects.get_or_create(
                    id_docente=teacher,
                    id_campo=field,
                )
                if created:
                    creados += 1
        total = creados + omitidos
        _log_carga("AFINIDAD_DOCENTE_CAMPO", revision_book.name, total, creados, 0, omitidos)
        results["step9"] = {"label": "Afinidad Docente-Campo", "total": total, "creados": creados, "actualizados": 0, "omitidos": omitidos, "msg": f"{creados} creadas, {omitidos} omitidas"}

    # ── STEP 10: DEMANDAS ACADEMICAS ──
    def _step10_demandas(self, main_book, careers_by_name, subjects_by_lookup, periodo, results):
        demand_sources = [
            ("FCACC-PLANIFICACION.xlsx", _sheet_rows(main_book, "ASIGNACION"), 1, 3, 4, 5, 9, 11),
        ]
        demand_bucket = {}
        creados = 0
        omitidos = 0
        for source_name, rows, carrera_idx, nivel_idx, paralelo_idx, subject_idx, total_hours_idx, total_idx in demand_sources:
            for row in rows[1:]:
                if not row or len(row) <= subject_idx:
                    omitidos += 1
                    continue
                carrera_name = _clean_text(row[carrera_idx])
                nivel = _valid_level(row[nivel_idx]) if len(row) > nivel_idx else None
                paralelo = _clean_text(row[paralelo_idx]) if len(row) > paralelo_idx else ""
                subject_name = _clean_text(row[subject_idx])
                if not carrera_name or not subject_name or nivel is None:
                    omitidos += 1
                    continue
                canonical_career = _canonical_name(carrera_name)
                canonical_career = CAREER_ALIASES.get(canonical_career, canonical_career)
                canonical_subject = _canonical_name(subject_name)
                carrera = careers_by_name.get(canonical_career)
                subject_matches = subjects_by_lookup.get((canonical_career, nivel, canonical_subject), [])
                subject = subject_matches[0] if subject_matches else None
                if not carrera or not subject:
                    omitidos += 1
                    continue
                key = (carrera.id_carrera, subject.id_asignatura)
                item = demand_bucket.setdefault(key, {"carrera": carrera, "subject": subject, "parallels": set(), "blank_rows": 0})
                if paralelo:
                    item["parallels"].add(paralelo)
                else:
                    item["blank_rows"] += 1
        for item in demand_bucket.values():
            numero_paralelos = max(1, len(item["parallels"]) + item["blank_rows"])
            _, created = PlanificacionDemandaAcademica.objects.update_or_create(
                id_asignatura=item["subject"],
                id_carrera=item["carrera"],
                id_periodo=periodo,
                defaults={"proyeccion_estudiantes": 0, "numero_paralelos": numero_paralelos},
            )
            if created:
                creados += 1
        total = creados + omitidos + len(demand_bucket)
        _log_carga("DEMANDAS_ACADEMICAS", main_book.name, total, creados, len(demand_bucket) - creados, omitidos)
        results["step10"] = {"label": "Demandas Academicas", "total": total, "creados": creados, "actualizados": len(demand_bucket) - creados, "omitidos": omitidos, "msg": f"{creados} creadas, {len(demand_bucket) - creados} actualizadas, {omitidos} omitidas"}

    # ── STEP 11: ASIGNACIONES DOCENTES ──
    def _step11_asignaciones(self, main_book, coor_files, careers_by_name, subjects_by_lookup, teacher_by_name, teacher_by_cedula, field_by_name, field_by_code, subject_field_by_id, periodo, sync_assignments, results):
        assignment_sources = [
            ("FCACC-PLANIFICACION.xlsx", _sheet_rows(main_book, "ASIGNACION"), 1, 3, 4, 5, 7, 11, 12, 22),
        ]
        for subdir, fp in coor_files:
            assignment_sources.append((f"{subdir}/{fp.name}", _sheet_rows(fp, "ASIGNACION"), 1, 3, 4, 5, 7, 11, 12, 22))
        default_field = field_by_name.get("UNIDAD BASICA") or CatalogoCampoConocimiento.objects.order_by("id_campo").first()
        assignment_bucket = {}
        skip_count = 0
        created_assignments = 0
        updated_assignments = 0
        for source_name, rows, carrera_idx, nivel_idx, paralelo_idx, subject_idx, field_idx, hours_idx, teacher_idx, cedula_idx in assignment_sources:
            for row in rows[1:]:
                if not row or len(row) <= max(carrera_idx, nivel_idx, subject_idx, teacher_idx):
                    skip_count += 1
                    continue
                carrera_name = _clean_text(row[carrera_idx])
                nivel = _valid_level(row[nivel_idx]) if len(row) > nivel_idx else None
                subject_name = _clean_text(row[subject_idx])
                teacher_name = _clean_text(row[teacher_idx])
                if not carrera_name or not subject_name or not teacher_name or nivel is None:
                    skip_count += 1
                    continue
                if _normalize_text(teacher_name) in {"SELECCIONE DOCENTE", "NO DEFINIDO", "#N/A", ""}:
                    skip_count += 1
                    continue
                horas_clase = _positive_int(row[hours_idx]) if len(row) > hours_idx else 0
                if horas_clase <= 0:
                    skip_count += 1
                    continue
                canonical_career = _canonical_name(carrera_name)
                canonical_career = CAREER_ALIASES.get(canonical_career, canonical_career)
                canonical_subject = _canonical_name(subject_name)
                carrera = careers_by_name.get(canonical_career)
                subject_matches = subjects_by_lookup.get((canonical_career, nivel, canonical_subject), [])
                subject = subject_matches[0] if subject_matches else None
                docente = teacher_by_name.get(_normalize_text(teacher_name))
                if not docente and len(row) > cedula_idx:
                    docente = teacher_by_cedula.get(_normalize_cedula(row[cedula_idx]))
                if not carrera or not subject or not docente:
                    skip_count += 1
                    continue
                field_name_raw = _clean_text(row[field_idx]) if len(row) > field_idx else ""
                field_alias = FIELD_ALIASES.get(_canonical_name(field_name_raw), field_name_raw)
                field = field_by_name.get(_normalize_text(field_alias))
                if not field and len(row) > field_idx:
                    field = field_by_code.get(_clean_text(row[field_idx]))
                if not field:
                    field = subject_field_by_id.get(subject.id_asignatura) or default_field
                if not field:
                    skip_count += 1
                    continue
                paralelo = _clean_text(row[paralelo_idx]) if len(row) > paralelo_idx else ""
                paralelo = (paralelo or "A")[:3]
                key = (docente.id_docente, subject.id_asignatura, periodo.id_periodo, paralelo)
                item = assignment_bucket.setdefault(key, {"docente": docente, "subject": subject, "periodo": periodo, "paralelo": paralelo, "id_carrera": carrera, "id_campo": field, "nivel_semestre_asignado": subject.nivel_semestre, "horas_complementarias": 0, "horas_clase": 0})
                item["horas_clase"] += horas_clase
        for item in assignment_bucket.values():
            _, created = PlanificacionAsignacionDocente.objects.update_or_create(
                id_docente=item["docente"],
                id_asignatura=item["subject"],
                id_periodo=item["periodo"],
                paralelo_asignado=item["paralelo"],
                defaults={
                    "id_carrera": item["id_carrera"],
                    "id_campo": item["id_campo"],
                    "nivel_semestre_asignado": item["nivel_semestre_asignado"],
                    "horas_clase": item["horas_clase"],
                    "horas_complementarias": item["horas_complementarias"],
                },
            )
            if created:
                created_assignments += 1
            else:
                updated_assignments += 1
        if sync_assignments:
            valid_keys = set(assignment_bucket.keys())
            for assignment in PlanificacionAsignacionDocente.objects.filter(id_periodo=periodo).only("id_asignacion", "id_docente_id", "id_asignatura_id", "id_periodo_id", "paralelo_asignado"):
                key = (assignment.id_docente_id, assignment.id_asignatura_id, assignment.id_periodo_id, (assignment.paralelo_asignado or "").strip())
                if key not in valid_keys:
                    assignment.delete()
        total = created_assignments + updated_assignments + skip_count
        _log_carga("ASIGNACIONES_DOCENTES", f"FCACC-PLANIFICACION.xlsx + {len(coor_files)} COOR files", total, created_assignments, updated_assignments, skip_count)
        results["step11"] = {"label": "Asignaciones Docentes", "total": total, "creados": created_assignments, "actualizados": updated_assignments, "omitidos": skip_count, "msg": f"{created_assignments} creadas, {updated_assignments} actualizadas, {skip_count} omitidas"}

    # ── STEP 12: MATRIZ F4 ──
    def _step12_f4(self, main_book, coor_files, career_by_code, careers_by_name, teacher_by_name, teacher_by_cedula, grado_afinidad_default, periodo, results):
        f4_sources = [
            ("FCACC-PLANIFICACION.xlsx", _sheet_rows(main_book, "ASIGNACION"), 1, 3, 4, 5, 7, 11, 12, 22),
        ]
        for fname in ["PLANIFICACION_ADMINISTRACION.xlsx", "PLANIFICACION_COMERCIO.xlsx", "PLANIFICACION_CONTABILIDAD.xlsx"]:
            fp = main_book.parent / fname
            if fp.exists():
                f4_sources.append((fname, _sheet_rows(fp, "ASIGNACION"), 0, 2, 3, 4, 5, 7, 9, 13))
        f4_rows = []
        created_f4 = 0
        updated_f4 = 0
        skipped_f4 = 0
        for source_name, rows, carrera_idx, nivel_idx, paralelo_idx, subject_idx, field_idx, hours_idx, teacher_idx, cedula_idx in f4_sources:
            for row in rows[1:]:
                if not row or len(row) <= max(carrera_idx, teacher_idx, subject_idx):
                    skipped_f4 += 1
                    continue
                career_code = _clean_text(row[2]) if len(row) > 2 else ""
                teacher_name = _clean_text(row[teacher_idx])
                activity_name = _clean_text(row[subject_idx]) if len(row) > subject_idx else ""
                activity_field = _normalize_text(row[field_idx]) if len(row) > field_idx else ""
                activity_kind = _clean_text(row[0]) if len(row) > 0 and row[0] else "Actividad"
                hours = _positive_int(row[hours_idx]) if len(row) > hours_idx else 0
                if career_code not in F4_ACTIVITY_CAREER_CODES and activity_field != "ACTIVIDAD":
                    continue
                if not teacher_name or not activity_name or hours <= 0:
                    skipped_f4 += 1
                    continue
                if _normalize_text(teacher_name) in {"SELECCIONE DOCENTE", "NO DEFINIDO", "#N/A", ""}:
                    skipped_f4 += 1
                    continue
                carrera = career_by_code.get(career_code)
                if not carrera:
                    canonical_career = CAREER_ALIASES.get(_canonical_name(career_code), _canonical_name(career_code))
                    carrera = careers_by_name.get(canonical_career)
                docente = teacher_by_name.get(_normalize_text(teacher_name))
                if not docente and len(row) > cedula_idx:
                    docente = teacher_by_cedula.get(_normalize_cedula(row[cedula_idx]))
                if not carrera or not docente:
                    skipped_f4 += 1
                    continue
                nivel = _clean_text(row[nivel_idx]) if len(row) > nivel_idx else ""
                h_adicional_1 = _positive_int(row[10]) if len(row) > 10 else 0
                h_adicional_2 = _positive_int(row[11]) if len(row) > 11 else 0
                h_investigacion = _positive_int(row[12]) if len(row) > 12 else 0
                additions = [
                    ("Actividad adicional 1", h_adicional_1),
                    ("Actividad adicional 2", h_adicional_2),
                    ("Investigacion", h_investigacion),
                ]
                base_added = False
                if activity_field == "ACTIVIDAD" or career_code in F4_ACTIVITY_CAREER_CODES:
                    f4_rows.append({
                        "docente": docente, "carrera": carrera,
                        "tipo_actividad": activity_kind, "nombre": activity_name,
                        "nivel": nivel, "horas": hours,
                        "observaciones": f"Importado desde {source_name}",
                    })
                    base_added = True
                for tipo_actividad, add_hours in additions:
                    if add_hours <= 0:
                        continue
                    f4_rows.append({
                        "docente": docente, "carrera": carrera,
                        "tipo_actividad": tipo_actividad, "nombre": activity_name,
                        "nivel": nivel, "horas": add_hours,
                        "observaciones": f"Importado desde {source_name}",
                    })
                if not base_added and not any(h > 0 for _, h in additions):
                    skipped_f4 += 1
        for item in f4_rows:
            obj, created = PlanificacionMatrizF4.objects.update_or_create(
                id_docente=item["docente"],
                id_carrera=item["carrera"],
                id_periodo=periodo,
                tipo_actividad=item["tipo_actividad"][:100],
                nombre_asignatura_actividad=item["nombre"][:200],
                nivel_semestre_actividad=item["nivel"][:20],
                defaults={
                    "id_grado_afinidad": grado_afinidad_default,
                    "horas_actividad": item["horas"],
                    "numero_paralelos_actividad": 1,
                    "observaciones": item["observaciones"],
                },
            )
            if created:
                created_f4 += 1
            else:
                updated_f4 += 1
        total = created_f4 + updated_f4 + skipped_f4
        _log_carga("MATRIZ_F4", f"FCACC-PLANIFICACION.xlsx + {len(coor_files)} COOR files", total, created_f4, updated_f4, skipped_f4)
        results["step12"] = {"label": "Matriz F4", "total": total, "creados": created_f4, "actualizados": updated_f4, "omitidos": skipped_f4, "msg": f"{created_f4} creados, {updated_f4} actualizados, {skipped_f4} omitidos"}
