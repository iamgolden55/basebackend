from django.urls import path, include
from rest_framework.routers import DefaultRouter
from api.views import UserProfileUpdateView, PasswordResetRequestView, PasswordResetConfirmView, UpdateOnboardingStatusView
from api.views import (
    HospitalRegistrationViewSet,
    UserHospitalRegistrationsView,
    SetPrimaryHospitalView,
    ApproveHospitalRegistrationView,
    HospitalAdminRegistrationView,
    hospital_list,
    approve_registration,
    HospitalLocationViewSet,
    hospital_registration,
    AppointmentViewSet,
    has_primary_hospital,
    check_user_exists,
    appointment_types,
    departments,
    DoctorAssignmentView,
    pending_hospital_registrations,
)
from rest_framework.decorators import api_view
from rest_framework.response import Response



router = DefaultRouter()
router.register(r'hospitals', HospitalLocationViewSet, basename='hospital')
router.register(r'appointments', AppointmentViewSet, basename='appointment')

@api_view(['GET'])
def health_check(request):
    return Response({"status": "healthy"})

urlpatterns = [
    path('profile/', UserProfileUpdateView.as_view(), name='profile-update'),
    path('password/reset/', PasswordResetRequestView.as_view(), name='password-reset-request'),
    path('password/reset/confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    path('onboarding/update/', UpdateOnboardingStatusView.as_view(), 
         name='update-onboarding-status'),
    
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