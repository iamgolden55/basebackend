# api/views/auth/__init__.py
# This file re-exports authentication-related views

from api.views.auth.authentication import (
    UserRegistrationView,
    EmailVerificationView,
    VerifyEmailToken,
    VerifyLoginOTPView,
    LoginView,
    CustomTokenObtainPairView,
    UserProfileUpdateView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    UpdateOnboardingStatusView,
    PatientMedicalRecordView,
    RequestMedicalRecordOTPView,
    VerifyMedicalRecordOTPView
)
