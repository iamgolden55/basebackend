# api/views/__init__.py
# This file re-exports views classes for backward compatibility with existing imports

# Auth Views
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
    PatientMedicalRecordView,
    RequestMedicalRecordOTPView,
    VerifyMedicalRecordOTPView,
    UpdateOnboardingStatusView
)

# Hospital Views
from api.views.hospital.hospital_views import (
    HospitalRegistrationViewSet,
    UserHospitalRegistrationsView,
    SetPrimaryHospitalView,
    ApproveHospitalRegistrationView,
    HospitalAdminRegistrationView,
    AppointmentViewSet,
    HospitalLocationViewSet
)

# Function views - reexport from hospital_views
from api.views.hospital.hospital_views import (
    has_primary_hospital,
    approve_registration,
    hospital_registration,
    hospital_list,
    check_user_exists,
    appointment_types,
    departments,
    pending_hospital_registrations,
    doctor_appointments,
    department_pending_appointments,
    accept_appointment,
    start_consultation,
    complete_consultation
)

# Medical Views
from api.views.medical.medical_views import *
