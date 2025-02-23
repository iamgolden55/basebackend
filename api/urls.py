from django.urls import path
from api.views import UserProfileUpdateView, PasswordResetRequestView, PasswordResetConfirmView, UpdateOnboardingStatusView
from api.views import (
    HospitalRegistrationViewSet,
    UserHospitalRegistrationsView,
    SetPrimaryHospitalView,
    ApproveHospitalRegistrationView,
    HospitalAdminRegistrationView,
    hospital_list,
    pending_registrations,
    approve_registration,
    hospital_registration
)

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
    path('hospitals/pending/', pending_registrations, name='pending-registrations'),
    path('hospitals/approve/<int:registration_id>/', approve_registration, name='approve-registration'),
    
]