from django.core.exceptions import ValidationError
from django.db import models


class CatalogoActividadComplementaria(models.Model):
    TIPOS = (
        ('COMPLEMENTARIA', 'Actividad complementaria'),
        ('INVESTIGACION', 'Investigación'),
        ('GESTION', 'Gestión académica'),
        ('VINCULACION', 'Vinculación'),
    )

    id_actividad = models.AutoField(primary_key=True)
    codigo_actividad = models.CharField(max_length=20, unique=True)
    nombre_actividad = models.CharField(max_length=150)
    tipo_actividad = models.CharField(max_length=20, choices=TIPOS, default='COMPLEMENTARIA')
    actividad_activa = models.BooleanField(default=True)

    class Meta:
        db_table = 'catalogo_actividad_complementaria'
        verbose_name = 'Actividad complementaria'
        verbose_name_plural = 'M5 · Planificación · Actividades complementarias'
        ordering = ('tipo_actividad', 'nombre_actividad')

    def __str__(self):
        return f'{self.codigo_actividad} - {self.nombre_actividad}'


class PlanificacionActividadDocente(models.Model):
    id_actividad_docente = models.BigAutoField(primary_key=True)
    id_docente = models.ForeignKey('docentes.DocenteFcacc', on_delete=models.RESTRICT, db_column='id_docente')
    id_periodo = models.ForeignKey('catalogos.CatalogoPeriodoAcademico', on_delete=models.RESTRICT, db_column='id_periodo')
    id_actividad = models.ForeignKey(CatalogoActividadComplementaria, on_delete=models.RESTRICT, db_column='id_actividad')
    horas_asignadas = models.PositiveSmallIntegerField(default=0)
    observaciones = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'planificacion_actividad_docente'
        verbose_name = 'Actividad asignada a docente'
        verbose_name_plural = 'M5 · Planificación · Actividades de docentes'
        constraints = [
            models.UniqueConstraint(
                fields=('id_docente', 'id_periodo', 'id_actividad'),
                name='uk_actividad_docente_periodo',
            ),
            models.CheckConstraint(
                check=models.Q(horas_asignadas__gt=0),
                name='chk_actividad_horas_positivas',
            ),
        ]

    def __str__(self):
        return f'{self.id_docente} - {self.id_actividad} ({self.horas_asignadas}h)'


    def clean(self):
        from .services import assert_periodo_editable
        assert_periodo_editable(self.id_periodo)


class PlanificacionDemandaAcademica(models.Model):
    id_demanda = models.BigAutoField(primary_key=True, db_column='id_demanda')
    id_asignatura = models.ForeignKey('curriculo.CurriculoAsignatura', on_delete=models.RESTRICT, db_column='id_asignatura')
    id_carrera = models.ForeignKey('catalogos.CatalogoCarrera', on_delete=models.RESTRICT, db_column='id_carrera')
    id_periodo = models.ForeignKey('catalogos.CatalogoPeriodoAcademico', on_delete=models.RESTRICT, db_column='id_periodo')
    proyeccion_estudiantes = models.IntegerField(default=0, db_column='proyeccion_estudiantes')
    numero_paralelos = models.SmallIntegerField(default=1, db_column='numero_paralelos')

    class Meta:
        managed = False
        db_table = 'planificacion_demanda_academica'
        unique_together = (('id_asignatura', 'id_carrera', 'id_periodo'),)
        verbose_name = 'Demanda Académica'
        verbose_name_plural = 'M5 · Planificación · Demanda Académica'

    def __str__(self):
        return f'{self.id_asignatura} - {self.id_periodo}'


    def clean(self):
        from .services import assert_periodo_editable
        assert_periodo_editable(self.id_periodo)


class PlanificacionAsignacionDocente(models.Model):
    id_asignacion = models.BigAutoField(primary_key=True, db_column='id_asignacion')
    id_docente = models.ForeignKey('docentes.DocenteFcacc', on_delete=models.RESTRICT, db_column='id_docente')
    id_asignatura = models.ForeignKey('curriculo.CurriculoAsignatura', on_delete=models.RESTRICT, db_column='id_asignatura')
    id_carrera = models.ForeignKey('catalogos.CatalogoCarrera', on_delete=models.RESTRICT, db_column='id_carrera')
    id_periodo = models.ForeignKey('catalogos.CatalogoPeriodoAcademico', on_delete=models.RESTRICT, db_column='id_periodo')
    id_campo = models.ForeignKey('catalogos.CatalogoCampoConocimiento', on_delete=models.RESTRICT, db_column='id_campo')
    nivel_semestre_asignado = models.SmallIntegerField(db_column='nivel_semestre_asignado')
    paralelo_asignado = models.CharField(max_length=3, db_column='paralelo_asignado')
    horas_clase = models.SmallIntegerField(default=0, db_column='horas_clase')
    horas_complementarias = models.SmallIntegerField(default=0, db_column='horas_complementarias')
    semanas_planificadas = models.PositiveSmallIntegerField(default=16, db_column='semanas_planificadas')
    comision_servicio = models.CharField(max_length=100, null=True, blank=True, db_column='comision_servicio')

    class Meta:
        managed = False
        db_table = 'planificacion_asignacion_docente'
        verbose_name = 'Asignación Docente (Planificación)'
        verbose_name_plural = 'M5 · Planificación · Asignación Docente'

    def __str__(self):
        return f'Docente {self.id_docente} → {self.id_asignatura} ({self.paralelo_asignado})'


    def clean(self):
        from .services import assert_periodo_editable
        assert_periodo_editable(self.id_periodo)

    @property
    def horas_clase_periodo(self):
        return (self.horas_clase or 0) * (self.semanas_planificadas or 0)


