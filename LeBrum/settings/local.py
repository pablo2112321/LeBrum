import os
import secrets

from .base import *

DEBUG = os.getenv('DEBUG', 'True').lower() in {'1', 'true', 'yes', 'on'}

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1,[::1]').split(',')
    if host.strip()
]

# En desarrollo se usa SQLite por defecto para mantener el entorno aislado.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Permite ejecutar localmente sin un secreto persistido, sin incluirlo en el codigo.
if not SECRET_KEY:
    SECRET_KEY = secrets.token_urlsafe(50)