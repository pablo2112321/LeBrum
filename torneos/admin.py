from django.contrib import admin, messages
from django.utils.html import format_html, format_html_join

from . import services
from .models import Inscripcion, Partida, Torneo, Videojuego


class InscripcionInline(admin.TabularInline):
    model = Inscripcion
    extra = 0
    fields = (
        'equipo',
        'jugadores_equipo',
        'estado_pago',
        'fichas_usadas',
        'pagador',
        'creado_el',
    )
    readonly_fields = ('jugadores_equipo', 'creado_el')

    @admin.display(description='Jugadores del equipo')
    def jugadores_equipo(self, obj):
        """Muestra los nicknames competitivos del roster inscrito."""
        if not obj.pk or not obj.equipo_id:
            return 'Equipo pendiente'
        jugadores = obj.equipo.miembros.select_related('usuario').order_by(
            '-es_capitan',
            'usuario__username',
        )
        if not jugadores:
            return 'Sin jugadores registrados'
        nicknames = ', '.join(
            miembro.usuario.tag_jugador or miembro.usuario.username
            for miembro in jugadores
        )
        return format_html('{}', nicknames)


class PartidaInline(admin.TabularInline):
    model = Partida
    extra = 0
    fields = (
        'ronda',
        'numero_partida',
        'equipo_local',
        'equipo_visitante',
        'estado',
        'ganador',
        'fecha_hora_programada',
    )


@admin.register(Torneo)
class TorneoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'estado', 'cuota', 'creado_el')
    list_filter = ('estado', 'modalidad', 'juego')
    search_fields = ('nombre', 'descripcion', 'juego__nombre')
    inlines = (InscripcionInline, PartidaInline)
    actions = ('accion_generar_bracket',)
    readonly_fields = ('resumen_bracket',)

    @admin.action(description='Generar bracket del torneo seleccionado')
    def accion_generar_bracket(self, request, queryset):
        generados = 0
        for torneo in queryset:
            try:
                generados += len(services.generar_bracket(torneo))
            except ValueError as exc:
                self.message_user(
                    request,
                    f'{torneo.nombre}: {exc}',
                    level=messages.ERROR,
                )
        if generados:
            self.message_user(
                request,
                f'Se generaron {generados} partidas de primera ronda.',
                level=messages.SUCCESS,
            )

    @admin.display(description='Resumen del bracket')
    def resumen_bracket(self, obj):
        """Resume las partidas del torneo directamente en su ficha administrativa."""
        if not obj.pk:
            return 'Guarda el torneo para consultar sus partidas.'
        partidas = obj.partidas.select_related(
            'equipo_local',
            'equipo_visitante',
            'ganador',
        ).order_by('ronda', 'numero_partida')
        if not partidas:
            return 'No hay partidas generadas.'
        return format_html_join(
            format_html('<br>'),
            'Ronda {} · Partida {}: {} vs {} · {} · Ganador: {}',
            (
                (
                    partida.ronda or 'Sin definir',
                    partida.numero_partida,
                    partida.equipo_local or 'Por definir',
                    partida.equipo_visitante or 'Por definir',
                    partida.get_estado_display(),
                    partida.ganador or 'Pendiente',
                )
                for partida in partidas
            ),
        )


@admin.register(Partida)
class PartidaAdmin(admin.ModelAdmin):
    list_display = (
        'torneo',
        'ronda',
        'numero_partida',
        'equipo_local',
        'equipo_visitante',
        'estado',
        'ganador',
    )
    list_filter = ('torneo', 'estado', 'ronda', 'en_disputa')
    search_fields = (
        'torneo__nombre',
        'equipo_local__nombre',
        'equipo_visitante__nombre',
    )
    actions = (
        'declarar_ganador_local',
        'declarar_ganador_visitante',
        'resolver_disputa_local',
        'resolver_disputa_visitante',
    )

    def _declarar_ganador(
        self,
        request,
        queryset,
        equipo_field: str,
        force: bool = False,
    ) -> None:
        procesadas = 0
        for partida in queryset.select_related(
            'equipo_local',
            'equipo_visitante',
        ):
            equipo_ganador = getattr(partida, equipo_field)
            if equipo_ganador is None:
                self.message_user(
                    request,
                    f'La partida #{partida.pk} no tiene equipo asignado en esa posición.',
                    level=messages.ERROR,
                )
                continue
            try:
                services.procesar_resultado(partida, equipo_ganador, force=force)
                procesadas += 1
            except ValueError as exc:
                self.message_user(
                    request,
                    f'Partida #{partida.pk}: {exc}',
                    level=messages.ERROR,
                )
        if procesadas:
            self.message_user(
                request,
                f'Se procesaron {procesadas} partida(s) correctamente.',
                level=messages.SUCCESS,
            )

    @admin.action(description='Declarar ganador al Local')
    def declarar_ganador_local(self, request, queryset):
        self._declarar_ganador(request, queryset, 'equipo_local')

    @admin.action(description='Declarar ganador al Visitante')
    def declarar_ganador_visitante(self, request, queryset):
        self._declarar_ganador(request, queryset, 'equipo_visitante')

    @admin.action(description='Resolver Disputa: Forzar Ganador Local')
    def resolver_disputa_local(self, request, queryset):
        self._declarar_ganador(request, queryset, 'equipo_local', force=True)

    @admin.action(description='Resolver Disputa: Forzar Ganador Visitante')
    def resolver_disputa_visitante(self, request, queryset):
        self._declarar_ganador(request, queryset, 'equipo_visitante', force=True)


@admin.register(Inscripcion)
class InscripcionAdmin(admin.ModelAdmin):
    list_display = ('equipo', 'torneo', 'creado_el', 'estado_pago')
    list_filter = ('estado_pago', 'torneo')
    search_fields = ('torneo__nombre', 'equipo__nombre')
    actions = ('accion_marcar_pagado',)

    @admin.action(description='Marcar inscripciones como Pagado')
    def accion_marcar_pagado(self, request, queryset):
        torneos = {inscripcion.torneo for inscripcion in queryset.select_related('torneo')}
        actualizadas = queryset.update(estado_pago=Inscripcion.ESTADO_PAGADO)
        for torneo in torneos:
            torneo.actualizar_estado_capacidad()
        self.message_user(
            request,
            f'{actualizadas} inscripción(es) marcada(s) como Pagado.',
            level=messages.SUCCESS,
        )


@admin.register(Videojuego)
class VideojuegoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'genero', 'imagen_portada')
    fields = ('nombre', 'genero', 'imagen_portada')
    search_fields = ('nombre', 'genero')
