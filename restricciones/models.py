from django.db import models


class Limitacion(models.Model):
    id_limitacion = models.AutoField(primary_key=True, db_column='id_limitacion')
    codigo_limitacion = models.CharField(max_length=15, unique=True, db_column='codigo_limitacion')
    nombre_limitacion = models.CharField(max_length=150, db_column='nombre_limitacion')
    hora_minima = models.IntegerField(db_column='hora_minima')
    hora_maxima = models.IntegerField(db_column='hora_maxima')

    class Meta:
        managed = False
        db_table = 'limitacion'
        verbose_name = 'Límite / Regla'
        verbose_name_plural = 'M7 · Limitaciones · Reglas'

    def __str__(self):
        return f'{self.nombre_limitacion} ({self.hora_minima}-{self.hora_maxima})'


class HistorialLimitacion(models.Model):
    id_historial = models.BigAutoField(primary_key=True, db_column='id_historial')
    id_docente = models.ForeignKey('docentes.DocenteFcacc', on_delete=models.RESTRICT, db_column='id_docente')
    id_limitacion = models.ForeignKey(Limitacion, on_delete=models.RESTRICT, db_column='id_limitacion')
    fecha_inicio_vigencia = models.DateField(db_column='fecha_inicio_vigencia')
    fecha_fin_vigencia = models.DateField(db_column='fecha_fin_vigencia')

    class Meta:
        managed = False
        db_table = 'historial_limitacion'
        verbose_name = 'Historial de Limitación'
        verbose_name_plural = 'M7 · Limitaciones · Historial'

    def __str__(self):
        return f'Docente {self.id_docente} → {self.id_limitacion} ({self.fecha_inicio_vigencia} - {self.fecha_fin_vigencia})'


class Cabecera(models.Model):
    id_cabecera = models.AutoField(primary_key=True, db_column='id_cabecera')
    descripcion_periodo = models.CharField(max_length=100, db_column='descripcion_periodo')

    class Meta:
        managed = False
        db_table = 'cabecera'
        verbose_name = 'Cabecera de Planificación'
        verbose_name_plural = 'M7 · Planif. Complementaria · Cabeceras'

    def __str__(self):
        return self.descripcion_periodo


class Cuerpo(models.Model):
    id_cuerpo = models.BigAutoField(primary_key=True, db_column='id_cuerpo')
    id_cabecera = models.ForeignKey(Cabecera, on_delete=models.CASCADE, db_column='id_cabecera')
    id_docente = models.ForeignKey('docentes.DocenteFcacc', on_delete=models.RESTRICT, db_column='id_docente')
    horas = models.IntegerField(db_column='horas')

    class Meta:
        managed = False
        db_table = 'cuerpo'
        verbose_name = 'Detalle de Horas (Cuerpo)'
        verbose_name_plural = 'M7 · Planif. Complementaria · Detalle Horas'

    def __str__(self):
        return f'Cabecera {self.id_cabecera} - Docente {self.id_docente}: {self.horas}h'
