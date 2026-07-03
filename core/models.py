from django.db import models
from django.core.validators import RegexValidator
from django.contrib.auth.models import AbstractUser, BaseUserManager

validate_10_digits = RegexValidator(
    r'^\d{10}$',
    'Este campo debe tener exactamente 10 dígitos numéricos.'
)


# =============================================================================
#  MODELOS EXISTENTES DE LA APP (gestionados por Django)
#  Se mantienen para no romper vistas, formularios y autenticación existentes
# =============================================================================

class UsuarioManager(BaseUserManager):
    def create_user(self, cedula, password=None, **extra_fields):
        if not cedula:
            raise ValueError('La cédula es obligatoria')
        user = self.model(cedula=cedula, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, cedula, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(cedula, password, **extra_fields)


class Usuario(AbstractUser):
    username = None
    cedula = models.CharField('Cédula', max_length=10, unique=True, validators=[validate_10_digits])
    USERNAME_FIELD = 'cedula'
    REQUIRED_FIELDS = []

    objects = UsuarioManager()

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def __str__(self):
        return self.cedula


class Pais(models.Model):
    nombre_pais = models.CharField('Nombre del país', max_length=100)
    nacionalidad = models.CharField('Nacionalidad', max_length=100)

    class Meta:
        verbose_name = 'País'
        verbose_name_plural = 'Países'

    def __str__(self):
        return self.nombre_pais


class Docente(models.Model):
    cedula = models.CharField('Cédula', max_length=10, unique=True, validators=[validate_10_digits])
    apellidos_nombres = models.CharField('Apellidos y nombres', max_length=255)
    telefono = models.CharField('Teléfono', max_length=10, blank=True, null=True, validators=[validate_10_digits])
    correo = models.EmailField('Correo', blank=True, null=True)

    class Meta:
        verbose_name = 'Docente'
        verbose_name_plural = 'Docentes'

    def __str__(self):
        return f'{self.apellidos_nombres} - {self.cedula}'


class Carrera(models.Model):
    nombre_carrera = models.CharField('Nombre de la carrera', max_length=200)

    class Meta:
        verbose_name = 'Carrera'
        verbose_name_plural = 'Carreras'

    def __str__(self):
        return self.nombre_carrera


class Dedicacion(models.Model):
    nombre_dedicacion = models.CharField('Nombre de dedicación', max_length=100)

    class Meta:
        verbose_name = 'Dedicación'
        verbose_name_plural = 'Dedicaciones'

    def __str__(self):
        return self.nombre_dedicacion


class Licencia(models.Model):
    nombre_licencia = models.CharField('Nombre de licencia', max_length=100)

    class Meta:
        verbose_name = 'Licencia'
        verbose_name_plural = 'Licencias'

    def __str__(self):
        return self.nombre_licencia


class Modalidad(models.Model):
    nombre_modalidad = models.CharField('Nombre de modalidad', max_length=100)

    class Meta:
        verbose_name = 'Modalidad'
        verbose_name_plural = 'Modalidades'

    def __str__(self):
        return self.nombre_modalidad


class Periodo(models.Model):
    id_carrera = models.ForeignKey(Carrera, on_delete=models.CASCADE, verbose_name='Carrera')
    nombre_periodo = models.CharField('Nombre del periodo', max_length=100)

    class Meta:
        verbose_name = 'Periodo'
        verbose_name_plural = 'Periodos'

    def __str__(self):
        return f'{self.nombre_periodo} - {self.id_carrera}'


class TipoPublicacion(models.Model):
    nombre = models.CharField('Nombre', max_length=100)

    class Meta:
        verbose_name = 'Tipo de publicación'
        verbose_name_plural = 'Tipos de publicación'

    def __str__(self):
        return self.nombre


class Curso(models.Model):
    nombre_curso = models.CharField('Nombre del curso', max_length=200)
    id_tipo_curso = models.ForeignKey(
        TipoPublicacion, on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name='Tipo de curso'
    )
    fecha_inicio = models.DateField('Fecha de inicio', blank=True, null=True)
    fecha_final = models.DateField('Fecha final', blank=True, null=True)
    hora_total = models.IntegerField('Horas totales', blank=True, null=True)

    class Meta:
        verbose_name = 'Curso'
        verbose_name_plural = 'Cursos'

    def __str__(self):
        return self.nombre_curso


class Titulo(models.Model):
    id_cedula = models.ForeignKey(Docente, on_delete=models.CASCADE, verbose_name='Docente')
    nombre = models.CharField('Nombre del título', max_length=255)
    id_pais = models.ForeignKey(
        Pais, on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name='País'
    )
    fecha_titulo = models.DateField('Fecha del título', blank=True, null=True)
    registro_titulo = models.CharField(
        'Registro del título', max_length=100, blank=True, null=True
    )
    fecha_senecyt = models.DateField('Fecha Senescyt', blank=True, null=True)
    registro_senecyt = models.CharField(
        'Registro Senescyt', max_length=100, blank=True, null=True
    )

    class Meta:
        verbose_name = 'Título'
        verbose_name_plural = 'Títulos'

    def __str__(self):
        return f'{self.nombre} - {self.id_cedula}'


class Publicacion(models.Model):
    nombre_publicacion = models.CharField('Nombre de la publicación', max_length=255)
    id_tipo_publicacion = models.ForeignKey(
        TipoPublicacion, on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name='Tipo de publicación'
    )
    fecha = models.DateField('Fecha', blank=True, null=True)
    codigo = models.CharField('Código', max_length=100, blank=True, null=True)
    funcion = models.CharField('Función', max_length=255, blank=True, null=True)
    id_docente = models.ForeignKey(
        Docente, on_delete=models.CASCADE, verbose_name='Docente'
    )

    class Meta:
        verbose_name = 'Publicación'
        verbose_name_plural = 'Publicaciones'

    def __str__(self):
        return self.nombre_publicacion


class DocenteTransaccional(models.Model):
    id_docente = models.ForeignKey(Docente, on_delete=models.CASCADE, verbose_name='Docente')
    id_modalidad = models.ForeignKey(
        Modalidad, on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name='Modalidad'
    )
    id_dedicacion = models.ForeignKey(
        Dedicacion, on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name='Dedicación'
    )
    id_carrera = models.ForeignKey(
        Carrera, on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name='Carrera'
    )
    id_periodo = models.ForeignKey(
        Periodo, on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name='Periodo'
    )
    id_licencia = models.ForeignKey(
        Licencia, on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name='Licencia'
    )
    observacion = models.TextField('Observación', blank=True, null=True)
    adj_archivo = models.FileField(
        'Archivo adjunto', upload_to='documentos/', blank=True, null=True
    )

    class Meta:
        verbose_name = 'Docente Transaccional'
        verbose_name_plural = 'Docentes Transaccionales'

    def __str__(self):
        return f'{self.id_docente} - {self.id_periodo}'


class CursoDocente(models.Model):
    id_curso = models.ForeignKey(Curso, on_delete=models.CASCADE, verbose_name='Curso')
    id_docente = models.ForeignKey(Docente, on_delete=models.CASCADE, verbose_name='Docente')

    class Meta:
        verbose_name = 'Curso - Docente'
        verbose_name_plural = 'Cursos - Docentes'
        unique_together = ('id_curso', 'id_docente')

    def __str__(self):
        return f'{self.id_curso} - {self.id_docente}'


# =============================================================================
#  MÓDULO 1 · CATÁLOGOS BASE (no gestionados — espejo de PostgreSQL)
# =============================================================================

class CatalogoCarrera(models.Model):
    id_carrera = models.AutoField(primary_key=True, db_column='ID_CARRERA')
    codigo_carrera = models.CharField(max_length=20, unique=True, db_column='CODIGO_CARRERA')
    nombre_carrera = models.CharField(max_length=120, db_column='NOMBRE_CARRERA')
    carrera_activa = models.BooleanField(default=True, db_column='CARRERA_ACTIVA')

    class Meta:
        managed = False
        db_table = 'catalogo_carrera'
        verbose_name = '[Catálogo] Carrera'
        verbose_name_plural = 'M1 · Catálogos · Carreras'

    def __str__(self):
        return f'{self.codigo_carrera} - {self.nombre_carrera}'


class CatalogoModalidadContratacion(models.Model):
    id_modalidad = models.AutoField(primary_key=True, db_column='ID_MODALIDAD')
    codigo_modalidad = models.CharField(max_length=15, unique=True, db_column='CODIGO_MODALIDAD')
    nombre_modalidad = models.CharField(max_length=50, db_column='NOMBRE_MODALIDAD')

    class Meta:
        managed = False
        db_table = 'catalogo_modalidad_contratacion'
        verbose_name = '[Catálogo] Modalidad Contratación'
        verbose_name_plural = 'M1 · Catálogos · Modalidades Contratación'

    def __str__(self):
        return self.nombre_modalidad


class CatalogoDedicacionHoraria(models.Model):
    id_dedicacion = models.AutoField(primary_key=True, db_column='ID_DEDICACION')
    codigo_dedicacion = models.CharField(max_length=5, unique=True, db_column='CODIGO_DEDICACION')
    nombre_dedicacion = models.CharField(max_length=30, db_column='NOMBRE_DEDICACION')

    class Meta:
        managed = False
        db_table = 'catalogo_dedicacion_horaria'
        verbose_name = '[Catálogo] Dedicación Horaria'
        verbose_name_plural = 'M1 · Catálogos · Dedicaciones Horarias'

    def __str__(self):
        return f'{self.codigo_dedicacion} - {self.nombre_dedicacion}'


class CatalogoTipoDocente(models.Model):
    id_tipo_docente = models.AutoField(primary_key=True, db_column='ID_TIPO_DOCENTE')
    codigo_tipo_docente = models.CharField(max_length=15, unique=True, db_column='CODIGO_TIPO_DOCENTE')
    nombre_tipo_docente = models.CharField(max_length=30, db_column='NOMBRE_TIPO_DOCENTE')

    class Meta:
        managed = False
        db_table = 'catalogo_tipo_docente'
        verbose_name = '[Catálogo] Tipo Docente'
        verbose_name_plural = 'M1 · Catálogos · Tipos Docente'

    def __str__(self):
        return self.nombre_tipo_docente


class CatalogoTipoLicencia(models.Model):
    id_licencia = models.AutoField(primary_key=True, db_column='ID_LICENCIA')
    codigo_licencia = models.CharField(max_length=15, unique=True, db_column='CODIGO_LICENCIA')
    nombre_licencia = models.CharField(max_length=50, db_column='NOMBRE_LICENCIA')

    class Meta:
        managed = False
        db_table = 'catalogo_tipo_licencia'
        verbose_name = '[Catálogo] Tipo Licencia'
        verbose_name_plural = 'M1 · Catálogos · Tipos Licencia'

    def __str__(self):
        return self.nombre_licencia


class CatalogoPais(models.Model):
    id_pais = models.AutoField(primary_key=True, db_column='ID_PAIS')
    codigo_iso_pais = models.CharField(max_length=2, unique=True, db_column='CODIGO_ISO_PAIS')
    nombre_pais = models.CharField(max_length=100, db_column='NOMBRE_PAIS')
    nombre_nacionalidad = models.CharField(max_length=100, db_column='NOMBRE_NACIONALIDAD')

    class Meta:
        managed = False
        db_table = 'catalogo_pais'
        verbose_name = '[Catálogo] País'
        verbose_name_plural = 'M1 · Catálogos · Países'

    def __str__(self):
        return self.nombre_pais


class CatalogoTituloPosgrado(models.Model):
    id_posgrado = models.AutoField(primary_key=True, db_column='ID_POSGRADO')
    codigo_posgrado = models.CharField(max_length=20, unique=True, db_column='CODIGO_POSGRADO')
    nombre_titulo_posgrado = models.CharField(max_length=200, db_column='NOMBRE_TITULO_POSGRADO')

    class Meta:
        managed = False
        db_table = 'catalogo_titulo_posgrado'
        verbose_name = '[Catálogo] Título Posgrado'
        verbose_name_plural = 'M1 · Catálogos · Títulos Posgrado'

    def __str__(self):
        return self.nombre_titulo_posgrado


class CatalogoCampoConocimiento(models.Model):
    id_campo = models.AutoField(primary_key=True, db_column='ID_CAMPO')
    codigo_campo = models.CharField(max_length=20, unique=True, db_column='CODIGO_CAMPO')
    nombre_campo_conocimiento = models.CharField(max_length=100, db_column='NOMBRE_CAMPO_CONOCIMIENTO')

    class Meta:
        managed = False
        db_table = 'catalogo_campo_conocimiento'
        verbose_name = '[Catálogo] Campo Conocimiento'
        verbose_name_plural = 'M1 · Catálogos · Campos Conocimiento'

    def __str__(self):
        return self.nombre_campo_conocimiento


class CatalogoGradoAfinidad(models.Model):
    id_grado_afinidad = models.AutoField(primary_key=True, db_column='ID_GRADO_AFINIDAD')
    codigo_grado_afinidad = models.CharField(max_length=10, unique=True, db_column='CODIGO_GRADO_AFINIDAD')
    nombre_grado_afinidad = models.CharField(max_length=50, db_column='NOMBRE_GRADO_AFINIDAD')
    nivel_prioridad = models.SmallIntegerField(db_column='NIVEL_PRIORIDAD')

    class Meta:
        managed = False
        db_table = 'catalogo_grado_afinidad'
        verbose_name = '[Catálogo] Grado Afinidad'
        verbose_name_plural = 'M1 · Catálogos · Grados Afinidad'

    def __str__(self):
        return f'{self.nombre_grado_afinidad} (prioridad {self.nivel_prioridad})'


class CatalogoTipoPublicacion(models.Model):
    id_tipo_publicacion = models.AutoField(primary_key=True, db_column='ID_TIPO_PUBLICACION')
    codigo_tipo_publicacion = models.CharField(max_length=15, unique=True, db_column='CODIGO_TIPO_PUBLICACION')
    nombre_tipo_publicacion = models.CharField(max_length=50, db_column='NOMBRE_TIPO_PUBLICACION')

    class Meta:
        managed = False
        db_table = 'catalogo_tipo_publicacion'
        verbose_name = '[Catálogo] Tipo Publicación'
        verbose_name_plural = 'M1 · Catálogos · Tipos Publicación'

    def __str__(self):
        return self.nombre_tipo_publicacion


class CatalogoTipoCursoCapacitacion(models.Model):
    id_tipo_curso = models.AutoField(primary_key=True, db_column='ID_TIPO_CURSO')
    codigo_tipo_curso = models.CharField(max_length=15, unique=True, db_column='CODIGO_TIPO_CURSO')
    nombre_tipo_curso = models.CharField(max_length=50, db_column='NOMBRE_TIPO_CURSO')

    class Meta:
        managed = False
        db_table = 'catalogo_tipo_curso_capacitacion'
        verbose_name = '[Catálogo] Tipo Curso Capacitación'
        verbose_name_plural = 'M1 · Catálogos · Tipos Curso Capacitación'

    def __str__(self):
        return self.nombre_tipo_curso


class CatalogoPeriodoAcademico(models.Model):
    id_periodo = models.AutoField(primary_key=True, db_column='ID_PERIODO')
    codigo_periodo = models.CharField(max_length=10, unique=True, db_column='CODIGO_PERIODO')
    nombre_periodo = models.CharField(max_length=20, db_column='NOMBRE_PERIODO')
    periodo_activo = models.BooleanField(default=False, db_column='PERIODO_ACTIVO')
    fecha_inicio_periodo = models.DateField(null=True, blank=True, db_column='FECHA_INICIO_PERIODO')
    fecha_fin_periodo = models.DateField(null=True, blank=True, db_column='FECHA_FIN_PERIODO')

    class Meta:
        managed = False
        db_table = 'catalogo_periodo_academico'
        verbose_name = '[Catálogo] Período Académico'
        verbose_name_plural = 'M1 · Catálogos · Períodos Académicos'

    def __str__(self):
        return self.nombre_periodo


class RelacionCarreraPeriodo(models.Model):
    id_carrera_periodo = models.AutoField(primary_key=True, db_column='ID_CARRERA_PERIODO')
    id_carrera = models.ForeignKey(CatalogoCarrera, on_delete=models.RESTRICT, db_column='ID_CARRERA')
    id_periodo = models.ForeignKey(CatalogoPeriodoAcademico, on_delete=models.RESTRICT, db_column='ID_PERIODO')

    class Meta:
        managed = False
        db_table = 'relacion_carrera_periodo'
        unique_together = (('id_carrera', 'id_periodo'),)
        verbose_name = '[Relación] Carrera × Período'
        verbose_name_plural = 'M1 · Catálogos · Carreras por Período'

    def __str__(self):
        return f'{self.id_carrera} - {self.id_periodo}'


# =============================================================================
#  MÓDULO 2 · DOCENTES
# =============================================================================

class DocenteFcacc(models.Model):
    id_docente = models.BigAutoField(primary_key=True, db_column='id_docente')
    cedula_docente = models.CharField(max_length=13, unique=True, db_column='cedula_docente')
    id_tipo_docente = models.ForeignKey(CatalogoTipoDocente, on_delete=models.RESTRICT, db_column='id_tipo_docente')
    id_modalidad = models.ForeignKey(CatalogoModalidadContratacion, on_delete=models.RESTRICT, db_column='id_modalidad')
    id_dedicacion = models.ForeignKey(CatalogoDedicacionHoraria, on_delete=models.RESTRICT, db_column='id_dedicacion')
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
    id_titulo = models.BigAutoField(primary_key=True, db_column='ID_TITULO')
    id_docente = models.ForeignKey(DocenteFcacc, on_delete=models.CASCADE, db_column='ID_DOCENTE')
    id_pais = models.ForeignKey(CatalogoPais, on_delete=models.RESTRICT, db_column='ID_PAIS')
    id_posgrado = models.ForeignKey(CatalogoTituloPosgrado, on_delete=models.SET_NULL, null=True, blank=True, db_column='ID_POSGRADO')
    nombre_titulo = models.CharField(max_length=200, db_column='NOMBRE_TITULO')
    nivel_titulo = models.SmallIntegerField(db_column='NIVEL_TITULO')
    fecha_obtencion_titulo = models.DateField(null=True, blank=True, db_column='FECHA_OBTENCION_TITULO')
    numero_registro_titulo = models.CharField(max_length=50, null=True, blank=True, db_column='NUMERO_REGISTRO_TITULO')
    numero_registro_senescyt = models.CharField(max_length=50, null=True, blank=True, unique=True, db_column='NUMERO_REGISTRO_SENESCYT')
    fecha_registro_senescyt = models.DateField(null=True, blank=True, db_column='FECHA_REGISTRO_SENESCYT')

    class Meta:
        managed = False
        db_table = 'docente_titulo_academico'
        verbose_name = 'Título Académico (Docente)'
        verbose_name_plural = 'M2 · Docentes · Títulos Académicos'

    def __str__(self):
        return f'{self.nombre_titulo} - {self.id_docente}'


class DocenteCampoAfinidad(models.Model):
    id_docente_campo = models.BigAutoField(primary_key=True, db_column='ID_DOCENTE_CAMPO')
    id_docente = models.ForeignKey(DocenteFcacc, on_delete=models.CASCADE, db_column='ID_DOCENTE')
    id_campo = models.ForeignKey(CatalogoCampoConocimiento, on_delete=models.RESTRICT, db_column='ID_CAMPO')

    class Meta:
        managed = False
        db_table = 'docente_campo_afinidad'
        unique_together = (('id_docente', 'id_campo'),)
        verbose_name = 'Campo Afinidad (Docente)'
        verbose_name_plural = 'M2 · Docentes · Campos Afinidad'

    def __str__(self):
        return f'Docente {self.id_docente} → {self.id_campo}'


class DocenteAsignacionCarreraPeriodo(models.Model):
    id_asignacion_carrera_periodo = models.BigAutoField(primary_key=True, db_column='ID_ASIGNACION_CARRERA_PERIODO')
    id_docente = models.ForeignKey(DocenteFcacc, on_delete=models.CASCADE, db_column='ID_DOCENTE')
    id_carrera = models.ForeignKey(CatalogoCarrera, on_delete=models.RESTRICT, db_column='ID_CARRERA')
    id_periodo = models.ForeignKey(CatalogoPeriodoAcademico, on_delete=models.RESTRICT, db_column='ID_PERIODO')
    id_licencia = models.ForeignKey(CatalogoTipoLicencia, on_delete=models.RESTRICT, db_column='ID_LICENCIA')
    horas_otras_unidades_academicas = models.IntegerField(default=0, db_column='HORAS_OTRAS_UNIDADES_ACADEMICAS')
    observacion_periodo = models.TextField(null=True, blank=True, db_column='OBSERVACION_PERIODO')

    class Meta:
        managed = False
        db_table = 'docente_asignacion_carrera_periodo'
        unique_together = (('id_docente', 'id_carrera', 'id_periodo'),)
        verbose_name = 'Asignación Docente → Carrera/Período'
        verbose_name_plural = 'M2 · Docentes · Asignaciones Carrera/Período'

    def __str__(self):
        return f'Docente {self.id_docente} → Carrera {self.id_carrera} · {self.id_periodo}'


class DocenteCursoCapacitacion(models.Model):
    id_curso = models.AutoField(primary_key=True, db_column='ID_CURSO')
    id_tipo_curso = models.ForeignKey(CatalogoTipoCursoCapacitacion, on_delete=models.RESTRICT, db_column='ID_TIPO_CURSO')
    nombre_curso_capacitacion = models.CharField(max_length=200, db_column='NOMBRE_CURSO_CAPACITACION')
    fecha_inicio_curso = models.DateField(null=True, blank=True, db_column='FECHA_INICIO_CURSO')
    fecha_fin_curso = models.DateField(null=True, blank=True, db_column='FECHA_FIN_CURSO')
    horas_totales_curso = models.SmallIntegerField(default=0, db_column='HORAS_TOTALES_CURSO')

    class Meta:
        managed = False
        db_table = 'docente_curso_capacitacion'
        verbose_name = 'Curso de Capacitación'
        verbose_name_plural = 'M2 · Docentes · Cursos Capacitación'

    def __str__(self):
        return self.nombre_curso_capacitacion


class DocenteParticipacionCurso(models.Model):
    id_participacion = models.BigAutoField(primary_key=True, db_column='ID_PARTICIPACION')
    id_docente = models.ForeignKey(DocenteFcacc, on_delete=models.CASCADE, db_column='ID_DOCENTE')
    id_curso = models.ForeignKey(DocenteCursoCapacitacion, on_delete=models.RESTRICT, db_column='ID_CURSO')
    fecha_participacion = models.DateField(db_column='FECHA_PARTICIPACION')

    class Meta:
        managed = False
        db_table = 'docente_participacion_curso'
        unique_together = (('id_docente', 'id_curso'),)
        verbose_name = 'Participación en Curso'
        verbose_name_plural = 'M2 · Docentes · Participaciones en Cursos'

    def __str__(self):
        return f'Docente {self.id_docente} → {self.id_curso}'


class DocentePublicacionAcademica(models.Model):
    id_publicacion = models.BigAutoField(primary_key=True, db_column='ID_PUBLICACION')
    id_docente = models.ForeignKey(DocenteFcacc, on_delete=models.CASCADE, db_column='ID_DOCENTE')
    id_tipo_publicacion = models.ForeignKey(CatalogoTipoPublicacion, on_delete=models.RESTRICT, db_column='ID_TIPO_PUBLICACION')
    nombre_publicacion = models.CharField(max_length=200, db_column='NOMBRE_PUBLICACION')
    fecha_publicacion = models.DateField(null=True, blank=True, db_column='FECHA_PUBLICACION')
    detalle_publicacion = models.TextField(null=True, blank=True, db_column='DETALLE_PUBLICACION')

    class Meta:
        managed = False
        db_table = 'docente_publicacion_academica'
        verbose_name = 'Publicación Académica (Docente)'
        verbose_name_plural = 'M2 · Docentes · Publicaciones Académicas'

    def __str__(self):
        return self.nombre_publicacion


# =============================================================================
#  MÓDULO 3 · SEGURIDAD
# =============================================================================

class SeguridadRol(models.Model):
    id_rol = models.AutoField(primary_key=True, db_column='ID_ROL')
    codigo_rol = models.CharField(max_length=15, unique=True, db_column='CODIGO_ROL')
    nombre_rol = models.CharField(max_length=50, db_column='NOMBRE_ROL')
    descripcion_rol = models.CharField(max_length=200, null=True, blank=True, db_column='DESCRIPCION_ROL')
    rol_activo = models.BooleanField(default=True, db_column='ROL_ACTIVO')

    class Meta:
        managed = False
        db_table = 'seguridad_rol'
        verbose_name = 'Rol de Seguridad'
        verbose_name_plural = 'M3 · Seguridad · Roles'

    def __str__(self):
        return self.nombre_rol


class SeguridadUsuario(models.Model):
    id_usuario = models.AutoField(primary_key=True, db_column='ID_USUARIO')
    id_docente = models.OneToOneField(DocenteFcacc, on_delete=models.SET_NULL, null=True, blank=True, db_column='ID_DOCENTE')
    nombre_usuario = models.CharField(max_length=100, unique=True, db_column='NOMBRE_USUARIO')
    contrasena_hash = models.CharField(max_length=255, db_column='CONTRASENA_HASH')
    usuario_activo = models.BooleanField(default=True, db_column='USUARIO_ACTIVO')
    fecha_ultimo_acceso = models.DateTimeField(null=True, blank=True, db_column='FECHA_ULTIMO_ACCESO')
    fecha_creacion_usuario = models.DateTimeField(auto_now_add=True, db_column='FECHA_CREACION_USUARIO')

    class Meta:
        managed = False
        db_table = 'seguridad_usuario'
        verbose_name = 'Usuario del Sistema'
        verbose_name_plural = 'M3 · Seguridad · Usuarios'

    def __str__(self):
        return self.nombre_usuario


class SeguridadUsuarioRol(models.Model):
    id_usuario_rol = models.BigAutoField(primary_key=True, db_column='ID_USUARIO_ROL')
    id_usuario = models.ForeignKey(SeguridadUsuario, on_delete=models.CASCADE, db_column='ID_USUARIO')
    id_rol = models.ForeignKey(SeguridadRol, on_delete=models.RESTRICT, db_column='ID_ROL')
    id_carrera = models.ForeignKey(CatalogoCarrera, on_delete=models.RESTRICT, db_column='ID_CARRERA')
    fecha_asignacion_rol = models.DateField(db_column='FECHA_ASIGNACION_ROL')

    class Meta:
        managed = False
        db_table = 'seguridad_usuario_rol'
        unique_together = (('id_usuario', 'id_rol', 'id_carrera'),)
        verbose_name = 'Asignación Usuario × Rol × Carrera'
        verbose_name_plural = 'M3 · Seguridad · Usuarios Roles'

    def __str__(self):
        return f'{self.id_usuario} → {self.id_rol} ({self.id_carrera})'


# =============================================================================
#  MÓDULO 4 · CURRÍCULO
# =============================================================================

class CurriculoAsignatura(models.Model):
    id_asignatura = models.AutoField(primary_key=True, db_column='ID_ASIGNATURA')
    codigo_asignatura = models.CharField(max_length=20, unique=True, db_column='CODIGO_ASIGNATURA')
    id_carrera = models.ForeignKey(CatalogoCarrera, on_delete=models.RESTRICT, db_column='ID_CARRERA')
    nombre_asignatura = models.CharField(max_length=200, db_column='NOMBRE_ASIGNATURA')
    horas_semanales_asignatura = models.SmallIntegerField(default=0, db_column='HORAS_SEMANALES_ASIGNATURA')
    nivel_semestre = models.SmallIntegerField(db_column='NIVEL_SEMESTRE')

    class Meta:
        managed = False
        db_table = 'curriculo_asignatura'
        verbose_name = 'Asignatura (Currículo)'
        verbose_name_plural = 'M4 · Currículo · Asignaturas'

    def __str__(self):
        return f'{self.codigo_asignatura} - {self.nombre_asignatura}'


class CurriculoAsignaturaCampo(models.Model):
    id_asignatura_campo = models.AutoField(primary_key=True, db_column='ID_ASIGNATURA_CAMPO')
    id_asignatura = models.ForeignKey(CurriculoAsignatura, on_delete=models.CASCADE, db_column='ID_ASIGNATURA')
    id_campo = models.ForeignKey(CatalogoCampoConocimiento, on_delete=models.RESTRICT, db_column='ID_CAMPO')

    class Meta:
        managed = False
        db_table = 'curriculo_asignatura_campo'
        unique_together = (('id_asignatura', 'id_campo'),)
        verbose_name = 'Asignatura × Campo Conocimiento'
        verbose_name_plural = 'M4 · Currículo · Asignaturas por Campo'

    def __str__(self):
        return f'{self.id_asignatura} → Campo {self.id_campo}'


class RelacionPosgradoCampo(models.Model):
    id_posgrado_campo = models.AutoField(primary_key=True, db_column='ID_POSGRADO_CAMPO')
    id_posgrado = models.ForeignKey(CatalogoTituloPosgrado, on_delete=models.CASCADE, db_column='ID_POSGRADO')
    id_campo = models.ForeignKey(CatalogoCampoConocimiento, on_delete=models.RESTRICT, db_column='ID_CAMPO')

    class Meta:
        managed = False
        db_table = 'relacion_posgrado_campo'
        unique_together = (('id_posgrado', 'id_campo'),)
        verbose_name = 'Posgrado × Campo Conocimiento'
        verbose_name_plural = 'M4 · Currículo · Posgrados por Campo'

    def __str__(self):
        return f'Posgrado {self.id_posgrado} → Campo {self.id_campo}'


# =============================================================================
#  MÓDULO 5 · PLANIFICACIÓN
# =============================================================================

class PlanificacionDemandaAcademica(models.Model):
    id_demanda = models.BigAutoField(primary_key=True, db_column='ID_DEMANDA')
    id_asignatura = models.ForeignKey(CurriculoAsignatura, on_delete=models.RESTRICT, db_column='ID_ASIGNATURA')
    id_carrera = models.ForeignKey(CatalogoCarrera, on_delete=models.RESTRICT, db_column='ID_CARRERA')
    id_periodo = models.ForeignKey(CatalogoPeriodoAcademico, on_delete=models.RESTRICT, db_column='ID_PERIODO')
    proyeccion_estudiantes = models.IntegerField(default=0, db_column='PROYECCION_ESTUDIANTES')
    numero_paralelos = models.SmallIntegerField(default=1, db_column='NUMERO_PARALELOS')

    class Meta:
        managed = False
        db_table = 'planificacion_demanda_academica'
        unique_together = (('id_asignatura', 'id_carrera', 'id_periodo'),)
        verbose_name = 'Demanda Académica'
        verbose_name_plural = 'M5 · Planificación · Demanda Académica'

    def __str__(self):
        return f'{self.id_asignatura} - {self.id_periodo}'


class PlanificacionAsignacionDocente(models.Model):
    id_asignacion = models.BigAutoField(primary_key=True, db_column='ID_ASIGNACION')
    id_docente = models.ForeignKey(DocenteFcacc, on_delete=models.RESTRICT, db_column='ID_DOCENTE')
    id_asignatura = models.ForeignKey(CurriculoAsignatura, on_delete=models.RESTRICT, db_column='ID_ASIGNATURA')
    id_carrera = models.ForeignKey(CatalogoCarrera, on_delete=models.RESTRICT, db_column='ID_CARRERA')
    id_periodo = models.ForeignKey(CatalogoPeriodoAcademico, on_delete=models.RESTRICT, db_column='ID_PERIODO')
    id_campo = models.ForeignKey(CatalogoCampoConocimiento, on_delete=models.RESTRICT, db_column='ID_CAMPO')
    nivel_semestre_asignado = models.SmallIntegerField(db_column='NIVEL_SEMESTRE_ASIGNADO')
    paralelo_asignado = models.CharField(max_length=3, db_column='PARALELO_ASIGNADO')
    horas_clase = models.SmallIntegerField(default=0, db_column='HORAS_CLASE')
    horas_complementarias = models.SmallIntegerField(default=0, db_column='HORAS_COMPLEMENTARIAS')
    comision_servicio = models.CharField(max_length=100, null=True, blank=True, db_column='COMISION_SERVICIO')

    class Meta:
        managed = False
        db_table = 'planificacion_asignacion_docente'
        verbose_name = 'Asignación Docente (Planificación)'
        verbose_name_plural = 'M5 · Planificación · Asignación Docente'

    def __str__(self):
        return f'Docente {self.id_docente} → {self.id_asignatura} ({self.paralelo_asignado})'


class PlanificacionRepartoHoras(models.Model):
    id_reparto = models.BigAutoField(primary_key=True, db_column='ID_REPARTO')
    id_docente = models.ForeignKey(DocenteFcacc, on_delete=models.RESTRICT, db_column='ID_DOCENTE')
    id_asignatura = models.ForeignKey(CurriculoAsignatura, on_delete=models.RESTRICT, db_column='ID_ASIGNATURA')
    id_periodo = models.ForeignKey(CatalogoPeriodoAcademico, on_delete=models.RESTRICT, db_column='ID_PERIODO')
    nivel_paralelo = models.CharField(max_length=5, db_column='NIVEL_PARALELO')
    horas_presenciales_asignadas = models.SmallIntegerField(default=0, db_column='HORAS_PRESENCIALES_ASIGNADAS')

    class Meta:
        managed = False
        db_table = 'planificacion_reparto_horas'
        unique_together = (('id_docente', 'id_asignatura', 'id_periodo', 'nivel_paralelo'),)
        verbose_name = 'Reparto de Horas'
        verbose_name_plural = 'M5 · Planificación · Reparto de Horas'

    def __str__(self):
        return f'Docente {self.id_docente} - {self.id_asignatura} ({self.nivel_paralelo})'


class PlanificacionMatrizF4(models.Model):
    id_registro_f4 = models.BigAutoField(primary_key=True, db_column='ID_REGISTRO_F4')
    id_docente = models.ForeignKey(DocenteFcacc, on_delete=models.RESTRICT, db_column='ID_DOCENTE')
    id_carrera = models.ForeignKey(CatalogoCarrera, on_delete=models.RESTRICT, db_column='ID_CARRERA')
    id_periodo = models.ForeignKey(CatalogoPeriodoAcademico, on_delete=models.RESTRICT, db_column='ID_PERIODO')
    id_grado_afinidad = models.ForeignKey(CatalogoGradoAfinidad, on_delete=models.RESTRICT, db_column='ID_GRADO_AFINIDAD')
    tipo_actividad = models.CharField(max_length=100, db_column='TIPO_ACTIVIDAD')
    nombre_asignatura_actividad = models.CharField(max_length=200, null=True, blank=True, db_column='NOMBRE_ASIGNATURA_ACTIVIDAD')
    nivel_semestre_actividad = models.CharField(max_length=20, null=True, blank=True, db_column='NIVEL_SEMESTRE_ACTIVIDAD')
    horas_actividad = models.SmallIntegerField(default=0, db_column='HORAS_ACTIVIDAD')
    numero_paralelos_actividad = models.SmallIntegerField(default=1, db_column='NUMERO_PARALELOS_ACTIVIDAD')
    observaciones = models.TextField(null=True, blank=True, db_column='OBSERVACIONES')

    class Meta:
        managed = False
        db_table = 'planificacion_matriz_f4'
        verbose_name = 'Matriz F4'
        verbose_name_plural = 'M5 · Planificación · Matriz F4'

    def __str__(self):
        return f'F4 · Docente {self.id_docente} - {self.tipo_actividad}'


class PlanificacionAulaHorario(models.Model):
    id_horario = models.AutoField(primary_key=True, db_column='ID_HORARIO')
    id_periodo = models.ForeignKey(CatalogoPeriodoAcademico, on_delete=models.RESTRICT, db_column='ID_PERIODO')
    nombre_aula = models.CharField(max_length=50, db_column='NOMBRE_AULA')
    turno_horario = models.CharField(max_length=10, db_column='TURNO_HORARIO')
    nivel_asignado = models.CharField(max_length=10, null=True, blank=True, db_column='NIVEL_ASIGNADO')

    class Meta:
        managed = False
        db_table = 'planificacion_aula_horario'
        unique_together = (('id_periodo', 'nombre_aula', 'turno_horario'),)
        verbose_name = 'Aula / Horario'
        verbose_name_plural = 'M5 · Planificación · Aulas y Horarios'

    def __str__(self):
        return f'{self.nombre_aula} - {self.turno_horario} ({self.id_periodo})'


# =============================================================================
#  MÓDULO 6 · AUDITORÍA
# =============================================================================

class AuditoriaRegistroCambios(models.Model):
    id_registro_auditoria = models.BigAutoField(primary_key=True, db_column='ID_REGISTRO_AUDITORIA')
    id_usuario = models.ForeignKey(SeguridadUsuario, on_delete=models.SET_NULL, null=True, blank=True, db_column='ID_USUARIO')
    nombre_tabla_afectada = models.CharField(max_length=60, db_column='NOMBRE_TABLA_AFECTADA')
    id_registro_afectado = models.BigIntegerField(db_column='ID_REGISTRO_AFECTADO')
    tipo_accion = models.CharField(max_length=10, db_column='TIPO_ACCION')
    valor_anterior = models.JSONField(null=True, blank=True, db_column='VALOR_ANTERIOR')
    valor_nuevo = models.JSONField(null=True, blank=True, db_column='VALOR_NUEVO')
    fecha_hora_cambio = models.DateTimeField(auto_now_add=True, db_column='FECHA_HORA_CAMBIO')
    direccion_ip_origen = models.CharField(max_length=45, null=True, blank=True, db_column='DIRECCION_IP_ORIGEN')

    class Meta:
        managed = False
        db_table = 'auditoria_registro_cambios'
        verbose_name = 'Registro de Auditoría'
        verbose_name_plural = 'M6 · Auditoría · Registro de Cambios'

    def __str__(self):
        return f'{self.tipo_accion} {self.nombre_tabla_afectada} #{self.id_registro_afectado}'


# =============================================================================
#  MÓDULO 7 · LIMITACIONES Y PLANIFICACIÓN COMPLEMENTARIA
# =============================================================================

class Limitacion(models.Model):
    id_limitacion = models.AutoField(primary_key=True, db_column='ID_LIMITACION')
    codigo_limitacion = models.CharField(max_length=15, unique=True, db_column='CODIGO_LIMITACION')
    nombre_limitacion = models.CharField(max_length=150, db_column='NOMBRE_LIMITACION')
    hora_minima = models.IntegerField(db_column='HORA_MINIMA')
    hora_maxima = models.IntegerField(db_column='HORA_MAXIMA')

    class Meta:
        managed = False
        db_table = 'limitacion'
        verbose_name = 'Límite / Regla'
        verbose_name_plural = 'M7 · Limitaciones · Reglas'

    def __str__(self):
        return f'{self.nombre_limitacion} ({self.hora_minima}-{self.hora_maxima})'


class HistorialLimitacion(models.Model):
    id_historial = models.BigAutoField(primary_key=True, db_column='ID_HISTORIAL')
    id_docente = models.ForeignKey(DocenteFcacc, on_delete=models.RESTRICT, db_column='ID_DOCENTE')
    id_limitacion = models.ForeignKey(Limitacion, on_delete=models.RESTRICT, db_column='ID_LIMITACION')
    fecha_inicio_vigencia = models.DateField(db_column='FECHA_INICIO_VIGENCIA')
    fecha_fin_vigencia = models.DateField(db_column='FECHA_FIN_VIGENCIA')

    class Meta:
        managed = False
        db_table = 'historial_limitacion'
        verbose_name = 'Historial de Limitación'
        verbose_name_plural = 'M7 · Limitaciones · Historial'

    def __str__(self):
        return f'Docente {self.id_docente} → {self.id_limitacion} ({self.fecha_inicio_vigencia} - {self.fecha_fin_vigencia})'


class Cabecera(models.Model):
    id_cabecera = models.AutoField(primary_key=True, db_column='ID_CABECERA')
    descripcion_periodo = models.CharField(max_length=100, db_column='DESCRIPCION_PERIODO')

    class Meta:
        managed = False
        db_table = 'cabecera'
        verbose_name = 'Cabecera de Planificación'
        verbose_name_plural = 'M7 · Planif. Complementaria · Cabeceras'

    def __str__(self):
        return self.descripcion_periodo


class Cuerpo(models.Model):
    id_cuerpo = models.BigAutoField(primary_key=True, db_column='ID_CUERPO')
    id_cabecera = models.ForeignKey(Cabecera, on_delete=models.CASCADE, db_column='ID_CABECERA')
    id_docente = models.ForeignKey(DocenteFcacc, on_delete=models.RESTRICT, db_column='ID_DOCENTE')
    horas = models.IntegerField(db_column='HORAS')

    class Meta:
        managed = False
        db_table = 'cuerpo'
        verbose_name = 'Detalle de Horas (Cuerpo)'
        verbose_name_plural = 'M7 · Planif. Complementaria · Detalle Horas'

    def __str__(self):
        return f'Cabecera {self.id_cabecera} - Docente {self.id_docente}: {self.horas}h'
