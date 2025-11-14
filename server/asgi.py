"""
ASGI config for healthcare messaging server

This module contains the ASGI application used by Django Channels
for handling both HTTP and WebSocket connections.
"""

import os
import django
from django.core.asgi import get_asgi_application

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')

# Initialize Django before importing models/consumers
django.setup()

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
from api.routing import websocket_urlpatterns
from api.middleware.websocket_auth import JWTAuthMiddlewareStack

# Create ASGI application that handles both HTTP and WebSocket
application = ProtocolTypeRouter({
    # Django's ASGI application to handle traditional HTTP requests
    "http": get_asgi_application(),
    
    # WebSocket chat handler with JWT authentication and security
    "websocket": AllowedHostsOriginValidator(
        JWTAuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
    ),
})
