# Description: This file contains the views for user registration, login, email verification, and email verification token verification.
import os
from django.shortcuts import render, get_object_or_404
from api.models import CustomUser, HospitalRegistration, Hospital, Appointment, Doctor, AppointmentFee
from api.models.medical.appointment_notification import AppointmentNotification
from rest_framework import generics, status, viewsets, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import ( 
    UserSerializer, CustomTokenObtainPairSerializer, 
    EmailVerificationSerializer, UserProfileSerializer, 
    PasswordResetRequestSerializer, PasswordResetConfirmSerializer, 
    OnboardingStatusSerializer, HospitalRegistrationSerializer, 
    HospitalAdminRegistrationSerializer, HospitalSerializer, 
    HospitalLocationSerializer, NearbyHospitalSerializer,
    AppointmentSerializer, AppointmentListSerializer,
    ExistingUserToAdminSerializer, PatientMedicalRecordSerializer
)
from django.contrib.auth import authenticate
from django.core.mail import send_mail
from django.core.cache import cache
from rest_framework.generics import RetrieveUpdateAPIView
from django.template.loader import render_to_string
from .utilis import rate_limit_otp
from django.utils.html import strip_tags 
import uuid, secrets
import logging
from rest_framework.decorators import api_view, permission_classes, action
from django.utils import timezone
from .utils.location_utils import get_location_from_ip
from django.conf import settings
from .utils.email import send_verification_email, send_welcome_email, send_appointment_confirmation_email, send_appointment_status_update_email, send_appointment_reassignment_email
from api.models.medical.doctor_assignment import doctor_assigner
from rest_framework.exceptions import ValidationError
from datetime import datetime, timedelta
from django.utils.dateparse import parse_date
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from api.models.medical.appointment import AppointmentType
from api.models.medical.department import Department
from api.models.medical.doctor_assignment import MLDoctorAssignment
import random
from api.models.medical.medical_record_access import MedicalRecordAccess

