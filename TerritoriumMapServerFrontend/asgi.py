"""
ASGI config for TerritoriumMapServerFrontend project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/howto/deployment/asgi/
"""

import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter, ChannelNameRouter
from django.core.asgi import get_asgi_application
from django.urls import re_path

from fileserver import consumers

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'TerritoriumMapServerFrontend.settings')

application = ProtocolTypeRouter(
    {
        "http": AuthMiddlewareStack(URLRouter([re_path(r'', get_asgi_application())])),
        "channel": ChannelNameRouter({
            "mq": consumers.MqConsumer.as_asgi(),
        }),
    }
)
