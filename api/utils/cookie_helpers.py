"""
Cookie Helper Functions for JWT Authentication

This module provides utility functions for managing httpOnly cookies
used to store JWT authentication tokens securely. These cookies are
inaccessible to JavaScript, providing protection against XSS attacks.

Security Features:
- HttpOnly flag prevents JavaScript access
- Secure flag ensures HTTPS-only transmission in production
- SameSite flag prevents CSRF attacks
"""

from django.conf import settings
from datetime import datetime, timedelta


def set_jwt_cookies(response, access_token, refresh_token):
    """
    Set JWT access and refresh tokens as httpOnly cookies.

    This function sets both access and refresh JWT tokens as secure httpOnly
    cookies on the response object. The cookies are configured with security
    flags to prevent XSS and CSRF attacks.

    Args:
        response: Django HttpResponse object
        access_token: JWT access token string
        refresh_token: JWT refresh token string

    Returns:
        Modified response object with cookies set

    Security:
        - HttpOnly: True (prevents JavaScript access)
        - Secure: True in production (HTTPS only)
        - SameSite: Lax (prevents CSRF, allows navigation)

    Example:
        ```python
        from rest_framework.response import Response
        from api.utils.cookie_helpers import set_jwt_cookies

        response = Response({'status': 'success'})
        set_jwt_cookies(response, access_token, refresh_token)
        return response
        ```
    """
    # Access token cookie - short-lived (30 minutes)
    response.set_cookie(
        key=settings.JWT_AUTH_COOKIE,
        value=access_token,
        max_age=settings.JWT_AUTH_COOKIE_MAX_AGE,
        httponly=settings.JWT_AUTH_HTTPONLY,
        secure=settings.JWT_AUTH_SECURE,
        samesite=settings.JWT_AUTH_SAMESITE,
        domain=settings.SESSION_COOKIE_DOMAIN if hasattr(settings, 'SESSION_COOKIE_DOMAIN') else None,
        path='/',  # Cookie available for all paths
    )

    # Refresh token cookie - long-lived (1 day)
    response.set_cookie(
        key=settings.JWT_AUTH_REFRESH_COOKIE,
        value=refresh_token,
        max_age=settings.JWT_AUTH_REFRESH_COOKIE_MAX_AGE,
        httponly=settings.JWT_AUTH_HTTPONLY,
        secure=settings.JWT_AUTH_SECURE,
        samesite=settings.JWT_AUTH_SAMESITE,
        domain=settings.SESSION_COOKIE_DOMAIN if hasattr(settings, 'SESSION_COOKIE_DOMAIN') else None,
        path='/',  # Cookie available for all paths
    )

    return response


def clear_jwt_cookies(response):
    """
    Clear JWT authentication cookies (used during logout).

    This function removes both access and refresh token cookies by setting
    their max_age to 0, effectively deleting them from the client's browser.

    Args:
        response: Django HttpResponse object

    Returns:
        Modified response object with cookies cleared

    Example:
        ```python
        from rest_framework.response import Response
        from api.utils.cookie_helpers import clear_jwt_cookies

        response = Response({'status': 'logged out'})
        clear_jwt_cookies(response)
        return response
        ```

    Security:
        This should be called on logout to ensure tokens are properly
        removed from the client, preventing unauthorized access.
    """
    # Clear access token cookie
    response.delete_cookie(
        key=settings.JWT_AUTH_COOKIE,
        path='/',
        domain=settings.SESSION_COOKIE_DOMAIN if hasattr(settings, 'SESSION_COOKIE_DOMAIN') else None,
        samesite=settings.JWT_AUTH_SAMESITE,
    )

    # Clear refresh token cookie
    response.delete_cookie(
        key=settings.JWT_AUTH_REFRESH_COOKIE,
        path='/',
        domain=settings.SESSION_COOKIE_DOMAIN if hasattr(settings, 'SESSION_COOKIE_DOMAIN') else None,
        samesite=settings.JWT_AUTH_SAMESITE,
    )

    return response


def get_jwt_token_from_cookie(request, cookie_name=None):
    """
    Extract JWT token from httpOnly cookie.

    This helper function retrieves the JWT token from the request cookies.
    It's primarily used by the JWTCookieAuthentication class.

    Args:
        request: Django HttpRequest object
        cookie_name: Optional cookie name (defaults to settings.JWT_AUTH_COOKIE)

    Returns:
        JWT token string or None if not found

    Example:
        ```python
        from api.utils.cookie_helpers import get_jwt_token_from_cookie

        token = get_jwt_token_from_cookie(request)
        if token:
            # Token found, validate it
            pass
        ```
    """
    if cookie_name is None:
        cookie_name = settings.JWT_AUTH_COOKIE

    return request.COOKIES.get(cookie_name)


def get_refresh_token_from_cookie(request):
    """
    Extract JWT refresh token from httpOnly cookie.

    Convenience function to get the refresh token specifically.

    Args:
        request: Django HttpRequest object

    Returns:
        Refresh token string or None if not found
    """
    return request.COOKIES.get(settings.JWT_AUTH_REFRESH_COOKIE)
