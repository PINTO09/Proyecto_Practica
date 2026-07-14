import os
from django.core.management.base import BaseCommand
from django.db import connection


def split_sql_statements(sql):
    statements = []
    current = []
    i = 0
    in_single_quote = False
    in_line_comment = False
    in_block_comment = False
    dollar_tag = None

    while i < len(sql):
        ch = sql[i]
        nxt = sql[i + 1] if i + 1 < len(sql) else ''

        if dollar_tag is not None:
            if sql.startswith(dollar_tag, i):
                closing_tag = dollar_tag
                current.append(closing_tag)
                dollar_tag = None
                i += len(closing_tag)
            else:
                current.append(ch)
                i += 1
            continue

        if in_line_comment:
            current.append(ch)
            if ch == '\n':
                in_line_comment = False
            i += 1
            continue

        if in_block_comment:
            current.append(ch)
            if ch == '*' and nxt == '/':
                current.append(nxt)
                i += 2
                in_block_comment = False
            else:
                i += 1
            continue

        if in_single_quote:
            current.append(ch)
            if ch == "'" and nxt == "'":
                current.append(nxt)
                i += 2
            elif ch == "'":
                in_single_quote = False
                i += 1
            else:
                i += 1
            continue

        if ch == '-' and nxt == '-':
            current.append(ch)
            current.append(nxt)
            in_line_comment = True
            i += 2
            continue

        if ch == '/' and nxt == '*':
            current.append(ch)
            current.append(nxt)
            in_block_comment = True
            i += 2
            continue

        if ch == "'":
            current.append(ch)
            in_single_quote = True
            i += 1
            continue

        if ch == '$':
            if nxt == '$':
                current.append('$$')
                dollar_tag = '$$'
                i += 2
                continue
            j = i + 1
            if j < len(sql) and (sql[j].isalpha() or sql[j] == '_'):
                while j < len(sql) and (sql[j].isalnum() or sql[j] == '_'):
                    j += 1
                if j < len(sql) and sql[j] == '$':
                    tag = sql[i:j + 1]
                    current.append(tag)
                    dollar_tag = tag
                    i = j + 1
                    continue

        if ch == ';':
            statement = ''.join(current).strip()
            if statement and statement != ';':
                statements.append(statement)
            current = []
            i += 1
            continue

        current.append(ch)
        i += 1

    tail = ''.join(current).strip()
    if tail and tail != ';':
        statements.append(tail)

    return statements


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

        statements = split_sql_statements(sql)

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
