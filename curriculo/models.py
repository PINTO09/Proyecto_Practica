from django.db import models


class CurriculoAsignatura(models.Model):
    id_asignatura = models.AutoField(primary_key=True, db_column='id_asignatura')
    codigo_asignatura = models.CharField(max_length=20, unique=True, db_column='codigo_asignatura')
    id_carrera = models.ForeignKey('catalogos.CatalogoCarrera', on_delete=models.RESTRICT, db_column='id_carrera')
    nombre_asignatura = models.CharField(max_length=200, db_column='nombre_asignatura')
    horas_semanales_asignatura = models.SmallIntegerField(default=0, db_column='horas_semanales_asignatura')
    nivel_semestre = models.SmallIntegerField(db_column='nivel_semestre')

    class Meta:
        managed = False
        db_table = 'curriculo_asignatura'
        verbose_name = 'Asignatura (Currículo)'
        verbose_name_plural = 'M4 · Currículo · Asignaturas'

    def __str__(self):
        return f'{self.codigo_asignatura} - {self.nombre_asignatura}'


class CurriculoAsignaturaCampo(models.Model):
    id_asignatura_campo = models.AutoField(primary_key=True, db_column='id_asignatura_campo')
    id_asignatura = models.ForeignKey(CurriculoAsignatura, on_delete=models.CASCADE, db_column='id_asignatura')
    id_campo = models.ForeignKey('catalogos.CatalogoCampoConocimiento', on_delete=models.RESTRICT, db_column='id_campo')

    class Meta:
        managed = False
        db_table = 'curriculo_asignatura_campo'
        unique_together = (('id_asignatura', 'id_campo'),)
        verbose_name = 'Asignatura × Campo Conocimiento'
        verbose_name_plural = 'M4 · Currículo · Asignaturas por Campo'

    def __str__(self):
        return f'{self.id_asignatura} → Campo {self.id_campo}'


class RelacionPosgradoCampo(models.Model):
    id_posgrado_campo = models.AutoField(primary_key=True, db_column='id_posgrado_campo')
    id_posgrado = models.ForeignKey('catalogos.CatalogoTituloPosgrado', on_delete=models.CASCADE, db_column='id_posgrado')
    id_campo = models.ForeignKey('catalogos.CatalogoCampoConocimiento', on_delete=models.RESTRICT, db_column='id_campo')

    class Meta:
        managed = False
        db_table = 'relacion_posgrado_campo'
        unique_together = (('id_posgrado', 'id_campo'),)
        verbose_name = 'Posgrado × Campo Conocimiento'
        verbose_name_plural = 'M4 · Currículo · Posgrados por Campo'

    def __str__(self):
        return f'Posgrado {self.id_posgrado} → Campo {self.id_campo}'
