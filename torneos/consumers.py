"""Consumer de estado de partidas para los capitanes participantes."""

from __future__ import annotations

from typing import Any

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from .models import Partida


class MatchStateConsumer(AsyncJsonWebsocketConsumer):
    """Entrega cambios de una partida exclusivamente a sus capitanes."""

    partida_id: int
    group_name: str

    async def connect(self) -> None:
        user = self.scope.get('user')
        try:
            self.partida_id = int(self.scope['url_route']['kwargs']['partida_id'])
        except (KeyError, TypeError, ValueError):
            await self.close(code=4400)
            return

        if not user or not user.is_authenticated or not await self._is_captain(user.pk):
            await self.close(code=4403)
            return

        self.group_name = f'match_{self.partida_id}'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        state = await self._state()
        if state is not None:
            await self.send_json({'type': 'match.snapshot', 'match': state})

    async def disconnect(self, close_code: int) -> None:
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def match_updated(self, event: dict[str, Any]) -> None:
        await self.send_json({
            'type': event.get('type', 'match.updated'),
            'match': event.get('match', {}),
        })

    @database_sync_to_async
    def _is_captain(self, user_id: int) -> bool:
        return Partida.objects.filter(pk=self.partida_id).filter(
            equipo_local__capitan_id=user_id,
        ).exists() or Partida.objects.filter(pk=self.partida_id).filter(
            equipo_visitante__capitan_id=user_id,
        ).exists()

    @database_sync_to_async
    def _state(self) -> dict[str, Any] | None:
        partida = Partida.objects.filter(pk=self.partida_id).first()
        if partida is None:
            return None
        return {
            'id': partida.pk,
            'estado': partida.estado,
            'ganador_id': partida.ganador_id,
            'en_disputa': partida.en_disputa,
            'equipo_local_id': partida.equipo_local_id,
            'equipo_visitante_id': partida.equipo_visitante_id,
        }
