# Description: This file contains the views for user registration, login, email verification, and email verification token verification.
import os
from django.shortcuts import render
from api.models import CustomUser
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import UserSerializer, CustomTokenObtainPairSerializer, EmailVerificationSerializer, UserProfileSerializer, PasswordResetRequestSerializer, PasswordResetConfirmSerializer, OnboardingStatusSerializer
from django.contrib.auth import authenticate
from django.core.mail import send_mail
from django.core.cache import cache
from rest_framework.generics import RetrieveUpdateAPIView
from django.template.loader import render_to_string
from .utilis import rate_limit_otp
from django.utils.html import strip_tags 
import uuid, secrets
import logging

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

    def perform_create(self, serializer):
        # Save the user first
        user = serializer.save()
        
        # Generate verification token
        user.email_verification_token = uuid.uuid4()
        user.save()

        # Generate verification link
        verification_link = f"{os.environ.get('SERVER_API_URL')}api/email/verify/{user.email_verification_token}/"

        # Use the new send_verification_email function
        if send_verification_email(user, verification_link):
            return Response({
                "message": "Registration successful! Please check your email for verification.",
                "email": user.email
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                "message": "Registration successful but failed to send verification email. Please try again later.",
                "email": user.email
            }, status=status.HTTP_201_CREATED)

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer   

class LoginView(APIView):
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        
        user = authenticate(request, username=email, password=password)
        if user is None:
            return Response({"error": "Invalid credentials"}, status=401)
            
        if user.otp_required_for_login:
            otp = user.generate_otp()
            # Send OTP email
            send_mail(
                'Login OTP',
                f'Your login OTP is: {otp}',
                'from@yourhealthcare.com',
                [user.email]
            )
            return Response({"message": "OTP sent", "require_otp": True})
            
        # If OTP not required, proceed with normal login
        refresh = RefreshToken.for_user(user)
        return Response({
            "tokens": {
                "access": str(refresh.access_token),
                "refresh": str(refresh)
            }
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
                
                # Generate tokens using CustomTokenObtainPairSerializer
                serializer = CustomTokenObtainPairSerializer()
                refresh = serializer.get_token(user)
                
                # Log successful verification
                logger.info(f"Successful OTP verification for user: {email}")
                
                return Response({
                    'tokens': {
                        'access': str(refresh.access_token),
                        'refresh': str(refresh)
                    },
                    'user_data': refresh['user_data']  # Include user data in response
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

            user.is_email_verified = True
            user.email_verification_token = None
            user.save()

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
    
    @rate_limit_otp(attempts=5, window=300)  # Fixed! 🛠️
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
                
                # Send email
               # reset_link = f"{os.environ.get('NEXTJS_URL')}/reset-password?token={token}"
                reset_link = f"{os.environ.get('NEXTJS_URL')}/auth/reset-password?token={token}"
                send_mail(
                    'Password Reset Request',
                    f'Click here to reset your password: {reset_link}',
                    os.environ.get('DEFAULT_FROM_EMAIL'),
                    [email],
                    html_message=render_to_string('email/password_reset.html', {
                        'reset_link': reset_link,
                        'user_name': user.first_name
                    })
                )
                return Response({'message': 'Password reset email sent! 📧'})
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
