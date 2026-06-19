from django.db import models
from django.core.validators import RegexValidator
from django.contrib.auth.models import AbstractUser, BaseUserManager

validate_10_digits = RegexValidator(
    r'^\d{10}$',
    'Este campo debe tener exactamente 10 dígitos numéricos.'
)


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
    nombre_publicacion = models.CharField(
        'Nombre de la publicación', max_length=255
    )
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
    id_docente = models.ForeignKey(
        Docente, on_delete=models.CASCADE, verbose_name='Docente'
    )
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
    id_curso = models.ForeignKey(
        Curso, on_delete=models.CASCADE, verbose_name='Curso'
    )
    id_docente = models.ForeignKey(
        Docente, on_delete=models.CASCADE, verbose_name='Docente'
    )

    class Meta:
        verbose_name = 'Curso - Docente'
        verbose_name_plural = 'Cursos - Docentes'
        unique_together = ('id_curso', 'id_docente')

    def __str__(self):
        return f'{self.id_curso} - {self.id_docente}'
