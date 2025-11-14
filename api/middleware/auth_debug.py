"""
Authentication Debug Middleware
Logs cookie and authentication information for debugging
"""
import logging

logger = logging.getLogger(__name__)


class AuthDebugMiddleware:
    """
    Middleware to debug authentication issues
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only log for medical record OTP endpoint
        if 'medical-record' in request.path:
            logger.info(f"🔍 Auth Debug for {request.path}")
            logger.info(f"  Method: {request.method}")
            logger.info(f"  Cookies: {list(request.COOKIES.keys())}")
            logger.info(f"  Has access_token cookie: {'access_token' in request.COOKIES}")
            logger.info(f"  Authorization header: {request.headers.get('Authorization', 'Not present')}")
            logger.info(f"  User authenticated: {request.user.is_authenticated if hasattr(request, 'user') else 'No user yet'}")

        response = self.get_response(request)

        # Log response for debugging
        if 'medical-record' in request.path:
            logger.info(f"  Response status: {response.status_code}")
            if hasattr(request, 'user'):
                logger.info(f"  Final user: {request.user} (authenticated: {request.user.is_authenticated})")

        return response
