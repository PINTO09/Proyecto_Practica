from django.db import models


class SeguridadRol(models.Model):
    id_rol = models.AutoField(primary_key=True, db_column='id_rol')
    codigo_rol = models.CharField(max_length=15, unique=True, db_column='codigo_rol')
    nombre_rol = models.CharField(max_length=50, db_column='nombre_rol')
    descripcion_rol = models.CharField(max_length=200, null=True, blank=True, db_column='descripcion_rol')
    rol_activo = models.BooleanField(default=True, db_column='rol_activo')

    class Meta:
        managed = False
        db_table = 'seguridad_rol'
        verbose_name = 'Rol de Seguridad'
        verbose_name_plural = 'M3 · Seguridad · Roles'

    def __str__(self):
        return self.nombre_rol


class SeguridadUsuario(models.Model):
    id_usuario = models.AutoField(primary_key=True, db_column='id_usuario')
    id_docente = models.OneToOneField('docentes.DocenteFcacc', on_delete=models.SET_NULL, null=True, blank=True, db_column='id_docente')
    nombre_usuario = models.CharField(max_length=100, unique=True, db_column='nombre_usuario')
    contrasena_hash = models.CharField(max_length=255, db_column='contrasena_hash')
    usuario_activo = models.BooleanField(default=True, db_column='usuario_activo')
    fecha_ultimo_acceso = models.DateTimeField(null=True, blank=True, db_column='fecha_ultimo_acceso')
    fecha_creacion_usuario = models.DateTimeField(auto_now_add=True, db_column='fecha_creacion_usuario')

    class Meta:
        managed = False
        db_table = 'seguridad_usuario'
        verbose_name = 'Usuario del Sistema'
        verbose_name_plural = 'M3 · Seguridad · Usuarios'

    def __str__(self):
        return self.nombre_usuario


class SeguridadUsuarioRol(models.Model):
    id_usuario_rol = models.BigAutoField(primary_key=True, db_column='id_usuario_rol')
    id_usuario = models.ForeignKey(SeguridadUsuario, on_delete=models.CASCADE, db_column='id_usuario')
    id_rol = models.ForeignKey(SeguridadRol, on_delete=models.RESTRICT, db_column='id_rol')
    id_carrera = models.ForeignKey('catalogos.CatalogoCarrera', on_delete=models.RESTRICT, db_column='id_carrera')
    fecha_asignacion_rol = models.DateField(db_column='fecha_asignacion_rol')

    class Meta:
        managed = False
        db_table = 'seguridad_usuario_rol'
        unique_together = (('id_usuario', 'id_rol', 'id_carrera'),)
        verbose_name = 'Asignación Usuario × Rol × Carrera'
        verbose_name_plural = 'M3 · Seguridad · Usuarios Roles'

    def __str__(self):
        return f'{self.id_usuario} → {self.id_rol} ({self.id_carrera})'
