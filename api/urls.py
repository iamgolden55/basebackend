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
    has_primary_hospital
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
    # Hospital registration endpoints
    path('hospitals/register/', 
         HospitalRegistrationViewSet.as_view({'post': 'create'}), 
         name='hospital-register'),
    
    path('hospitals/registrations/', 
         UserHospitalRegistrationsView.as_view(), 
         name='user-hospital-registrations'),
    
    path('hospitals/<int:hospital_id>/set-primary/', 
         SetPrimaryHospitalView.as_view(), 
         name='set-primary-hospital'),
    path('hospitals/registrations/<int:registration_id>/approve/',
         ApproveHospitalRegistrationView.as_view(),
         name='approve-hospital-registration'),
    path('hospitals/admin/register/', 
         HospitalAdminRegistrationView.as_view(), 
         name='hospital-admin-register'),
    path('hospitals/', hospital_list, name='hospital-list'),
    path('hospitals/pending/<int:registration_id>/', approve_registration, name='approve-registration'),
    path('user/has-primary-hospital/', has_primary_hospital, name='has-primary-hospital'),
    path('', include(router.urls)),
    path('health-check/', health_check, name='health-check'),
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