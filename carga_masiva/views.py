import uuid

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.management.base import CommandError
from django.shortcuts import redirect, render

from accounts.decorators import module_permission_required

from . import services
from .forms import CargaMasivaUploadForm

SESSION_KEY = 'carga_masiva'


@login_required
@module_permission_required('carga_masiva', 'change')
def subir_archivos(request):
    if request.method == 'POST':
        form = CargaMasivaUploadForm(request.POST, request.FILES)
        if form.is_valid():
            # Si había una carga anterior sin confirmar, se limpia su carpeta
            # temporal antes de empezar una nueva.
            estado_previo = request.session.get(SESSION_KEY)
            if estado_previo:
                services.cleanup_temp(estado_previo.get('token'))

            token = uuid.uuid4().hex
            try:
                _base_dir, detected_labels = services.detect_and_build_dir(
                    form.cleaned_data['archivo'], token,
                )
            except services.ArchivoNoReconocido as exc:
                services.cleanup_temp(token)
                form.add_error('archivo', str(exc))
            else:
                request.session[SESSION_KEY] = {
                    'token': token,
                    'periodo_codigo': form.cleaned_data['periodo_codigo'],
                    'periodo_nombre': form.cleaned_data['periodo_nombre'],
                    'detected_labels': detected_labels,
                    'nombre_archivo': form.cleaned_data['archivo'].name,
                }
                return redirect('carga_masiva:previsualizar')
    else:
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
    try:
        diff, steps_results = services.run_import(
            base_dir, estado['periodo_codigo'], estado['periodo_nombre'], commit=False,
        )
    except CommandError as exc:
        messages.error(request, f'No se pudo procesar la carga: {exc}')
        services.cleanup_temp(estado['token'])
        del request.session[SESSION_KEY]
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
        messages.warning(request, 'Primero debes subir los archivos a cargar.')
        return redirect('carga_masiva:subir')

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
        messages.error(request, f'No se pudo completar la carga: {exc}')
        return redirect('carga_masiva:previsualizar')

    services.apply_audit_log(request, diff)
    services.cleanup_temp(estado['token'])
    del request.session[SESSION_KEY]

    total_nuevas = sum(len(c['new']) for c in diff.values())
    total_modificadas = sum(len(c['changed']) for c in diff.values())
    total_retiradas = sum(len(c.get('removed', [])) for c in diff.values())
    excluidas_msg = f' Excluiste {len(excluded_pairs)} fila(s) a pedido tuyo.' if excluded_pairs else ''
    messages.success(
        request,
        f'Carga aplicada: {total_nuevas} registros creados, '
        f'{total_modificadas} modificados, {total_retiradas} retirados.'
        f'{excluidas_msg} Cada cambio quedó registrado en Auditoría.',
    )
    pasos_con_datos = [r for r in steps_results.values() if r['total'] > 0]
    return render(request, 'carga_masiva/confirmado.html', {
        'active_section': 'carga_masiva_subir',
        'steps_results': sorted(pasos_con_datos, key=lambda r: r['label']),
        'total_nuevas': total_nuevas,
        'total_retiradas': total_retiradas,
        'total_modificadas': total_modificadas,
    })
