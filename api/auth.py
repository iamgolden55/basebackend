from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

class EmailBackend(ModelBackend):
    def authenticate(self, request, username=None, email=None, password=None, **kwargs):
        UserModel = get_user_model()
        
        # Try to authenticate with email if provided
        if email:
            try:
                user = UserModel.objects.get(email=email)
                if user.check_password(password):
                    return user
            except UserModel.DoesNotExist:
                return None
        
        # Fall back to username authentication
        if username:
            try:
                # Try to find user by username or email
                user = UserModel.objects.get(
                    Q(username=username) | Q(email=username)
                )
                if user.check_password(password):
                    return user
            except UserModel.DoesNotExist:
                return None

        return None


# JWT Cookie Authentication for httpOnly cookie-based auth
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.conf import settings


class JWTCookieAuthentication(JWTAuthentication):
    """
    Custom JWT authentication that checks for tokens in cookies first,
    then falls back to Authorization header for backwards compatibility.

    This provides enhanced security by storing JWT tokens in httpOnly cookies,
    making them inaccessible to JavaScript and protecting against XSS attacks.
    """

    def authenticate(self, request):
        # First, try to get token from cookie
        cookie_name = getattr(settings, 'JWT_AUTH_COOKIE', 'access_token')
        raw_token = request.COOKIES.get(cookie_name)

        if raw_token is None:
            # Fall back to Authorization header for backwards compatibility
            return super().authenticate(request)

        # Validate the cookie token
        try:
            validated_token = self.get_validated_token(raw_token)
            return self.get_user(validated_token), validated_token
        except (InvalidToken, TokenError):
            # If cookie token is invalid, try header as fallback
            return super().authenticate(request)

