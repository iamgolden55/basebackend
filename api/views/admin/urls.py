from django.urls import path
from .platform_admin_views import (
    PlatformStatsView,
    PlatformUsersView,
    PlatformHospitalsView,
    HospitalLicenseAdminView,
    HospitalStaffAdminView,
    PlatformPaymentsView,
    platform_analytics,
    export_appointment_analytics_csv,
    SystemPerformanceStatsView
)
from .hospital_contacts_view import HospitalAdminContactsView

urlpatterns = [
    # Platform admin dashboard endpoints
    path('platform/stats/', PlatformStatsView.as_view(), name='platform-stats'),
    path('platform/users/', PlatformUsersView.as_view(), name='platform-users'),
    path('platform/hospitals/', PlatformHospitalsView.as_view(), name='platform-hospitals'),
    path('platform/hospital-licenses/', HospitalLicenseAdminView.as_view(), name='hospital-license-admin'),
    path('platform/hospital-staff/', HospitalStaffAdminView.as_view(), name='hospital-staff-admin'),
    path('platform/payments/', PlatformPaymentsView.as_view(), name='platform-payments'),
    path('platform/contacts/', HospitalAdminContactsView.as_view(), name='hospital-admin-contacts'),
    path('platform/analytics/', platform_analytics, name='platform-analytics'),
    path('platform/export/appointments-csv/', export_appointment_analytics_csv, name='export-appointment-analytics-csv'),
    path('platform/system-performance/', SystemPerformanceStatsView.as_view(), name='system-performance-stats'),
]