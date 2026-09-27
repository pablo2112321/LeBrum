from django.contrib import admin

from .models import Equipo, MiembroEquipo


class MiembroEquipoInline(admin.TabularInline):
    model = MiembroEquipo
    extra = 0
    fields = ("usuario", "es_capitan")
    autocomplete_fields = ("usuario",)


@admin.register(Equipo)
class EquipoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "tag", "modo", "capitan", "miembros_count")
    list_filter = ("modo",)
    search_fields = ("nombre", "tag", "capitan__username")
    autocomplete_fields = ("capitan",)
    inlines = (MiembroEquipoInline,)

    @admin.display(description="Miembros")
    def miembros_count(self, obj):
        return obj.miembros.count()


@admin.register(MiembroEquipo)
class MiembroEquipoAdmin(admin.ModelAdmin):
    list_display = ("equipo", "usuario", "es_capitan")
    list_filter = ("es_capitan", "equipo__modo")
    search_fields = ("equipo__nombre", "usuario__username")
    autocomplete_fields = ("equipo", "usuario")
