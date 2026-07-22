from django.db import models


class CatalogoCarrera(models.Model):
    id_carrera = models.AutoField(primary_key=True, db_column='id_carrera')
    codigo_carrera = models.CharField(max_length=20, unique=True, db_column='codigo_carrera')
    nombre_carrera = models.CharField(max_length=120, db_column='nombre_carrera')
    carrera_activa = models.BooleanField(default=True, db_column='carrera_activa')
    es_actividad = models.BooleanField(default=False, db_column='es_actividad')

    class Meta:
        managed = False
        db_table = 'catalogo_carrera'
        verbose_name = '[Catálogo] Carrera'
        verbose_name_plural = 'M1 · Catálogos · Carreras'

    def __str__(self):
        return f'{self.codigo_carrera} - {self.nombre_carrera}'


class CatalogoModalidadContratacion(models.Model):
    id_modalidad = models.AutoField(primary_key=True, db_column='id_modalidad')
    codigo_modalidad = models.CharField(max_length=15, unique=True, db_column='codigo_modalidad')
    nombre_modalidad = models.CharField(max_length=50, db_column='nombre_modalidad')

    class Meta:
        managed = False
        db_table = 'catalogo_modalidad_contratacion'
        verbose_name = '[Catálogo] Modalidad Contratación'
        verbose_name_plural = 'M1 · Catálogos · Modalidades Contratación'

    def __str__(self):
        return self.nombre_modalidad


class CatalogoDedicacionHoraria(models.Model):
    id_dedicacion = models.AutoField(primary_key=True, db_column='id_dedicacion')
    codigo_dedicacion = models.CharField(max_length=5, unique=True, db_column='codigo_dedicacion')
    nombre_dedicacion = models.CharField(max_length=30, db_column='nombre_dedicacion')

    class Meta:
        managed = False
        db_table = 'catalogo_dedicacion_horaria'
        verbose_name = '[Catálogo] Dedicación Horaria'
        verbose_name_plural = 'M1 · Catálogos · Dedicaciones Horarias'

    def __str__(self):
        return f'{self.codigo_dedicacion} - {self.nombre_dedicacion}'


class CatalogoTipoDocente(models.Model):
    id_tipo_docente = models.AutoField(primary_key=True, db_column='id_tipo_docente')
    codigo_tipo_docente = models.CharField(max_length=15, unique=True, db_column='codigo_tipo_docente')
    nombre_tipo_docente = models.CharField(max_length=30, db_column='nombre_tipo_docente')

    class Meta:
        managed = False
        db_table = 'catalogo_tipo_docente'
        verbose_name = '[Catálogo] Tipo Docente'
        verbose_name_plural = 'M1 · Catálogos · Tipos Docente'

    def __str__(self):
        return self.nombre_tipo_docente


class CatalogoTipoLicencia(models.Model):
    id_licencia = models.AutoField(primary_key=True, db_column='id_licencia')
    codigo_licencia = models.CharField(max_length=15, unique=True, db_column='codigo_licencia')
    nombre_licencia = models.CharField(max_length=50, db_column='nombre_licencia')

    class Meta:
        managed = False
        db_table = 'catalogo_tipo_licencia'
        verbose_name = '[Catálogo] Tipo Licencia'
        verbose_name_plural = 'M1 · Catálogos · Tipos Licencia'

    def __str__(self):
        return self.nombre_licencia


class CatalogoPais(models.Model):
    id_pais = models.AutoField(primary_key=True, db_column='id_pais')
    codigo_iso_pais = models.CharField(max_length=2, unique=True, db_column='codigo_iso_pais')
    nombre_pais = models.CharField(max_length=100, db_column='nombre_pais')
    nombre_nacionalidad = models.CharField(max_length=100, db_column='nombre_nacionalidad')

    class Meta:
        managed = False
        db_table = 'catalogo_pais'
        verbose_name = '[Catálogo] País'
        verbose_name_plural = 'M1 · Catálogos · Países'

    def __str__(self):
        return self.nombre_pais


class CatalogoTituloPosgrado(models.Model):
    id_posgrado = models.AutoField(primary_key=True, db_column='id_posgrado')
    codigo_posgrado = models.CharField(max_length=20, unique=True, db_column='codigo_posgrado')
    nombre_titulo_posgrado = models.CharField(max_length=200, db_column='nombre_titulo_posgrado')

    class Meta:
        managed = False
        db_table = 'catalogo_titulo_posgrado'
        verbose_name = '[Catálogo] Título Posgrado'
        verbose_name_plural = 'M1 · Catálogos · Títulos Posgrado'

    def __str__(self):
        return self.nombre_titulo_posgrado


class CatalogoCampoConocimiento(models.Model):
    id_campo = models.AutoField(primary_key=True, db_column='id_campo')
    codigo_campo = models.CharField(max_length=20, unique=True, db_column='codigo_campo')
    nombre_campo_conocimiento = models.CharField(max_length=100, db_column='nombre_campo_conocimiento')

    class Meta:
        managed = False
        db_table = 'catalogo_campo_conocimiento'
        verbose_name = '[Catálogo] Campo Conocimiento'
        verbose_name_plural = 'M1 · Catálogos · Campos Conocimiento'

    def __str__(self):
        return self.nombre_campo_conocimiento


