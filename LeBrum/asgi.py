"""
ASGI config for LeBrum project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

import os
import importlib.util

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'LeBrum.settings.local')

if importlib.util.find_spec('channels') is not None:
    from channels.auth import AuthMiddlewareStack
    from channels.routing import ProtocolTypeRouter, URLRouter

    from torneos.routing import websocket_urlpatterns

    application = ProtocolTypeRouter({
        'http': get_asgi_application(),
        'websocket': AuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
    })
else:
    application = get_asgi_application()
