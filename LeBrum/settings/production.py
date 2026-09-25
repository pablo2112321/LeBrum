import os

from django.core.exceptions import ImproperlyConfigured

from .base import *

DEBUG = False

def _required_environment_variable(name: str) -> str:
    """Obtiene una variable obligatoria y falla si no fue configurada."""
    value = os.getenv(name, '').strip()
    if not value:
        raise ImproperlyConfigured(f'La variable de entorno {name} es obligatoria.')
    return value

SECRET_KEY = _required_environment_variable('SECRET_KEY')

ALLOWED_HOSTS = [
    host.strip()
    for host in _required_environment_variable('DJANGO_ALLOWED_HOSTS').split(',')
    if host.strip()
]

CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.getenv('DJANGO_CSRF_TRUSTED_ORIGINS', '').split(',')
    if origin.strip()
]

DATABASE_URL = _required_environment_variable('DATABASE_URL')

import dj_database_url

DATABASES = {
    'default': dj_database_url.parse(
        DATABASE_URL,
        conn_max_age=600,
        ssl_require=True,
    )
}

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True