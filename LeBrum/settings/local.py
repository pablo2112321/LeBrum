from .base import *

DEBUG = True

ALLOWED_HOSTS = ['*'] # Permite conexiones desde tu computadora

# Base de datos de Desarrollo (Supabase actual)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'postgres',                                 
        'USER': 'postgres',                                 
        'PASSWORD': 'Spokcillo2003@',                   
        'HOST': 'db.yygmroyjyxbmkpchrmpw.supabase.co',      
        'PORT': '5432',                                     
    }
}