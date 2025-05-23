from functools import cache
import os
import uuid
import secrets
import random
import logging
import time

from django.shortcuts import render
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone
from django.conf import settings
from django.contrib.auth import authenticate
from django.core.cache import cache

from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.exceptions import ValidationError
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


from api.models import CustomUser
from api.models.medical.medical_record_access import MedicalRecordAccess
from api.serializers import (
    UserSerializer, CustomTokenObtainPairSerializer,
    EmailVerificationSerializer, UserProfileSerializer,
    PasswordResetRequestSerializer, PasswordResetConfirmSerializer,
    PatientMedicalRecordSerializer, OnboardingStatusSerializer,
    ChangePasswordSerializer
)
from api.utilis import rate_limit_otp
from api.utils.location_utils import get_location_from_ip, get_client_ip
from api.utils.email import send_verification_email, send_welcome_email

# Logger setup
logger = logging.getLogger(__name__)

# After your imports but before class definitions
def send_verification_email(user, verification_link):
    # Make sure the verification_link matches your URL pattern
    base_url = os.environ.get('SERVER_API_URL').rstrip('/')
    verification_link = f"{base_url}/api/email/verify/{user.email_verification_token}/"
    
    context = {
        'user': user,
        'verification_link': verification_link,
    }
    
    html_message = render_to_string('email/verification.html', context)
    plain_message = strip_tags(html_message)
    
    try:
        send_mail(
            subject='Verify Your Healthcare Account',
            message=plain_message,
            from_email=os.environ.get('DEFAULT_FROM_EMAIL'),
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        logger.error(f"Failed to send verification email: {str(e)}")
        return False
    
def format_secondary_languages(secondary_languages):
    """Utility function to convert secondary_languages to the proper format"""
    if secondary_languages is None:
        return []
    elif isinstance(secondary_languages, str):
        # Check if it's a string representation of a list like "['yo', 'en']"
        if secondary_languages.startswith('[') and secondary_languages.endswith(']'):
            # Remove brackets and split by comma
            langs = secondary_languages.strip('[]')
            # Handle empty list case
            if not langs:
                return []
            else:
                # Split by comma and remove quotes and whitespace
                return [lang.strip().strip("'").strip('"') for lang in langs.split(',')]
        # Handle the case when it's a comma-separated string like "yoruba,hausa"
        else:
            return [lang.strip() for lang in secondary_languages.split(',') if lang.strip()]
    return secondary_languages  # If it's already a list or other format

class UserRegistrationView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    permission_classes = [AllowAny]
    serializer_class = UserSerializer

    def create(self, request, *args, **kwargs):
        try:
            # Log the incoming request data (mask the password for security)
            log_data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
            if 'password' in log_data:
                log_data['password'] = '********'
            print(f"[Registration] Received data: {log_data}")
            
            # Format the consents data if it's nested
            if 'consents' in request.data:
                consents = request.data.pop('consents')
                request.data['consent_terms'] = consents.get('terms', False)
                request.data['consent_hipaa'] = consents.get('hipaa', False)
                request.data['consent_data_processing'] = consents.get('dataProcessing', False)

            serializer = self.get_serializer(data=request.data)
            if not serializer.is_valid():
                # Format validation errors
                formatted_errors = {}
                for field, errors in serializer.errors.items():
                    if isinstance(errors, list):
                        formatted_errors[field] = errors[0]  # Get the first error message
                    else:
                        formatted_errors[field] = errors
                
                # Log the validation errors
                print(f"[Registration] Validation errors: {serializer.errors}")
                print(f"[Registration] Required fields: {UserSerializer.Meta.fields}")

                return Response({
                    'status': 'error',
                    'message': 'Validation failed',
                    'errors': formatted_errors
                }, status=status.HTTP_400_BAD_REQUEST)

            # Save the user
            user = serializer.save()
            
            # Generate verification token
            user.email_verification_token = uuid.uuid4()
            user.save()

            # Generate verification link
            verification_link = f"{os.environ.get('SERVER_API_URL')}api/email/verify/{user.email_verification_token}/"

            # Send verification email
            email_sent = send_verification_email(user, verification_link)

            response_data = {
                'status': 'success',
                'message': 'Registration successful! Please check your email for verification.',
                'email': user.email,
                'email_status': 'sent' if email_sent else 'failed'
            }

            if not email_sent:
                response_data['email_error'] = 'Failed to send verification email. Please contact support.'

            print(f"[Registration] User created successfully: {user.email}")
            return Response(response_data, status=status.HTTP_201_CREATED)

        except Exception as e:
            # Log the error for debugging
            logger.error(f"Registration error: {str(e)}")
            print(f"[Registration] Error: {str(e)}")
            import traceback
            print(f"[Registration] Traceback: {traceback.format_exc()}")
            return Response({
                'status': 'error',
                'message': 'An unexpected error occurred during registration.',
                'detail': str(e) if settings.DEBUG else 'Please try again later.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Custom throttle classes for regular user authentication
class UserLoginRateThrottle(AnonRateThrottle):
    """Rate limiting for regular user login attempts.
    
    This protects the user login endpoint from brute force and
    dictionary attacks by limiting the rate of attempts.
    """
    rate = '5/minute'  # Allow 5 attempts per minute
    scope = 'user_login'
    
    def get_cache_key(self, request, view):
        # Use the IP address as the unique identifier for rate limiting
        # This will block repeated attempts from the same source
        ident = self.get_ident(request)
        return f"{self.scope}:{ident}"

class FailedLoginTracker:
    """Tracks failed login attempts to implement more sophisticated protections."""
    
    @staticmethod
    def increment_failed_attempts(username):
        """Increments the failed attempt counter for a particular username."""
        key = f"failed_login_{username}"
        attempts = cache.get(key, 0)
        attempts += 1
        
        # Store the attempt count for 30 minutes
        cache.set(key, attempts, timeout=1800)
        
        # Log suspicious activity after threshold
        if attempts >= 10:
            logger.warning(
                f"SECURITY_WARNING: High number of failed login attempts for {username}. "
                f"Count: {attempts}"
            )
            
        return attempts
    
    @staticmethod
    def reset_failed_attempts(username):
        """Resets the failed attempt counter on successful login."""
        key = f"failed_login_{username}"
        cache.delete(key)

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    throttle_classes = [UserLoginRateThrottle]
    
    def post(self, request, *args, **kwargs):
        # Get the username from the request
        username = request.data.get('username', '')
        
        # Call the parent post method to attempt authentication
        response = super().post(request, *args, **kwargs)
        
        # If authentication was successful (status code 200), reset the failed attempts counter
        if response.status_code == status.HTTP_200_OK and username:
            FailedLoginTracker.reset_failed_attempts(username)
        # If authentication failed, increment the failed attempts counter
        elif username:
            attempts = FailedLoginTracker.increment_failed_attempts(username)
            
            # If too many failed attempts, enhance the rate limiting
            if attempts >= 5:
                # Force a delay based on the number of attempts to slow down brute force
                import time
                time.sleep(min(attempts * 0.5, 5))  # Max delay of 5 seconds
        
        return response

class LoginView(APIView):
    throttle_classes = [UserLoginRateThrottle]  # Add rate limiting to prevent brute force attacks
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def send_suspicious_login_email(self, user, ip_address, device_info):
        """Send email notification about suspicious login attempt"""
        # Get location info from IP
        location_info = get_location_from_ip(ip_address)
        location = f"{location_info.get('city', 'Unknown')}, {location_info.get('country', 'Unknown')}"
        
        # Log detailed information about the suspicious login attempt
        logger.warning(f"SECURITY ALERT: Suspicious login attempt detected")
        logger.warning(f"User: {user.email}, IP: {ip_address}, Location: {location}, Device: {device_info}")
        
        # Generate a password reset token for the user
        token = secrets.token_urlsafe(32)
        user.password_reset_token = token
        user.save()
        
        # Ensure the NEXTJS_URL ends with a slash if it doesn't already
        nextjs_url = os.environ.get('NEXTJS_URL', 'http://localhost:5173/')
        if not nextjs_url.endswith('/'):
            nextjs_url += '/'
        
        # Construct the reset link with proper formatting
        reset_link = f"{nextjs_url}reset-password?token={token}"
        
        # Debug logging - only log non-sensitive information
        print(f"Generated password reset token for suspicious login email")
        print(f"Reset link generated for user: {user.email}")
        
        # Log to secure logger with limited info
        logger.info(f"Password reset token generated for user {user.email} after suspicious login attempt")
        
        # Prepare context for email template
        context = {
            'user': user,
            'ip_address': ip_address,
            'location': location,
            'device': device_info,
            'timestamp': timezone.now().strftime('%b %d %Y %H:%M:%S %Z'),
            'frontend_url': nextjs_url.rstrip('/'),
            'reset_link': reset_link
        }
        
        # Render the email template
        try:
            html_message = render_to_string('email/suspicious_login.html', context)
            plain_message = strip_tags(html_message)
            logger.info(f"Email template rendered successfully for {user.email}")
        except Exception as template_error:
            logger.error(f"Failed to render email template: {str(template_error)}")
            return False
        
        # Log email configuration
        email_host = os.environ.get('EMAIL_HOST')
        email_port = os.environ.get('EMAIL_PORT')
        email_user = os.environ.get('EMAIL_HOST_USER')
        from_email = os.environ.get('DEFAULT_FROM_EMAIL')
        logger.info(f"Email configuration: Host={email_host}, Port={email_port}, User={email_user}, From={from_email}")
        
        try:
            # Attempt to send the email
            logger.info(f"Attempting to send suspicious login email to {user.email}")
            result = send_mail(
                subject='PHB Healthcare - Suspicious Login Attempt',
                message=plain_message,
                from_email=from_email,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )
            logger.info(f"Suspicious login email sent to {user.email}, Result: {result}")
            
            # Gmail special case warning
            if user.email == from_email:
                logger.warning(f"ATTENTION: Sender and recipient emails are the same ({user.email}). Gmail may filter this email.")
                print(f"WARNING: Sender and recipient emails are the same. Gmail may filter this email to {user.email}.")
                
            return True
        except Exception as e:
            logger.error(f"Failed to send suspicious login email: {str(e)}")
            print(f"ERROR: Failed to send suspicious login email to {user.email}: {str(e)}")
            return False
        
    def post(self, request):
        # Implement direct rate limiting by IP
        ip = self.get_client_ip(request)
        cache_key = f"login_attempts:{ip}"
        attempts = cache.get(cache_key, 0)
        
        # Get the email from the request for account lockout checks
        email = request.data.get('email')
        
        # Check if account is locked
        if email:
            # Check if this account has been verified through password reset
            verified_key = f"verified_reset:{email}"
            is_verified_reset = cache.get(verified_key, False)
            
            # If the account was verified through password reset, clear any lockouts
            if is_verified_reset:
                account_lockout_key = f"account_lockout:{email}"
                cache.delete(account_lockout_key)
                cache.delete(f"account_lockout_expiry:{email}")
                cache.delete(f"account_attempts:{email}")
                cache.delete(verified_key)  # Clear the verified flag after use
                logging.info(f"Account lockout bypassed for {email} after password reset verification")
            else:
                # Proceed with normal lockout check
                account_lockout_key = f"account_lockout:{email}"
                is_locked = cache.get(account_lockout_key, False)
                
                if is_locked:
                    # Get the remaining lockout time
                    lockout_expiry = cache.get(f"account_lockout_expiry:{email}", 0)
                    current_time = int(time.time())
                    remaining_time = max(0, lockout_expiry - current_time)
                    
                    # Convert seconds to minutes and seconds
                    minutes = remaining_time // 60
                    seconds = remaining_time % 60
                    time_msg = f"{minutes} minutes and {seconds} seconds" if minutes > 0 else f"{seconds} seconds"
                    
                    return Response({
                        "status": "error",
                        "message": f"Account temporarily locked. Please try again in {time_msg} or reset your password.",
                        "account_locked": True,
                        "remaining_time": remaining_time
                    }, status=status.HTTP_403_FORBIDDEN)
        
        # Increment the counter
        cache.set(cache_key, attempts + 1, timeout=60)  # Reset after 60 seconds
        
        # If we have an email, always check for account lockout threshold first
        if email:
            account_attempts_key = f"account_attempts:{email}"
            account_attempts = cache.get(account_attempts_key, 0) + 1
            cache.set(account_attempts_key, account_attempts, timeout=1800)  # 30 minutes
            
            # Debug logging for account attempts
            print(f"DEBUG: Account {email} has {account_attempts} failed login attempts")
            logger.warning(f"Account {email} has {account_attempts} failed login attempts")
            
            # Send suspicious login email after 3 failed attempts
            if account_attempts >= 5:
                try:
                    user = CustomUser.objects.get(email=email)
                    device_info = request.META.get('HTTP_USER_AGENT', 'Unknown Device')
                    email_sent = self.send_suspicious_login_email(user, ip, device_info)
                    print(f"DEBUG: Suspicious login email sent to {email}: {email_sent}")
                except CustomUser.DoesNotExist:
                    logger.warning(f"Attempted to send suspicious login email to non-existent user: {email}")
            
            # If account has had 5 or more failed attempts, lock it for 15 minutes
            if account_attempts >= 5:
                # Set account lockout
                lockout_duration = 15 * 60  # 15 minutes in seconds
                expiry_time = int(time.time()) + lockout_duration
                
                cache.set(account_lockout_key, True, timeout=lockout_duration)
                cache.set(f"account_lockout_expiry:{email}", expiry_time, timeout=lockout_duration)
                
                return Response({
                    "status": "error",
                    "message": "Account locked due to too many failed attempts. Please try again in 15 minutes or reset your password.",
                    "account_locked": True
                }, status=status.HTTP_403_FORBIDDEN)
        
        # If too many attempts from the same IP, block the request
        if attempts >= 5:  # 5 attempts max for IP-based rate limiting
            # Regular rate limiting response
            return Response({
                "status": "error",
                "message": "Too many login attempts. Please try again later.",
                "rate_limited": True
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        # Increment the counter
        cache.set(cache_key, attempts + 1, timeout=60)  # Reset after 60 seconds
        
        # Log data safely, masking the password
        log_data = request.data.copy() # Create a copy to avoid modifying the original data
        if 'password' in log_data:
            log_data['password'] = '********'
        print(f"Login attempt with data: {log_data}") # <-- Log the masked data instead

        print(f"Content-Type: {request.content_type}")

        email = request.data.get('email')
        password = request.data.get('password')

        # This print statement is okay as it already masks the password
        print(f"Extracted email: {email}, password: {'*' * len(password) if password else None}")
        
        if not email or not password:
            return Response({
                "status": "error",
                "message": "Email and password are required"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if user exists first
        try:
            user_exists = CustomUser.objects.filter(email=email).exists()
            print(f"User exists check: {user_exists}")
            if not user_exists:
                return Response({
                    "status": "error",
                    "message": "Invalid credentials"
                }, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            print(f"Error checking user existence: {str(e)}")
            return Response({
                "status": "error",
                "message": "An error occurred during authentication"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Try authentication with email parameter explicitly
        user = authenticate(request, email=email, password=password)
        print(f"Authentication result: {user}")
        
        # If that fails, try with username parameter (for backward compatibility)
        if user is None:
            user = authenticate(request, username=email, password=password)
            print(f"Second authentication attempt result: {user}")
        
        if user is None:
            return Response({
                "status": "error",
                "message": "Invalid credentials"
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Check if email is verified
        if not user.is_email_verified:
            # Generate new verification token if needed
            if not user.email_verification_token:
                user.email_verification_token = uuid.uuid4()
                user.save()
            
            # Send verification email
            verification_link = f"{os.environ.get('SERVER_API_URL')}api/email/verify/{user.email_verification_token}/"
            email_sent = send_verification_email(user, verification_link)
            
            return Response({
                "status": "error",
                "message": "Email not verified. Please check your email for verification link.",
                "email_sent": email_sent,
                "requires_verification": True
            }, status=status.HTTP_403_FORBIDDEN)
            
        if user.otp_required_for_login:
            otp = user.generate_otp()
            
            # Get location info from IP
            ip_address = request.META.get('REMOTE_ADDR', '127.0.0.1')
            location_info = get_location_from_ip(ip_address)
            
            # Get device info
            device = request.META.get('HTTP_USER_AGENT', 'Unknown Device')
            
            # Prepare context for email template
            context = {
                'user': user,
                'otp': otp,
                'location': f"{location_info.get('city', 'Unknown')}, {location_info.get('country', 'Unknown')}",
                'device': device,
                'timestamp': timezone.now().strftime('%b %d %Y %H:%M:%S %Z'),
                'frontend_url': os.environ.get('NEXTJS_URL').rstrip('/')
            }
            
            # Send OTP email using template
            html_message = render_to_string('email/otp.html', context)
            plain_message = strip_tags(html_message)
            
            try:
                send_mail(
                    subject='PHB Login Verification Code',
                    message=plain_message,
                    from_email=os.environ.get('DEFAULT_FROM_EMAIL'),
                    recipient_list=[user.email],
                    html_message=html_message,
                    fail_silently=False,
                )
                
                return Response({
                    "status": "pending",
                    "message": "OTP sent to your email",
                    "require_otp": True
                })
                
            except Exception as e:
                logger.error(f"Failed to send OTP email to {user.email}: {str(e)}")
                return Response({
                    "status": "error",
                    "message": "Failed to send OTP email. Please try again.",
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        # If OTP not required and email is verified, proceed with normal login
        refresh = RefreshToken.for_user(user)
        
        # Create user data dictionary
        user_data = {
            'id': user.id,
            'email': user.email,
            'full_name': f"{user.first_name} {user.last_name}".strip(),
            'is_verified': user.is_email_verified,
            'role': user.role,
            'hpn': user.hpn,
            'nin': user.nin,
            'phone': user.phone,
            'country': user.country,
            'state': user.state,
            'city': user.city,
            'date_of_birth': user.date_of_birth,
            'gender': user.gender,
            'has_completed_onboarding': user.has_completed_onboarding,
            'preferred_language': user.preferred_language,
            'secondary_languages': format_secondary_languages(user.secondary_languages),
            'custom_language': user.custom_language
        }
        
        return Response({
            "status": "success",
            "message": "Login successful",
            "tokens": {
                "access": str(refresh.access_token),
                "refresh": str(refresh)
            },
            "user_data": user_data
        })

class UserProfileUpdateView(RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user
        
    def partial_update(self, request, *args, **kwargs):
        # Print the incoming data for debugging
        print(f"[ProfileUpdate] Received data: {request.data}")
        
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, 
            data=request.data, 
            partial=True
        )
        
        if serializer.is_valid():
            # Print the validated data
            print(f"[ProfileUpdate] Validated data: {serializer.validated_data}")
            serializer.save()
            return Response(serializer.data)
        else:
            # Log detailed validation errors
            print(f"[ProfileUpdate] Validation errors: {serializer.errors}")
            # Print field requirements for debugging
            print(f"[ProfileUpdate] Field requirements: {[field.field_name for field in serializer._writable_fields]}")
            # Return detailed error response
            return Response({
                "status": "error",
                "message": "Profile update failed",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        # Add logging for PUT requests too
        print(f"[ProfileUpdate] PUT request received with data: {request.data}")
        
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        
        if serializer.is_valid():
            print(f"[ProfileUpdate] PUT valid data: {serializer.validated_data}")
            self.perform_update(serializer)
            return Response(serializer.data)
            print("Profile Data", serializer.data)
        else:
            # Log detailed validation errors for PUT
            print(f"[ProfileUpdate] PUT validation errors: {serializer.errors}")
            print(f"[ProfileUpdate] PUT field requirements: {[field.field_name for field in serializer._writable_fields]}")
            return Response({
                "status": "error",
                "message": "Profile update failed",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

class VerifyLoginOTPView(APIView):
    authentication_classes = []  # No JWT auth needed for OTP verification
    
    @rate_limit_otp(attempts=5, window=300)  # 5 attempts per 5 minutes
    def post(self, request):
        email = request.data.get('email')
        otp = request.data.get('otp')
        
        if not email or not otp:
            return Response({
                'error': 'Email and OTP are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = CustomUser.objects.get(email=email)
            
            # Check if OTP exists and is valid
            if not user.otp or not user.otp_created_at:
                return Response({
                    'error': 'No active OTP found. Please request a new one.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Verify OTP
            if user.verify_otp(otp):
                # Clear any rate limiting records on success
                cache_key = f'otp_attempts:{request.META.get("REMOTE_ADDR")}:{email}'
                cache.delete(cache_key)
                
                # Clear any account lockout records on successful verification
                account_lockout_key = f"account_lockout:{email}"
                account_attempts_key = f"account_attempts:{email}"
                lockout_expiry_key = f"account_lockout_expiry:{email}"
                
                # Delete all lockout-related cache entries
                cache.delete(account_lockout_key)
                cache.delete(account_attempts_key)
                cache.delete(lockout_expiry_key)
                
                # Log the account unlock
                logger.info(f"Account unlocked after successful OTP verification for user: {email}")
                
                # Get client IP and device info for security logging
                ip_address = request.META.get('REMOTE_ADDR', '127.0.0.1')
                device_info = request.META.get('HTTP_USER_AGENT', 'Unknown Device')
                
                # Generate tokens
                refresh = RefreshToken.for_user(user)
                
                # Create user data dictionary
                user_data = {
                    'id': user.id,
                    'email': user.email,
                    'full_name': f"{user.first_name} {user.last_name}".strip(),
                    'is_verified': user.is_email_verified,
                    'role': user.role,
                    'hpn': user.hpn,
                    'nin': user.nin,
                    'phone': user.phone,
                    'country': user.country,
                    'state': user.state,
                    'city': user.city,
                    'date_of_birth': user.date_of_birth,
                    'gender': user.gender,
                    'has_completed_onboarding': user.has_completed_onboarding,
                    'preferred_language': user.preferred_language,
                    'secondary_languages': format_secondary_languages(user.secondary_languages),
                    'custom_language': user.custom_language
                }
                
                # Log successful verification
                logger.info(f"Successful OTP verification for user: {email}")
                
                return Response({
                    'tokens': {
                        'access': str(refresh.access_token),
                        'refresh': str(refresh)
                    },
                    'user_data': user_data
                })
            
            # Log failed attempt
            logger.warning(f"Failed OTP verification attempt for user: {email}")
            
            return Response({
                'error': 'Invalid OTP'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except CustomUser.DoesNotExist:
            logger.warning(f"OTP verification attempted for non-existent user: {email}")
            return Response({
                'error': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Unexpected error during OTP verification: {str(e)}")
            return Response({
                'error': 'An error occurred during verification'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class EmailVerificationView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    
    def create(self, request, *args, **kwargs):
        user = request.user
        user.email_verification_token = uuid.uuid4()
        user.save()
        
        verification_link = f"{os.environ.get('SERVER_API_URL')}api/email/verify/{user.email_verification_token}/"
        
        if send_verification_email(user, verification_link):
            return Response({"message": "Verification email sent"})
        else:
            return Response(
                {"error": "Failed to send verification email"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class VerifyEmailToken(generics.GenericAPIView):
    queryset = CustomUser.objects.all()
    permission_classes = [AllowAny]
    serializer_class = EmailVerificationSerializer
    lookup_field = 'email_verification_token'
    
    def get(self, request, *args, **kwargs):
        try:
            # Get frontend URL from environment
            frontend_url = os.environ.get('NEXTJS_URL').rstrip('/')
            
            user = self.get_object()
            if user.is_email_verified:
                return render(request, 'email/verification_result.html', {
                    'status': 'already_verified',
                    'message': 'Email already verified',
                    'frontend_url': f"{frontend_url}/"  # Add trailing slash for template
                })

            # Verify the email
            user.is_email_verified = True
            user.email_verification_token = None
            user.save()

            # Send welcome email
            welcome_email_sent = send_welcome_email(user)
            logger.info(f"Welcome email {'sent successfully' if welcome_email_sent else 'failed to send'} for user: {user.email}")

            return render(request, 'email/verification_result.html', {
                'status': 'success',
                'message': 'Email verified successfully',
                'frontend_url': f"{frontend_url}/"
            })
            
        except CustomUser.DoesNotExist:
            return render(request, 'email/verification_result.html', {
                'status': 'error',
                'message': 'Invalid verification token',
                'frontend_url': f"{frontend_url}/"
            })
        
class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]
    
    @rate_limit_otp(attempts=5, window=300)
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            try:
                user = CustomUser.objects.get(email=email)
                # Generate token
                token = secrets.token_urlsafe(32)
                user.password_reset_token = token
                user.save()
                
                # Get location info from IP
                ip_address = request.META.get('REMOTE_ADDR', '127.0.0.1')
                location_info = get_location_from_ip(ip_address)
                
                # Get user agent info
                user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown Device')
                
                # Create context with all required information
                # Ensure the NEXTJS_URL ends with a slash if it doesn't already
                nextjs_url = os.environ.get('NEXTJS_URL', 'http://localhost:5173/')
                if not nextjs_url.endswith('/'):
                    nextjs_url += '/'
                
                # Construct the reset link with proper formatting
                reset_link = f"{nextjs_url}reset-password?token={token}"
                
                # Debug logging - only log non-sensitive information
                logging.info(f"Password reset token generated for user: {email}")
                logging.info(f"NEXTJS_URL from env: {nextjs_url}")
                logging.info(f"Reset link generated successfully")
                
                context = {
                    'reset_link': reset_link,
                    'token': token,  # Also pass token separately for debugging
                    'user_name': user.first_name or 'there',
                    'country': location_info.get('country', 'Unknown'),
                    'city': location_info.get('city', 'Unknown'),
                    'ip_address': ip_address,
                    'device': user_agent,
                    'date': timezone.now().strftime('%b %d %Y %H:%M:%S %Z')
                }
                
                # Send email with context
                send_mail(
                    'Password Reset Request',
                    'Click here to reset your password',
                    os.environ.get('DEFAULT_FROM_EMAIL'),
                    [email],
                    html_message=render_to_string('email/reset-password.html', context)
                )
                
                return Response({
                    'message': 'Password reset email sent! 📧',
                    'debug_info': {  # This is for debugging only
                        'location': location_info,
                        'ip': ip_address
                    }
                })
            except CustomUser.DoesNotExist:
                # Don't reveal if email exists
                return Response({'message': 'If this email exists, a reset link will be sent. 📧'})
        return Response(serializer.errors, status=400)

class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        # Log the incoming request data for debugging
        token_from_request = request.data.get('token', 'No token in request')
        logging.debug(f"Password reset attempt with token: {token_from_request[:10]}...")
        
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            token = serializer.validated_data['token']
            try:
                # Check if any user has this token (for debugging)
                users_with_token = CustomUser.objects.filter(password_reset_token=token)
                if not users_with_token.exists():
                    logging.warning(f"No users found with token starting with {token[:10]}...")
                    # Check if there are any users with reset tokens (for debugging)
                    users_with_any_token = CustomUser.objects.exclude(password_reset_token__isnull=True).exclude(password_reset_token='')
                    if users_with_any_token.exists():
                        logging.debug(f"There are {users_with_any_token.count()} users with reset tokens")
                    
                user = CustomUser.objects.get(password_reset_token=token)
                
                # Reset the password
                user.set_password(serializer.validated_data['new_password'])
                user.password_reset_token = None  # Invalidate token
                
                # If account was locked due to failed attempts, unlock it
                # Clear both account-based and IP-based lockouts
                account_cache_key = f"login_attempts:{user.email}"
                cache.delete(account_cache_key)  # Clear the account-based failed attempts counter
                
                # Also clear any IP-based rate limiting that might be associated with this account
                # Since we don't know which IP was used, we'll add a special flag to indicate this account
                # has been verified through password reset
                verified_key = f"verified_reset:{user.email}"
                cache.set(verified_key, True, 86400)  # Set for 24 hours
                
                logging.info(f"Account lockout cleared for {user.email} after password reset")
                
                user.save()
                logging.info(f"Password reset successful for user: {user.email}")
                return Response({'message': 'Password reset successful! 🎉 You can now log in with your new password.'})
            except CustomUser.DoesNotExist:
                logging.warning(f"Password reset failed: No user found with token starting with {token[:10]}...")
                return Response(
                    {'error': 'Invalid or expired reset token! 🚫 Please request a new password reset link.'}, 
                    status=400
                )
        else:
            logging.warning(f"Password reset validation failed: {serializer.errors}")
            return Response(serializer.errors, status=400)     

class UpdateOnboardingStatusView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = OnboardingStatusSerializer(request.user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Onboarding status updated! 🎉"}, 
                          status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)    

class RequestMedicalRecordOTPView(APIView):
    """
    Endpoint for requesting an OTP specifically for accessing medical records.
    This adds an extra layer of security beyond the initial login.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        user = request.user
        
        # Generate a new 6-digit OTP
        medical_record_otp = ''.join(random.choices('0123456789', k=6))
        
        # Store OTP and its creation time
        user.medical_record_otp = medical_record_otp
        user.medical_record_otp_created_at = timezone.now()
        user.save()
        
        # Send OTP via email
        subject = "Medical Record Access Code"
        message = f"Your verification code to access medical records is: {medical_record_otp}\n\nThis code will expire in 10 minutes."
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        
        return Response(
            {"message": "Medical record access code sent to your email"},
            status=status.HTTP_200_OK
        )

class VerifyMedicalRecordOTPView(APIView):
    """
    Endpoint to verify the medical record-specific OTP.
    On successful verification, grants a temporary access token for medical records.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        user = request.user
        otp = request.data.get('otp')
        
        if not otp:
            return Response(
                {"error": "OTP is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if OTP exists and is not expired (10 minute expiry)
        if not hasattr(user, 'medical_record_otp') or not user.medical_record_otp:
            return Response(
                {"error": "No OTP requested or OTP expired. Please request a new one."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        otp_created_at = user.medical_record_otp_created_at
        if otp_created_at and (timezone.now() - otp_created_at).total_seconds() > 600:  # 10 minutes
            # Clear expired OTP
            user.medical_record_otp = None
            user.medical_record_otp_created_at = None
            user.save()
            return Response(
                {"error": "OTP expired. Please request a new one."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Verify OTP
        if user.medical_record_otp != otp:
            return Response(
                {"error": "Invalid OTP"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Generate a temporary medical record access token (valid for 30 minutes)
        med_token = ''.join(random.choices('0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ', k=32))
        user.medical_record_access_token = med_token
        user.medical_record_token_created_at = timezone.now()
        
        # Clear used OTP
        user.medical_record_otp = None
        user.medical_record_otp_created_at = None
        user.save()
        
        return Response(
            {
                "message": "Medical record access granted",
                "med_access_token": med_token,
                "expires_in": 900  # 15 minutes in seconds (changed from 30 minutes)
            },
            status=status.HTTP_200_OK
        )

class PatientMedicalRecordView(APIView):
    """
    Secure endpoint for patients to access their own medical records
    Uses multiple layers of security:
    1. Authentication required (JWT)
    2. User can only access their own record
    3. Additional medical record-specific verification required
    4. Sensitive data is filtered at serializer level
    5. All access is logged for audit purposes
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            # Verify the user has a medical record
            if not hasattr(request.user, 'medical_record') or request.user.medical_record is None:
                return Response(
                    {"error": "Medical record not found"}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Verify medical record access token
            med_access_token = request.headers.get('X-Med-Access-Token')
            
            if not med_access_token:
                return Response(
                    {
                        "error": "Medical record access token required", 
                        "code": "MED_ACCESS_REQUIRED"
                    }, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Check if token exists and is not expired (30 minute validity)
            if not hasattr(request.user, 'medical_record_access_token') or \
               request.user.medical_record_access_token != med_access_token:
                return Response(
                    {
                        "error": "Invalid medical record access token",
                        "code": "INVALID_MED_ACCESS"
                    }, 
                    status=status.HTTP_403_FORBIDDEN
                )
                
            token_created_at = request.user.medical_record_token_created_at
            if token_created_at and (timezone.now() - token_created_at).total_seconds() > 900:  # 15 minutes (changed from 30 minutes)
                # Clear expired token
                request.user.medical_record_access_token = None
                request.user.medical_record_token_created_at = None
                request.user.save()
                return Response(
                    {
                        "error": "Medical record access expired. Please verify again after 15 minutes.",
                        "code": "MED_ACCESS_EXPIRED"
                    }, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Log access for audit purposes
            MedicalRecordAccess.objects.create(
                user=request.user,
                access_time=timezone.now(),
                ip_address=get_client_ip(request)
            )
            
            # Return the medical record data
            serializer = PatientMedicalRecordSerializer(request.user.medical_record)
            return Response(serializer.data)
            
        except Exception as e:
            # Log the error
            logger.error(f"Error accessing medical record: {str(e)}")
            return Response(
                {"error": "An error occurred while accessing medical records"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            if user.check_password(serializer.validated_data['current_password']):
                # Set new password
                user.set_password(serializer.validated_data['new_password'])
                user.save()
                
                # Get location info from IP and device info for the email
                ip_address = get_client_ip(request)
                location_info = get_location_from_ip(ip_address)
                device = request.META.get('HTTP_USER_AGENT', 'Unknown Device')
                
                # Prepare context for the email template
                context = {
                    'user': user,
                    'timestamp': timezone.now().strftime('%b %d %Y %H:%M:%S %Z'),
                    'location': f"{location_info.get('city', 'Unknown')}, {location_info.get('country', 'Unknown')}",
                    'device': device,
                    'frontend_url': os.environ.get('NEXTJS_URL', '').rstrip('/')
                }
                
                # Render the email template
                html_message = render_to_string('email/password_change_confirmation.html', context)
                plain_message = strip_tags(html_message)
                
                # Send the confirmation email
                try:
                    send_mail(
                        subject='PHB Healthcare - Password Changed Successfully',
                        message=plain_message,
                        from_email=os.environ.get('DEFAULT_FROM_EMAIL'),
                        recipient_list=[user.email],
                        html_message=html_message,
                        fail_silently=False,
                    )
                    logger.info(f"Password change confirmation email sent to {user.email}")
                except Exception as e:
                    logger.error(f"Failed to send password change confirmation email: {str(e)}")
                
                return Response({'message': 'Password changed successfully! 🎉'})
            else:
                return Response({'error': 'Current password is incorrect'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

      