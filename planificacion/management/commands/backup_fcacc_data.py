import json
from datetime import datetime
from pathlib import Path

from django.core.management.base import BaseCommand
from django.core.serializers.json import DjangoJSONEncoder
from django.db import connection


class Command(BaseCommand):
    help = "Crea un respaldo JSON de las tablas funcionales FCACC sin modificar la base."

    def add_arguments(self, parser):
        parser.add_argument("--output", default=None, help="Ruta del archivo JSON de salida.")

    def handle(self, *args, **options):
        project_dir = Path(__file__).resolve().parents[3]
        default_name = f"fcacc_{datetime.now():%Y%m%d_%H%M%S}.json"
        output = Path(options["output"] or project_dir / "backups" / default_name)
        if not output.is_absolute():
            output = project_dir / output
        output.parent.mkdir(parents=True, exist_ok=True)

        prefixes = (
            "catalogo_", "curriculo_", "docente", "planificacion_",
            "relacion_posgrado_", "carga_historial",
        )
        available = connection.introspection.table_names()
        tables = sorted(table for table in available if table.startswith(prefixes))
        payload = {"created_at": datetime.now(), "database_vendor": connection.vendor, "tables": {}}
        quote = connection.ops.quote_name
        with connection.cursor() as cursor:
            for table in tables:
                cursor.execute(f"SELECT * FROM {quote(table)}")
                columns = [column.name for column in cursor.description]
                payload["tables"][table] = [
                    dict(zip(columns, row)) for row in cursor.fetchall()
                ]

        with output.open("w", encoding="utf-8") as stream:
            json.dump(payload, stream, cls=DjangoJSONEncoder, ensure_ascii=False, indent=2)
        total = sum(len(rows) for rows in payload["tables"].values())
        self.stdout.write(self.style.SUCCESS(
            f"Respaldo creado: {output} ({len(tables)} tablas, {total} filas)"
        ))
