import os
import uuid
import secrets
import logging
import pyotp
import json
from datetime import datetime, timedelta
from functools import wraps

from django.utils import timezone
from django.contrib.auth import authenticate, get_user_model
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
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

from api.models import CustomUser, Hospital
from api.models.medical.hospital_auth import HospitalAdmin
from api.serializers import HospitalAdminLoginSerializer, Hospital2FAVerificationSerializer
from api.utils.location_utils import get_location_from_ip, get_client_ip
from api.utils.cookie_helpers import set_jwt_cookies, clear_jwt_cookies

# Logger setup
logger = logging.getLogger(__name__)

# Custom throttle classes
class HospitalAdminLoginRateThrottle(AnonRateThrottle):
    """Rate limiting for hospital admin login attempts."""
    scope = 'hospital_admin_login'
    rate = '5/minute'  # Stricter rate limiting for admin access

class HospitalAdmin2FARateThrottle(AnonRateThrottle):
    """Rate limiting for 2FA verification attempts."""
    scope = 'hospital_admin_2fa'
    rate = '3/minute'  # Very strict rate for 2FA attempts

# Security decorator for additional protection
def security_audit(action_type):
    """Decorator that adds comprehensive security auditing to views."""
    def decorator(func):
        @wraps(func)
        def wrapper(self, request, *args, **kwargs):
            # Start time for performance tracking
            start_time = timezone.now()
            
            # Track request metadata
            ip_address = get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
            email = request.data.get('email')
            
            # Create audit record
            audit_data = {
                'timestamp': timezone.now().isoformat(),
                'action': action_type,
                'ip_address': ip_address,
                'user_agent': user_agent,
                'email': email,
                'status': 'initiated'
            }
            
            # Get geolocation data if available
            location_info = get_location_from_ip(ip_address)
            if location_info:
                audit_data['location'] = {
                    'country': location_info.get('country'),
                    'city': location_info.get('city')
                }
            
            # Execute the original function
            try:
                response = func(self, request, *args, **kwargs)
                
                # Update audit record with result
                audit_data['status'] = 'success' if response.status_code < 400 else 'failed'
                audit_data['response_code'] = response.status_code
                audit_data['duration_ms'] = (timezone.now() - start_time).total_seconds() * 1000
                
                # Log the audit data
                log_level = logging.INFO if audit_data['status'] == 'success' else logging.WARNING
                logger.log(log_level, f"SECURITY_AUDIT: {json.dumps(audit_data)}")
                
                # Check for suspicious activity patterns
                self._check_suspicious_activity(audit_data)
                
                return response
                
            except Exception as e:
                # Log any exceptions
                audit_data['status'] = 'error'
                audit_data['error'] = str(e)
                logger.error(f"SECURITY_AUDIT_ERROR: {json.dumps(audit_data)}")
                raise
                
        return wrapper
    return decorator

