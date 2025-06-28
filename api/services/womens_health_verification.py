# api/services/womens_health_verification.py

import random
import string
from datetime import timedelta
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class WomensHealthVerificationService:
    """Service for handling women's health verification via OTP"""
    
    OTP_LENGTH = 6
    OTP_EXPIRY_MINUTES = 5
    MAX_OTP_REQUESTS_PER_HOUR = 5
    MAX_VERIFICATION_ATTEMPTS = 3
    
    @classmethod
    def generate_otp(cls) -> str:
        """Generate a 6-digit OTP"""
        return ''.join(random.choices(string.digits, k=cls.OTP_LENGTH))
    
    @classmethod
    def is_otp_expired(cls, otp_created_at) -> bool:
        """Check if OTP has expired"""
        if not otp_created_at:
            return True
        
        now = timezone.now()
        expiry_time = otp_created_at + timedelta(minutes=cls.OTP_EXPIRY_MINUTES)
        return now > expiry_time
    
    @classmethod
    def validate_otp_format(cls, otp: str) -> bool:
        """Validate OTP format"""
        if not otp:
            return False
        
        return otp.isdigit() and len(otp) == cls.OTP_LENGTH
    
    @classmethod
    def check_rate_limit(cls, user) -> bool:
        """Check if user has exceeded OTP request rate limit"""
        if not user.womens_health_otp_created_at:
            return True
        
        now = timezone.now()
        one_hour_ago = now - timedelta(hours=1)
        
        # In a real implementation, this would track multiple requests
        # For now, we'll just check if the last request was recent
        if user.womens_health_otp_created_at > one_hour_ago:
            # Simple rate limiting - allow if last request was more than 1 minute ago
            one_minute_ago = now - timedelta(minutes=1)
            return user.womens_health_otp_created_at < one_minute_ago
        
        return True
    
    @classmethod
    def send_verification_email(cls, user, otp: str) -> bool:
        """Send OTP verification email to user"""
        try:
            subject = "Women's Health Verification Code - PHB"
            
            message = f"""
Hello {user.get_full_name() or user.email},

Your verification code for accessing Women's Health features is:

{otp}

This code will expire in {cls.OTP_EXPIRY_MINUTES} minutes.

If you didn't request this verification, please ignore this email.

Best regards,
PHB Health Team
            """.strip()
            
            html_message = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Women's Health Verification</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; }}
        .header {{ background-color: #e91e63; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; }}
        .otp {{ font-size: 32px; font-weight: bold; color: #e91e63; text-align: center; margin: 20px 0; padding: 15px; background-color: #f5f5f5; border-radius: 8px; }}
        .footer {{ color: #666; font-size: 12px; text-align: center; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Women's Health Verification</h1>
    </div>
    <div class="content">
        <p>Hello {user.get_full_name() or user.email},</p>
        
        <p>Your verification code for accessing Women's Health features is:</p>
        
        <div class="otp">{otp}</div>
        
        <p>This code will expire in <strong>{cls.OTP_EXPIRY_MINUTES} minutes</strong>.</p>
        
        <p>If you didn't request this verification, please ignore this email.</p>
        
        <div class="footer">
            <p>Best regards,<br>PHB Health Team</p>
        </div>
    </div>
</body>
</html>
            """.strip()
            
            send_mail(
                subject=subject,
                message=message,
                html_message=html_message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@phb.com'),
                recipient_list=[user.email],
                fail_silently=False,
            )
            
            logger.info(f"Verification email sent to user {user.id} ({user.email})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send verification email to user {user.id}: {str(e)}")
            return False
    
    @classmethod
    def request_verification(cls, user) -> dict:
        """
        Request verification OTP for user
        
        Returns:
            dict: {'success': bool, 'message': str, 'otp': str (only in debug mode)}
        """
        try:
            # Check if user is already verified
            if user.womens_health_verified:
                return {
                    'success': False,
                    'message': 'User is already verified for women\'s health features'
                }
            
            # Check rate limiting
            if not cls.check_rate_limit(user):
                return {
                    'success': False,
                    'message': 'Too many requests. Please wait before requesting another verification code.'
                }
            
            # Generate new OTP
            otp = cls.generate_otp()
            
            # Store OTP with atomic transaction
            with transaction.atomic():
                user.womens_health_otp = otp
                user.womens_health_otp_created_at = timezone.now()
                user.save(update_fields=['womens_health_otp', 'womens_health_otp_created_at'])
            
            # Send email
            email_sent = cls.send_verification_email(user, otp)
            
            if not email_sent:
                # Clear OTP if email failed
                user.womens_health_otp = None
                user.womens_health_otp_created_at = None
                user.save(update_fields=['womens_health_otp', 'womens_health_otp_created_at'])
                
                return {
                    'success': False,
                    'message': 'Failed to send verification email. Please try again later.'
                }
            
            result = {
                'success': True,
                'message': f'Verification code sent to {user.email}. Code expires in {cls.OTP_EXPIRY_MINUTES} minutes.'
            }
            
            # Include OTP in response only in debug mode
            if getattr(settings, 'DEBUG', False):
                result['otp'] = otp
            
            logger.info(f"OTP verification requested for user {user.id}")
            return result
            
        except Exception as e:
            logger.error(f"Error requesting verification for user {user.id}: {str(e)}")
            return {
                'success': False,
                'message': 'An error occurred while processing your request. Please try again later.'
            }
    
    @classmethod
    def verify_otp(cls, user, provided_otp: str) -> dict:
        """
        Verify OTP and complete verification if valid
        
        Returns:
            dict: {'success': bool, 'message': str, 'verified': bool}
        """
        try:
            # Validate OTP format
            if not cls.validate_otp_format(provided_otp):
                return {
                    'success': False,
                    'message': 'Invalid verification code format. Please enter a 6-digit code.',
                    'verified': False
                }
            
            # Check if user already verified
            if user.womens_health_verified:
                return {
                    'success': True,
                    'message': 'User is already verified for women\'s health features',
                    'verified': True
                }
            
            # Check if OTP exists
            if not user.womens_health_otp:
                return {
                    'success': False,
                    'message': 'No verification code found. Please request a new code.',
                    'verified': False
                }
            
            # Check if OTP is expired
            if cls.is_otp_expired(user.womens_health_otp_created_at):
                # Clear expired OTP
                user.womens_health_otp = None
                user.womens_health_otp_created_at = None
                user.save(update_fields=['womens_health_otp', 'womens_health_otp_created_at'])
                
                return {
                    'success': False,
                    'message': 'Verification code has expired. Please request a new code.',
                    'verified': False
                }
            
            # Check if OTP matches
            if user.womens_health_otp != provided_otp:
                logger.warning(f"Invalid OTP attempt for user {user.id}")
                return {
                    'success': False,
                    'message': 'Invalid verification code. Please check and try again.',
                    'verified': False
                }
            
            # OTP is valid - complete verification
            with transaction.atomic():
                user.womens_health_verified = True
                user.womens_health_verification_date = timezone.now()
                user.womens_health_otp = None  # Clear OTP after successful verification
                user.womens_health_otp_created_at = None
                user.save(update_fields=[
                    'womens_health_verified',
                    'womens_health_verification_date',
                    'womens_health_otp',
                    'womens_health_otp_created_at'
                ])
            
            logger.info(f"User {user.id} successfully verified for women's health features")
            
            return {
                'success': True,
                'message': 'Verification successful! You now have access to women\'s health features.',
                'verified': True
            }
            
        except Exception as e:
            logger.error(f"Error verifying OTP for user {user.id}: {str(e)}")
            return {
                'success': False,
                'message': 'An error occurred during verification. Please try again later.',
                'verified': False
            }
    
    @classmethod
    def get_verification_status(cls, user) -> dict:
        """
        Get current verification status for user
        
        Returns:
            dict: {'verified': bool, 'verification_date': datetime, 'has_pending_otp': bool}
        """
        return {
            'verified': user.womens_health_verified,
            'verification_date': user.womens_health_verification_date,
            'has_pending_otp': bool(user.womens_health_otp and not cls.is_otp_expired(user.womens_health_otp_created_at)),
            'otp_expires_at': (
                user.womens_health_otp_created_at + timedelta(minutes=cls.OTP_EXPIRY_MINUTES)
                if user.womens_health_otp_created_at else None
            )
        }
    
    @classmethod
    def cleanup_expired_otps(cls) -> int:
        """
        Clean up expired OTPs from the database
        
        Returns:
            int: Number of expired OTPs cleaned up
        """
        try:
            expiry_threshold = timezone.now() - timedelta(minutes=cls.OTP_EXPIRY_MINUTES)
            
            expired_otps = User.objects.filter(
                womens_health_otp__isnull=False,
                womens_health_otp_created_at__lt=expiry_threshold
            )
            
            count = expired_otps.count()
            
            expired_otps.update(
                womens_health_otp=None,
                womens_health_otp_created_at=None
            )
            
            logger.info(f"Cleaned up {count} expired OTPs")
            return count
            
        except Exception as e:
            logger.error(f"Error cleaning up expired OTPs: {str(e)}")
            return 0
    
    @classmethod
    def revoke_verification(cls, user, reason: str = None) -> bool:
        """
        Revoke women's health verification for a user
        
        Args:
            user: User instance
            reason: Optional reason for revocation
            
        Returns:
            bool: Success status
        """
        try:
            with transaction.atomic():
                user.womens_health_verified = False
                user.womens_health_verification_date = None
                user.womens_health_otp = None
                user.womens_health_otp_created_at = None
                user.save(update_fields=[
                    'womens_health_verified',
                    'womens_health_verification_date',
                    'womens_health_otp',
                    'womens_health_otp_created_at'
                ])
            
            logger.info(f"Verification revoked for user {user.id}. Reason: {reason or 'Not specified'}")
            return True
            
        except Exception as e:
            logger.error(f"Error revoking verification for user {user.id}: {str(e)}")
            return False


class WomensHealthPermissionMixin:
    """Mixin to check women's health verification permission"""
    
    def check_womens_health_permission(self, user) -> bool:
        """Check if user has women's health permission"""
        return user.is_authenticated and user.womens_health_verified
    
    def require_womens_health_verification(self, user):
        """Raise ValidationError if user is not verified"""
        if not self.check_womens_health_permission(user):
            raise ValidationError(
                "Access to women's health features requires verification. "
                "Please complete the verification process first."
            )


def requires_womens_health_verification(view_func):
    """Decorator to require women's health verification for view functions"""
    def wrapped_view(request, *args, **kwargs):
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            from django.http import JsonResponse
            return JsonResponse(
                {'error': 'Authentication required'}, 
                status=401
            )
        
        if not request.user.womens_health_verified:
            from django.http import JsonResponse
            return JsonResponse(
                {'error': 'Women\'s health verification required'}, 
                status=403
            )
        
        return view_func(request, *args, **kwargs)
    
    return wrapped_view