class CatalogoGradoAfinidad(models.Model):
    id_grado_afinidad = models.AutoField(primary_key=True, db_column='id_grado_afinidad')
    codigo_grado_afinidad = models.CharField(max_length=10, unique=True, db_column='codigo_grado_afinidad')
    nombre_grado_afinidad = models.CharField(max_length=50, db_column='nombre_grado_afinidad')
    nivel_prioridad = models.SmallIntegerField(db_column='nivel_prioridad')

    class Meta:
        managed = False
        db_table = 'catalogo_grado_afinidad'
        verbose_name = '[Catálogo] Grado Afinidad'
        verbose_name_plural = 'M1 · Catálogos · Grados Afinidad'

    def __str__(self):
        return f'{self.nombre_grado_afinidad} (prioridad {self.nivel_prioridad})'


class CatalogoTipoPublicacion(models.Model):
    id_tipo_publicacion = models.AutoField(primary_key=True, db_column='id_tipo_publicacion')
    codigo_tipo_publicacion = models.CharField(max_length=15, unique=True, db_column='codigo_tipo_publicacion')
    nombre_tipo_publicacion = models.CharField(max_length=50, db_column='nombre_tipo_publicacion')

    class Meta:
        managed = False
        db_table = 'catalogo_tipo_publicacion'
        verbose_name = '[Catálogo] Tipo Publicación'
        verbose_name_plural = 'M1 · Catálogos · Tipos Publicación'

    def __str__(self):
        return self.nombre_tipo_publicacion


class CatalogoTipoCursoCapacitacion(models.Model):
    id_tipo_curso = models.AutoField(primary_key=True, db_column='id_tipo_curso')
    codigo_tipo_curso = models.CharField(max_length=15, unique=True, db_column='codigo_tipo_curso')
    nombre_tipo_curso = models.CharField(max_length=50, db_column='nombre_tipo_curso')

    class Meta:
        managed = False
        db_table = 'catalogo_tipo_curso_capacitacion'
        verbose_name = '[Catálogo] Tipo Curso Capacitación'
        verbose_name_plural = 'M1 · Catálogos · Tipos Curso Capacitación'

    def __str__(self):
        return self.nombre_tipo_curso


class CatalogoPeriodoAcademico(models.Model):
    id_periodo = models.AutoField(primary_key=True, db_column='id_periodo')
    codigo_periodo = models.CharField(max_length=10, unique=True, db_column='codigo_periodo')
    nombre_periodo = models.CharField(max_length=20, db_column='nombre_periodo')
    periodo_activo = models.BooleanField(default=False, db_column='periodo_activo')
    fecha_inicio_periodo = models.DateField(null=True, blank=True, db_column='fecha_inicio_periodo')
    fecha_fin_periodo = models.DateField(null=True, blank=True, db_column='fecha_fin_periodo')

    class Meta:
        managed = False
        db_table = 'catalogo_periodo_academico'
        verbose_name = '[Catálogo] Período Académico'
        verbose_name_plural = 'M1 · Catálogos · Períodos Académicos'

    def __str__(self):
        return self.nombre_periodo


class RelacionCarreraPeriodo(models.Model):
    id_carrera_periodo = models.AutoField(primary_key=True, db_column='id_carrera_periodo')
    id_carrera = models.ForeignKey(CatalogoCarrera, on_delete=models.RESTRICT, db_column='id_carrera')
    id_periodo = models.ForeignKey(CatalogoPeriodoAcademico, on_delete=models.RESTRICT, db_column='id_periodo')

    class Meta:
        managed = False
        db_table = 'relacion_carrera_periodo'
        unique_together = (('id_carrera', 'id_periodo'),)
        verbose_name = '[Relación] Carrera × Período'
        verbose_name_plural = 'M1 · Catálogos · Carreras por Período'

    def __str__(self):
        return f'{self.id_carrera} - {self.id_periodo}'


class LimiteHorario(models.Model):
    id_limite = models.AutoField(primary_key=True)
    id_modalidad = models.ForeignKey(CatalogoModalidadContratacion, on_delete=models.CASCADE, db_column='id_modalidad')
    horas_maximas = models.PositiveSmallIntegerField('Horas máximas de clase')
    horas_complementarias_maximas = models.PositiveSmallIntegerField('Horas complementarias máximas', default=0)
    activo = models.BooleanField(default=True)

    class Meta:
        managed = True
        db_table = 'limite_horario'
        verbose_name = 'Límite Horario'
        verbose_name_plural = 'M1 · Catálogos · Límites Horarios'
        unique_together = (('id_modalidad',),)

    def __str__(self):
        return f'{self.id_modalidad} — {self.horas_maximas}h'
