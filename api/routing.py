"""
WebSocket URL routing for healthcare messaging system

This module defines the WebSocket URL patterns for real-time messaging,
including chat rooms, presence updates, and notification channels.
"""

from django.urls import re_path
from api.consumers.messaging import (
    ChatConsumer,
    PresenceConsumer,
    NotificationConsumer,
    TypingIndicatorConsumer
)

websocket_urlpatterns = [
    # Chat room WebSocket - for real-time messaging in conversations
    re_path(r'ws/chat/(?P<conversation_id>[0-9a-f-]{36})/$', ChatConsumer.as_asgi()),
    
    # Presence updates - for online/offline status and last seen
    re_path(r'ws/presence/$', PresenceConsumer.as_asgi()),
    
    # Real-time notifications - for emergency alerts, mentions, etc.
    re_path(r'ws/notifications/$', NotificationConsumer.as_asgi()),
    
    # Typing indicators - for "user is typing..." functionality
    re_path(r'ws/typing/(?P<conversation_id>[0-9a-f-]{36})/$', TypingIndicatorConsumer.as_asgi()),
]