class PlanificacionRepartoHoras(models.Model):
    id_reparto = models.BigAutoField(primary_key=True, db_column='id_reparto')
    id_docente = models.ForeignKey('docentes.DocenteFcacc', on_delete=models.RESTRICT, db_column='id_docente')
    id_asignatura = models.ForeignKey('curriculo.CurriculoAsignatura', on_delete=models.RESTRICT, db_column='id_asignatura')
    id_periodo = models.ForeignKey('catalogos.CatalogoPeriodoAcademico', on_delete=models.RESTRICT, db_column='id_periodo')
    nivel_paralelo = models.CharField(max_length=5, db_column='nivel_paralelo')
    horas_presenciales_asignadas = models.SmallIntegerField(default=0, db_column='horas_presenciales_asignadas')

    class Meta:
        managed = False
        db_table = 'planificacion_reparto_horas'
        unique_together = (('id_docente', 'id_asignatura', 'id_periodo', 'nivel_paralelo'),)
        verbose_name = 'Reparto de Horas'
        verbose_name_plural = 'M5 · Planificación · Reparto de Horas'

    def __str__(self):
        return f'Docente {self.id_docente} - {self.id_asignatura} ({self.nivel_paralelo})'


    def clean(self):
        from .services import assert_periodo_editable
        assert_periodo_editable(self.id_periodo)


class PlanificacionMatrizF4(models.Model):
    id_registro_f4 = models.BigAutoField(primary_key=True, db_column='id_registro_f4')
    id_docente = models.ForeignKey('docentes.DocenteFcacc', on_delete=models.RESTRICT, db_column='id_docente')
    id_carrera = models.ForeignKey('catalogos.CatalogoCarrera', on_delete=models.RESTRICT, db_column='id_carrera')
    id_periodo = models.ForeignKey('catalogos.CatalogoPeriodoAcademico', on_delete=models.RESTRICT, db_column='id_periodo')
    id_grado_afinidad = models.ForeignKey('catalogos.CatalogoGradoAfinidad', on_delete=models.RESTRICT, db_column='id_grado_afinidad')
    tipo_actividad = models.CharField(max_length=100, db_column='tipo_actividad')
    nombre_asignatura_actividad = models.CharField(max_length=200, null=True, blank=True, db_column='nombre_asignatura_actividad')
    nivel_semestre_actividad = models.CharField(max_length=20, null=True, blank=True, db_column='nivel_semestre_actividad')
    horas_actividad = models.SmallIntegerField(default=0, db_column='horas_actividad')
    numero_paralelos_actividad = models.SmallIntegerField(default=1, db_column='numero_paralelos_actividad')
    observaciones = models.TextField(null=True, blank=True, db_column='observaciones')

    class Meta:
        managed = False
        db_table = 'planificacion_matriz_f4'
        verbose_name = 'Matriz F4'
        verbose_name_plural = 'M5 · Planificación · Matriz F4'

    def __str__(self):
        return f'F4 · Docente {self.id_docente} - {self.tipo_actividad}'


    def clean(self):
        from .services import assert_periodo_editable
        assert_periodo_editable(self.id_periodo)


