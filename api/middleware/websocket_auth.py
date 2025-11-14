"""
Custom WebSocket authentication middleware for JWT tokens
"""

import logging
from urllib.parse import parse_qs
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.db import close_old_connections
from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
import jwt
from django.conf import settings

logger = logging.getLogger('messaging.websocket')
User = get_user_model()


@database_sync_to_async
def get_user_from_token(token_string):
    """
    Get user from JWT token string
    """
    try:
        # Validate the token
        UntypedToken(token_string)
        
        # Decode the token to get user info
        decoded_data = jwt.decode(
            token_string, 
            settings.SECRET_KEY, 
            algorithms=["HS256"]
        )
        
        # Get user from the token
        user_id = decoded_data.get('user_id')
        if user_id:
            user = User.objects.get(id=user_id)
            return user
        
    except (InvalidToken, TokenError, User.DoesNotExist, jwt.ExpiredSignatureError, jwt.InvalidTokenError) as e:
        logger.warning(f"Invalid WebSocket token: {e}")
        
    return AnonymousUser()


class JWTAuthMiddleware(BaseMiddleware):
    """
    Custom middleware that takes JWT token from query string and authenticates user
    """
    
    async def __call__(self, scope, receive, send):
        # Close old database connections to prevent usage of timed out connections
        close_old_connections()
        
        # Get token from query string
        query_string = scope.get('query_string', b'').decode()
        query_params = parse_qs(query_string)
        token = query_params.get('token', [None])[0]
        
        if token:
            logger.info(f"WebSocket connection with token: {token[:20]}...")
            scope['user'] = await get_user_from_token(token)
            logger.info(f"Authenticated user: {scope['user']}")
        else:
            logger.warning("WebSocket connection without token")
            scope['user'] = AnonymousUser()
        
        return await super().__call__(scope, receive, send)


def JWTAuthMiddlewareStack(inner):
    """
    Create a middleware stack with JWT authentication
    """
    return JWTAuthMiddleware(inner)