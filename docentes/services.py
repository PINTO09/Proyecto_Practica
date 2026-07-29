from datetime import timedelta
import re
import unicodedata


def merge_date_ranges(ranges):
    """Une períodos solapados o consecutivos y descarta rangos inválidos."""
    valid_ranges = sorted(
        (start, end)
        for start, end in ranges
        if start is not None and end is not None and start <= end
    )
    merged = []
    for start, end in valid_ranges:
        if not merged or start > merged[-1][1] + timedelta(days=1):
            merged.append([start, end])
            continue
        if end > merged[-1][1]:
            merged[-1][1] = end
    return [(start, end) for start, end in merged]


def inclusive_days(ranges):
    """Total de días calendario, incluyendo el inicio y el fin."""
    return sum((end - start).days + 1 for start, end in merge_date_ranges(ranges))


def humanize_duration(days):
    """Representación legible; los días permanecen como la medida exacta."""
    if not days:
        return '0 días'
    years, remainder = divmod(days, 365)
    months, remaining_days = divmod(remainder, 30)
    parts = []
    if years:
        parts.append(f'{years} año{"s" if years != 1 else ""}')
    if months:
        parts.append(f'{months} mes{"es" if months != 1 else ""}')
    if remaining_days or not parts:
        parts.append(f'{remaining_days} día{"s" if remaining_days != 1 else ""}')
    return ', '.join(parts)


def normalize_academic_title(value):
    value = unicodedata.normalize('NFKD', value or '')
    value = ''.join(char for char in value if not unicodedata.combining(char))
    return re.sub(r'[^A-Z0-9]+', ' ', value.upper()).strip()


def classify_postgraduate_title(title):
    """Clasifica títulos de cuarto nivel sin asumir que todo es maestría."""
    catalog_name = ''
    if getattr(title, 'id_posgrado_id', None) and getattr(title, 'id_posgrado', None):
        catalog_name = title.id_posgrado.nombre_titulo_posgrado
    name = normalize_academic_title(catalog_name or getattr(title, 'nombre_titulo', ''))
    if (getattr(title, 'nivel_titulo', 0) or 0) < 4 and not getattr(title, 'id_posgrado_id', None):
        return None
    if re.search(r'\b(DOCTOR|DOCTORA|DOCTORADO|PHD|PH D)\b', name):
        return 'doctorates'
    if re.search(r'\b(MAESTRIA|MASTER|MAGISTER|MSC|M SC)\b', name):
        return 'masters'
    if re.search(r'\b(ESPECIALISTA|ESPECIALIZACION)\b', name):
        return 'specializations'
    return 'other'


def unique_postgraduate_titles(titles):
    """Retorna (título, categoría) sin duplicar el mismo título por docente."""
    unique = []
    seen = set()
    for title in titles:
        category = classify_postgraduate_title(title)
        if not category:
            continue
        catalog_name = ''
        if getattr(title, 'id_posgrado_id', None) and getattr(title, 'id_posgrado', None):
            catalog_name = title.id_posgrado.nombre_titulo_posgrado
        display_name = catalog_name or getattr(title, 'nombre_titulo', '')
        key = normalize_academic_title(display_name)
        if not key or key in seen:
            continue
        seen.add(key)
        unique.append((title, category))
    return unique
