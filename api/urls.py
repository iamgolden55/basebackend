from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.views.generic import RedirectView

# Auth views
from api.views.auth.authentication import (
    UserProfileUpdateView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    PatientMedicalRecordView,
    RequestMedicalRecordOTPView,
    VerifyMedicalRecordOTPView,
    UpdateOnboardingStatusView,
    ChangePasswordView,
)

# Hospital admin auth views
from api.views.auth.hospital_admin_auth import (
    HospitalAdminLoginView,
    VerifyHospitalAdmin2FAView
)
from api.views.auth.hospital_admin_password import HospitalAdminPasswordChangeView
from api.views.auth.hospital_admin_reset import (
    HospitalAdminResetRequestView,
    HospitalAdminResetVerifyView,
    HospitalAdminResetCompleteView
)

# Hospital views
from api.views.hospital.hospital_views import (
    HospitalRegistrationViewSet,
    UserHospitalRegistrationsView,
    SetPrimaryHospitalView,
    ApproveHospitalRegistrationView,
    HospitalAdminRegistrationView,
    hospital_list,
    approve_registration,
    HospitalLocationViewSet,
    hospital_registration,
    has_primary_hospital,
    check_user_exists,
    appointment_types,
    departments,
    pending_hospital_registrations,
    doctor_appointments,
    AppointmentViewSet,
    department_pending_appointments,
    accept_appointment,
    start_consultation,
    complete_consultation,
    add_doctor_notes,
    cancel_appointment,
    mark_appointment_no_show,
    create_prescription,
    patient_prescriptions,
    appointment_prescriptions
)

# Medical views
from api.views.medical.medical_views import DoctorAssignmentView

# Patient Admission views
from api.views.hospital.admission_views import PatientAdmissionViewSet

# Notification views
from api.views.utils.notification_views import InAppNotificationViewSet

from rest_framework.decorators import api_view
from rest_framework.response import Response



router = DefaultRouter()
router.register(r'hospitals', HospitalLocationViewSet, basename='hospital')
router.register(r'appointments', AppointmentViewSet, basename='appointment')
router.register(r'notifications', InAppNotificationViewSet, basename='notification')
router.register(r'admissions', PatientAdmissionViewSet, basename='admission')

@api_view(['GET'])
def health_check(request):
    return Response({"status": "healthy"})