# Base Auth mixin for common security features
class SecurityMixin:
    """Mixin that provides security features for authentication views."""
    
    def _check_suspicious_activity(self, audit_data):
        """Check for patterns of suspicious activity and take action."""
        email = audit_data.get('email')
        ip_address = audit_data.get('ip_address')
        
        if not email or not ip_address:
            return
            
        # Check for multiple failures from same IP
        cache_key = f'failed_attempts:{ip_address}'
        failed_attempts = cache.get(cache_key, 0)
        
        if audit_data['status'] == 'failed':
            # Increment failed attempts
            failed_attempts += 1
            cache.set(cache_key, failed_attempts, timeout=3600)  # 1 hour
            
            # Alert on suspicious activity
            if failed_attempts >= 10:
                logger.critical(
                    f"SECURITY_ALERT: Multiple failed login attempts detected. "
                    f"IP: {ip_address}, Attempts: {failed_attempts}, Email: {email}"
                )
                
                # Send security alert email to the real contact email - NOT the admin username
                try:
                    # Get the real contact email for this admin username
                    contact_email = None
                    
                    # Try to find the hospital admin record
                    try:
                        # First check if this is an existing admin username
                        admin = HospitalAdmin.objects.get(email=email)
                        # If we have a contact_email, use that
                        if admin.contact_email:
                            contact_email = admin.contact_email
                            logger.info(f"Sending security alert to contact_email: {contact_email}")
                        # Otherwise try getting the email from the user account
                        elif admin.user.email != email:
                            contact_email = admin.user.email
                            logger.info(f"Sending security alert to user.email: {contact_email}")
                    except HospitalAdmin.DoesNotExist:
                        # If this isn't an admin username but a real email, use it directly
                        if '@' in email and not email.endswith('@example.com') and not email.endswith('@phb.com'):
                            contact_email = email
                    
                    # Only send if we found a valid contact email
                    if contact_email:
                        # Only send one alert per email per lockout period
                        alert_sent_key = f'security_alert_sent:{email}'
                        if not cache.get(alert_sent_key):
                            # Mark as sent to prevent multiple alerts
                            cache.set(alert_sent_key, True, timeout=15*60)  # 15 minutes (lockout duration)
                            
                            # Find the hospital name if possible
                            hospital_name = "Public Health Bureau"
                            try:
                                admin = HospitalAdmin.objects.get(email=email)
                                hospital_name = admin.hospital.name
                            except:
                                pass
                            
                            # Get location info
                            location = "Unknown"
                            location_info = audit_data.get('location', {})
                            if location_info:
                                city = location_info.get('city', 'Unknown')
                                country = location_info.get('country', 'Unknown')
                                if city != 'Unknown' or country != 'Unknown':
                                    location = f"{city}, {country}".replace('Unknown, ', '').replace(', Unknown', '')
                            
                            # Prepare context for the HTML template
                            context = {
                                'hospital_name': hospital_name,
                                'admin_email': email,
                                'ip_address': ip_address,
                                'location': location,
                                'attempts': failed_attempts,
                                'timestamp': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
                                'status': "ACCOUNT LOCKED",
                                'lockout_duration': 15,  # minutes
                                'current_year': timezone.now().year,
                                'reset_password_url': f"{os.environ.get('NEXTJS_URL', 'http://localhost:5173').rstrip('/')}/hospital-admin/reset-password/request?email={email}"
                            }
                            
                            # Render email template
                            html_message = render_to_string('email/security_alert.html', context)
                            plain_message = strip_tags(html_message)
                            
                            # Send the email
                            send_mail(
                                subject=f'SECURITY ALERT: Account Locked - {hospital_name}',
                                message=plain_message,
                                from_email=os.environ.get('DEFAULT_FROM_EMAIL', 'security@publichealthbureau.com'),
                                recipient_list=[contact_email],
                                html_message=html_message,
                                fail_silently=True  # Don't fail if email sending fails
                            )
                except Exception as e:
                    logger.error(f"Failed to send security alert email: {str(e)}")
                
                # Implement actual account lockout after too many failed attempts
                # Create a lockout key specific to this email
                lockout_key = f'account_lockout:{email}'
                lockout_duration = 15  # minutes
                
                # Check if account is already locked
                if not cache.get(lockout_key):
                    # Lock the account for 15 minutes
                    cache.set(lockout_key, True, timeout=lockout_duration*60)
                    logger.critical(f"SECURITY_ACTION: Account {email} locked for {lockout_duration} minutes due to too many failed attempts")
                    
                    # Create a record of when the lockout expires
                    lockout_expires = timezone.now() + timezone.timedelta(minutes=lockout_duration)
                    cache.set(f'{lockout_key}_expires', lockout_expires.isoformat(), timeout=lockout_duration*60)
                
        # Track per-email failed attempts to detect credential stuffing
        email_key = f'failed_attempts:email:{email}'
        email_attempts = cache.get(email_key, 0)
        
        if audit_data['status'] == 'failed':
            email_attempts += 1
            cache.set(email_key, email_attempts, timeout=86400)  # 24 hours
            
            # Different thresholds for email-based attacks
            if email_attempts >= 5:
                logger.warning(
                    f"SECURITY_WARNING: Multiple failed login attempts for email. "
                    f"Email: {email}, Attempts: {email_attempts}"
                )
                
                # Send security warning email to the real contact email - NOT the admin username
                # This follows the same pattern as critical alerts but with a different message
                try:
                    # Get the real contact email for this admin username
                    contact_email = None
                    
                    # Try to find the hospital admin record
                    try:
                        # First check if this is an existing admin username
                        admin = HospitalAdmin.objects.get(email=email)
                        # If we have a contact_email, use that
                        if admin.contact_email:
                            contact_email = admin.contact_email
                            logger.info(f"Sending security warning to contact_email: {contact_email}")
                        # Otherwise try getting the email from the user account
                        elif admin.user.email != email:
                            contact_email = admin.user.email
                            logger.info(f"Sending security warning to user.email: {contact_email}")
                    except HospitalAdmin.DoesNotExist:
                        # If this isn't an admin username but a real email, use it directly
                        if '@' in email and not email.endswith('@example.com') and not email.endswith('@phb.com'):
                            contact_email = email
                    
                    # Only send if we found a valid contact email and not too frequently (max once per hour)
                    if contact_email:
                        cache_key = f'warning_email_sent:{email}'
                        if not cache.get(cache_key):
                            # Set a flag to prevent sending too many emails
                            cache.set(cache_key, True, timeout=3600)  # 1 hour
                            
                            # Find the hospital name if possible
                            hospital_name = "Public Health Bureau"
                            try:
                                admin = HospitalAdmin.objects.get(email=email)
                                hospital_name = admin.hospital.name
                            except:
                                pass
                            
                            # Get location info
                            location = "Unknown"
                            location_info = audit_data.get('location', {})
                            if location_info:
                                city = location_info.get('city', 'Unknown')
                                country = location_info.get('country', 'Unknown')
                                if city != 'Unknown' or country != 'Unknown':
                                    location = f"{city}, {country}".replace('Unknown, ', '').replace(', Unknown', '')
                            
                            # Prepare context for the HTML template
                            context = {
                                'hospital_name': hospital_name,
                                'admin_email': email,
                                'ip_address': ip_address,
                                'location': location,
                                'attempts': email_attempts,
                                'timestamp': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
                                'status': "WARNING",
                                'lockout_duration': 0,  # No lockout yet, just a warning
                                'current_year': timezone.now().year,
                                'reset_password_url': f"{os.environ.get('NEXTJS_URL', 'http://localhost:5173').rstrip('/')}/hospital-admin/reset-password/request?email={email}"
                            }
                            
                            # Render email template
                            html_message = render_to_string('email/security_alert.html', context)
                            plain_message = strip_tags(html_message)
                            
                            # Send the email
                            send_mail(
                                subject=f'Security Warning: Multiple Failed Login Attempts - {hospital_name}',
                                message=plain_message,
                                from_email=os.environ.get('DEFAULT_FROM_EMAIL', 'security@publichealthbureau.com'),
                                recipient_list=[contact_email],
                                html_message=html_message,
                                fail_silently=True  # Don't fail if email sending fails
                            )
                except Exception as e:
                    logger.error(f"Failed to send security warning email: {str(e)}")
                
        # Record successful logins for auditing patterns
        if audit_data['status'] == 'success':
            # Log successful login with location data for audit trail
            location = audit_data.get('location', {})
            logger.info(
                f"ADMIN_LOGIN_SUCCESS: Email: {email}, IP: {ip_address}, "
                f"Country: {location.get('country', 'Unknown')}, City: {location.get('city', 'Unknown')}"
            )
            
            # Clear failed login attempts and lockouts on successful login
            # This ensures that if a user successfully logs in, they get a fresh start
            email_key = f'failed_attempts:email:{email}'
            ip_key = f'failed_attempts:{ip_address}'
            lockout_key = f'account_lockout:{email}'
            warning_key = f'warning_email_sent:{email}'
            alert_key = f'security_alert_sent:{email}'
            
            # Clear all security counters and flags
            cache.delete(email_key)  # Clear email-based attempt counter
            cache.delete(ip_key)     # Clear IP-based attempt counter
            cache.delete(lockout_key) # Remove any lockout status
            cache.delete(f'{lockout_key}_expires') # Clear lockout expiry timestamp
            cache.delete(warning_key) # Clear warning email flag
            cache.delete(alert_key)   # Clear alert email flag
            
            logger.info(f"Security counters reset for successful login: {email}")
            
            # Store the successful login timestamp for future security checks
            last_login_key = f'last_successful_login:{email}'
            login_data = {
                'timestamp': timezone.now().isoformat(),
                'ip_address': ip_address,
                'location': location,
                'user_agent': audit_data.get('user_agent')
            }
            cache.set(last_login_key, json.dumps(login_data), timeout=60*60*24*30)  # 30 days

