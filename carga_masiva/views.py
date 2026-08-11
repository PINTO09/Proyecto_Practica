import uuid

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.core.management.base import CommandError
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse

from accounts.decorators import module_permission_required

from . import services
from .forms import CargaMasivaUploadForm

SESSION_KEY = 'carga_masiva'
RESULTADO_SESSION_KEY = 'carga_masiva_resultado'


def _preview_cache_key(token):
    return f'carga_masiva:preview:{token}'


def _error_response(mensaje, *, status=400):
    return JsonResponse({'ok': False, 'error': mensaje}, status=status)


@login_required
@module_permission_required('carga_masiva', 'change')
def subir_archivos(request):
    if request.method == 'POST':
        form = CargaMasivaUploadForm(request.POST, request.FILES)
        if not form.is_valid():
            errores = [str(e) for errs in form.errors.values() for e in errs]
            return _error_response(' '.join(errores) or 'Revisa los datos del formulario.')

        # Si había una carga anterior sin confirmar, se limpia su carpeta
        # temporal antes de empezar una nueva.
        estado_previo = request.session.get(SESSION_KEY)
        if estado_previo:
            services.cleanup_temp(estado_previo.get('token'))

        token = uuid.uuid4().hex
        periodo_codigo = form.cleaned_data['periodo_codigo']
        periodo_nombre = form.cleaned_data['periodo_nombre']
        try:
            base_dir, detected_labels = services.detect_and_build_dir(
                form.cleaned_data['archivo'], token,
            )
            # La vista previa se corre aquí mismo (no solo al llegar a la
            # pantalla de previsualización) para poder mostrar cualquier
            # error del importador -de archivo o inesperado- en el modal de
            # esta misma pantalla, sin navegar a ninguna parte. El resultado
            # se guarda en caché un momento para no volver a correrlo al
            # llegar a la previsualización.
            resultado = services.run_import(base_dir, periodo_codigo, periodo_nombre, commit=False)
        except services.ArchivoNoReconocido as exc:
            services.cleanup_temp(token)
            return _error_response(str(exc))
        except CommandError as exc:
            services.cleanup_temp(token)
            return _error_response(f'No se pudo procesar la carga: {exc}')
        except Exception as exc:
            services.cleanup_temp(token)
            return _error_response(f'Ocurrió un error inesperado al analizar el archivo: {exc}')

        cache.set(_preview_cache_key(token), resultado, timeout=300)
        request.session[SESSION_KEY] = {
            'token': token,
            'periodo_codigo': periodo_codigo,
            'periodo_nombre': periodo_nombre,
            'detected_labels': detected_labels,
            'nombre_archivo': form.cleaned_data['archivo'].name,
        }
        return JsonResponse({'ok': True, 'redirect': reverse('carga_masiva:previsualizar')})

    form = CargaMasivaUploadForm()
    return render(request, 'carga_masiva/upload.html', {
        'active_section': 'carga_masiva_subir',
        'form': form,
    })


@login_required
@module_permission_required('carga_masiva', 'change')
def previsualizar(request):
    estado = request.session.get(SESSION_KEY)
    if not estado:
        messages.warning(request, 'Primero debes subir los archivos a cargar.')
        return redirect('carga_masiva:subir')

    base_dir = services.temp_dir(estado['token'])
    cache_key = _preview_cache_key(estado['token'])
    cached = cache.get(cache_key)
    if cached is not None:
        cache.delete(cache_key)
        diff, steps_results = cached
    else:
        try:
            diff, steps_results = services.run_import(
                base_dir, estado['periodo_codigo'], estado['periodo_nombre'], commit=False,
            )
        except Exception as exc:
            services.cleanup_temp(estado['token'])
            del request.session[SESSION_KEY]
            messages.error(request, f'No se pudo procesar la carga: {exc}')
            return redirect('carga_masiva:subir')

    # Los datos de las filas nuevas/modificadas de entidades excluibles se
    # guardan en sesion: son la unica fuente disponible para "excluir esta
    # fila" al confirmar (una fila nueva no existe todavia en la BD, la
    # vista previa siempre revierte sus cambios).
    estado['excludable_data'] = services.excludable_items_from_diff(diff)
    request.session[SESSION_KEY] = estado
    request.session.modified = True

    diff_display = []
    total_nuevas = 0
    total_modificadas = 0
    total_retiradas = 0
    for model, changes in diff.items():
        removed = changes.get('removed', [])
        total_nuevas += len(changes['new'])
        total_modificadas += len(changes['changed'])
        total_retiradas += len(removed)
        diff_display.append({
            'label': changes['label'],
            'excludable': changes.get('excludable', False),
            'new': changes['new'],
            'new_total': len(changes['new']),
            'changed': changes['changed'],
            'changed_total': len(changes['changed']),
            'removed': removed,
            'removed_total': len(removed),
        })

    # Con la deteccion automatica, los tipos de dato que no vienen en este
    # archivo procesan 0 filas (van con un archivo vacio) - se ocultan del
    # resumen para no confundir con una tabla llena de ceros.
    pasos_con_datos = [r for r in steps_results.values() if r['total'] > 0]

    return render(request, 'carga_masiva/preview.html', {
        'active_section': 'carga_masiva_subir',
        'periodo_codigo': estado['periodo_codigo'],
        'periodo_nombre': estado['periodo_nombre'],
        'nombre_archivo': estado.get('nombre_archivo'),
        'detected_labels': estado.get('detected_labels', []),
        'diff_display': diff_display,
        'steps_results': sorted(pasos_con_datos, key=lambda r: r['label']),
        'total_nuevas': total_nuevas,
        'total_modificadas': total_modificadas,
        'total_retiradas': total_retiradas,
        'hay_cambios': bool(diff),
    })


