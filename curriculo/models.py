from django.db import models
from django.core.exceptions import ValidationError
from decimal import Decimal


class CurriculoAsignatura(models.Model):
    id_asignatura = models.AutoField(primary_key=True, db_column='id_asignatura')
    codigo_asignatura = models.CharField(max_length=20, unique=True, db_column='codigo_asignatura')
    id_carrera = models.ForeignKey('catalogos.CatalogoCarrera', on_delete=models.RESTRICT, db_column='id_carrera')
    nombre_asignatura = models.CharField(max_length=200, db_column='nombre_asignatura')
    horas_semanales_asignatura = models.SmallIntegerField(default=0, db_column='horas_semanales_asignatura')
    nivel_semestre = models.SmallIntegerField(db_column='nivel_semestre')
    es_actividad = models.BooleanField(default=False, db_column='es_actividad')
    horas_aula = models.DecimalField(
        'Horas semanales en aula', max_digits=5, decimal_places=2,
        default=0, db_column='horas_aula',
    )
    horas_centro_computo = models.DecimalField(
        'Horas semanales en centro de cómputo',
        max_digits=5, decimal_places=2, default=0,
        db_column='horas_centro_computo',
    )

    class Meta:
        managed = False
        db_table = 'curriculo_asignatura'
        verbose_name = 'Asignatura (Currículo)'
        verbose_name_plural = 'M4 · Currículo · Asignaturas'

    def __str__(self):
        prefix = '[ACT] ' if self.es_actividad else ''
        return f'{prefix}{self.codigo_asignatura} - {self.nombre_asignatura}'

    def clean(self):
        super().clean()
        if self.es_actividad:
            self.horas_aula = Decimal(self.horas_semanales_asignatura or 0)
            self.horas_centro_computo = Decimal('0')
            return
        aula = self.horas_aula
        centro = self.horas_centro_computo
        total = Decimal(self.horas_semanales_asignatura or 0)
        if aula is None or centro is None or aula + centro != total:
            raise ValidationError(
                'Las horas de aula y centro de cómputo '
                'deben sumar las horas semanales de la asignatura.'
            )

    @property
    def porcentaje_aula(self):
        total = Decimal(self.horas_semanales_asignatura or 0)
        return round(self.horas_aula * 100 / total, 2) if total else Decimal('0')

    @property
    def porcentaje_centro_computo(self):
        total = Decimal(self.horas_semanales_asignatura or 0)
        return round(self.horas_centro_computo * 100 / total, 2) if total else Decimal('0')

    def save(self, *args, **kwargs):
        if (
            (self.horas_semanales_asignatura or 0) > 0
            and not self.horas_aula and not self.horas_centro_computo
        ):
            self.horas_aula = Decimal(self.horas_semanales_asignatura)
        super().save(*args, **kwargs)


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
