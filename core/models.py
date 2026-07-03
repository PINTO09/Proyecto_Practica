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
    id_carrera = models.AutoField(primary_key=True, db_column='id_carrera')
    codigo_carrera = models.CharField(max_length=20, unique=True, db_column='codigo_carrera')
    nombre_carrera = models.CharField(max_length=120, db_column='nombre_carrera')
    carrera_activa = models.BooleanField(default=True, db_column='carrera_activa')

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
    id_titulo = models.BigAutoField(primary_key=True, db_column='id_titulo')
    id_docente = models.ForeignKey(DocenteFcacc, on_delete=models.CASCADE, db_column='id_docente')
    id_pais = models.ForeignKey(CatalogoPais, on_delete=models.RESTRICT, db_column='id_pais')
    id_posgrado = models.ForeignKey(CatalogoTituloPosgrado, on_delete=models.SET_NULL, null=True, blank=True, db_column='id_posgrado')
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
    id_campo = models.ForeignKey(CatalogoCampoConocimiento, on_delete=models.RESTRICT, db_column='id_campo')

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
    id_carrera = models.ForeignKey(CatalogoCarrera, on_delete=models.RESTRICT, db_column='id_carrera')
    id_periodo = models.ForeignKey(CatalogoPeriodoAcademico, on_delete=models.RESTRICT, db_column='id_periodo')
    id_licencia = models.ForeignKey(CatalogoTipoLicencia, on_delete=models.RESTRICT, db_column='id_licencia')
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
    id_tipo_curso = models.ForeignKey(CatalogoTipoCursoCapacitacion, on_delete=models.RESTRICT, db_column='id_tipo_curso')
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
    id_tipo_publicacion = models.ForeignKey(CatalogoTipoPublicacion, on_delete=models.RESTRICT, db_column='id_tipo_publicacion')
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


# =============================================================================
#  MÓDULO 3 · SEGURIDAD
# =============================================================================

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
    id_docente = models.OneToOneField(DocenteFcacc, on_delete=models.SET_NULL, null=True, blank=True, db_column='id_docente')
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
    id_carrera = models.ForeignKey(CatalogoCarrera, on_delete=models.RESTRICT, db_column='id_carrera')
    fecha_asignacion_rol = models.DateField(db_column='fecha_asignacion_rol')

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
    id_asignatura = models.AutoField(primary_key=True, db_column='id_asignatura')
    codigo_asignatura = models.CharField(max_length=20, unique=True, db_column='codigo_asignatura')
    id_carrera = models.ForeignKey(CatalogoCarrera, on_delete=models.RESTRICT, db_column='id_carrera')
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
    id_campo = models.ForeignKey(CatalogoCampoConocimiento, on_delete=models.RESTRICT, db_column='id_campo')

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
    id_posgrado = models.ForeignKey(CatalogoTituloPosgrado, on_delete=models.CASCADE, db_column='id_posgrado')
    id_campo = models.ForeignKey(CatalogoCampoConocimiento, on_delete=models.RESTRICT, db_column='id_campo')

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
    id_demanda = models.BigAutoField(primary_key=True, db_column='id_demanda')
    id_asignatura = models.ForeignKey(CurriculoAsignatura, on_delete=models.RESTRICT, db_column='id_asignatura')
    id_carrera = models.ForeignKey(CatalogoCarrera, on_delete=models.RESTRICT, db_column='id_carrera')
    id_periodo = models.ForeignKey(CatalogoPeriodoAcademico, on_delete=models.RESTRICT, db_column='id_periodo')
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


