# utils.py
from django.core.cache import cache
from rest_framework.response import Response
from functools import wraps
from datetime import datetime, timedelta

def rate_limit_otp(attempts=5, window=300):  # 5 attempts per 5 minutes
    def decorator(func):
        @wraps(func)
        def wrapper(self, request, *args, **kwargs):
            ip = request.META.get('REMOTE_ADDR')
            email = request.data.get('email', '')
            cache_key = f'otp_attempts:{ip}:{email}'
            
            attempts_data = cache.get(cache_key, {'count': 0, 'first_attempt': datetime.now()})
            
            # Reset attempts if window has passed
            if datetime.now() - attempts_data['first_attempt'] > timedelta(seconds=window):
                attempts_data = {'count': 0, 'first_attempt': datetime.now()}
            
            if attempts_data['count'] >= attempts:
                return Response({
                    'error': 'Too many attempts. Please try again later.',
                    'wait_time': str(timedelta(seconds=window))
                }, status=429)
            
            attempts_data['count'] += 1
            cache.set(cache_key, attempts_data, window)
            
            return func(self, request, *args, **kwargs)
        return wrapper
    return decorator