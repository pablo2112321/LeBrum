import os
from .base import *

DEBUG = False

# Aquí luego pondrás el dominio real de LeBrum (ej. lebrum.com)
ALLOWED_HOSTS = ['lebrum-production.up.railway.app', 'tu-dominio.com'] 

# En producción, la contraseña y datos no se escriben aquí, se leen del servidor de forma segura
import dj_database_url # Esta librería la instalaremos después para producción
DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL')
    )
}