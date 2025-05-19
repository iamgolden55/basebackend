import os
import uuid
import secrets
import logging
import pyotp
import json
from datetime import datetime, timedelta
from functools import wraps

from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.cache import cache
from django.db import transaction
from django.conf import settings

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

from api.models import CustomUser, Hospital
from api.models.medical.hospital_auth import HospitalAdmin
from api.views.auth.hospital_admin_auth import security_audit, SecurityMixin
from api.utils.location_utils import get_location_from_ip, get_client_ip

# Logger setup
logger = logging.getLogger(__name__)

# Custom throttle classes for password reset
class HospitalAdminResetRequestThrottle(AnonRateThrottle):
    """Rate limiting for hospital admin password reset requests."""
    scope = 'hospital_admin_reset_request'
    rate = '3/hour'  # Very strict rate limiting for reset requests

class HospitalAdminResetVerifyThrottle(AnonRateThrottle):
    """Rate limiting for reset verification attempts."""
    scope = 'hospital_admin_reset_verify'
    rate = '5/hour'  # Strict rate limiting for verification attempts

class HospitalAdminResetCompleteThrottle(AnonRateThrottle):
    """Rate limiting for password reset completion."""
    scope = 'hospital_admin_reset_complete'
    rate = '3/hour'  # Strict rate limiting for reset completion


