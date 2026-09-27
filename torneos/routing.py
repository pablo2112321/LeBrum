"""Rutas WebSocket del dominio de torneos."""

from django.urls import re_path

from .consumers import MatchStateConsumer


websocket_urlpatterns = [
    re_path(r'^ws/torneos/partidas/(?P<partida_id>\d+)/$', MatchStateConsumer.as_asgi()),
]
