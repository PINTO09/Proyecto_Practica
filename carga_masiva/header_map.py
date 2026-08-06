"""Mapeo por encabezados para la carga masiva.

Permite reconocer hojas de un Excel cualquiera por el nombre de sus columnas
(no por su posición) y reordenarlas al layout canónico que espera
``import_complete_fcacc``. Así un archivo propio de docentes o planificación
con hojas/columnas en otro orden se procesa igual que los libros oficiales
FCACC.

Una hoja se reconoce si su primera fila contiene suficientes encabezados
conocidos. Después se reordenan las columnas según el encabezado encontrado y
se produce una hoja con el nombre canónico y las columnas en la posición
esperada por el importador.
"""
from planificacion.management.commands.import_complete_fcacc import _normalize_text


# Posición canónica (la que usa el importador) -> sinónimos de encabezado.
# Los sinónimos se guardan en MAYÚSCULAS sin tildes con espacios simples; al
# comparar se normaliza igual el encabezado real (incluida la variante con
# guiones bajos, p.ej. NOMBRE_DOCENTE == NOMBRE DOCENTE).
COLUMN_SYNONYMS = {
    'MDOCENTES': {
        0: ['ID DOCENTE', 'CEDULA', 'CEDULA DOCENTE', 'DOCUMENTO', 'IDENTIFICACION', 'CI'],
        1: ['DATOS DOCENTE', 'NOMBRES', 'NOMBRES COMPLETOS', 'NOMBRES Y APELLIDOS',
            'APELLIDOS Y NOMBRES', 'NOMBRE', 'NOMBRE COMPLETO', 'NOMBRE DEL DOCENTE',
            'APELLIDOS', 'DOCENTE'],
        2: ['UNIDAD', 'UNIDAD ORGANICA', 'UNIDAD ACADEMICA', 'DEPARTAMENTO', 'FACULTAD'],
        3: ['CORREO', 'CORREO INSTITUCIONAL', 'EMAIL', 'CORREO ELECTRONICO',
            'CORREO ELECTRONICO INSTITUCIONAL'],
        4: ['CELULAR', 'TELEFONO', 'CEL', 'MOVIL', 'NUMERO CELULAR', 'TELEFONO CELULAR'],
        6: ['DEDICACION', 'DEDICACION HORARIA', 'TIPO DE DEDICACION', 'DEDICACION SEMANAL'],
        7: ['MODALIDAD', 'MODALIDAD TH', 'MODALIDAD DE CONTRATACION', 'TIPO DE MODALIDAD'],
        8: ['TIPO SANGRE', 'TIPO DE SANGRE', 'GRUPO SANGUINEO', 'GRUPO SANGUINEO', 'SANGRE'],
    },
    'EDU_DOCENTE': {
        1: ['NOMBRE DOCENTE', 'NOMBRES', 'NOMBRE', 'DOCENTE', 'NOMBRE DEL DOCENTE'],
        2: ['IDENTIFICACION', 'CEDULA', 'CEDULA DOCENTE', 'DOCUMENTO'],
        3: ['MAESTRIA', 'TITULO', 'NOMBRE MAESTRIA', 'TITULO POSGRADO', 'NOMBRE TITULO', 'POSGRADO'],
        5: ['ID MAESRIA', 'ID MAESTRIA', 'CODIGO MAESTRIA', 'CODIGO POSGRADO'],
    },
    'DET_DOCENTE': {
        1: ['NOM DOCE', 'NOMBRE DOCENTE', 'NOMBRES', 'NOMBRE', 'DOCENTE'],
        2: ['C DET DOC', 'CAMPOS', 'CAMPOS DE CONOCIMIENTO', 'CAMPO', 'CAMPO CONOCIMIENTO',
            'AREAS', 'AREA', 'CAMPOS CONOCIMIENTO'],
    },
    'ASIGNACION': {
        1: ['CARRERA', 'NOMBRE CARRERA', 'CARRERA NOMBRE'],
        2: ['ID CARRERA', 'CODIGO CARRERA'],
        3: ['NIVEL', 'SEMESTRE', 'NIVEL ACADEMICO', 'ID NIVEL'],
        4: ['PARALELO', 'PARALELO ASIGNADO'],
        5: ['ASIGNATURA', 'NOM ASIG', 'MATERIA', 'NOMBRE ASIGNATURA'],
        6: ['ID ASIG', 'ID ASIG CAM DET', 'CODIGO ASIGNATURA', 'CODIGO'],
        7: ['CAMPO', 'CAMPO CONOCIMIENTO', 'DETALLADO', 'ID DETALLADO'],
        11: ['TOTAL', 'HORAS', 'HORAS CLASE', 'TOTAL HORAS', 'HORAS SEMANALES'],
        12: ['NOMBRE DOCENT', 'NOMBRE DOCENTE', 'DOCENTE', 'NOMBRE DEL DOCENTE'],
        22: ['CEDULA DOCENTE', 'CEDULA', 'IDENTIFICACION', 'DOCUMENTO'],
    },
    'MAE_CARRERA': {
        0: ['ID CARRERA', 'CODIGO CARRERA', 'CODIGO'],
        1: ['NOMBRE CARRERA', 'CARRERA', 'NOMBRE'],
        6: ['ESTADO', 'ESTADO CARRERA', 'VIGENCIA'],
    },
    'MAE_ASIGNATURA': {
        0: ['ID ASIG', 'CODIGO ASIGNATURA', 'CODIGO'],
        1: ['NOM ASIG', 'NOMBRE ASIGNATURA', 'ASIGNATURA', 'NOMBRE'],
        2: ['HORAS', 'HORAS SEMANALES', 'TOTAL HORAS'],
        4: ['ID CARRERA', 'CODIGO CARRERA'],
        6: ['ID NIVEL', 'NIVEL', 'SEMESTRE'],
    },
    'MAE_CONOCIMIENTO': {
        0: ['ID DDETALLADO', 'ID DETALLADO', 'CODIGO CAMPO', 'CODIGO'],
        1: ['CAMPO DETALLADO', 'NOMBRE CAMPO', 'CAMPO CONOCIMIENTO', 'CAMPO', 'NOMBRE'],
    },
    'MAESTRIA': {
        0: ['ID MAESTRIA', 'CODIGO POSGRADO', 'CODIGO'],
        1: ['NOMBRE MAESTRIA', 'MAESTRIA', 'NOMBRE TITULO POSGRADO', 'POSGRADO', 'NOMBRE'],
    },
    'MAESTRIA_DETALLADO': {
        1: ['MAESTRIA', 'NOMBRE MAESTRIA', 'POSGRADO'],
        2: ['ID MAESTRIA', 'CODIGO POSGRADO'],
        3: ['CAMPO DETALLADO', 'NOMBRE CAMPO', 'CAMPO'],
        4: ['ID DETALLADO', 'CODIGO CAMPO'],
    },
    'DET_ASIG': {
        5: ['ID ASIG', 'CODIGO ASIGNATURA'],
        7: ['ID DETALLADO', 'CODIGO CAMPO'],
    },
}

