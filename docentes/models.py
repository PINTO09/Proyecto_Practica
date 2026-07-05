from django.db import models


class DocenteFcacc(models.Model):
    id_docente = models.BigAutoField(primary_key=True, db_column='id_docente')
    cedula_docente = models.CharField(max_length=13, unique=True, db_column='cedula_docente')
    id_tipo_docente = models.ForeignKey('catalogos.CatalogoTipoDocente', on_delete=models.RESTRICT, db_column='id_tipo_docente')
    id_modalidad = models.ForeignKey('catalogos.CatalogoModalidadContratacion', on_delete=models.RESTRICT, db_column='id_modalidad')
    id_dedicacion = models.ForeignKey('catalogos.CatalogoDedicacionHoraria', on_delete=models.RESTRICT, db_column='id_dedicacion')
    nombres_completos = models.CharField(max_length=200, db_column='nombres_completos')
    unidad_organica = models.CharField(max_length=100, null=True, blank=True, db_column='unidad_organica')
    correo_institucional = models.EmailField(max_length=100, null=True, blank=True, unique=True, db_column='correo_institucional')
    numero_celular = models.CharField(max_length=15, null=True, blank=True, db_column='numero_celular')
    tipo_sangre = models.CharField(max_length=5, null=True, blank=True, db_column='tipo_sangre')
    docente_activo = models.BooleanField(default=True, db_column='docente_activo')
    fecha_creacion_registro = models.DateTimeField(auto_now_add=True, db_column='fecha_creacion_registro')

    class Meta:
        managed = False
        db_table = 'docente'
        verbose_name = 'Docente (FCACC)'
        verbose_name_plural = 'M2 · Docentes'

    def __str__(self):
        return f'{self.nombres_completos} - {self.cedula_docente}'


class DocenteTituloAcademico(models.Model):
    id_titulo = models.BigAutoField(primary_key=True, db_column='id_titulo')
    id_docente = models.ForeignKey(DocenteFcacc, on_delete=models.CASCADE, db_column='id_docente')
    id_pais = models.ForeignKey('catalogos.CatalogoPais', on_delete=models.RESTRICT, db_column='id_pais')
    id_posgrado = models.ForeignKey('catalogos.CatalogoTituloPosgrado', on_delete=models.SET_NULL, null=True, blank=True, db_column='id_posgrado')
    nombre_titulo = models.CharField(max_length=200, db_column='nombre_titulo')
    nivel_titulo = models.SmallIntegerField(db_column='nivel_titulo')
    fecha_obtencion_titulo = models.DateField(null=True, blank=True, db_column='fecha_obtencion_titulo')
    numero_registro_titulo = models.CharField(max_length=50, null=True, blank=True, db_column='numero_registro_titulo')
    numero_registro_senescyt = models.CharField(max_length=50, null=True, blank=True, unique=True, db_column='numero_registro_senescyt')
    fecha_registro_senescyt = models.DateField(null=True, blank=True, db_column='fecha_registro_senescyt')

    class Meta:
        managed = False
        db_table = 'docente_titulo_academico'
        verbose_name = 'Título Académico (Docente)'
        verbose_name_plural = 'M2 · Docentes · Títulos Académicos'

    def __str__(self):
        return f'{self.nombre_titulo} - {self.id_docente}'


class DocenteCampoAfinidad(models.Model):
    id_docente_campo = models.BigAutoField(primary_key=True, db_column='id_docente_campo')
    id_docente = models.ForeignKey(DocenteFcacc, on_delete=models.CASCADE, db_column='id_docente')
    id_campo = models.ForeignKey('catalogos.CatalogoCampoConocimiento', on_delete=models.RESTRICT, db_column='id_campo')

    class Meta:
        managed = False
        db_table = 'docente_campo_afinidad'
        unique_together = (('id_docente', 'id_campo'),)
        verbose_name = 'Campo Afinidad (Docente)'
        verbose_name_plural = 'M2 · Docentes · Campos Afinidad'

    def __str__(self):
        return f'Docente {self.id_docente} → {self.id_campo}'