class PlanificacionAsignacionDocente(models.Model):
    id_asignacion = models.BigAutoField(primary_key=True, db_column='id_asignacion')
    id_docente = models.ForeignKey(DocenteFcacc, on_delete=models.RESTRICT, db_column='id_docente')
    id_asignatura = models.ForeignKey(CurriculoAsignatura, on_delete=models.RESTRICT, db_column='id_asignatura')
    id_carrera = models.ForeignKey(CatalogoCarrera, on_delete=models.RESTRICT, db_column='id_carrera')
    id_periodo = models.ForeignKey(CatalogoPeriodoAcademico, on_delete=models.RESTRICT, db_column='id_periodo')
    id_campo = models.ForeignKey(CatalogoCampoConocimiento, on_delete=models.RESTRICT, db_column='id_campo')
    nivel_semestre_asignado = models.SmallIntegerField(db_column='nivel_semestre_asignado')
    paralelo_asignado = models.CharField(max_length=3, db_column='paralelo_asignado')
    horas_clase = models.SmallIntegerField(default=0, db_column='horas_clase')
    horas_complementarias = models.SmallIntegerField(default=0, db_column='horas_complementarias')
    comision_servicio = models.CharField(max_length=100, null=True, blank=True, db_column='comision_servicio')

    class Meta:
        managed = False
        db_table = 'planificacion_asignacion_docente'
        verbose_name = 'Asignación Docente (Planificación)'
        verbose_name_plural = 'M5 · Planificación · Asignación Docente'

    def __str__(self):
        return f'Docente {self.id_docente} → {self.id_asignatura} ({self.paralelo_asignado})'


class PlanificacionRepartoHoras(models.Model):
    id_reparto = models.BigAutoField(primary_key=True, db_column='id_reparto')
    id_docente = models.ForeignKey(DocenteFcacc, on_delete=models.RESTRICT, db_column='id_docente')
    id_asignatura = models.ForeignKey(CurriculoAsignatura, on_delete=models.RESTRICT, db_column='id_asignatura')
    id_periodo = models.ForeignKey(CatalogoPeriodoAcademico, on_delete=models.RESTRICT, db_column='id_periodo')
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


class PlanificacionMatrizF4(models.Model):
    id_registro_f4 = models.BigAutoField(primary_key=True, db_column='id_registro_f4')
    id_docente = models.ForeignKey(DocenteFcacc, on_delete=models.RESTRICT, db_column='id_docente')
    id_carrera = models.ForeignKey(CatalogoCarrera, on_delete=models.RESTRICT, db_column='id_carrera')
    id_periodo = models.ForeignKey(CatalogoPeriodoAcademico, on_delete=models.RESTRICT, db_column='id_periodo')
    id_grado_afinidad = models.ForeignKey(CatalogoGradoAfinidad, on_delete=models.RESTRICT, db_column='id_grado_afinidad')
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


class PlanificacionAulaHorario(models.Model):
    id_horario = models.AutoField(primary_key=True, db_column='id_horario')
    id_periodo = models.ForeignKey(CatalogoPeriodoAcademico, on_delete=models.RESTRICT, db_column='id_periodo')
    nombre_aula = models.CharField(max_length=50, db_column='nombre_aula')
    turno_horario = models.CharField(max_length=10, db_column='turno_horario')
    nivel_asignado = models.CharField(max_length=10, null=True, blank=True, db_column='nivel_asignado')

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
    id_registro_auditoria = models.BigAutoField(primary_key=True, db_column='id_registro_auditoria')
    id_usuario = models.ForeignKey(SeguridadUsuario, on_delete=models.SET_NULL, null=True, blank=True, db_column='id_usuario')
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


# =============================================================================
#  MÓDULO 7 · LIMITACIONES Y PLANIFICACIÓN COMPLEMENTARIA
# =============================================================================

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
    id_docente = models.ForeignKey(DocenteFcacc, on_delete=models.RESTRICT, db_column='id_docente')
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
    id_docente = models.ForeignKey(DocenteFcacc, on_delete=models.RESTRICT, db_column='id_docente')
    horas = models.IntegerField(db_column='horas')

    class Meta:
        managed = False
        db_table = 'cuerpo'
        verbose_name = 'Detalle de Horas (Cuerpo)'
        verbose_name_plural = 'M7 · Planif. Complementaria · Detalle Horas'

    def __str__(self):
        return f'Cabecera {self.id_cabecera} - Docente {self.id_docente}: {self.horas}h'