class PlanificacionAulaHorario(models.Model):
    DIAS = (
        (1, 'Lunes'), (2, 'Martes'), (3, 'Miércoles'),
        (4, 'Jueves'), (5, 'Viernes'), (6, 'Sábado'),
    )

    id_horario = models.AutoField(primary_key=True, db_column='id_horario')
    id_periodo = models.ForeignKey('catalogos.CatalogoPeriodoAcademico', on_delete=models.RESTRICT, db_column='id_periodo')
    nombre_aula = models.CharField(max_length=50, db_column='nombre_aula')
    turno_horario = models.CharField(max_length=10, db_column='turno_horario')
    nivel_asignado = models.CharField(max_length=10, null=True, blank=True, db_column='nivel_asignado')
    id_asignacion = models.ForeignKey(
        PlanificacionAsignacionDocente, on_delete=models.RESTRICT,
        db_column='id_asignacion', null=True, blank=True,
    )
    dia_semana = models.PositiveSmallIntegerField(choices=DIAS, default=1, db_column='dia_semana')
    hora_inicio = models.TimeField(null=True, blank=True, db_column='hora_inicio')
    hora_fin = models.TimeField(null=True, blank=True, db_column='hora_fin')

    class Meta:
        managed = False
        db_table = 'planificacion_aula_horario'
        unique_together = (('id_periodo', 'nombre_aula', 'dia_semana', 'hora_inicio'),)
        verbose_name = 'Aula / Horario'
        verbose_name_plural = 'M5 · Planificación · Aulas y Horarios'

    def __str__(self):
        return f'{self.nombre_aula} - {self.turno_horario} ({self.id_periodo})'

    def clean(self):
        from .services import assert_periodo_editable
        assert_periodo_editable(self.id_periodo)
        if not self.hora_inicio or not self.hora_fin:
            raise ValidationError('Debe indicar la hora de inicio y finalización.')
        if self.hora_inicio >= self.hora_fin:
            raise ValidationError({'hora_fin': 'La hora final debe ser posterior a la inicial.'})
        if self.id_asignacion_id and self.id_asignacion.id_periodo_id != self.id_periodo_id:
            raise ValidationError({'id_asignacion': 'La asignación pertenece a otro período.'})
        overlaps = PlanificacionAulaHorario.objects.filter(
            id_periodo=self.id_periodo,
            dia_semana=self.dia_semana,
            hora_inicio__lt=self.hora_fin,
            hora_fin__gt=self.hora_inicio,
        )
        if self.pk:
            overlaps = overlaps.exclude(pk=self.pk)
        if overlaps.filter(nombre_aula__iexact=self.nombre_aula).exists():
            raise ValidationError('El aula ya está ocupada en ese día y rango horario.')
        if self.id_asignacion_id and overlaps.filter(
            id_asignacion__id_docente_id=self.id_asignacion.id_docente_id,
        ).exists():
            raise ValidationError('El docente ya tiene otra clase en ese rango horario.')


class PlanificacionCapacidadEspecial(models.Model):
    id_capacidad = models.BigAutoField(primary_key=True, db_column='id_capacidad')
    id_periodo = models.ForeignKey('catalogos.CatalogoPeriodoAcademico', on_delete=models.RESTRICT, db_column='id_periodo')
    id_carrera = models.ForeignKey('catalogos.CatalogoCarrera', on_delete=models.RESTRICT, db_column='id_carrera')
    estudiante_nombre = models.CharField(max_length=200, db_column='estudiante_nombre')
    condicion = models.CharField(max_length=200, db_column='condicion', null=True, blank=True)
    informes_adjuntos = models.TextField(null=True, blank=True, db_column='informes_adjuntos')
    nivel_asignado = models.CharField(max_length=10, null=True, blank=True, db_column='nivel_asignado')
    paralelo_asignado = models.CharField(max_length=20, null=True, blank=True, db_column='paralelo_asignado')

    class Meta:
        managed = False
        db_table = 'planificacion_capacidad_especial'
        verbose_name = 'Capacidad Especial'
        verbose_name_plural = 'M5 · Planificación · Capacidades Especiales'

    def __str__(self):
        return f'{self.estudiante_nombre} - {self.condicion}'


class CargaHistorial(models.Model):
    id_carga = models.BigAutoField(primary_key=True, db_column='id_carga')
    fecha_carga = models.DateTimeField(auto_now_add=True, db_column='fecha_carga')
    tipo_carga = models.CharField(max_length=50, db_column='tipo_carga')
    archivo_origen = models.CharField(max_length=255, db_column='archivo_origen')
    total_registros = models.IntegerField(default=0, db_column='total_registros')
    registros_creados = models.IntegerField(default=0, db_column='registros_creados')
    registros_actualizados = models.IntegerField(default=0, db_column='registros_actualizados')
    registros_omitidos = models.IntegerField(default=0, db_column='registros_omitidos')
    detalle_errores = models.TextField(null=True, blank=True, db_column='detalle_errores')
    estado = models.CharField(max_length=20, default='COMPLETADO', db_column='estado')

    class Meta:
        db_table = 'carga_historial'
        verbose_name = 'Historial de Carga'
        verbose_name_plural = 'M8 · Cargas de Datos'

    def __str__(self):
        return f'{self.tipo_carga} - {self.fecha_carga}'