# Configure logger
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

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class LoginView(APIView):
    def post(self, request):
        # Add debugging logs
        # print(f"Login attempt with data: {request.data}") # <-- Comment out or remove this line

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
            'has_completed_onboarding': user.has_completed_onboarding
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
        print("Received data:", request.data)  # Debug print 🔍
        
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, 
            data=request.data, 
            partial=True
        )
        
        if serializer.is_valid():
            # Print the validated data
            print("Validated data:", serializer.validated_data)  # Debug print 🔍
            serializer.save()
            return Response(serializer.data)
            
        return Response(serializer.errors, status=400)  
    
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
                    'has_completed_onboarding': user.has_completed_onboarding
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
                context = {
                    'reset_link': f"{os.environ.get('NEXTJS_URL')}reset-password?token={token}",
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
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            token = serializer.validated_data['token']
            try:
                user = CustomUser.objects.get(password_reset_token=token)
                user.set_password(serializer.validated_data['new_password'])
                user.password_reset_token = None  # Invalidate token
                user.save()
                return Response({'message': 'Password reset successful! 🎉'})
            except CustomUser.DoesNotExist:
                return Response(
                    {'error': 'Invalid or expired reset token! 🚫'}, 
                    status=400
                )
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

class HospitalRegistrationViewSet(viewsets.ModelViewSet):
    serializer_class = HospitalRegistrationSerializer
    permission_classes = [IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        # Add debug logging
        print("Received data:", request.data)  # Debug print 🔍
        
        # Validate hospital exists
        hospital_id = request.data.get('hospital')
        if not hospital_id:
            return Response({
                'error': 'Hospital ID is required',
                'available_hospitals': list(Hospital.objects.values('id', 'name'))
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            hospital = Hospital.objects.get(id=hospital_id)
        except Hospital.DoesNotExist:
            return Response({
                'error': 'Hospital not found',
                'available_hospitals': list(Hospital.objects.values('id', 'name'))
            }, status=status.HTTP_404_NOT_FOUND)

        # Create serializer with modified data
        serializer = self.get_serializer(data={
            'hospital_id': hospital_id,  # Use hospital_id instead of hospital
            'is_primary': request.data.get('is_primary', False),
            'user': request.user.id  # Make sure user is included
        })
        
        if serializer.is_valid():
            self.perform_create(serializer)
            return Response({
                "message": "Hospital registration request submitted successfully! 🏥",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
        else:
            print("Serializer errors:", serializer.errors)  # Debug print 🔍
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class UserHospitalRegistrationsView(generics.ListAPIView):
    serializer_class = HospitalRegistrationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'is_hospital_admin') and user.is_hospital_admin:
            # For hospital admins: show all registrations for their hospital
            return HospitalRegistration.objects.filter(
                hospital=user.hospital
            ).select_related('user', 'hospital')
        else:
            # For regular users: show their own registrations
            return HospitalRegistration.objects.filter(
                user=user
            ).select_related('user', 'hospital')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        if not serializer.data:
            return Response({
                "message": "No registrations found! 🔍",
                "hint": "Users need to register first using /api/hospitals/register/"
            }, status=status.HTTP_200_OK)
            
        return Response(serializer.data)

class SetPrimaryHospitalView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, hospital_id):
        success = request.user.set_primary_hospital(hospital_id)
        
        if success:
            return Response({
                "message": "Primary hospital updated successfully! 🏥✨",
            }, status=status.HTTP_200_OK)
        
        return Response({
            "error": "Could not set primary hospital. Please ensure you're registered with this hospital first! 🚫"
        }, status=status.HTTP_400_BAD_REQUEST)    

class ApproveHospitalRegistrationView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, registration_id):
        # Get the registration
        registration = get_object_or_404(HospitalRegistration, id=registration_id)
        
        # Check if user is hospital admin
        if request.user.role != 'hospital_admin':
            return Response({
                "error": "Only hospital administrators can approve registrations! 🚫"
            }, status=status.HTTP_403_FORBIDDEN)
            
        # Check if user is admin of this specific hospital
        if request.user.hospital != registration.hospital:
            return Response({
                "error": "You can only approve registrations for your hospital! 🏥"
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Approve the registration
        registration.approve_registration()
        
        return Response({
            "message": "Registration approved successfully! 🎉",
            "registration": {
                "id": registration.id,
                "hospital": registration.hospital.name,
                "user": registration.user.email,
                "status": "approved",
                "approved_date": registration.approved_date
            }
        }, status=status.HTTP_200_OK)    

class HospitalAdminRegistrationView(generics.CreateAPIView):
    permission_classes = [AllowAny]  # Initially allow anyone, but you might want to restrict this
    
    def get_serializer_class(self):
        if self.request.data.get('existing_user', False):
            return ExistingUserToAdminSerializer
        return HospitalAdminRegistrationSerializer
    
    def post(self, request, *args, **kwargs):
        is_existing_user = request.data.get('existing_user', False)
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=request.data)
        
        if serializer.is_valid():
            admin = serializer.save()
            
            response_data = {
                "message": "Hospital admin registered successfully! 🏥✨",
                "admin": {
                    "email": admin.email,
                    "name": admin.name,
                    "hospital": admin.hospital.name,
                    "position": admin.position
                }
            }
            
            if is_existing_user:
                response_data["admin"]["existing_user_converted"] = True
                
            return Response(response_data, status=status.HTTP_201_CREATED)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AppointmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing appointments 🏥
    
    This ViewSet provides comprehensive functionality for managing medical appointments,
    including creating, retrieving, updating, and deleting appointments, as well as
    specialized actions like cancellation, rescheduling, approval, and referral.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = AppointmentSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ['doctor__first_name', 'doctor__last_name', 'chief_complaint', 'status']
    ordering_fields = ['appointment_date', 'created_at', 'priority']
    ordering = ['-appointment_date']
    filterset_fields = ['status', 'appointment_type', 'priority', 'hospital', 'department']

    def get_queryset(self):
        """
        Filter appointments based on user role and query parameters
        """
        user = self.request.user
        
        # Debug info
        print(f"\n--- Appointment filtering for user ID: {user.id} ---")
        print(f"User role: {user.role}")
        print(f"Has doctor_profile: {hasattr(user, 'doctor_profile')}")
        print(f"Has hospital_admin: {hasattr(user, 'hospital_admin')}")
        
        # Base queryset with select_related for better performance
        base_qs = Appointment.objects.select_related(
            'doctor', 'doctor__user', 'hospital', 'department'
        )
        
        # Check for view_as parameter to override default role filtering
        view_as = self.request.query_params.get('view_as')
        print(f"View as parameter: {view_as}")
        
        # Filter based on view_as parameter first, then role
        if view_as == 'doctor' and hasattr(user, 'doctor_profile'):
            # Explicitly show appointments where user is the doctor
            queryset = base_qs.filter(doctor=user.doctor_profile)
            print("Filtering as doctor (explicit override)")
        elif view_as == 'patient':
            # Explicitly show appointments where user is the patient
            queryset = base_qs.filter(patient=user)
            print("Filtering as patient (explicit override)")
        elif hasattr(user, 'hospital_admin'):
            # Hospital admins see all appointments for their hospital
            queryset = base_qs.filter(hospital=user.hospital_admin.hospital)
            print("Filtering as hospital admin")
        else:
            # Default behavior: show patient appointments
            # This is the key change - all users (including doctors) 
            # see their patient appointments by default
            queryset = base_qs.filter(patient=user)
            print("Filtering as patient (default behavior)")
        
        # Apply date filters if provided
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        try:
            if start_date:
                start_date = timezone.make_aware(
                    datetime.strptime(start_date, '%Y-%m-%d')
                )
                queryset = queryset.filter(appointment_date__gte=start_date)
            
            if end_date:
                end_date = timezone.make_aware(
                    datetime.strptime(end_date, '%Y-%m-%d')
                ).replace(hour=23, minute=59, second=59)
                queryset = queryset.filter(appointment_date__lte=end_date)
                
        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid date format in query params: {e}")
        
        # Filter by upcoming appointments if requested
        upcoming = self.request.query_params.get('upcoming')
        if upcoming and upcoming.lower() == 'true':
            queryset = queryset.filter(
                appointment_date__gte=timezone.now(),
                status__in=['pending', 'confirmed', 'rescheduled']
            )
        
        print(f"Query returned {queryset.count()} appointments")
        return queryset

    def get_serializer_class(self):
        """
        Use different serializers based on the action
        """
        if self.action == 'list':
            return AppointmentListSerializer
        elif self.action == 'cancel':
            return AppointmentCancelSerializer
        elif self.action == 'reschedule':
            return AppointmentRescheduleSerializer
        elif self.action == 'approve':
            return AppointmentApproveSerializer
        elif self.action == 'refer':
            return AppointmentReferSerializer
        return AppointmentSerializer

    def create(self, request, *args, **kwargs):
        """Override create method to add debug logging and fix common issues"""
        import traceback
        import json
        
        print("\n\n====================================================")
        print("=============== APPOINTMENT CREATE DEBUG ============")
        print("====================================================")
        
        # Print request data in a more readable format
        print(f"REQUEST DATA (raw): {request.data}")
        
        # Try to print as formatted JSON for better readability
        try:
            if hasattr(request.data, '_mutable'):
                # For QueryDict
                data_copy = request.data.copy()
                print(f"REQUEST DATA (pretty): {json.dumps(data_copy, indent=2, default=str)}")
            else:
                # For regular dict or other data types
                print(f"REQUEST DATA (pretty): {json.dumps(request.data, indent=2, default=str)}")
        except Exception as e:
            print(f"Could not pretty-print request data: {e}")
        
        print(f"CONTENT TYPE: {request.content_type}")
        print(f"METHOD: {request.method}")
        print(f"USER: {request.user.id} - {request.user.email}")
        
        # Create a mutable copy of request.data
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        
        # Field name mapping - Fix common field name mismatches
        field_mapping = {
            'department_id': 'department',
            'doctor_id': 'doctor_id',  # Keep as is - serializer expects doctor_id
            'fee_id': None  # Remove fee_id completely
        }
        
        # Apply field name mapping
        for frontend_field, backend_field in field_mapping.items():
            if frontend_field in data:
                # Only rename if backend field is different and not None
                if backend_field and backend_field != frontend_field:
                    data[backend_field] = data.pop(frontend_field)
                    print(f"Mapped field {frontend_field} to {backend_field}")
                # Remove if backend field is explicitly None
                elif backend_field is None:
                    data.pop(frontend_field)
                    print(f"Removed field {frontend_field}")
                # Otherwise, keep the field as is (e.g., doctor_id)
                else:
                    print(f"Kept field {frontend_field} as is")
        
        # CRITICAL FIX: If hospital is None, get the user's primary hospital
        if data.get('hospital') is None:
            try:
                # Get user's primary hospital
                from api.models.medical.hospital_registration import HospitalRegistration
                primary_hospital = HospitalRegistration.objects.filter(
                    user=request.user,
                    is_primary=True,
                    status='approved'
                ).first()
                
                if primary_hospital:
                    data['hospital'] = primary_hospital.hospital.id
                    print(f"Using user's primary hospital: {primary_hospital.hospital.id} ({primary_hospital.hospital.name})")
                else:
                    # If no primary hospital, get any approved hospital
                    any_hospital = HospitalRegistration.objects.filter(
                        user=request.user,
                        status='approved'
                    ).first()
                    
                    if any_hospital:
                        data['hospital'] = any_hospital.hospital.id
                        print(f"Using user's approved hospital: {any_hospital.hospital.id} ({any_hospital.hospital.name})")
                    else:
                        print("User has no approved hospitals. Cannot proceed with appointment.")
                        return Response(
                            {"error": "You need to be registered with a hospital before booking appointments."},
                            status=status.HTTP_400_BAD_REQUEST
                        )
            except Exception as e:
                print(f"Error getting user's hospital: {str(e)}")
        
        # Fix appointment_type - convert from display name to database value
        if data.get('appointment_type') == 'First Visit':
            data['appointment_type'] = 'first_visit'
            print("Fixed appointment_type: 'First Visit' -> 'first_visit'")
        elif data.get('appointment_type') == 'Follow Up':
            data['appointment_type'] = 'follow_up'
            print("Fixed appointment_type: 'Follow Up' -> 'follow_up'")
        
        # IMPORTANT FIX: If the doctor is from a different hospital than the patient's,
        # we should use an available doctor from the patient's hospital
        if 'doctor_id' in data and data.get('hospital') is not None:
            try:
                doctor = Doctor.objects.get(id=data['doctor_id'])
                if doctor.hospital.id != data['hospital']:
                    print(f"Doctor {doctor.id} is from hospital {doctor.hospital.id}, but patient's hospital is {data['hospital']}")
                    
                    # Find an available doctor from the correct hospital
                    from django.db.models import Q
                    available_doctors = Doctor.objects.filter(
                        Q(department_id=data.get('department')),
                        Q(hospital_id=data.get('hospital')),
                        Q(is_active=True),
                        Q(available_for_appointments=True)
                    )
                    
                    if available_doctors.exists():
                        # Use the first available doctor
                        new_doctor = available_doctors.first()
                        data['doctor_id'] = new_doctor.id
                        print(f"Found available doctor {new_doctor.id} from correct hospital {data['hospital']}")
                    else:
                        print(f"No available doctors found in department {data.get('department')} at hospital {data['hospital']}")
                        doctor_id = data.pop('doctor_id', None)
                        print(f"Removed doctor_id {doctor_id} to allow auto-assignment")
            except Doctor.DoesNotExist:
                print(f"Doctor with ID {data.get('doctor_id')} does not exist")
                data.pop('doctor_id', None)
            except Exception as e:
                print(f"Error checking doctor's hospital: {str(e)}")
        
        # Call parent create method but catch validation errors
        try:
            # Use our modified data
            print(f"PROCESSED DATA: {data}")
            serializer = self.get_serializer(data=data)
            
            # Check serializer validation
            if not serializer.is_valid():
                print(f"VALIDATION ERRORS: {serializer.errors}")
                
                # Print more specific details about each validation error
                for field, errors in serializer.errors.items():
                    print(f"  - Field '{field}': {errors}")
                
                # Create a more detailed error response
                detailed_response = {
                    'status': 'error',
                    'message': 'Validation failed',
                    'errors': serializer.errors,
                    'data_received': {
                        key: value for key, value in data.items() 
                        if key not in ['password', 'token']  # Don't log sensitive data
                    },
                    'help': 'Check the error details for each field and ensure all required fields are provided correctly.'
                }
                
                return Response(
                    detailed_response,
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            print("SERIALIZER VALIDATED SUCCESSFULLY")
            print(f"VALIDATED DATA: {serializer.validated_data}")
            
            # Continue with normal create process
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        
        except Exception as e:
            print(f"EXCEPTION: {str(e)}")
            print(f"EXCEPTION TYPE: {type(e).__name__}")
            print(f"TRACEBACK: {traceback.format_exc()}")
            
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        finally:
            print("====================================================")
            print("=============== END DEBUG INFO =====================")
            print("====================================================\n\n")

    def perform_create(self, serializer):
        """
        Set the patient to the current user when creating an appointment
        """
        # Validate appointment date is not in the past
        appointment_date = serializer.validated_data.get('appointment_date')
        if appointment_date and appointment_date < timezone.now():
            raise ValidationError("Cannot create appointments in the past.")
        
        # No fee handling needed anymore - removing all fee-related code
        
        hospital = serializer.validated_data.get('hospital')
        department = serializer.validated_data.get('department')
        
        # Check if doctor_id is provided
        doctor = serializer.validated_data.get('doctor')
        
        # If no doctor provided or doctor is not available, find an available doctor
        if not doctor or not self._is_doctor_available(doctor, appointment_date):
            if doctor:
                print(f"Doctor {doctor.id} is not available at {appointment_date}")
            else:
                print(f"No doctor specified, finding available doctor")
            
            # Find available doctors from the user's hospital
            try:
                from django.db.models import Q
                available_doctors = Doctor.objects.filter(
                    Q(department=department),
                    Q(hospital=hospital),
                    Q(is_active=True),
                    Q(available_for_appointments=True)
                )
                
                print(f"Found {available_doctors.count()} potential doctors in department {department.id} at hospital {hospital.id}")
                
                # Try to find an available doctor
                doctor_found = False
                for doc in available_doctors:
                    if self._is_doctor_available(doc, appointment_date):
                        doctor = doc
                        serializer.validated_data['doctor'] = doctor
                        print(f"Found available doctor: {doctor.id}")
                        doctor_found = True
                        break
                
                if not doctor_found:
                    print("No available doctors found at the specified time")
                    raise ValidationError("No doctors available at the requested time. Please choose a different time or department.")
            except Exception as e:
                print(f"Error finding available doctor: {str(e)}")
                raise ValidationError(f"Error finding available doctor: {str(e)}")
        
        # Save the appointment - no need to set fee-related fields
        appointment = serializer.save(patient=self.request.user)
        
        # Send confirmation (with error handling)
        try:
            self._send_appointment_confirmation(appointment)
        except Exception as e:
            logger.error(f"Failed to send appointment confirmation: {e}")
            # Don't raise the error - appointment creation should succeed even if notification fails
        
        return appointment

    def _is_doctor_available(self, doctor, appointment_date):
        """
        Check if a doctor is available for a given appointment date
        """
        print(f"\n--- Checking availability for Doctor {doctor.id} at {appointment_date} ---")
        
        # Check if date is within doctor's consultation days
        day_name = appointment_date.strftime('%a')  # Get 3-letter day name
        consultation_days = [d.strip() for d in doctor.consultation_days.split(',')]
        print(f"Day of appointment: {day_name}")
        print(f"Doctor consultation days: {consultation_days}")
        
        # Make the day check more flexible by ignoring case and allowing more formats
        day_matches = any(day.lower() in day_name.lower() for day in consultation_days) or \
                      any(day_name.lower() in day.lower() for day in consultation_days)
                      
        if not day_matches and day_name not in consultation_days:
            print(f"Doctor {doctor.id} doesn't work on {day_name}")
            return False
        
        # Check if time is within consultation hours
        appointment_time = appointment_date.time()
        print(f"Appointment time: {appointment_time}")
        print(f"Doctor hours: {doctor.consultation_hours_start} - {doctor.consultation_hours_end}")
        
        # Skip time check if consultation hours are not set
        if doctor.consultation_hours_start is None or doctor.consultation_hours_end is None:
            print(f"Doctor {doctor.id} has no consultation hours set, assuming available")
        else:
            if not (doctor.consultation_hours_start <= appointment_time <= doctor.consultation_hours_end):
                print(f"Appointment time {appointment_time} is outside doctor's hours ({doctor.consultation_hours_start} - {doctor.consultation_hours_end})")
                return False
        
        # Check for overlapping appointments
        appointment_end = appointment_date + timedelta(minutes=doctor.appointment_duration)
        print(f"Appointment duration: {doctor.appointment_duration} minutes")
        print(f"Checking for overlapping appointments between {appointment_date} and {appointment_end}")
        
        overlapping = Appointment.objects.filter(
            doctor=doctor,
            status__in=['pending', 'confirmed', 'in_progress', 'scheduled', 'checking_in'],
            appointment_date__date=appointment_date.date(),  # Only check appointments on the same day
            appointment_date__gte=appointment_date - timedelta(minutes=doctor.appointment_duration),  # Start time is before or at the requested end time
            appointment_date__lt=appointment_end  # Start time is before the end of the requested slot
        )
        
        if overlapping.exists():
            print(f"Found {overlapping.count()} overlapping appointments:")
            for appt in overlapping:
                print(f"  - Appointment {appt.id} at {appt.appointment_date}")
            return False
        
        print(f"Doctor {doctor.id} is available at {appointment_date}")
        return True

    def _send_appointment_confirmation(self, appointment):
        """
        Send appointment confirmation with error handling
        """
        try:
            # Create email notification for the patient
            AppointmentNotification.objects.create(
                appointment=appointment,
                recipient=appointment.patient,
                notification_type='email',
                event_type='booking_confirmation',
                subject='Appointment Confirmation',
                message=f'Your appointment with Dr. {appointment.doctor.user.get_full_name()} '
                        f'has been scheduled for {appointment.appointment_date.strftime("%B %d, %Y at %I:%M %p")}.',
                scheduled_time=timezone.now()
            )
            
            # Create SMS notification for the patient
            AppointmentNotification.objects.create(
                appointment=appointment,
                recipient=appointment.patient,
                notification_type='sms',
                event_type='booking_confirmation',
                subject='Appointment Confirmation',
                message=f'Your appointment with Dr. {appointment.doctor.user.get_full_name()} '
                        f'has been scheduled for {appointment.appointment_date.strftime("%B %d, %Y at %I:%M %p")}.',
                scheduled_time=timezone.now()
            )
            
            # Create notification for the doctor
            AppointmentNotification.objects.create(
                appointment=appointment,
                recipient=appointment.doctor.user,
                notification_type='email',
                event_type='booking_confirmation',
                subject='New Appointment',
                message=f'New appointment scheduled with {appointment.patient.get_full_name()} '
                        f'on {appointment.appointment_date.strftime("%B %d, %Y at %I:%M %p")}.',
                scheduled_time=timezone.now()
            )
            
            # Create reminders
            appointment.create_reminders()
            
        except Exception as e:
            logger.error(f"Error sending appointment confirmation: {str(e)}")
            # Don't raise the error - appointment creation should succeed even if notification fails

    @action(detail=True, methods=['get'], url_path='summary')
    def summary(self, request, pk=None):
        """
        Return a detailed summary of the appointment
        """
        appointment = self.get_object()
        serializer = AppointmentSerializer(appointment, context={'request': request})
        
        # Ensure consistent patient name formatting
        if appointment.patient:
            patient_name = f"{appointment.patient.first_name} {appointment.patient.last_name}"
        else:
            patient_name = None
        
        # Get appointment summary data
        summary_data = {
            # Appointment details
            "appointment_id": appointment.appointment_id,
            "doctor": serializer.data.get('doctor_full_name'),
            "date": serializer.data.get('formatted_date'),
            "time": serializer.data.get('formatted_time'),
            "formatted_date_time": serializer.data.get('formatted_date_time'),
            "hospital": appointment.hospital.name,
            "department": appointment.department.name,
            "type": serializer.data.get('type') or serializer.data.get('formatted_appointment_type'),
            "priority": serializer.data.get('formatted_priority'),
            "duration": f"{appointment.duration} minutes",
            "status": serializer.data.get('status_display'),
            
            # Patient details
            "patient_name": patient_name,  # Use consistently formatted patient name
            "chief_complaint": appointment.chief_complaint or "None specified",
            "symptoms": appointment.symptoms or "None",
            "medical_history": appointment.medical_history or "None",
            "allergies": appointment.allergies or "None",
            "current_medications": appointment.current_medications or "None",
            
            # Additional info
            "important_notes": serializer.data.get('important_notes'),
            "payment_required": appointment.payment_required,
            "payment_status": appointment.payment_status,
            "is_insurance_based": appointment.is_insurance_based,
            "insurance_details": appointment.insurance_details if appointment.is_insurance_based else None,
            "notes": appointment.notes or "",
            "created_at": appointment.created_at.strftime("%B %d, %Y at %I:%M %p") if appointment.created_at else None,
            "updated_at": appointment.updated_at.strftime("%B %d, %Y at %I:%M %p") if appointment.updated_at else None,
        }
        
        return Response(summary_data)

    @action(detail=True, methods=['patch'], url_path='status')
    def update_status(self, request, pk=None):
        """
        Update the status of an appointment and send email notification to the patient
        """
        try:
            appointment = self.get_object()
            
            # Validate the status
            new_status = request.data.get('status')
            
            if not new_status:
                return Response({
                    'status': 'error',
                    'message': 'Status field is required'
                }, status=status.HTTP_400_BAD_REQUEST)
                
            if new_status not in dict(Appointment.STATUS_CHOICES):
                return Response({
                    'status': 'error',
                    'message': f'Invalid status: {new_status}. Valid statuses are: {", ".join(dict(Appointment.STATUS_CHOICES).keys())}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Handle auto-reassignment for cancelled appointments
            if new_status == 'cancelled':
                cancellation_reason = request.data.get('cancellation_reason')
                if not cancellation_reason:
                    return Response({
                        'status': 'error',
                        'message': 'Cancellation reason is required'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Save the cancellation reason to both notes and the dedicated field
                appointment.notes = f"Cancelled by Dr. {appointment.doctor.user.get_full_name()}. Reason: {cancellation_reason}\n\n" + (appointment.notes or "")
                appointment.cancellation_reason = cancellation_reason
                appointment.cancelled_at = timezone.now()
                
                # Find another available doctor in the same department
                from api.models import Doctor
                department = appointment.department
                hospital = appointment.hospital
                
                # Get doctors in the same department, excluding the current one
                alternative_doctors = Doctor.objects.filter(
                    department=department,
                    hospital=hospital,
                    is_active=True
                ).exclude(id=appointment.doctor.id)
                
                # If there are alternative doctors, reassign instead of cancelling
                if alternative_doctors.exists():
                    # Find an available doctor for this timeslot
                    appointment_date = appointment.appointment_date
                    available_doctor = None
                    
                    for doctor in alternative_doctors:
                        # Check if this doctor is available at this time
                        if doctor.is_available_at(appointment_date):
                            available_doctor = doctor
                            break
                    
                    if available_doctor:
                        # Reassign to the new doctor instead of cancelling
                        previous_doctor = appointment.doctor
                        appointment.doctor = available_doctor
                        appointment.status = 'pending'  # Reset to pending for the new doctor
                        appointment.save()
                        
                        # Send reassignment email
                        from api.utils.email import send_appointment_reassignment_email
                        send_appointment_reassignment_email(appointment, previous_doctor, cancellation_reason)
                        
                        serializer = self.get_serializer(appointment)
                        return Response({
                            'status': 'success',
                            'message': f'Appointment reassigned to Dr. {available_doctor.user.get_full_name()}',
                            'data': serializer.data
                        })
                
                # If no available doctor found, proceed with cancellation
                appointment.status = new_status
                appointment.save()
            else:
                # Regular status update
                appointment.status = new_status
                appointment.save()
            
            # Send status update email
            from api.utils.email import send_appointment_status_update_email
            send_appointment_status_update_email(appointment)
            
            serializer = self.get_serializer(appointment)
            return Response({
                'status': 'success',
                'message': f'Appointment status updated to {new_status}',
                'data': serializer.data
            })
        except Exception as e:
            logger.error(f"Error updating appointment status: {str(e)}")
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class HospitalLocationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for location-based hospital search and registration.
    """
    queryset = Hospital.objects.all()
    serializer_class = HospitalLocationSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def nearby(self, request):
        """
        Find nearby hospitals based on user's location or IP address.
        With fallback to user's profile location if no hospitals found.
        """
        # Get location parameters
        latitude = request.query_params.get('latitude')
        longitude = request.query_params.get('longitude')
        radius = request.query_params.get('radius', 10)  # Default 10km radius

        try:
            # If coordinates not provided, try to get location from IP
            if not (latitude and longitude):
                ip_address = request.META.get('REMOTE_ADDR')
                location_info = get_location_from_ip(ip_address)
                if location_info:
                    latitude = location_info.get('latitude')
                    longitude = location_info.get('longitude')

            # Convert to float and initialize hospitals to empty list
            hospitals = []
            
            # Only search by coordinates if we have them
            if latitude and longitude:
                # Convert to float
                latitude = float(latitude)
                longitude = float(longitude)
                radius = float(radius)

                # Find nearby hospitals
                hospitals = Hospital.find_nearby_hospitals(
                    latitude=latitude,
                    longitude=longitude,
                    radius_km=radius
                )

            # If no hospitals found through geolocation, fallback to user's profile location
            if not hospitals:
                user = request.user
                location_message = "No nearby hospitals found."
                
                # Check if user has state/city in their profile
                if user.state or user.city:
                    query = Q()
                    
                    # Add state and city filters if available
                    if user.city:
                        query |= Q(city__iexact=user.city)
                    
                    if user.state:
                        query |= Q(state__iexact=user.state)
                    
                    # Find hospitals matching the user's location
                    location_hospitals = Hospital.objects.filter(query)
                    
                    if location_hospitals.exists():
                        hospitals = location_hospitals
                        location_message = f"Showing hospitals in your profile location: {user.city or ''}, {user.state or ''}".strip(", ")
                
                # If still no hospitals, return all as last resort
                if not hospitals:
                    hospitals = Hospital.objects.all()
                    location_message = "No hospitals found in your area. Showing all hospitals."
                
                # Serialize the results
                serializer = HospitalSerializer(
                    hospitals,
                    many=True
                )
                
                return Response({
                    'message': location_message,
                    'hospitals': serializer.data
                })
            
            # Serialize the nearby results
            serializer = NearbyHospitalSerializer(
                hospitals,
                many=True,
                context={'request': request}
            )

            return Response({
                'hospitals': serializer.data,
                'location': {
                    'latitude': latitude,
                    'longitude': longitude,
                    'radius_km': radius
                }
            })

        except (ValueError, TypeError) as e:
            return Response(
                {"error": f"Invalid location parameters: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def register(self, request, pk=None):
        """
        Register the current user with a hospital.
        """
        hospital = self.get_object()
        user = request.user

        # Check if already registered
        existing_registration = HospitalRegistration.objects.filter(
            user=user,
            hospital=hospital
        ).first()

        if existing_registration:
            return Response({
                "error": "Already registered with this hospital",
                "registration": HospitalRegistrationSerializer(existing_registration).data
            }, status=status.HTTP_400_BAD_REQUEST)

        # Create new registration
        try:
            # Check if this is the user's first registration
            is_first_registration = not HospitalRegistration.objects.filter(
                user=user
            ).exists()

            registration = HospitalRegistration.objects.create(
                user=user,
                hospital=hospital,
                is_primary=is_first_registration,  # Set as primary if first registration
                status='pending'
            )

            return Response({
                "message": "Registration request submitted successfully",
                "registration": HospitalRegistrationSerializer(registration).data
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                "error": f"Registration failed: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def set_primary(self, request, pk=None):
        """
        Set a hospital as the user's primary hospital.
        """
        hospital = self.get_object()
        user = request.user

        try:
            # Check if registered and approved
            registration = HospitalRegistration.objects.filter(
                user=user,
                hospital=hospital,
                status='approved'
            ).first()

            if not registration:
                return Response({
                    "error": "Must be registered and approved with this hospital first"
                }, status=status.HTTP_400_BAD_REQUEST)

            # Update primary status
            HospitalRegistration.objects.filter(
                user=user,
                is_primary=True
            ).update(is_primary=False)

            registration.is_primary = True
            registration.save()

            return Response({
                "message": "Primary hospital updated successfully",
                "registration": HospitalRegistrationSerializer(registration).data
            })

        except Exception as e:
            return Response({
                "error": f"Failed to set primary hospital: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def has_primary_hospital(request):
    """
    Check if the authenticated user has a registered primary hospital
    
    Returns:
        {
            "has_primary": true/false,
            "primary_hospital": { hospital data } or null
        }
    """
    # Get the user's registered hospitals
    primary_registration = HospitalRegistration.objects.filter(
        user=request.user,
        is_primary=True
    ).first()
    
    if primary_registration:
        return Response({
            "has_primary": True,
            "primary_hospital": {
                "id": primary_registration.hospital.id,
                "name": primary_registration.hospital.name,
                "address": primary_registration.hospital.address,
                "city": primary_registration.hospital.city,
                "country": primary_registration.hospital.country,
                "registration_date": primary_registration.created_at,
                "status": primary_registration.status,
            }
        })
    else:
        return Response({
            "has_primary": False,
            "primary_hospital": None
        })

# existing views continue here...        

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def approve_registration(request, registration_id):
    # Check if user is hospital admin
    if not request.user.role == 'hospital_admin':
        return Response({
            'detail': 'Only hospital admins can approve registrations'
        }, status=403)
    
    # Get the registration
    try:
        registration = HospitalRegistration.objects.get(id=registration_id)
    except HospitalRegistration.DoesNotExist:
        return Response({
            'detail': 'Registration not found'
        }, status=404)
    
    # Check if admin belongs to the same hospital
    if request.user.hospital_admin_profile.hospital != registration.hospital:
        return Response({
            'detail': 'You can only approve registrations for your hospital'
        }, status=403)
    
    # Approve the registration
    registration.status = 'approved'
    registration.approved_date = timezone.now()
    registration.save()
    
    serializer = HospitalRegistrationSerializer(registration)
    return Response({
        'message': 'Registration approved successfully! 🎉',
        'registration': serializer.data
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def hospital_registration(request):
    try:
        # Validate input data
        hospital_id = request.data.get('hospital')
        is_primary = request.data.get('is_primary', False)
        
        if not hospital_id:
            return Response({
                'error': 'Hospital ID is required',
                'available_hospitals': list(Hospital.objects.values('id', 'name'))
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get the hospital
        try:
            hospital = Hospital.objects.get(id=hospital_id)
        except Hospital.DoesNotExist:
            return Response({
                'error': 'Hospital not found',
                'available_hospitals': list(Hospital.objects.values('id', 'name'))
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if registration already exists
        if HospitalRegistration.objects.filter(user=request.user, hospital=hospital).exists():
            return Response({
                'error': 'You are already registered with this hospital'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create registration
        registration = HospitalRegistration.objects.create(
            user=request.user,
            hospital=hospital,
            is_primary=is_primary,
            status='pending'
        )
        
        serializer = HospitalRegistrationSerializer(registration)
        return Response({
            'message': 'Registration request submitted successfully! 🎉',
            'registration': serializer.data
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def hospital_list(request):
    hospitals = Hospital.objects.all()
    serializer = HospitalSerializer(hospitals, many=True)
    return Response({
        'hospitals': serializer.data
    })

@api_view(['GET'])
@permission_classes([AllowAny])
def check_user_exists(request):
    """
    Check if a user exists by email and if they're already a hospital admin.
    This is used in the hospital admin registration flow for converting existing users.
    
    Query params:
    - email: The email to check
    
    Returns:
    {
        "exists": true/false,
        "is_admin": true/false
    }
    """
    email = request.query_params.get('email')
    if not email:
        return Response({
            "error": "Email parameter is required"
        }, status=status.HTTP_400_BAD_REQUEST)
    
    user_exists = CustomUser.objects.filter(email=email).exists()
    is_admin = False
    
    if user_exists:
        user = CustomUser.objects.get(email=email)
        is_admin = hasattr(user, 'hospital_admin_profile')
    
    return Response({
        "exists": user_exists,
        "is_admin": is_admin
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def appointment_types(request):
    # Filter by hospital if provided
    hospital_id = request.query_params.get('hospital')
    
    if hospital_id:
        # Get hospital-specific types and global types
        types = AppointmentType.objects.filter(
            (Q(hospital_id=hospital_id) | Q(hospital__isnull=True)),
            is_active=True
        ).order_by('name', '-hospital_id')
        # Deduplicate by name: prefer hospital-specific over global
        seen = set()
        unique_types = []
        for t in types:
            if t.name not in seen:
                unique_types.append(t)
                seen.add(t.name)
        types = unique_types
    else:
        # Get all active global types only
        types = AppointmentType.objects.filter(is_active=True, hospital__isnull=True)
    
    data = [{"id": type.id, "name": type.name, "description": type.description} for type in types]
    return Response(data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def departments(request):
    # Get hospital_id from query params if provided
    hospital_id = request.query_params.get('hospital')
    
    if hospital_id:
        # If hospital_id is provided, verify user is registered with this hospital
        hospital_registration = HospitalRegistration.objects.filter(
            user=request.user,
            hospital_id=hospital_id,
            status='approved'
        ).first()
        
        if not hospital_registration:
            return Response({
                'status': 'error',
                'message': 'You are not registered with this hospital'
            }, status=status.HTTP_403_FORBIDDEN)
            
        departments = Department.objects.filter(hospital_id=hospital_id)
    else:
        # If no hospital_id provided, get departments from user's primary hospital
        primary_registration = HospitalRegistration.objects.filter(
            user=request.user,
            is_primary=True,
            status='approved'
        ).first()
        
        if not primary_registration:
            return Response({
                'status': 'error',
                'message': 'No primary hospital found. Please register with a hospital first.'
            }, status=status.HTTP_404_NOT_FOUND)
            
        departments = Department.objects.filter(hospital=primary_registration.hospital)
    
    data = [{"id": dept.id, "name": dept.name, "code": dept.code} for dept in departments]
    return Response({
        'status': 'success',
        'departments': data
    })

# Add this new class for doctor assignment
class DoctorAssignmentView(APIView):
    """
    API endpoint for doctor assignment based on department, hospital, and appointment details.
    This endpoint allows finding available time slots without exposing individual doctor names.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        # Log incoming request data for debugging
        print(f"DoctorAssignment received data: {request.data}")
        data = request.data
        
        try:
            # Extract data from request - accepting frontend parameter names
            # Fix: We're now using the variable names that match the frontend
            department_id = data.get('department')
            appointment_type = data.get('appointment_type')
            appointment_date = data.get('preferred_date')
            hospital_id = data.get('hospital')
            
            # These are additional parameters from frontend that we'll accept but not require
            chief_complaint = data.get('chief_complaint')
            priority = data.get('priority')
            preferred_language = data.get('preferred_language')
            
            print(f"Extracted fields: department={department_id}, "
                  f"appointment_type={appointment_type}, "
                  f"preferred_date={appointment_date}, "
                  f"hospital={hospital_id}, "
                  f"chief_complaint={chief_complaint}, "
                  f"priority={priority}, "
                  f"preferred_language={preferred_language}")
            
            # Validate required fields
            missing_fields = []
            if not department_id:
                missing_fields.append('department')
            if not appointment_type:
                missing_fields.append('appointment_type')
            if not appointment_date:
                missing_fields.append('preferred_date')
                
            if missing_fields:
                error_msg = f"Missing required fields: {', '.join(missing_fields)}"
                print(f"Validation error: {error_msg}")
                return Response({
                    'status': 'error',
                    'message': error_msg
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Parse appointment date
            try:
                if isinstance(appointment_date, str):
                    # Convert to datetime if it's a string
                    parsed_date = parse_date(appointment_date)
                    if not parsed_date:
                        raise ValueError(f"Invalid date format: {appointment_date}")
                    appointment_date = parsed_date
                    print(f"Parsed preferred_date: {appointment_date}")
            except Exception as e:
                error_msg = f"Invalid date format: {str(e)}"
                print(f"Date parsing error: {error_msg}")
                return Response({
                    'status': 'error',
                    'message': error_msg
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get user's primary hospital if hospital_id is not provided
            if not hospital_id:
                print(f"No hospital provided, looking for hospitals for user {request.user.id}")
                
                # First try to get primary approved hospital
                hospital_registration = HospitalRegistration.objects.filter(
                    user=request.user, 
                    is_primary=True,
                    status='approved'
                ).first()
                
                if not hospital_registration:
                    # If no primary approved hospital, try to get any approved hospital
                    hospital_registration = HospitalRegistration.objects.filter(
                        user=request.user,
                        status='approved'
                    ).first()
                
                if not hospital_registration:
                    # If no approved hospital, check if there are any pending registrations
                    pending_registration = HospitalRegistration.objects.filter(
                        user=request.user,
                        status='pending'
                    ).exists()
                    
                    if pending_registration:
                        error_msg = 'You have pending hospital registrations. Please wait for approval or contact admin.'
                    else:
                        # Check if user has any hospital registrations at all
                        any_registration = HospitalRegistration.objects.filter(
                            user=request.user
                        ).exists()
                        
                        
                        if any_registration:
                            error_msg = 'None of your hospital registrations are approved. Please contact admin.'
                        else:
                            error_msg = 'You are not registered with any hospital. Please register with a hospital first.'
                    
                    print(f"Hospital error: {error_msg}")
                    return Response({
                        'status': 'error',
                        'message': error_msg
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                hospital_id = hospital_registration.hospital.id
                print(f"Using hospital: {hospital_id} ({hospital_registration.hospital.name})")
                
                # For debugging
                print(f"All hospital registrations for user {request.user.id}:")
                all_registrations = HospitalRegistration.objects.filter(user=request.user)
                for reg in all_registrations:
                    print(f"  - Hospital: {reg.hospital.name}, Primary: {reg.is_primary}, Status: {reg.status}")
            
            # Validate department exists in the hospital
            try:
                department = Department.objects.get(id=department_id)
                print(f"Found department: {department.name}")
            except Department.DoesNotExist:
                error_msg = f'Department not found with ID: {department_id}'
                print(f"Department error: {error_msg}")
                return Response({
                    'status': 'error',
                    'message': error_msg
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Validate appointment type
            try:
                appointment_type_obj = AppointmentType.objects.get(id=appointment_type)
                print(f"Found appointment type: {appointment_type_obj.name}")
            except AppointmentType.DoesNotExist:
                # Try with lowercase ID or by name
                try:
                    # Try first by name match
                    appointment_type_obj = AppointmentType.objects.filter(
                        name__iexact=appointment_type
                    ).first()
                    
                    if not appointment_type_obj:
                        # Then try by ID case-insensitive
                        appointment_type_obj = AppointmentType.objects.filter(
                            id__iexact=appointment_type
                        ).first()
                        
                    if not appointment_type_obj:
                        raise AppointmentType.DoesNotExist()
                        
                    print(f"Found appointment type using alternative method: {appointment_type_obj.name}")
                except:
                    error_msg = f'Invalid appointment type: {appointment_type}'
                    print(f"Appointment type error: {error_msg}")
                    return Response({
                        'status': 'error',
                        'message': error_msg
                    }, status=status.HTTP_400_BAD_REQUEST)

            # Find available doctors in this department at this hospital
            doctors = Doctor.objects.filter(
                department_id=department_id,
                hospital_id=hospital_id,
                is_active=True,
                available_for_appointments=True
            )
            
            print(f"Found {doctors.count()} doctors in department {department_id} at hospital {hospital_id}")
            
            if not doctors.exists():
                error_msg = f'No doctors available in department {department.name}'
                print(f"Doctors error: {error_msg}")
                return Response({
                    'status': 'error',
                    'message': error_msg
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Find available time slots for the given date
            available_slots = []
            
            # Business hours (9am to 5pm)
            start_hour = 9
            end_hour = 17
            
            print(f"Generating time slots for date: {appointment_date}")
            
            # Generate all possible slots
            for hour in range(start_hour, end_hour):
                for minute in [0, 30]:  # 30-minute slots
                    slot_time = f"{hour:02d}:{minute:02d}"
                    
                    # Create a datetime for this slot
                    slot_datetime = datetime.combine(
                        appointment_date, 
                        datetime.strptime(slot_time, "%H:%M").time(),
                        tzinfo=timezone.get_current_timezone()
                    )
                    
                    # Skip slots in the past
                    if slot_datetime < timezone.now():
                        print(f"Skipping past time slot: {slot_time}")
                        continue
                    
                    # Check if any doctor is available at this time
                    slot_available = False
                    for doctor in doctors:
                        # Check if the doctor has consultation hours set
                        if doctor.consultation_hours_start is None or doctor.consultation_hours_end is None:
                            # If no consultation hours, assume standard working hours
                            is_working_hours = start_hour <= slot_datetime.hour < end_hour
                        else:
                            # Use the doctor's defined hours
                            doctor_time = slot_datetime.time()
                            is_working_hours = doctor.consultation_hours_start <= doctor_time <= doctor.consultation_hours_end
                        
                        # Check day of week
                        day_name = slot_datetime.strftime('%a')  # Get 3-letter day name
                        if doctor.consultation_days:
                            consultation_days = [d.strip() for d in doctor.consultation_days.split(',')]
                            # Make the day check more flexible
                            day_matches = any(day.lower() in day_name.lower() for day in consultation_days) or \
                                         any(day_name.lower() in day.lower() for day in consultation_days) or \
                                         day_name in consultation_days
                        else:
                            # If no consultation days specified, assume all days
                            day_matches = True
                        
                        if not (is_working_hours and day_matches):
                            # Skip this doctor if not working at this time
                            continue
                        
                        # Check if the doctor has an existing appointment at this time
                        conflicting_appointment = Appointment.objects.filter(
                            doctor=doctor,
                            appointment_date=slot_datetime,
                            status__in=['scheduled', 'confirmed', 'checking_in', 'pending', 'in_progress']
                        ).exists()
                        
                        if not conflicting_appointment:
                            # This doctor is available at this time slot
                            slot_available = True
                            print(f"Doctor {doctor.id} is available at {slot_time}")
                            break
                    
                    if slot_available:
                        available_slots.append({
                            'time': slot_time,
                            'datetime': slot_datetime.isoformat()
                        })
            
            print(f"Generated {len(available_slots)} available time slots")
            
            response_data = {
                'status': 'success',
                'department': {
                    'id': department.id,
                    'name': department.name
                },
                'appointment_type': {
                    'id': appointment_type_obj.id,
                    'name': appointment_type_obj.name
                },
                'preferred_date': appointment_date.isoformat() if hasattr(appointment_date, 'isoformat') else appointment_date,
                'available_slots': available_slots
            }
            
            print(f"Returning {len(available_slots)} available slots")
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            import traceback
            error_msg = f"Error in doctor assignment: {str(e)}\n{traceback.format_exc()}"
            print(error_msg)
            logger.error(error_msg)
            return Response({
                'status': 'error',
                'message': str(e),
                'detail': traceback.format_exc() if settings.DEBUG else 'An error occurred processing your request'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def pending_hospital_registrations(request):
    """
    Lists all hospitals with pending user registrations.
    - Admin/staff users can see all hospitals with pending registrations
    - Hospital admins can see pending registrations for their own hospital
    - Regular users cannot access this endpoint
    """
    # Check permissions
    is_admin = request.user.is_staff or request.user.is_superuser
    is_hospital_admin = request.user.role == 'hospital_admin'
    
    if not (is_admin or is_hospital_admin):
        return Response({
            'error': 'You do not have permission to view pending registrations'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # For hospital admins, only show their hospital
    if is_hospital_admin and not is_admin:
        # Get the admin's hospital
        try:
            admin_hospital = request.user.hospital_admin_profile.hospital
            
            # Get pending registrations for this hospital
            pending_registrations = HospitalRegistration.objects.filter(
                status='pending',
                hospital=admin_hospital
            ).select_related('hospital', 'user')
            
            # Format the response
            registrations_list = []
            for registration in pending_registrations:
                registrations_list.append({
                    'id': registration.id,
                    'user_id': registration.user.id,
                    'user_email': registration.user.email,
                    'user_name': f"{registration.user.first_name} {registration.user.last_name}",
                    'registration_date': registration.created_at
                })
            
            return Response({
                'hospital': {
                    'id': admin_hospital.id, 
                    'name': admin_hospital.name
                },
                'pending_registrations': registrations_list,
                'total_pending': len(registrations_list)
            })
        
        except Exception as e:
            return Response({
                'error': f'Error retrieving hospital information: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # For admin/staff, show all hospitals with pending registrations
    else:
        # Get all pending registrations
        pending_registrations = HospitalRegistration.objects.filter(
            status='pending'
        ).select_related('hospital', 'user')
        
        # Group registrations by hospital
        hospitals_with_pending = {}
        for registration in pending_registrations:
            hospital_id = registration.hospital.id
            hospital_name = registration.hospital.name
            
            if hospital_id not in hospitals_with_pending:
                hospitals_with_pending[hospital_id] = {
                    'id': hospital_id,
                    'name': hospital_name,
                    'pending_registrations': []
                }
            
            hospitals_with_pending[hospital_id]['pending_registrations'].append({
                'id': registration.id,
                'user_id': registration.user.id,
                'user_email': registration.user.email,
                'user_name': f"{registration.user.first_name} {registration.user.last_name}",
                'registration_date': registration.created_at
            })
        
        # Add count to each hospital
        for hospital_id in hospitals_with_pending:
            hospitals_with_pending[hospital_id]['total_pending'] = len(
                hospitals_with_pending[hospital_id]['pending_registrations']
            )
        
        return Response({
            'hospitals_with_pending': list(hospitals_with_pending.values()),
            'total_hospitals': len(hospitals_with_pending),
            'total_pending_registrations': sum(
                len(h['pending_registrations']) for h in hospitals_with_pending.values()
            )
        })

class DoctorAppointmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing doctor appointments 🏥
    
    This ViewSet provides functionality for doctors to manage their appointments,
    including retrieving and updating appointment status.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = AppointmentSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ['patient__first_name', 'patient__last_name', 'chief_complaint', 'status']
    ordering_fields = ['appointment_date', 'created_at', 'priority']
    ordering = ['-appointment_date']
    filterset_fields = ['status', 'appointment_type', 'priority']
    lookup_field = 'appointment_id'
    
    def get_queryset(self):
        """
        Return appointments where the current user is the doctor
        """
        user = self.request.user
        
        # Check if user has a doctor profile
        if not hasattr(user, 'doctor_profile'):
            return Appointment.objects.none()
            
        # Base queryset - get doctor's appointments
        queryset = Appointment.objects.filter(
            doctor=user.doctor_profile
        ).select_related(
            'doctor', 'doctor__user', 'hospital', 'department', 'patient'
        ).order_by('-appointment_date')
        
        # Apply date filters if provided
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        try:
            if start_date:
                start_date = timezone.make_aware(
                    datetime.strptime(start_date, '%Y-%m-%d')
                )
                queryset = queryset.filter(appointment_date__gte=start_date)
            
            if end_date:
                end_date = timezone.make_aware(
                    datetime.strptime(end_date, '%Y-%m-%d')
                ).replace(hour=23, minute=59, second=59)
                queryset = queryset.filter(appointment_date__lte=end_date)
                
        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid date format in query params: {e}")
        
        # Filter by upcoming appointments if requested
        upcoming = self.request.query_params.get('upcoming')
        if upcoming and upcoming.lower() == 'true':
            queryset = queryset.filter(
                appointment_date__gte=timezone.now(),
                status__in=['pending', 'confirmed', 'rescheduled']
            )
        
        # Filter by status if provided
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        logger.info(f"Doctor appointment query returned {queryset.count()} appointments")
        return queryset
    
    def get_serializer_class(self):
        """
        Use different serializers based on the action
        """
        if self.action in ['list', 'upcoming', 'today']:
            return AppointmentListSerializer
        return AppointmentSerializer
    
    @action(detail=True, methods=['patch'], url_path='status')
    def update_status(self, request, appointment_id=None):
        """
        Update the status of an appointment and send email notification to the patient
        """
        try:
            appointment = self.get_object()
            
            # Validate the status
            new_status = request.data.get('status')
            
            if not new_status:
                return Response({
                    'status': 'error',
                    'message': 'Status field is required'
                }, status=status.HTTP_400_BAD_REQUEST)
                
            if new_status not in dict(Appointment.STATUS_CHOICES):
                return Response({
                    'status': 'error',
                    'message': f'Invalid status: {new_status}. Valid statuses are: {", ".join(dict(Appointment.STATUS_CHOICES).keys())}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Handle auto-reassignment for cancelled appointments
            if new_status == 'cancelled':
                cancellation_reason = request.data.get('cancellation_reason')
                if not cancellation_reason:
                    return Response({
                        'status': 'error',
                        'message': 'Cancellation reason is required'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Save the cancellation reason to both notes and the dedicated field
                appointment.notes = f"Cancelled by Dr. {appointment.doctor.user.get_full_name()}. Reason: {cancellation_reason}\n\n" + (appointment.notes or "")
                appointment.cancellation_reason = cancellation_reason
                appointment.cancelled_at = timezone.now()
                
                # Find another available doctor in the same department
                from api.models import Doctor
                department = appointment.department
                hospital = appointment.hospital
                
                # Get doctors in the same department, excluding the current one
                alternative_doctors = Doctor.objects.filter(
                    department=department,
                    hospital=hospital,
                    is_active=True
                ).exclude(id=appointment.doctor.id)
                
                # If there are alternative doctors, reassign instead of cancelling
                if alternative_doctors.exists():
                    # Find an available doctor for this timeslot
                    appointment_date = appointment.appointment_date
                    available_doctor = None
                    
                    for doctor in alternative_doctors:
                        # Check if this doctor is available at this time
                        if doctor.is_available_at(appointment_date):
                            available_doctor = doctor
                            break
                    
                    if available_doctor:
                        # Reassign to the new doctor instead of cancelling
                        previous_doctor = appointment.doctor
                        appointment.doctor = available_doctor
                        appointment.status = 'pending'  # Reset to pending for the new doctor
                        appointment.save()
                        
                        # Send reassignment email
                        from api.utils.email import send_appointment_reassignment_email
                        send_appointment_reassignment_email(appointment, previous_doctor, cancellation_reason)
                        
                        serializer = self.get_serializer(appointment)
                        return Response({
                            'status': 'success',
                            'message': f'Appointment reassigned to Dr. {available_doctor.user.get_full_name()}',
                            'data': serializer.data
                        })
                
                # If no available doctor found, proceed with cancellation
                appointment.status = new_status
                appointment.save()
            else:
                # Regular status update
                appointment.status = new_status
                appointment.save()
            
            # Send status update email
            from api.utils.email import send_appointment_status_update_email
            send_appointment_status_update_email(appointment)
            
            serializer = self.get_serializer(appointment)
            return Response({
                'status': 'success',
                'message': f'Appointment status updated to {new_status}',
                'data': serializer.data
            })
        except Exception as e:
            logger.error(f"Error updating appointment status: {str(e)}")
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['patch'], url_path='notes')
    def update_notes(self, request, appointment_id=None):
        """
        Update notes for an appointment
        """
        try:
            appointment = self.get_object()
            
            # Validate the notes
            notes = request.data.get('notes')
            
            if notes is None:
                return Response({
                    'status': 'error',
                    'message': 'Notes field is required'
                }, status=status.HTTP_400_BAD_REQUEST)
                
            # Update the notes
            appointment.notes = notes
            appointment.save()
            
            # Return the updated appointment
            serializer = self.get_serializer(appointment)
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Error updating appointment notes: {str(e)}")
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'], url_path='summary')
    def summary(self, request, appointment_id=None):
        """
        Return a detailed summary of the appointment
        """
        appointment = self.get_object()
        serializer = AppointmentSerializer(appointment, context={'request': request})
        
        # Ensure consistent patient name formatting
        if appointment.patient:
            patient_name = f"{appointment.patient.first_name} {appointment.patient.last_name}"
        else:
            patient_name = None
        
        # Get appointment summary data
        summary_data = {
            # Appointment details
            "appointment_id": appointment.appointment_id,
            "doctor": serializer.data.get('doctor_full_name'),
            "date": serializer.data.get('formatted_date'),
            "time": serializer.data.get('formatted_time'),
            "formatted_date_time": serializer.data.get('formatted_date_time'),
            "hospital": appointment.hospital.name,
            "department": appointment.department.name,
            "type": serializer.data.get('type') or serializer.data.get('formatted_appointment_type'),
            "priority": serializer.data.get('formatted_priority'),
            "duration": f"{appointment.duration} minutes",
            "status": serializer.data.get('status_display'),
            
            # Patient details
            "patient_name": patient_name,  # Use consistently formatted patient name
            "chief_complaint": appointment.chief_complaint or "None specified",
            "symptoms": appointment.symptoms or "None",
            "medical_history": appointment.medical_history or "None",
            "allergies": appointment.allergies or "None",
            "current_medications": appointment.current_medications or "None",
            
            # Additional info
            "important_notes": serializer.data.get('important_notes'),
            "payment_required": appointment.payment_required,
            "payment_status": appointment.payment_status,
            "is_insurance_based": appointment.is_insurance_based,
            "insurance_details": appointment.insurance_details if appointment.is_insurance_based else None,
            "notes": appointment.notes or "",
            "created_at": appointment.created_at.strftime("%B %d, %Y at %I:%M %p") if appointment.created_at else None,
            "updated_at": appointment.updated_at.strftime("%B %d, %Y at %I:%M %p") if appointment.updated_at else None,
        }
        
        return Response(summary_data)
    
    @action(detail=False, methods=['get'], url_path='upcoming')
    def upcoming(self, request):
        """
        Return upcoming appointments for the doctor
        """
        queryset = self.get_queryset().filter(
            appointment_date__gte=timezone.now(),
            status__in=['pending', 'confirmed', 'rescheduled']
        )
        
        serializer = AppointmentListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='today')
    def today(self, request):
        """
        Return today's appointments for the doctor
        """
        today = timezone.now().date()
        queryset = self.get_queryset().filter(
            appointment_date__date=today
        )
        
        serializer = AppointmentListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        """
        Return appointment statistics for the doctor
        """
        try:
            user = request.user
            
            # Check if user has a doctor profile
            if not hasattr(user, 'doctor_profile'):
                return Response({
                    'status': 'error',
                    'message': 'You are not registered as a doctor in the system'
                }, status=status.HTTP_403_FORBIDDEN)
                
            # Get doctor's appointments
            appointments = Appointment.objects.filter(
                doctor=user.doctor_profile
            )
            
            # Calculate statistics
            today = timezone.now().date()
            
            # Total appointments
            total = appointments.count()
            
            # Today's appointments
            today_count = appointments.filter(appointment_date__date=today).count()
            
            # Upcoming appointments
            upcoming_count = appointments.filter(
                appointment_date__gte=timezone.now(),
                status__in=['pending', 'confirmed', 'rescheduled']
            ).count()
            
            # Completed appointments
            completed_count = appointments.filter(status='completed').count()
            
            # Cancelled appointments
            cancelled_count = appointments.filter(status='cancelled').count()
            
            # No-show appointments
            no_show_count = appointments.filter(status='no_show').count()
            
            # Status distribution
            status_counts = {}
            for status_choice, _ in Appointment.STATUS_CHOICES:
                status_counts[status_choice] = appointments.filter(status=status_choice).count()
                
            # Return statistics
            return Response({
                'total_appointments': total,
                'today_appointments': today_count,
                'upcoming_appointments': upcoming_count,
                'completed_appointments': completed_count,
                'cancelled_appointments': cancelled_count,
                'no_show_appointments': no_show_count,
                'status_distribution': status_counts
            })
        except Exception as e:
            import traceback
            return Response({
                'status': 'error',
                'message': str(e),
                'detail': traceback.format_exc() if settings.DEBUG else 'An error occurred processing your request'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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

# Helper function to get client IP address for audit logs
def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