class HospitalAdminLoginView(SecurityMixin, APIView):
    """
    Dedicated login endpoint for hospital administrators.
    This enforces domain validation and additional security measures.
    """
    authentication_classes = []  # Disable authentication - this is the login endpoint!
    permission_classes = [AllowAny]
    throttle_classes = [HospitalAdminLoginRateThrottle]
    
    @security_audit('hospital_admin_login_attempt')
    def post(self, request):
        # Log data safely, masking the password
        log_data = request.data.copy()
        if 'password' in log_data:
            log_data['password'] = '********'
        logger.info(f"Hospital admin login attempt: {log_data}")
        
        serializer = HospitalAdminLoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        hospital_code = serializer.validated_data['hospital_code']
        
        # Check if this account is locked due to too many failed attempts
        lockout_key = f'account_lockout:{email}'
        if cache.get(lockout_key):
            # Account is locked - get expiry time if available
            expires_key = f'{lockout_key}_expires'
            expiry_time = cache.get(expires_key)
            
            if expiry_time:
                try:
                    expiry_time = datetime.fromisoformat(expiry_time)
                    # Check if lockout period has expired
                    if timezone.now() >= expiry_time:
                        # Lockout period has expired - clear the lockout and allow login
                        logger.info(f"Lockout period expired for {email} - clearing lockout")
                        cache.delete(lockout_key)
                        cache.delete(expires_key)
                        # Continue with login process - don't return error response
                    else:
                        # Lockout still active - calculate remaining time
                        remaining_minutes = max(1, int((expiry_time - timezone.now()).total_seconds() / 60))
                        message = f"Account temporarily locked due to too many failed attempts. Try again in {remaining_minutes} minutes."
                        return Response({
                            "status": "error",
                            "message": message
                        }, status=status.HTTP_403_FORBIDDEN)
                except (ValueError, TypeError):
                    # If we can't parse the expiry time, clear the lockout to avoid permanent lockouts
                    logger.warning(f"Invalid lockout expiry time for {email} - clearing lockout")
                    cache.delete(lockout_key)
                    cache.delete(expires_key)
                    # Continue with login process
            else:
                # No expiry time found - clear the lockout to prevent permanent lockouts
                logger.warning(f"No lockout expiry time for {email} - clearing lockout")
                cache.delete(lockout_key)
                # Continue with login process
        
        # Verify hospital code
        from django.conf import settings
        
        # In development, provide more flexibility with hospital codes
        if settings.DEBUG:
            # Allow fallback to find hospitals by other means if code doesn't match
            try:
                hospital = Hospital.objects.get(registration_number=hospital_code)
            except Hospital.DoesNotExist:
                # Try to find by ID if the code looks like an ID
                if hospital_code.isdigit():
                    try:
                        hospital = Hospital.objects.get(id=int(hospital_code))
                    except Hospital.DoesNotExist:
                        pass
                
                # If still not found, return error
                if not 'hospital' in locals():
                    return Response({
                        "status": "error",
                        "message": "Invalid hospital code. For development: you can use hospital ID or registration number."
                    }, status=status.HTTP_401_UNAUTHORIZED)
        else:
            # In production, strictly validate hospital code
            try:
                hospital = Hospital.objects.get(registration_number=hospital_code)
            except Hospital.DoesNotExist:
                return Response({
                    "status": "error",
                    "message": "Invalid hospital code. Please contact your system administrator."
                }, status=status.HTTP_401_UNAUTHORIZED)
            
        # Check if user exists and is a hospital admin
        try:
            user = CustomUser.objects.get(email=email)
            if user.role != 'hospital_admin':
                return Response({
                    "status": "error",
                    "message": "This account does not have hospital administrator privileges"
                }, status=status.HTTP_403_FORBIDDEN)
                
            # Verify admin is associated with the hospital
            try:
                admin = HospitalAdmin.objects.get(user=user, hospital=hospital)
            except HospitalAdmin.DoesNotExist:
                return Response({
                    "status": "error",
                    "message": "You are not authorized to access this hospital's system"
                }, status=status.HTTP_403_FORBIDDEN)
                
        except CustomUser.DoesNotExist:
            return Response({
                "status": "error",
                "message": "Invalid credentials"
            }, status=status.HTTP_401_UNAUTHORIZED)
            
        # Authenticate the user
        authenticated_user = authenticate(request, email=email, password=password)
        if not authenticated_user:
            return Response({
                "status": "error",
                "message": "Invalid credentials"
            }, status=status.HTTP_401_UNAUTHORIZED)
            
        # Generate and send 2FA code
        # Here we'll simulate using TOTP for 2FA
        totp_secret = pyotp.random_base32()
        totp = pyotp.TOTP(totp_secret)
        verification_code = totp.now()
        
        # Store the code in cache with 10-minute expiry
        cache_key = f"hospital_admin_2fa_{email}"
        cache.set(cache_key, {
            'code': verification_code,
            'secret': totp_secret,
            'timestamp': timezone.now().timestamp(),
            'attempts': 0
        }, timeout=600)  # 10 minutes
        
        # Get location and device info for the email
        ip_address = get_client_ip(request)
        location_info = get_location_from_ip(ip_address)
        device = request.META.get('HTTP_USER_AGENT', 'Unknown Device')
        
        # Prepare email context
        context = {
            'user': authenticated_user,
            'code': verification_code,
            'hospital': hospital.name,
            'location': f"{location_info.get('city', 'Unknown')}, {location_info.get('country', 'Unknown')}",
            'device': device,
            'timestamp': timezone.now().strftime('%b %d %Y %H:%M:%S %Z'),
            'frontend_url': os.environ.get('NEXTJS_URL', '').rstrip('/')
        }
        
        # CRITICAL: At this point, we have verified the admin has proper authentication
        # But we need to make sure the 2FA code gets sent to their REAL email, not the admin username
        
        # We already have the admin object from line 226: admin = HospitalAdmin.objects.get(user=user, hospital=hospital)
        # Let's use that to get their contact email
        
        # Use real contact email if available, otherwise try other methods to find it
        if admin.contact_email:
            # Preferred: Use the dedicated contact_email field
            contact_email = admin.contact_email
            logger.info(f"Using contact_email field for 2FA: {contact_email}")
        elif admin.hospital.email:
            # Option 2: Try the hospital email if that's meant to reach the admin
            contact_email = admin.hospital.email
            logger.info(f"Using hospital email for 2FA: {contact_email}")
        elif authenticated_user.email != email:
            # Option 3: If the user object email is different from the login username, use that
            contact_email = authenticated_user.email
            logger.info(f"Using authenticatedUser.email for 2FA: {contact_email}")
        else:
            # Last resort: Use the admin username (not ideal if it's not a real inbox)
            contact_email = email
            logger.warning(f"FALLBACK: Using admin username as email for 2FA: {contact_email}")
            
        # Always log where we're sending the 2FA code    
        logger.info(f"Sending 2FA code to email: {contact_email} (admin username: {email})")
        
        # Update the database if we found a contact email but it's not saved
        if contact_email != email and not admin.contact_email:
            logger.info(f"Updating admin.contact_email to {contact_email} for future use")
            admin.contact_email = contact_email
            admin.save()
            
        # Send verification email to their REAL contact email
        html_message = render_to_string('email/hospital_admin_2fa.html', context)
        plain_message = strip_tags(html_message)
        
        try:
            send_mail(
                subject=f'Hospital Admin Login Verification - {hospital.name}',
                message=plain_message,
                from_email=os.environ.get('DEFAULT_FROM_EMAIL'),
                recipient_list=[contact_email],  # Use contact_email instead of admin username
                html_message=html_message,
                fail_silently=False,
            )
            
            # Return response requiring 2FA
            return Response({
                "status": "2fa_required",
                "message": "Verification code sent to your email",
                "email": email,
                "hospital_name": hospital.name
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Failed to send 2FA email: {str(e)}")
            return Response({
                "status": "error",
                "message": "Failed to send verification code. Please try again."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class VerifyHospitalAdmin2FAView(SecurityMixin, APIView):
    """
    Endpoint for verifying hospital admin 2FA codes and completing login.
    """
    authentication_classes = []  # Disable authentication - users are logging in!
    permission_classes = [AllowAny]
    throttle_classes = [HospitalAdmin2FARateThrottle]
    
    @security_audit('hospital_admin_2fa_verification')
    def post(self, request):
        serializer = Hospital2FAVerificationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        email = serializer.validated_data['email']
        verification_code = serializer.validated_data['verification_code']
        device_id = serializer.validated_data.get('device_id')
        remember_device = serializer.validated_data.get('remember_device', False)
        
        # Retrieve the stored code
        cache_key = f"hospital_admin_2fa_{email}"
        cached_data = cache.get(cache_key)
        
        if not cached_data:
            return Response({
                "status": "error",
                "message": "Verification code expired or not found. Please request a new code."
            }, status=status.HTTP_400_BAD_REQUEST)
            
        # Check for too many attempts
        cached_data['attempts'] = cached_data.get('attempts', 0) + 1
        if cached_data['attempts'] > 5:
            cache.delete(cache_key)
            return Response({
                "status": "error",
                "message": "Too many failed attempts. Please request a new code."
            }, status=status.HTTP_400_BAD_REQUEST)
            
        # Update attempts in cache
        cache.set(cache_key, cached_data, timeout=600)
        
        # Verify the code (using TOTP or direct comparison)
        totp = pyotp.TOTP(cached_data['secret'])
        
        # Log for debugging
        logger.info(f"Verifying code '{verification_code}' for {email}")
        logger.info(f"Generated code was '{cached_data['code']}' with secret {cached_data['secret']}")
        
        # In development mode, provide more flexibility
        if settings.DEBUG:
            # Option 1: Direct comparison with the stored code
            direct_match = verification_code == cached_data['code']
            
            # Option 2: TOTP verification with wider window
            totp_match = totp.verify(verification_code, valid_window=10)  # Much wider window in dev
            
            if not (direct_match or totp_match):
                return Response({
                    "status": "error",
                    "message": "Invalid verification code. Please try again."
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            # Strict verification in production with narrow window
            if not totp.verify(verification_code, valid_window=1):
                return Response({
                    "status": "error",
                    "message": "Invalid verification code. Please try again."
                }, status=status.HTTP_400_BAD_REQUEST)
            
        # If we got here, 2FA is successful - authenticate the user
        try:
            user = CustomUser.objects.get(email=email)
            
            # Generate tokens
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)

            # Clear the code from cache
            cache.delete(cache_key)

            # If remember device is set, store a trusted device token
            if remember_device and device_id:
                trusted_device_key = f"trusted_device_{user.id}_{device_id}"
                trusted_token = secrets.token_hex(32)
                # Store for 30 days
                cache.set(trusted_device_key, trusted_token, timeout=60*60*24*30)

            # Get user's hospital
            hospital_admin = HospitalAdmin.objects.get(user=user)
            hospital = hospital_admin.hospital

            # Check if password change is required
            password_change_required = hospital_admin.password_change_required

            # Log successful login
            logger.info(f"Hospital admin login successful: {email} for {hospital.name}, password change required: {password_change_required}")

            # Create response with enhanced data
            response_data = {
                "status": "success",
                "message": "Login successful",
                "tokens": {
                    "access": access_token,
                    "refresh": refresh_token
                },
                "user_data": {
                    'id': user.id,
                    'email': user.email,
                    'full_name': f"{user.first_name} {user.last_name}".strip(),
                    'role': 'hospital_admin',
                    'hospital': {
                        'id': hospital.id,
                        'name': hospital.name,
                        'code': hospital.registration_number
                    },
                    'is_verified': True,
                    'position': hospital_admin.position,
                    'password_change_required': password_change_required
                }
            }

            response = Response(response_data)

            # Set JWT tokens as httpOnly cookies
            set_jwt_cookies(response, access_token, refresh_token)

            return response
                
        except (CustomUser.DoesNotExist, HospitalAdmin.DoesNotExist) as e:
            return Response({
                "status": "error",
                "message": "User not found or not authorized as hospital admin"
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error in 2FA verification: {str(e)}")
            return Response({
                "status": "error",
                "message": "An error occurred during verification"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
