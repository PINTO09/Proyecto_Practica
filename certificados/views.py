from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import module_permission_required

from .forms import FirmanteCertificadoForm, GenerarCertificadoForm
from .models import CertificadoEmitido, FirmanteCertificado
from .services import build_certificate_snapshot


@module_permission_required('certificados', 'change')
def generar_certificado(request):
    form = GenerarCertificadoForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        snapshot = build_certificate_snapshot(
            form.cleaned_data['tipo'], form.cleaned_data['docente']
        )
        if not snapshot['filas']:
            form.add_error(
                'docente',
                'El docente no tiene información registrada para este tipo de certificado.',
            )
        else:
            signer = form.cleaned_data['firmante']
            with transaction.atomic():
                certificate = CertificadoEmitido.objects.create(
                    tipo=form.cleaned_data['tipo'],
                    docente=form.cleaned_data['docente'],
                    firmante=signer,
                    firmante_nombre=signer.nombres_completos,
                    firmante_cargo=signer.cargo,
                    fecha_emision=form.cleaned_data['fecha_emision'],
                    ciudad=form.cleaned_data['ciudad'],
                    datos_certificados=snapshot,
                    emitido_por=request.user,
                )
            messages.success(request, f'Certificado {certificate.codigo} generado correctamente.')
            return redirect('certificados:previsualizar', pk=certificate.pk)
    return render(request, 'certificados/generar.html', {
        'form': form, 'active_section': 'certificado_generar',
    })


@module_permission_required('certificados', 'view')
def emisiones(request):
    query = (request.GET.get('q') or '').strip()
    items = CertificadoEmitido.objects.select_related('docente', 'firmante', 'emitido_por')
    if query:
        from django.db.models import Q
        items = items.filter(
            Q(codigo__icontains=query) |
            Q(docente__cedula_docente__icontains=query) |
            Q(docente__nombres_completos__icontains=query)
        )
    return render(request, 'certificados/emisiones.html', {
        'items': items[:250], 'search_value': query,
        'active_section': 'certificado_emisiones',
    })


@module_permission_required('certificados', 'view')
def previsualizar(request, pk):
    certificate = get_object_or_404(
        CertificadoEmitido.objects.select_related('firmante', 'docente'), pk=pk
    )
    return render(request, 'certificados/documento.html', {
        'certificado': certificate,
        'datos': certificate.datos_certificados,
        'active_section': 'certificado_emisiones',
    })


@module_permission_required('certificados', 'change')
def firmantes(request, pk=None):
    instance = get_object_or_404(FirmanteCertificado, pk=pk) if pk else None
    form = FirmanteCertificadoForm(request.POST or None, request.FILES or None, instance=instance)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Firmante guardado correctamente.')
        return redirect('certificados:firmantes')
    return render(request, 'certificados/firmantes.html', {
        'form': form,
        'editing': instance,
        'items': FirmanteCertificado.objects.all(),
        'active_section': 'certificado_firmantes',
    })
