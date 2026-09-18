"""Abre las interfaces con RequestFactory y transacciones PostgreSQL de solo lectura.

No envía formularios ni ejecuta acciones de modificación. El informe no contiene
HTML ni datos de los registros, únicamente rutas, estados y errores.
"""
import json
import os
from pathlib import Path
import sys
import traceback
import argparse
import logging
from unittest.mock import patch
from html.parser import HTMLParser
from urllib.parse import urlsplit, urlencode, urljoin
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_docente.settings')

import django
django.setup()

from django.contrib.auth import get_user_model
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.backends.signed_cookies import SessionStore
from django.core.exceptions import PermissionDenied
from django.db import connection, transaction
from django.http import Http404
from django.template import engines
from django.test import Client, RequestFactory, override_settings
from django.contrib.staticfiles import finders
from django.urls import URLResolver, get_resolver, reverse, resolve
from certificados.models import CertificadoEmitido, FirmanteCertificado
from planificacion.models import BitacoraUsoLaboratorio
from planificacion.models import PlanificacionAsignacionDocente
from catalogos.models import CatalogoPeriodoAcademico

parser = argparse.ArgumentParser()
parser.add_argument('--role', default='Administrador')
parser.add_argument('--follow-links', action='store_true')
parser.add_argument('--filters-only', action='store_true')
parser.add_argument('--http', action='store_true', help='Incluye middleware usando el cliente de Django.')
args = parser.parse_args()
linked_urls = set()
static_assets = set()
client = Client(HTTP_HOST='localhost')
if args.http:
    override_settings(SESSION_ENGINE='django.contrib.sessions.backends.signed_cookies').enable()
    logging.getLogger('django.request').disabled = True


class Links(HTMLParser):
    def __init__(self, base_url):
        super().__init__()
        self.base_url = base_url

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        resource = attributes.get('src') if tag in ('script', 'img') else attributes.get('href') if tag == 'link' else None
        if resource and resource.startswith('/static/'):
            static_assets.add(urlsplit(resource).path.removeprefix('/static/'))
        if tag == 'a':
            if attributes.get('aria-disabled') == 'true' or 'disabled' in attributes.get('class', '').split():
                return
            href = attributes.get('href', '')
            if href and not href.startswith(('#', 'javascript:', 'mailto:', 'tel:')):
                linked_urls.add(urljoin(self.base_url, href))


def patterns(resolver, namespaces=()):
    for item in resolver.url_patterns:
        if isinstance(item, URLResolver):
            if item.namespace == 'admin':
                continue
            yield from patterns(item, namespaces + ((item.namespace,) if item.namespace else ()))
        elif item.name:
            yield ':'.join((*namespaces, item.name)), item


def arguments(name, pattern):
    keys = set(pattern.pattern.converters)
    if not keys:
        return [{}]
    if keys == {'tipo'}:
        return [{'tipo': item} for item in ('funciones', 'catedras', 'dedicacion')]
    model = getattr(getattr(pattern.callback, 'view_class', None), 'model', None)
    if name in ('certificados:previsualizar', 'core:ver_certificado_propio'):
        model = CertificadoEmitido
    if name == 'certificados:firmante_editar':
        model = FirmanteCertificado
    if name in ('planificacion:bitacora_laboratorios_editar', 'planificacion:bitacora_laboratorios_eliminar'):
        model = BitacoraUsoLaboratorio
    if keys == {'usuario_id'}:
        return [{'usuario_id': user.pk}]
    if keys == {'pk'} and model is not None:
        pk = model.objects.values_list('pk', flat=True).first()
        return [{'pk': pk}] if pk is not None else []
    return []


def inspect_url(name, url):
    request = RequestFactory().get(url)
    request.user = user
    request.session = SessionStore()
    request._messages = FallbackStorage(request)
    match = resolve(request.path)
    request.resolver_match = match
    record = {'name': name, 'url': url}
    try:
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute('SET TRANSACTION READ ONLY')
                cursor.execute("SET LOCAL statement_timeout = '15000ms'")
            if args.http:
                with patch('django.contrib.auth.get_user', return_value=user):
                    response = client.get(url)
            else:
                response = match.func(request, *match.args, **match.kwargs)
            if hasattr(response, 'render'):
                response.render()
            record['status'] = response.status_code
            if response.status_code == 200 and 'text/html' in response.get('Content-Type', ''):
                Links(url).feed(response.content.decode(response.charset))
            if 300 <= response.status_code < 400:
                record['redirect'] = response.get('Location')
            response.close()
    except PermissionDenied:
        record['status'] = 403
    except Http404:
        record['status'] = 404
    except Exception as exc:
        record.update(status=500, error=f'{type(exc).__name__}: {exc}', traceback=traceback.format_exc())
        print(f'ERROR {url}: {record["error"]}', flush=True)
    return record


user = get_user_model().objects.filter(is_active=True, groups__name=args.role).order_by('-is_superuser').first()
if user is None:
    raise SystemExit('Se requiere un administrador existente para revisar las interfaces.')

results = []
skipped = []
for name, pattern in patterns(get_resolver()):
    if args.filters_only:
        continue
    if any(token in name for token in ('logout', 'restablecer_password', 'cambiar_estado_periodo',
                                       'copiar_planificacion', 'asignar_docente_operativa',
                                       'api_crear_asignacion', 'carga_masiva:confirmar')):
        skipped.append({'name': name, 'reason': 'Acción de modificación'})
        continue
    try:
        options = arguments(name, pattern)
        if not options:
            skipped.append({'name': name, 'reason': 'Sin registro de ejemplo o parámetros especiales'})
        for kwargs in options:
            results.append(inspect_url(name, reverse(name, kwargs=kwargs)))
            if len(results) % 25 == 0:
                print(f'Revisadas {len(results)} rutas', flush=True)
    except Exception as exc:
        results.append({'name': name, 'status': 500, 'error': f'{type(exc).__name__}: {exc}',
                        'traceback': traceback.format_exc()})

