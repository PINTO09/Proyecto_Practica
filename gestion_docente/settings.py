import os
from pathlib import Path
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-me')

# DEBUG puede venir de una variable de entorno no booleana.
# Si no es un valor válido, asumimos modo producción seguro.
def parse_bool(value, default=False):
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {'true', '1', 'yes', 'on'}:
        return True
    if text in {'false', '0', 'no', 'off', ''}:
        return False
    return default

DEBUG = (
    parse_bool(config('DEBUG', default='True')) or
    parse_bool(config('LOCAL_DEVELOPMENT', default='False'))
)
# En desarrollo se permite acceder con la IP LAN del equipo. En producción se
# debe declarar ALLOWED_HOSTS explícitamente en el archivo .env.
_default_allowed_hosts = '*' if DEBUG else 'localhost,127.0.0.1'
ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS',
    default=_default_allowed_hosts,
    cast=lambda v: [s.strip() for s in v.split(',') if s.strip()],
)

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
    'accounts',
    'catalogos',
    'docentes',
    'curriculo',
    'planificacion',
    'seguridad',
    'auditoria',
    'restricciones',
    'reportes',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'accounts.middleware.ForcePasswordChangeMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'gestion_docente.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': False,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'accounts.context_processors.module_access',
            ],
            'loaders': [
                ('django.template.loaders.cached.Loader', [
                    'django.template.loaders.filesystem.Loader',
                    'django.template.loaders.app_directories.Loader',
                ]),
            ],
        },
    },
]
if DEBUG:
    TEMPLATES[0]['OPTIONS']['loaders'] = [
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    ]

WSGI_APPLICATION = 'gestion_docente.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
        'CONN_MAX_AGE': 300,
        'OPTIONS': {
            'client_encoding': 'latin1',
        },
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# La sesión institucional expira después de 8 horas de inactividad y las
# cookies no quedan disponibles para JavaScript.
SESSION_COOKIE_AGE = 15 * 60  # 15 minutes of inactivity
SESSION_SAVE_EVERY_REQUEST = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_CONTENT_TYPE_NOSNIFF = True

LANGUAGE_CODE = 'es-ec'
TIME_ZONE = 'America/Guayaquil'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
# Los recursos fuente viven dentro de cada aplicación (por ejemplo,
# core/static). La carpeta STATIC_ROOT es únicamente la salida de collectstatic.
STATICFILES_DIRS = []
STATIC_ROOT = BASE_DIR / 'static'

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'core.Usuario'
AUTHENTICATION_BACKENDS = ['accounts.auth_backend.CedulaAuthBackend']

LOGIN_URL = 'core:login'
LOGIN_REDIRECT_URL = 'core:dashboard'

LOGOUT_REDIRECT_URL = 'core:landing'

GRUPO_ADMINISTRADOR = 'Administrador'
GRUPO_AUTORIDAD = 'Autoridad'
GRUPO_COORDINADOR = 'Coordinador'
GRUPO_USUARIO = 'Usuario'
GRUPO_FUNCIONARIO = 'Funcionario'

ROLES = [
    GRUPO_ADMINISTRADOR,
    GRUPO_AUTORIDAD,
    GRUPO_COORDINADOR,
    GRUPO_USUARIO,
    GRUPO_FUNCIONARIO,
]


