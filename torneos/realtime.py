"""Publicación opcional de eventos de partidas por WebSocket."""

from __future__ import annotations

from typing import Any


def publish_match_event(partida: Any, event_type: str = 'match.updated') -> None:
    """Publica un cambio sin romper el flujo si Channels no está instalado."""
    try:
        from asgiref.sync import async_to_sync
        from channels.layers import get_channel_layer
    except ImportError:
        return

    layer = get_channel_layer()
    if layer is None:
        return
    payload = {
        'type': event_type,
        'match': {
            'id': partida.pk,
            'estado': partida.estado,
            'ganador_id': partida.ganador_id,
            'en_disputa': partida.en_disputa,
            'equipo_local_id': partida.equipo_local_id,
            'equipo_visitante_id': partida.equipo_visitante_id,
        },
    }
    try:
        async_to_sync(layer.group_send)(f'match_{partida.pk}', payload)
    except Exception:
        # La actualización HTTP es la fuente de verdad si el layer no está
        # disponible o un backend externo falla.
        return
