from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView, TokenObtainPairView
from api.views import (
    UserRegistrationView, 
    EmailVerificationView, 
    VerifyEmailToken,
    VerifyLoginOTPView,
    LoginView,
    CustomTokenObtainPairView
)
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("api.urls")), # I Included the API URLs
    path('api/registration/', UserRegistrationView.as_view(), name='user-registration'),
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/email/send-verification/', EmailVerificationView.as_view(), name='send-verification'),
    path('api/email/verify/<uuid:email_verification_token>/', VerifyEmailToken.as_view(), name='verify-email'),
    path('api/verify-login-otp/', VerifyLoginOTPView.as_view(), name='verify-otp'),  # Keep only one
    path('api/login/', LoginView.as_view(), name='login'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)