class DocenteAsignacionCarreraPeriodo(models.Model):
    id_asignacion_carrera_periodo = models.BigAutoField(primary_key=True, db_column='id_asignacion_carrera_periodo')
    id_docente = models.ForeignKey(DocenteFcacc, on_delete=models.CASCADE, db_column='id_docente')
    id_carrera = models.ForeignKey('catalogos.CatalogoCarrera', on_delete=models.RESTRICT, db_column='id_carrera')
    id_periodo = models.ForeignKey('catalogos.CatalogoPeriodoAcademico', on_delete=models.RESTRICT, db_column='id_periodo')
    id_licencia = models.ForeignKey('catalogos.CatalogoTipoLicencia', on_delete=models.RESTRICT, db_column='id_licencia')
    horas_otras_unidades_academicas = models.IntegerField(default=0, db_column='horas_otras_unidades_academicas')
    observacion_periodo = models.TextField(null=True, blank=True, db_column='observacion_periodo')

    class Meta:
        managed = False
        db_table = 'docente_asignacion_carrera_periodo'
        unique_together = (('id_docente', 'id_carrera', 'id_periodo'),)
        verbose_name = 'Asignación Docente → Carrera/Período'
        verbose_name_plural = 'M2 · Docentes · Asignaciones Carrera/Período'

    def __str__(self):
        return f'Docente {self.id_docente} → Carrera {self.id_carrera} · {self.id_periodo}'


class DocenteCursoCapacitacion(models.Model):
    id_curso = models.AutoField(primary_key=True, db_column='id_curso')
    id_tipo_curso = models.ForeignKey('catalogos.CatalogoTipoCursoCapacitacion', on_delete=models.RESTRICT, db_column='id_tipo_curso')
    nombre_curso_capacitacion = models.CharField(max_length=200, db_column='nombre_curso_capacitacion')
    fecha_inicio_curso = models.DateField(null=True, blank=True, db_column='fecha_inicio_curso')
    fecha_fin_curso = models.DateField(null=True, blank=True, db_column='fecha_fin_curso')
    horas_totales_curso = models.SmallIntegerField(default=0, db_column='horas_totales_curso')

    class Meta:
        managed = False
        db_table = 'docente_curso_capacitacion'
        verbose_name = 'Curso de Capacitación'
        verbose_name_plural = 'M2 · Docentes · Cursos Capacitación'

    def __str__(self):
        return self.nombre_curso_capacitacion


class DocenteParticipacionCurso(models.Model):
    id_participacion = models.BigAutoField(primary_key=True, db_column='id_participacion')
    id_docente = models.ForeignKey(DocenteFcacc, on_delete=models.CASCADE, db_column='id_docente')
    id_curso = models.ForeignKey(DocenteCursoCapacitacion, on_delete=models.RESTRICT, db_column='id_curso')
    fecha_participacion = models.DateField(db_column='fecha_participacion')

    class Meta:
        managed = False
        db_table = 'docente_participacion_curso'
        unique_together = (('id_docente', 'id_curso'),)
        verbose_name = 'Participación en Curso'
        verbose_name_plural = 'M2 · Docentes · Participaciones en Cursos'

    def __str__(self):
        return f'Docente {self.id_docente} → {self.id_curso}'


class DocentePublicacionAcademica(models.Model):
    id_publicacion = models.BigAutoField(primary_key=True, db_column='id_publicacion')
    id_docente = models.ForeignKey(DocenteFcacc, on_delete=models.CASCADE, db_column='id_docente')
    id_tipo_publicacion = models.ForeignKey('catalogos.CatalogoTipoPublicacion', on_delete=models.RESTRICT, db_column='id_tipo_publicacion')
    nombre_publicacion = models.CharField(max_length=200, db_column='nombre_publicacion')
    fecha_publicacion = models.DateField(null=True, blank=True, db_column='fecha_publicacion')
    detalle_publicacion = models.TextField(null=True, blank=True, db_column='detalle_publicacion')

    class Meta:
        managed = False
        db_table = 'docente_publicacion_academica'
        verbose_name = 'Publicación Académica (Docente)'
        verbose_name_plural = 'M2 · Docentes · Publicaciones Académicas'

    def __str__(self):
        return self.nombre_publicacion
