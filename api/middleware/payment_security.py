from django.core.cache import cache
from django.http import HttpResponseForbidden
from django.conf import settings
from django.utils import timezone
import json

class PaymentSecurityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/api/payments/'):
            try:
                # Get client info
                ip = self.get_client_ip(request)
                
                # Check IP blocking
                if self.is_ip_blocked(ip):
                    return HttpResponseForbidden('IP blocked for security reasons')
                
                # Check rate limiting
                if self.is_rate_limited(ip):
                    return HttpResponseForbidden('Too many payment requests')
                
                # Check country restrictions
                if not self.is_country_allowed(request):
                    return HttpResponseForbidden('Country not supported for payments')
                
                # Check for suspicious patterns
                if self.is_suspicious_activity(request):
                    self.log_suspicious_activity(request)
                    return HttpResponseForbidden('Suspicious activity detected')
                
                # Track daily transaction amounts
                if request.method == 'POST':
                    if self.exceeds_daily_limit(request):
                        return HttpResponseForbidden('Daily transaction limit exceeded')
                
            except Exception as e:
                self.log_security_error(request, e)
                return HttpResponseForbidden('Payment security check failed')
        
        return self.get_response(request)
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')
    
    def is_ip_blocked(self, ip):
        """Check if IP is in blocked list"""
        # Check static blocked IPs
        if ip in settings.PAYMENT_SECURITY['blocked_ips']:
            return True
            
        # Check dynamically blocked IPs
        return cache.get(f'blocked_ip_{ip}', False)
    
    def is_rate_limited(self, ip):
        """Check and update rate limiting"""
        window = settings.PAYMENT_SECURITY['rate_limit']['window']
        max_requests = settings.PAYMENT_SECURITY['rate_limit']['max_requests']
        
        # Get current count
        key = f'payment_requests_{ip}'
        count = cache.get(key, 0)
        
        if count >= max_requests:
            return True
            
        # Increment count
        if count == 0:
            cache.set(key, 1, window)  # Set with expiry
        else:
            cache.incr(key)
            
        return False
    
    def is_country_allowed(self, request):
        """Check if request country is allowed"""
        country_code = request.META.get('HTTP_CF_IPCOUNTRY')  # If using Cloudflare
        if not country_code:
            # Implement your geolocation logic here
            return True  # Default to True if can't determine
            
        return country_code in settings.PAYMENT_SECURITY['allowed_countries']
    
    def is_suspicious_activity(self, request):
        """Check for suspicious patterns"""
        if request.method != 'POST':
            return False
            
        try:
            data = json.loads(request.body)
            
            # Check for rapid successive attempts
            key = f"payment_attempts_{self.get_client_ip(request)}"
            attempts = cache.get(key, [])
            now = timezone.now().timestamp()
            
            # Remove old attempts
            attempts = [t for t in attempts if now - t < 300]  # Last 5 minutes
            
            if len(attempts) >= settings.PAYMENT_SECURITY['max_attempts']:
                return True
                
            attempts.append(now)
            cache.set(key, attempts, 300)
            
            # Add more suspicious patterns here
            
            return False
            
        except:
            return True
    
    def exceeds_daily_limit(self, request):
        """Check if transaction exceeds daily limit"""
        try:
            data = json.loads(request.body)
            amount = float(data.get('amount', 0))
            
            ip = self.get_client_ip(request)
            key = f"daily_transactions_{ip}_{timezone.now().date()}"
            
            total = cache.get(key, 0)
            new_total = total + amount
            
            if new_total > settings.PAYMENT_SECURITY['daily_limit']:
                return True
                
            cache.set(key, new_total, 86400)  # 24 hours
            return False
            
        except:
            return True
    
    def log_suspicious_activity(self, request):
        """Log suspicious payment activity"""
        from django.core.mail import send_mail
        
        ip = self.get_client_ip(request)
        
        # Log to cache for temporary tracking
        key = f"suspicious_activity_{ip}"
        activities = cache.get(key, [])
        activities.append({
            'timestamp': timezone.now().isoformat(),
            'path': request.path,
            'method': request.method,
            'user_agent': request.META.get('HTTP_USER_AGENT'),
        })
        cache.set(key, activities, 86400)
        
        # If multiple suspicious activities, block IP
        if len(activities) >= 3:
            cache.set(f'blocked_ip_{ip}', True, 3600)  # Block for 1 hour
            
            # Alert security team
            send_mail(
                'Suspicious Payment Activity Detected',
                f'Multiple suspicious payment activities detected from IP: {ip}',
                settings.DEFAULT_FROM_EMAIL,
                [settings.SECURITY_TEAM_EMAIL],
                fail_silently=True,
            )
    
    def log_security_error(self, request, error):
        """Log security-related errors"""
        from django.core.mail import send_mail
        
        error_data = {
            'timestamp': timezone.now().isoformat(),
            'ip': self.get_client_ip(request),
            'path': request.path,
            'method': request.method,
            'error': str(error),
        }
        
        # Log to cache for monitoring
        key = 'payment_security_errors'
        errors = cache.get(key, [])
        errors.append(error_data)
        cache.set(key, errors[-100:], 86400)  # Keep last 100 errors
        
        # Alert if critical error
        if isinstance(error, (ValueError, TypeError)):
            send_mail(
                'Payment Security Error',
                f'Critical payment security error detected: {error}',
                settings.DEFAULT_FROM_EMAIL,
                [settings.SECURITY_TEAM_EMAIL],
                fail_silently=True,
            ) 