@login_required
@module_permission_required('carga_masiva', 'change')
def confirmar(request):
    if request.method != 'POST':
        return redirect('carga_masiva:previsualizar')

    estado = request.session.get(SESSION_KEY)
    if not estado:
        return _error_response('La sesión de la carga expiró o ya fue confirmada. Vuelve a subir el archivo.')

    base_dir = services.temp_dir(estado['token'])

    excluded_keys = request.POST.getlist('excluir')
    excludable_data = estado.get('excludable_data', {})
    excluded_pairs = services.resolve_excluded_pairs(excluded_keys, excludable_data)
    services.apply_exclusions(base_dir, excluded_pairs)

    try:
        diff, steps_results = services.run_import(
            base_dir, estado['periodo_codigo'], estado['periodo_nombre'], commit=True,
        )
    except CommandError as exc:
        return _error_response(f'No se pudo completar la carga: {exc}')
    except Exception as exc:
        return _error_response(f'Ocurrió un error inesperado al aplicar la carga: {exc}')

    # La carga ya se aplicó de verdad en este punto (run_import hizo commit).
    # Si registrar la auditoría falla por algo imprevisto, no se le puede
    # decir al usuario "hubo un error" -los datos sí se guardaron-, así que
    # se registra el problema en el log del servidor y se sigue igual.
    try:
        services.apply_audit_log(request, diff, nombre_archivo=estado.get('nombre_archivo') or 'archivo sin nombre')
    except Exception:
        import logging
        logging.getLogger(__name__).exception('No se pudo registrar la auditoría de la carga masiva %s', estado['token'])

    services.cleanup_temp(estado['token'])
    del request.session[SESSION_KEY]

    pasos_con_datos = [r for r in steps_results.values() if r['total'] > 0]
    request.session[RESULTADO_SESSION_KEY] = {
        'steps_results': sorted(pasos_con_datos, key=lambda r: r['label']),
        'total_nuevas': sum(len(c['new']) for c in diff.values()),
        'total_modificadas': sum(len(c['changed']) for c in diff.values()),
        'total_retiradas': sum(len(c.get('removed', [])) for c in diff.values()),
        'excluidas': len(excluded_pairs),
    }
    return JsonResponse({'ok': True, 'redirect': reverse('carga_masiva:confirmado')})


@login_required
@module_permission_required('carga_masiva', 'change')
def confirmado(request):
    resultado = request.session.pop(RESULTADO_SESSION_KEY, None)
    if not resultado:
        return redirect('carga_masiva:subir')

    excluidas_msg = (
        f" Excluiste {resultado['excluidas']} fila(s) a pedido tuyo."
        if resultado.get('excluidas') else ''
    )
    messages.success(
        request,
        f"Carga aplicada: {resultado['total_nuevas']} registros creados, "
        f"{resultado['total_modificadas']} modificados, {resultado['total_retiradas']} retirados."
        f"{excluidas_msg} Cada cambio quedó registrado en Auditoría.",
    )
    return render(request, 'carga_masiva/confirmado.html', {
        'active_section': 'carga_masiva_subir',
        'steps_results': resultado['steps_results'],
        'total_nuevas': resultado['total_nuevas'],
        'total_modificadas': resultado['total_modificadas'],
        'total_retiradas': resultado['total_retiradas'],
    })
