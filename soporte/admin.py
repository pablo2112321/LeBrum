from django.contrib import admin

from .models import MensajeTicket, TicketSoporte


class MensajeTicketInline(admin.TabularInline):
    model = MensajeTicket
    extra = 0
    readonly_fields = ('fecha_envio',)
    fields = ('remitente', 'contenido_mensaje', 'url_adjunto', 'fecha_envio')


@admin.register(TicketSoporte)
class TicketSoporteAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'categoria', 'estado', 'partida', 'fecha_creacion')
    list_filter = ('estado', 'categoria', 'fecha_creacion')
    search_fields = ('usuario__username', 'usuario__email', 'mensajes__contenido_mensaje')
    autocomplete_fields = ('usuario', 'partida')
    readonly_fields = ('fecha_creacion', 'fecha_termino')
    inlines = (MensajeTicketInline,)
    date_hierarchy = 'fecha_creacion'


@admin.register(MensajeTicket)
class MensajeTicketAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'remitente', 'fecha_envio')
    search_fields = ('contenido_mensaje', 'remitente__username')
    list_filter = ('fecha_envio',)
    readonly_fields = ('fecha_envio',)