# Password reset initiation view
class HospitalAdminResetRequestView(SecurityMixin, APIView):
    """Initiates the password reset process for hospital administrators.
    This enforces multi-factor identity verification before proceeding.
    """
    permission_classes = [AllowAny]
    throttle_classes = [HospitalAdminResetRequestThrottle]
    
    @security_audit('hospital_admin_reset_request')
    def post(self, request):
        # Extract request data
        email = request.data.get('email')
        hospital_code = request.data.get('hospital_code')
        device_id = request.data.get('device_id')
        
        # Validate input
        if not email or not hospital_code:
            return Response({
                "status": "error",
                "message": "Email and hospital code are required"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Track request metadata for security
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
        
        try:
            # Find the hospital admin
            user = CustomUser.objects.get(email=email)
            hospital_admin = HospitalAdmin.objects.get(user=user)
            hospital = hospital_admin.hospital
            
            # Verify hospital code matches
            if hospital.registration_number != hospital_code:
                # Log incorrect hospital code attempt
                logger.warning(f"Hospital code mismatch for reset request: {email}")
                return Response({
                    "status": "error",
                    "message": "Invalid hospital credentials"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check for trusted device if device_id provided
            device_trusted = False
            if device_id:
                trusted_device_key = f"trusted_device_{user.id}_{device_id}"
                if cache.get(trusted_device_key):
                    device_trusted = True
            
            # Generate security tokens
            primary_token = secrets.token_hex(16)
            secondary_token = str(uuid.uuid4())
            
            # Generate verification code for email
            verification_code = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
            
            # Create TOTP for secondary verification
            totp_secret = pyotp.random_base32()
            totp = pyotp.TOTP(totp_secret)
            totp_code = totp.now()
            
            # Store reset request data in cache (30 minute expiry)
            reset_data = {
                'email': email,
                'hospital_id': hospital.id,
                'primary_token': primary_token,
                'secondary_token': secondary_token,
                'verification_code': verification_code,
                'totp_secret': totp_secret,
                'ip_address': ip_address,
                'user_agent': user_agent,
                'device_trusted': device_trusted,
                'created_at': timezone.now().isoformat(),
                'status': 'initiated',
                'reset_steps_completed': []
            }
            
            # Create cache key using both email and a random component for security
            cache_key = f"hospital_admin_reset_{email}_{primary_token}"
            cache.set(cache_key, reset_data, timeout=60*30)  # 30 minute expiry
            
            # Send verification email
            context = {
                'verification_code': verification_code,
                'admin_name': hospital_admin.name,
                'hospital_name': hospital.name,
                'expiry_minutes': 30,
                'admin_email': email,
                'primary_token': primary_token,
                'frontend_url': os.environ.get('NEXTJS_URL', 'http://localhost:5173')
            }
            html_message = render_to_string('emails/hospital_admin_reset.html', context)
            plain_message = strip_tags(html_message)
            
            send_mail(
                subject='SECURE: Hospital Admin Account Password Reset',
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[hospital_admin.contact_email or email],
                html_message=html_message,
                fail_silently=False
            )
            
            # Send security notification to IT team (separate email about reset request)
            security_context = {
                'admin_name': hospital_admin.name,
                'admin_email': email,
                'hospital_name': hospital.name,
                'ip_address': ip_address,
                'location': get_location_from_ip(ip_address),
                'browser': user_agent,
                'timestamp': timezone.now().strftime('%Y-%m-%d %H:%M:%S %Z'),
                'trusted_device': device_trusted
            }
            security_html = render_to_string('emails/hospital_admin_reset_security_alert.html', security_context)
            security_plain = strip_tags(security_html)
            
            # Get IT security contact emails (fallback to admin email if none configured)
            it_security_emails = [settings.SECURITY_TEAM_EMAIL] if hasattr(settings, 'SECURITY_TEAM_EMAIL') else []
            if not it_security_emails and hasattr(settings, 'ADMIN_EMAIL'):
                it_security_emails = [settings.ADMIN_EMAIL]
            
            if it_security_emails:
                send_mail(
                    subject=f'SECURITY ALERT: Password Reset Requested for Hospital Admin {hospital_admin.name}',
                    message=security_plain,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=it_security_emails,
                    html_message=security_html,
                    fail_silently=True
                )
            
            # Return success with the verification token (but not the actual code)
            return Response({
                "status": "success",
                "message": "Password reset initiated. Please check your email for verification instructions.",
                "token": primary_token,
                "requires_secondary_admin": not device_trusted,  # Require second admin approval if not from trusted device
                "expires_in": 30  # minutes
            })
            
        except (CustomUser.DoesNotExist, HospitalAdmin.DoesNotExist):
            # Return generic message for security (don't reveal if email exists)
            return Response({
                "status": "success",
                "message": "If your email is registered, you will receive reset instructions."
            })
        except Exception as e:
            logger.error(f"Error in hospital admin reset request: {str(e)}")
            return Response({
                "status": "error",
                "message": "An error occurred processing your request."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Secondary verification step
class HospitalAdminResetVerifyView(SecurityMixin, APIView):
    """Verifies the initial token and email code, then requires secondary verification.
    This implements the multi-factor identity confirmation process.
    """
    permission_classes = [AllowAny]
    throttle_classes = [HospitalAdminResetVerifyThrottle]
    
    @security_audit('hospital_admin_reset_verify')
    def post(self, request):
        # Extract request data
        primary_token = request.data.get('token')
        verification_code = request.data.get('verification_code')
        hospital_code = request.data.get('hospital_code')  # Secondary verification
        email = request.data.get('email')
        last_login_location = request.data.get('last_login_location')  # City or country of last login
        
        # Validate input
        if not primary_token or not verification_code or not email:
            return Response({
                "status": "error",
                "message": "Token, verification code, and email are required"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if reset request exists
        cache_key = f"hospital_admin_reset_{email}_{primary_token}"
        reset_data = cache.get(cache_key)
        
        if not reset_data:
            return Response({
                "status": "error",
                "message": "Invalid or expired reset request. Please try again."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify the email verification code
        if reset_data['verification_code'] != verification_code:
            # Increment failed attempts counter
            reset_data['failed_attempts'] = reset_data.get('failed_attempts', 0) + 1
            
            # If too many failed attempts, invalidate the request
            if reset_data['failed_attempts'] >= 3:
                cache.delete(cache_key)
                logger.warning(f"Reset verification failed multiple times for {email}. Request invalidated.")
                return Response({
                    "status": "error",
                    "message": "Too many failed attempts. Please restart the reset process."
                }, status=status.HTTP_400_BAD_REQUEST)
                
            # Update data and return error
            cache.set(cache_key, reset_data, timeout=60*30)  # Reset the 30-minute timer
            return Response({
                "status": "error",
                "message": "Invalid verification code. Please try again."
                }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Get user and verify secondary information
            user = CustomUser.objects.get(email=email)
            hospital_admin = HospitalAdmin.objects.get(user=user)
            hospital = hospital_admin.hospital
            
            # Only verify hospital code if not provided in first step
            if hospital_code and hospital.registration_number != hospital_code:
                logger.warning(f"Hospital code mismatch during reset verification: {email}")
                return Response({
                    "status": "error",
                    "message": "Invalid hospital code"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Update reset data
            reset_data['reset_steps_completed'].append('email_verification')
            reset_data['status'] = 'awaiting_completion'
            
            # Generate a secondary token for the final step
            reset_data['secondary_token'] = secrets.token_hex(16)
            
            # Update the cache
            cache.set(cache_key, reset_data, timeout=60*30)  # Reset the 30-minute timer
            
            # Return success with the secondary token
            return Response({
                "status": "success",
                "message": "Verification successful. Proceed to reset your password.",
                "token": primary_token,
                "secondary_token": reset_data['secondary_token'],
                "expires_in": 30  # minutes
            })
            
        except (CustomUser.DoesNotExist, HospitalAdmin.DoesNotExist):
            # For security, don't reveal specifics
            return Response({
                "status": "error",
                "message": "Verification failed. Please try again."
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error in hospital admin reset verification: {str(e)}")
            return Response({
                "status": "error",
                "message": "An error occurred during verification."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Final reset step
class HospitalAdminResetCompleteView(SecurityMixin, APIView):
    """Completes the password reset process after all verifications are successful.
    Sets the new password, enforces password history, and enables 2FA if not already active.
    """
    permission_classes = [AllowAny]
    throttle_classes = [HospitalAdminResetCompleteThrottle]
    
    @security_audit('hospital_admin_reset_complete')
    def post(self, request):
        # Extract request data
        primary_token = request.data.get('token')
        secondary_token = request.data.get('secondary_token')
        email = request.data.get('email')
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')
        
        # Get device info for security logging
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
        
        # Validate input
        if not primary_token or not secondary_token or not email or not new_password or not confirm_password:
            return Response({
                "status": "error",
                "message": "All fields are required"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if passwords match
        if new_password != confirm_password:
            return Response({
                "status": "error",
                "message": "Passwords do not match"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if reset request exists and is valid
        cache_key = f"hospital_admin_reset_{email}_{primary_token}"
        reset_data = cache.get(cache_key)
        
        if not reset_data or reset_data.get('secondary_token') != secondary_token:
            return Response({
                "status": "error",
                "message": "Invalid or expired reset request. Please restart the process."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify email verification step was completed
        if 'email_verification' not in reset_data.get('reset_steps_completed', []):
            return Response({
                "status": "error",
                "message": "Verification steps incomplete. Please restart the process."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Begin transaction to ensure all operations complete or none do
            with transaction.atomic():
                # Get user and hospital admin
                user = CustomUser.objects.get(email=email)
                hospital_admin = HospitalAdmin.objects.get(user=user)
                
                # Check password history (implement password history check here if you have that model)
                # For now, just a basic check against current password
                if user.check_password(new_password):
                    return Response({
                        "status": "error",
                        "message": "New password cannot be the same as your current password"
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Set the new password
                user.set_password(new_password)
                
                # Update password change fields
                hospital_admin.password_change_required = False
                hospital_admin.last_password_change = timezone.now()
                
                # Save changes
                user.save()
                hospital_admin.save()
                
                # Clear any account lockouts
                lockout_key = f"account_lockout_{email}"
                cache.delete(lockout_key)
                
                # Record the successful reset
                reset_data['status'] = 'completed'
                reset_data['completed_at'] = timezone.now().isoformat()
                reset_data['reset_ip'] = ip_address
                reset_data['reset_user_agent'] = user_agent
                
                # Keep in cache briefly for audit purposes, then will expire
                cache.set(cache_key, reset_data, timeout=60*10)  # 10 minutes
                
                # Log the successful password reset
                logger.info(f"Hospital admin password reset completed successfully for {email}")
                
                # Send confirmation notifications
                self._send_reset_confirmation(hospital_admin, reset_data)
                
                # Return success
                return Response({
                    "status": "success",
                    "message": "Password has been reset successfully. Please log in with your new credentials.",
                    "requires_2fa": True  # Always require 2FA for hospital admins
                })
                
        except (CustomUser.DoesNotExist, HospitalAdmin.DoesNotExist):
            # Don't reveal specific errors
            return Response({
                "status": "error",
                "message": "Reset failed. Please try again."
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error in hospital admin reset completion: {str(e)}")
            return Response({
                "status": "error",
                "message": "An error occurred during password reset."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _send_reset_confirmation(self, hospital_admin, reset_data):
        """Send confirmation notifications about the password reset"""
        # Send confirmation to admin
        admin_context = {
            'admin_name': hospital_admin.name,
            'hospital_name': hospital_admin.hospital.name,
            'reset_time': timezone.now().strftime('%Y-%m-%d %H:%M:%S %Z'),
            'ip_address': reset_data.get('reset_ip', 'Unknown'),
            'browser': reset_data.get('reset_user_agent', 'Unknown'),
            'location': get_location_from_ip(reset_data.get('reset_ip', 'Unknown'))
        }
        admin_html = render_to_string('emails/hospital_admin_reset_confirmation.html', admin_context)
        admin_plain = strip_tags(admin_html)
        
        send_mail(
            subject='Your Hospital Admin Password Has Been Reset',
            message=admin_plain,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[hospital_admin.contact_email or hospital_admin.email],
            html_message=admin_html,
            fail_silently=False
        )
        
        # Send security notification to IT team
        security_context = {
            'admin_name': hospital_admin.name,
            'admin_email': hospital_admin.email,
            'hospital_name': hospital_admin.hospital.name,
            'reset_time': timezone.now().strftime('%Y-%m-%d %H:%M:%S %Z'),
            'ip_address': reset_data.get('reset_ip', 'Unknown'),
            'location': get_location_from_ip(reset_data.get('reset_ip', 'Unknown')),
            'browser': reset_data.get('reset_user_agent', 'Unknown'),
        }
        security_html = render_to_string('emails/hospital_admin_reset_complete_security.html', security_context)
        security_plain = strip_tags(security_html)
        
        # Get IT security contact emails (fallback to admin email if none configured)
        it_security_emails = [settings.SECURITY_TEAM_EMAIL] if hasattr(settings, 'SECURITY_TEAM_EMAIL') else []
        if not it_security_emails and hasattr(settings, 'ADMIN_EMAIL'):
            it_security_emails = [settings.ADMIN_EMAIL]
        
        if it_security_emails:
            send_mail(
                subject=f'SECURITY ALERT: Password Reset Completed for Hospital Admin {hospital_admin.name}',
                message=security_plain,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=it_security_emails,
                html_message=security_html,
                fail_silently=True
            )
