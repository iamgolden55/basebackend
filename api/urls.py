from django.urls import path
from api.views import UserProfileUpdateView, PasswordResetRequestView, PasswordResetConfirmView, UpdateOnboardingStatusView

urlpatterns = [
    path('profile/', UserProfileUpdateView.as_view(), name='profile-update'),
    path('password/reset/', PasswordResetRequestView.as_view(), name='password-reset-request'),
    path('password/reset/confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    path('onboarding/update/', UpdateOnboardingStatusView.as_view(), 
         name='update-onboarding-status'),
]