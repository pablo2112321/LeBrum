import os
import importlib.util
from pathlib import Path

from dotenv import load_dotenv

# Carga las variables locales sin sobrescribir variables definidas por el entorno.
BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / '.env')

SECRET_KEY = os.getenv('SECRET_KEY', '')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Apps
    'usuarios',
    'equipos',
    'torneos',
    'soporte',
    'principal',
    'auditoria',
    
]

# Channels es opcional para que las instalaciones existentes conserven el
# fallback HTTP si todavía no han actualizado sus dependencias.
CHANNELS_AVAILABLE = importlib.util.find_spec('channels') is not None
if CHANNELS_AVAILABLE:
    INSTALLED_APPS.append('channels')

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'auditoria.middleware.SensitiveAccessAuditMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'LeBrum.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'usuarios.context_processors.notificaciones_usuario',
                'torneos.context_processors.admin_overview',
                'equipos.context_processors.jugador_equipo',
            ],
        },
    },
]

WSGI_APPLICATION = 'LeBrum.wsgi.application'
ASGI_APPLICATION = 'LeBrum.asgi.application'

if CHANNELS_AVAILABLE:
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels.layers.InMemoryChannelLayer',
        },
    }

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'es-es' # Cambiado a español
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
# Evidencias de partidas: no deben quedar bajo MEDIA_ROOT ni servirse como
# archivos estáticos. En producción, configurar el servidor para no publicar
# esta ruta y usar PRIVATE_MEDIA_SCANNER como hook de antivirus externo.
PRIVATE_MEDIA_ROOT = Path(os.getenv('PRIVATE_MEDIA_ROOT', BASE_DIR / 'private_media'))
PRIVATE_MEDIA_SCANNER = os.getenv('PRIVATE_MEDIA_SCANNER', '')

# Límite de defensa en profundidad para peticiones multipartaria.
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024

AUTH_USER_MODEL = 'usuarios.Usuario'

LOGIN_REDIRECT_URL = 'redireccionar_segun_rol'
LOGOUT_REDIRECT_URL = 'login'
LOGIN_URL = 'login'

RIOT_API_KEY = os.getenv('RIOT_API_KEY', '')
STEAM_API_KEY = os.getenv('STEAM_API_KEY', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', '')