if args.filters_only:
    assignment = PlanificacionAsignacionDocente.objects.first()
    period = CatalogoPeriodoAcademico.objects.filter(periodo_activo=True).first() or CatalogoPeriodoAcademico.objects.first()
    for name, pattern in patterns(get_resolver()):
        if name.endswith('_list') and not pattern.pattern.converters:
            results.append(inspect_url(name, reverse(name) + '?q=a&cant=10'))
    if assignment:
        common = {'periodo': assignment.id_periodo_id, 'carrera': assignment.id_carrera_id}
        for path in ('/planificacion/operativa/', '/planificacion/consolidado-docentes/',
                     '/planificacion/paralelos-matriz/', '/planificacion/control-calidad/',
                     '/planificacion/asignacion-inteligente/', '/planificacion/asignaciones/',
                     '/planificacion/demanda/', '/planificacion/matriz-f4/',
                     '/reportes/', '/reportes/carga-docente/', '/reportes/resumen-horas/',
                     '/curriculo/asignaturas/'):
            results.append(inspect_url('filtros', path + '?' + urlencode(common)))
        api_params = {
            'planificacion:api_asignatura_info': {'id': assignment.id_asignatura_id},
            'planificacion:api_recommendations': {'asignatura': assignment.id_asignatura_id, **common},
            'planificacion:api_validar_horas': {'id_docente': assignment.id_docente_id, 'id_periodo': assignment.id_periodo_id},
            'planificacion:api_check_affinity': {'asignatura': assignment.id_asignatura_id, 'docente': assignment.id_docente_id},
            'planificacion:api_teacher_load': {'docente': assignment.id_docente_id, **common},
            'planificacion:api_asignacion_docente_aula': {'asignatura': assignment.id_asignatura_id, **common},
            'certificados:api_docentes_por_tipo': {'tipo': 'FUNCIONES', 'filtro': 'ACTIVIDADES', **common},
            'certificados:api_actividades': {'docente': assignment.id_docente_id, **common},
        }
        for name, params in api_params.items():
            results.append(inspect_url(name, reverse(name) + '?' + urlencode(params)))
    for name, pattern in patterns(get_resolver()):
        if not name.endswith('_list'):
            continue
        model = getattr(getattr(pattern.callback, 'view_class', None), 'model', None)
        if model is not None:
            pk = model.objects.values_list('pk', flat=True).first()
            if pk is not None:
                params = {'app': model._meta.app_label, 'model': model._meta.model_name, 'pk': pk}
                results.append(inspect_url('core:api_modelo_info', reverse('core:api_modelo_info') + '?' + urlencode(params)))

if args.follow_links:
    visited = {item.get('url') for item in results}
    per_route = Counter()
    for href in sorted(linked_urls.copy()):
        parsed = urlsplit(href)
        if parsed.scheme or parsed.netloc or not parsed.path.startswith('/'):
            continue
        url = parsed.path + ('?' + parsed.query if parsed.query else '')
        if url in visited or parsed.path.startswith(('/admin/', '/media/', '/static/')):
            continue
        try:
            match = resolve(parsed.path)
        except Exception:
            results.append({'name': 'enlace', 'url': url, 'status': 404})
            continue
        if any(token in match.url_name for token in ('logout', 'restablecer_password', 'copiar_planificacion',
                                                      'cambiar_estado_periodo', 'asignar_docente', 'confirmar')):
            continue
        # Muestrea tres registros distintos por pantalla; conserva los filtros.
        if per_route[match.view_name] >= 3 and not parsed.query:
            continue
        if per_route[match.view_name] >= 5:
            continue
        per_route[match.view_name] += 1
        visited.add(url)
        results.append(inspect_url(match.view_name, url))
        if len(results) % 25 == 0:
            print(f'Revisadas {len(results)} rutas y enlaces', flush=True)

template_errors = []
templates = [path for directory in ROOT.iterdir() if directory.is_dir()
             and directory.name not in ('venv', '.git', 'staticfiles', 'media')
             for path in directory.rglob('*.html')]
for path in templates:
    try:
        engines['django'].from_string(path.read_text(encoding='utf-8-sig'))
    except Exception as exc:
        template_errors.append({'path': str(path.relative_to(ROOT)), 'error': f'{type(exc).__name__}: {exc}'})

report = {'scope': f'GET {args.role}, {"Client y middleware" if args.http else "RequestFactory"}, PostgreSQL solo lectura',
          'summary': dict(Counter(item['status'] for item in results)),
          'results': results, 'skipped': skipped,
          'templates_checked': len(templates), 'template_errors': template_errors,
          'navigation_errors': [item for item in results if item['status'] >= 400 and item.get('url') in linked_urls],
          'static_assets_checked': len(static_assets),
          'missing_static_assets': sorted(asset for asset in static_assets if not finders.find(asset))}
suffix = '_filtros' if args.filters_only else ''
(ROOT / 'docs' / f'auditoria_interfaces_{args.role.lower()}{suffix}.json').write_text(
    json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8',
)
print(json.dumps({key: report[key] for key in ('summary', 'templates_checked', 'template_errors', 'navigation_errors', 'missing_static_assets')}, ensure_ascii=False))
