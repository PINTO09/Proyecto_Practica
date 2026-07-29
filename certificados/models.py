import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class FirmanteCertificado(models.Model):
    nombres_completos = models.CharField(max_length=200)
    cargo = models.CharField(max_length=200)
    activo = models.BooleanField(default=True)
    orden = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ('orden', 'nombres_completos')
        verbose_name = 'Firmante de certificado'
        verbose_name_plural = 'Firmantes de certificados'

    def __str__(self):
        return f'{self.nombres_completos} · {self.cargo}'


class CertificadoEmitido(models.Model):
    TIPOS = (
        ('DEDICACION', 'Historial de dedicación'),
        ('CATEDRAS', 'Historial de cátedras'),
        ('FUNCIONES', 'Funciones y comisiones'),
    )

    codigo = models.CharField(max_length=30, unique=True, editable=False)
    tipo = models.CharField(max_length=20, choices=TIPOS)
    docente = models.ForeignKey(
        'docentes.DocenteFcacc', on_delete=models.PROTECT,
        related_name='certificados_emitidos',
    )
    firmante = models.ForeignKey(
        FirmanteCertificado, on_delete=models.PROTECT,
        related_name='certificados_emitidos',
    )
    firmante_nombre = models.CharField(max_length=200)
    firmante_cargo = models.CharField(max_length=200)
    fecha_emision = models.DateField(default=timezone.localdate)
    ciudad = models.CharField(max_length=80, default='Manta')
    datos_certificados = models.JSONField()
    emitido_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='certificados_generados',
    )
    creado_el = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-creado_el',)
        verbose_name = 'Certificado emitido'
        verbose_name_plural = 'Certificados emitidos'

    def save(self, *args, **kwargs):
        if not self.codigo:
            self.codigo = f'CERT-{timezone.localdate():%Y}-{uuid.uuid4().hex[:8].upper()}'
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.codigo} · {self.docente}'