urlpatterns = [
    path('profile/', UserProfileUpdateView.as_view(), name='profile-update'),
    path('password/reset/', PasswordResetRequestView.as_view(), name='password-reset-request'),
    path('password/reset/confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    path('password/change/', ChangePasswordView.as_view(), name='password-change'),
    path('onboarding/update/', UpdateOnboardingStatusView.as_view(), 
         name='update-onboarding-status'),
         
    # ============= HOSPITAL ADMIN AUTH ENDPOINTS =============
    # Dedicated endpoints for hospital administrators with enhanced security
    path('hospitals/admin/login/', 
         HospitalAdminLoginView.as_view(), 
         name='hospital-admin-login'),
    path('hospitals/admin/verify-2fa/', 
         VerifyHospitalAdmin2FAView.as_view(), 
         name='hospital-admin-verify-2fa'),
    path('hospitals/admin/change-password/', 
          HospitalAdminPasswordChangeView.as_view(), 
          name='hospital-admin-change-password'),
    
    # Hospital admin password reset flow with enhanced security
    path('hospitals/admin/reset-password/request/',
         HospitalAdminResetRequestView.as_view(),
         name='hospital-admin-reset-request'),
    path('hospitals/admin/reset-password/verify/',
         HospitalAdminResetVerifyView.as_view(),
         name='hospital-admin-reset-verify'),
    path('hospitals/admin/reset-password/complete/',
         HospitalAdminResetCompleteView.as_view(),
         name='hospital-admin-reset-complete'),
    
    # ============= HOSPITAL REGISTRATION ENDPOINTS =============
    # IMPORTANT: These endpoints are for users to register with EXISTING hospitals.
    # They do NOT create new hospitals. Hospitals must be pre-created in the system.
    
    # Register a user with an existing hospital - requires hospital_id in the request
    # POST data should include hospital ID, not hospital creation data
    path('hospitals/register/', 
         HospitalRegistrationViewSet.as_view({'post': 'create'}), 
         name='hospital-register'),
    
    # Get all hospitals that the current user is registered with
    # Returns empty list if user has no registrations
    path('hospitals/registrations/', 
         UserHospitalRegistrationsView.as_view(), 
         name='user-hospital-registrations'),
    
    # Set primary hospital endpoint -- This is the endpoint for the users to set their primary hospital.
    # Users must be registered with the hospital first before setting it as primary
    path('hospitals/<int:hospital_id>/set-primary/', 
         SetPrimaryHospitalView.as_view(), 
         name='set-primary-hospital'),
    
    # Approve hospital registration endpoint -- This is the endpoint for the hospital admins to approve the hospital registrations.
    # Only hospital admins can approve registrations for their own hospital
    path('hospitals/registrations/<int:registration_id>/approve/',
         ApproveHospitalRegistrationView.as_view(),
         name='approve-hospital-registration'),
    
    # Hospital admin registration endpoint -- This is the endpoint for the users to register as a hospital admin.
    # Can convert existing users to admins using existing_user=True and user_email parameters
    path('hospitals/admin/register/', 
         HospitalAdminRegistrationView.as_view(), 
         name='hospital-admin-register'),
    
    # Check user exists endpoint -- This is the endpoint for the users to check if a user exists by email and if they're already a hospital admin.
    path('hospitals/admin/check-user/', 
         check_user_exists,
         name='check-user-exists'),
    
    # Hospital list endpoint -- This is the endpoint for the users to get the list of hospitals.
    # Returns all available pre-existing hospitals in the system
    path('hospitals/', hospital_list, name='hospital-list'),
    
    # Approve registration endpoint -- This is the endpoint for the hospital admins to approve the hospital registrations.
    path('hospitals/pending/<int:registration_id>/', approve_registration, name='approve-registration'),
    
    # Has primary hospital endpoint -- This is the endpoint for the users to check if they have a primary hospital.
    path('user/has-primary-hospital/', has_primary_hospital, name='has-primary-hospital'),
    
    # Get all hospitals with pending user registrations - admin/staff only
    path('hospitals/pending-registrations/', 
         pending_hospital_registrations, 
         name='pending-hospital-registrations'),
    
    path('', include(router.urls)),
    
    path('health-check/', health_check, name='health-check'),
    
    # New endpoints for appointment booking
    path('appointment-types/', appointment_types, name='appointment-types'),
    path('departments/', departments, name='departments'),
    path('doctor-assignment/', DoctorAssignmentView.as_view(), name='doctor-assignment'),
    
    # New endpoint for patient medical records - secure access
    path('patient/medical-record/', PatientMedicalRecordView.as_view(), name='patient-medical-record'),
    path('patient/medical-record/request-otp/', RequestMedicalRecordOTPView.as_view(), name='request-medical-record-otp'),
    path('patient/medical-record/verify-otp/', VerifyMedicalRecordOTPView.as_view(), name='verify-medical-record-otp'),
    
    # New endpoint for doctor's appointments
    path('doctor-appointments/', doctor_appointments, name='doctor-appointments'),
    
    # New endpoint for doctor-appointments with appointment ID - redirects to appointments endpoint
    path('doctor-appointments/<str:appointment_id>/', 
         lambda request, appointment_id: RedirectView.as_view(
             url='/api/appointments/{}/'.format(appointment_id), 
             permanent=True
         )(request), 
         name='doctor-appointments-detail'),

    # New endpoint for doctor-appointments status update
    path('doctor-appointments/<str:appointment_id>/status/', 
         lambda request, appointment_id: RedirectView.as_view(
             url='/api/appointments/{}/status/'.format(appointment_id), 
             permanent=False
         )(request), 
         name='doctor-appointments-status'),

    # New endpoint for doctor-appointments complete-consultation redirect
    path('doctor-appointments/<str:appointment_id>/complete-consultation/', 
         lambda request, appointment_id: RedirectView.as_view(
             url='/api/appointments/{}/complete-consultation/'.format(appointment_id), 
             permanent=False
         )(request), 
         name='doctor-appointments-complete-consultation'),

     # New endpoint for doctor profile
     

    # New endpoints for department pending appointments workflow
    path('department-pending-appointments/', department_pending_appointments, name='department-pending-appointments'),
    path('appointments/<str:appointment_id>/accept/', accept_appointment, name='accept-appointment'),
    path('appointments/<str:appointment_id>/start-consultation/', start_consultation, name='start-consultation'),
    path('appointments/<str:appointment_id>/complete-consultation/', complete_consultation, name='complete-consultation'),
    path('appointments/<str:appointment_id>/add-notes/', add_doctor_notes, name='add-doctor-notes'),
    path('appointments/<str:appointment_id>/cancel/', cancel_appointment, name='cancel-appointment'),
    path('appointments/<str:appointment_id>/no-show/', mark_appointment_no_show, name='mark-appointment-no-show'),
    
    # Prescription endpoints
    path('appointments/<str:appointment_id>/prescriptions/', create_prescription, name='create-prescription'),
    path('appointments/<str:appointment_id>/prescriptions/view/', appointment_prescriptions, name='appointment-prescriptions'),
    path('prescriptions/', patient_prescriptions, name='patient-prescriptions'),
    path('prescriptions/<str:appointment_id>/', patient_prescriptions, name='patient-prescriptions-by-appointment'),
]

# Available endpoints:
# GET /api/hospitals/nearby/?latitude=<lat>&longitude=<lng>&radius=<km>
# POST /api/hospitals/<id>/register/
# POST /api/hospitals/<id>/set-primary/

# Appointment endpoints:
# GET /api/appointments/ - List all appointments for the current user
# POST /api/appointments/ - Create a new appointment
# GET /api/appointments/<id>/ - Get details of a specific appointment
# PUT/PATCH /api/appointments/<id>/ - Update an appointment
# DELETE /api/appointments/<id>/ - Delete an appointment
# POST /api/appointments/<id>/cancel/ - Cancel an appointment
# POST /api/appointments/<id>/reschedule/ - Reschedule an appointment
# POST /api/appointments/<id>/approve/ - Approve an appointment
# POST /api/appointments/<id>/refer/ - Refer an appointment to another hospital
# POST /api/appointments/<id>/complete/ - Mark an appointment as completed
# GET /api/appointments/upcoming/ - Get upcoming appointments
# GET /api/appointments/today/ - Get today's appointments

# Prescription endpoints:
# POST /api/appointments/<id>/prescriptions/ - Create prescriptions for a specific appointment
# POST /api/prescriptions/ - Create prescriptions with appointment_id in the request body
# GET /api/appointments/<id>/prescriptions/view/ - View prescriptions for a specific appointment
# GET /api/prescriptions/view/ - View all prescriptions for the current user