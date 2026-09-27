from django.contrib import admin
from .models import Noticia, Transmision, MensajeChat, ProductoTienda, CompraTienda


@admin.register(Noticia, Transmision, MensajeChat, ProductoTienda, CompraTienda)
class ModuloAdmin(admin.ModelAdmin):
    """Registro administrativo básico para los módulos del lobby."""
    list_display = ('__str__',)

# Register your models here.
