from django.db import models


class AuditoriaRegistroCambios(models.Model):
    id_registro_auditoria = models.BigAutoField(primary_key=True, db_column='id_registro_auditoria')
    id_usuario = models.ForeignKey('seguridad.SeguridadUsuario', on_delete=models.SET_NULL, null=True, blank=True, db_column='id_usuario')
    nombre_tabla_afectada = models.CharField(max_length=60, db_column='nombre_tabla_afectada')
    id_registro_afectado = models.BigIntegerField(db_column='id_registro_afectado')
    tipo_accion = models.CharField(max_length=10, db_column='tipo_accion')
    valor_anterior = models.JSONField(null=True, blank=True, db_column='valor_anterior')
    valor_nuevo = models.JSONField(null=True, blank=True, db_column='valor_nuevo')
    fecha_hora_cambio = models.DateTimeField(auto_now_add=True, db_column='fecha_hora_cambio')
    direccion_ip_origen = models.CharField(max_length=45, null=True, blank=True, db_column='direccion_ip_origen')

    class Meta:
        managed = False
        db_table = 'auditoria_registro_cambios'
        verbose_name = 'Registro de Auditoría'
        verbose_name_plural = 'M6 · Auditoría · Registro de Cambios'

    def __str__(self):
        return f'{self.tipo_accion} {self.nombre_tabla_afectada} #{self.id_registro_afectado}'
