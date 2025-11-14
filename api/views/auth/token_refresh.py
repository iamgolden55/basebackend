"""
Token Refresh View with Cookie Support

This module provides a custom token refresh endpoint that works with
httpOnly cookies instead of requiring tokens in request body.

Security Enhancement:
- Reads refresh token from httpOnly cookie (inaccessible to JavaScript)
- Returns new access token also as httpOnly cookie
- Supports token rotation for enhanced security
- Falls back to request body for backwards compatibility
"""

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from django.conf import settings
from api.utils.cookie_helpers import set_jwt_cookies, clear_jwt_cookies


class CookieTokenRefreshView(APIView):
    """
    Refresh JWT access token using refresh token from cookie.

    This endpoint reads the refresh token from the httpOnly cookie,
    validates it, and returns a new access token (also as a cookie).
    Supports token rotation where a new refresh token is also issued.

    Authentication:
        No authentication required (uses refresh token from cookie)

    Request:
        POST /api/token/refresh-cookie/
        No body required (token read from cookie)

        Optional body for backwards compatibility:
        {
            "refresh": "refresh_token_string"
        }

    Response Success (200):
        {
            "status": "success",
            "message": "Token refreshed successfully",
            "tokens": {
                "access": "new_access_token",
                "refresh": "new_refresh_token"  // Only if rotation enabled
            }
        }

        Cookies Set:
        - access_token: New JWT access token (httpOnly, 30 min)
        - refresh_token: New refresh token if rotation enabled (httpOnly, 1 day)

    Response Failure (401):
        {
            "detail": "Refresh token not found in cookie or request body"
        }

        OR

        {
            "detail": "Invalid or expired refresh token"
        }

        Cookies Cleared on failure

    Security:
        - httpOnly cookies prevent JavaScript access (XSS protection)
        - Automatic token rotation reduces token theft impact
        - Failed refresh clears all auth cookies
        - Compatible with CORS via credentials: 'include'

    Example Usage (Frontend):
        ```javascript
        // Cookies automatically sent with request
        const response = await fetch('/api/token/refresh-cookie/', {
            method: 'POST',
            credentials: 'include',  // Important: sends cookies
        });

        // Access token automatically updated in cookie
        // No manual token storage needed
        ```
    """

    # No authentication required - this endpoint is public
    permission_classes = []
    authentication_classes = []

    def post(self, request):
        """
        Refresh access token using refresh token from cookie or request body.

        Process:
        1. Try to get refresh token from cookie
        2. Fall back to request body if cookie not found
        3. Validate refresh token
        4. Generate new access token
        5. If rotation enabled, generate new refresh token
        6. Set new tokens as httpOnly cookies
        7. Return success response
        """
        # Try to get refresh token from cookie first (preferred method)
        refresh_token = request.COOKIES.get(settings.JWT_AUTH_REFRESH_COOKIE)

        # Fall back to request body for backwards compatibility
        # This allows old clients using localStorage to still work
        if not refresh_token:
            refresh_token = request.data.get('refresh')

        # If no refresh token found anywhere, return error
        if not refresh_token:
            return Response(
                {
                    'status': 'error',
                    'detail': 'Refresh token not found in cookie or request body'
                },
                status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            # Validate and refresh the token
            # This checks if the refresh token is valid and not expired
            refresh = RefreshToken(refresh_token)
            access_token = str(refresh.access_token)

            # If token rotation is enabled, generate new refresh token
            # This is a security best practice - each refresh gets a new token
            if settings.SIMPLE_JWT.get('ROTATE_REFRESH_TOKENS', False):
                # Set new JTI (JWT ID) and expiration for refresh token
                refresh.set_jti()
                refresh.set_exp()
                new_refresh_token = str(refresh)
            else:
                # If rotation disabled, reuse the same refresh token
                new_refresh_token = refresh_token

            # Prepare response data
            response_data = {
                'status': 'success',
                'message': 'Token refreshed successfully',
                # Include tokens in response for backwards compatibility
                # Clients using cookies can ignore these
                'tokens': {
                    'access': access_token,
                    'refresh': new_refresh_token
                }
            }

            # Create response object
            response = Response(response_data, status=status.HTTP_200_OK)

            # Set new tokens as httpOnly cookies
            # This is the primary mechanism - cookies are more secure
            set_jwt_cookies(response, access_token, new_refresh_token)

            return response

        except (TokenError, InvalidToken) as e:
            # Token validation failed - token is invalid or expired
            # Clear any existing auth cookies for security
            response = Response(
                {
                    'status': 'error',
                    'detail': 'Invalid or expired refresh token',
                    'error': str(e)
                },
                status=status.HTTP_401_UNAUTHORIZED
            )

            # Clear invalid cookies to prevent confusion
            clear_jwt_cookies(response)

            return response

        except Exception as e:
            # Unexpected error occurred
            response = Response(
                {
                    'status': 'error',
                    'detail': 'An error occurred while refreshing token',
                    'error': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

            # Clear cookies on error for safety
            clear_jwt_cookies(response)

            return response
