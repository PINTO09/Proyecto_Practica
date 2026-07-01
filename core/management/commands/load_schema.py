import os
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Carga el esquema SQL de la base de datos FCACC'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            default=None,
            help='Ruta al archivo SQL (por defecto: schema_fcacc.sql en la raíz)',
        )

    def handle(self, *args, **options):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        file_path = options['file'] or os.path.join(base_dir, 'schema_fcacc.sql')

        if not os.path.exists(file_path):
            self.stderr.write(self.style.ERROR(f'Archivo no encontrado: {file_path}'))
            return

        self.stdout.write(f'Leyendo {file_path}...')
        with open(file_path, 'r', encoding='utf-8') as f:
            sql = f.read()

        statements = []
        current = []
        for line in sql.split('\n'):
            stripped = line.strip()
            if stripped.upper().startswith('--') or stripped.startswith('--'):
                continue
            current.append(line)
            if stripped.endswith(';') and not stripped.startswith('--'):
                statements.append('\n'.join(current))
                current = []

        if current:
            statements.append('\n'.join(current))

        success = 0
        errors = 0
        with connection.cursor() as cursor:
            for i, stmt in enumerate(statements):
                stmt = stmt.strip()
                if not stmt or stmt == ';':
                    continue
                try:
                    cursor.execute(stmt)
                    success += 1
                except Exception as e:
                    errors += 1
                    if errors <= 5:
                        self.stderr.write(self.style.WARNING(
                            f'  [{i + 1}] {e}'
                        ))

        self.stdout.write(self.style.SUCCESS(
            f'\nEsquema cargado: {success} sentencias OK, {errors} errores (omitidos)'
        ))
