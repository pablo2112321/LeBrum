from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import SolicitudPrivacidad, Usuario
from auditoria.services import record_audit_event


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = (
        "username",
        "email",
        "rol_plataforma",
        "rating_competitivo",
        "is_staff",
        "is_active",
    )
    list_filter = ("rol_plataforma", "is_staff", "is_active", "estado_conexion")
    search_fields = ("username", "email", "riot_id", "steam_id", "discord_id")
    fieldsets = UserAdmin.fieldsets + (
        (
            "Perfil competitivo",
            {
                "fields": (
                    "rol_plataforma",
                    "tag_jugador",
                    "riot_id",
                    "steam_id",
                    "discord_id",
                    "rating_competitivo",
                    "puntos_globales",
                    "puntos_xp",
                    "victorias",
                    "derrotas",
                    "kda",
                    "saldo_fichas",
                )
            },
        ),
        (
            "Personalización",
            {
                "fields": (
                    "avatar",
                    "banner_perfil",
                    "titulo_equipado",
                    "estado_equipado",
                    "estado_conexion",
                    "fondo_perfil",
                )
            },
        ),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            "Perfil competitivo",
            {"fields": ("rol_plataforma", "riot_id", "steam_id")},
        ),
    )

    def save_model(self, request, obj, form, change):
        previous_balance = None
        if change:
            previous_balance = type(obj).objects.get(pk=obj.pk).saldo_fichas
        super().save_model(request, obj, form, change)
        if change and previous_balance != obj.saldo_fichas:
            record_audit_event(
                'balance_change',
                request=request,
                target=obj,
                metadata={
                    'before': previous_balance,
                    'after': obj.saldo_fichas,
                    'source': 'admin',
                },
            )


@admin.register(SolicitudPrivacidad)
class SolicitudPrivacidadAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'tipo', 'estado', 'creada_el', 'procesada_el')
    list_filter = ('tipo', 'estado')
    search_fields = ('usuario__username', 'usuario__email', 'detalle')
    readonly_fields = ('creada_el', 'procesada_el', 'procesada_por')