# Para considerar una hoja como tal: posiciones imprescindibles (required) y
# cantidad mínima de columnas reconocidas (min_matches). Evita que una lista
# genérica de nombres se interprete como otra entidad.
SHEET_SIGNATURES = {
    'MDOCENTES': {'required': (0, 1), 'min_matches': 3},
    'EDU_DOCENTE': {'required': (1, 3), 'min_matches': 2},
    'DET_DOCENTE': {'required': (1, 2), 'min_matches': 2},
    'ASIGNACION': {'required': (1, 5, 12), 'min_matches': 5},
    'MAE_CARRERA': {'required': (0, 1), 'min_matches': 2},
    'MAE_ASIGNATURA': {'required': (0, 1), 'min_matches': 3},
    'MAE_CONOCIMIENTO': {'required': (0, 1), 'min_matches': 2},
    'MAESTRIA': {'required': (0, 1), 'min_matches': 2},
    'MAESTRIA_DETALLADO': {'required': (1, 3), 'min_matches': 2},
    'DET_ASIG': {'required': (5, 7), 'min_matches': 2},
}

# Orden de prioridad para desempatar cuando varias firmas encajan.
SHEET_ORDER = [
    'MDOCENTES', 'EDU_DOCENTE', 'DET_DOCENTE', 'ASIGNACION',
    'MAE_ASIGNATURA', 'MAE_CARRERA', 'MAE_CONOCIMIENTO',
    'MAESTRIA_DETALLADO', 'MAESTRIA', 'DET_ASIG',
]


def _header_keys(value):
    """Variantes normalizadas de un encabezado: con y sin guiones bajos."""
    norm = _normalize_text(value)
    return {norm, norm.replace('_', ' ')}


def detect_sheet(header_row):
    """Reconoce la hoja por su fila de encabezados.

    Devuelve (nombre_canónico, col_map) donde col_map asocia cada posición
    canónica con el índice de columna real del Excel, o (None, {}) si la hoja
    no encaja con ninguna firma conocida.
    """
    if not header_row:
        return None, {}
    keys = [_header_keys(h) for h in header_row]
    best = None
    for sheet_name in SHEET_ORDER:
        synonyms = COLUMN_SYNONYMS[sheet_name]
        signature = SHEET_SIGNATURES[sheet_name]
        col_map = {}
        used = set()
        for pos in sorted(synonyms):
            wanted = set(synonyms[pos])
            for idx, keyset in enumerate(keys):
                if idx in used:
                    continue
                if keyset & wanted:
                    col_map[pos] = idx
                    used.add(idx)
                    break
        required_ok = all(p in col_map for p in signature['required'])
        if required_ok and len(col_map) >= signature['min_matches']:
            score = len(col_map)
            if best is None or score > best[0]:
                best = (score, sheet_name, col_map)
    if best:
        return best[1], best[2]
    return None, {}


def rebuild_rows(rows, col_map):
    """Reordena filas (encabezado incluido) al layout canónico.

    Las posiciones canónicas que no tienen columna en el Excel original se
    dejan vacías para que el importador nunca se quede sin esa columna.
    """
    if not rows:
        return []
    max_pos = max(col_map)
    rebuilt = []
    for row in rows:
        new_row = [None] * (max_pos + 1)
        for pos, idx in col_map.items():
            new_row[pos] = row[idx] if idx < len(row) else None
        rebuilt.append(new_row)
    return rebuilt
