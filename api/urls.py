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
    appointment_prescriptions,
    get_appointment_notes,
    edit_appointment_notes,
    delete_appointment_notes,
    get_departments_for_doctor,
    get_hospital_departments,
    get_doctor_based_on_department,
    create_department,
    hospital_appointments,
    check_appointment_conflict
)

# Medical views
from api.views.medical.medical_views import DoctorAssignmentView
from api.views.medical.appointment_medical_access_views import (
    DoctorMedicalAccessRequestView,
    PatientMedicalAccessControlView,
    DoctorMedicalRecordAccessView,
    get_appointment_access_status,
    get_patient_active_accesses
)

# Patient Admission views
from api.views.hospital.admission_views import PatientAdmissionViewSet

# Patient search views
from api.views.hospital.patient_views import search_patients

# Doctor views  
from api.views.medical_staff.doctor_views import DoctorListView
from api.views.medical_staff.staff_views import StaffManagementView

# Payment views
from api.views.payment.payment_views import (
    PaymentInitializeView,
    PaymentVerifyView,
    PaymentHistoryView,
    PaymentWebhookView,
    PaymentStatsView,
    PaymentStatusView
)

# Notification views
from api.views.utils.notification_views import InAppNotificationViewSet

# Women's Health views
from api.views.womens_health_views import (
    WomensHealthVerificationView,
    WomensHealthVerifyOTPView,
    WomensHealthProfileView,
    MenstrualCycleView,
    MenstrualCycleDetailView,
    PregnancyRecordView,
    FertilityTrackingView,
    HealthGoalView,
    DailyHealthLogView,
    HealthScreeningView,
    womens_health_dashboard_data
)

# Agent views
from api.views.agent_views import (
    # Analytics Agent endpoints
    analytics_agent_status,
    analyze_cycle_irregularities,
    predict_next_period,
    predict_fertility_window,
    generate_health_insights,
    get_personalized_recommendations,
    assess_health_risks,
    analyze_patterns,
    
    # Performance Agent endpoints
    performance_agent_status,
    optimize_database_queries,
    refresh_cache_layer,
    monitor_system_performance,
    
    # Clinical Agent endpoints
    clinical_agent_status,
    get_health_screening_recommendations,
    schedule_medical_appointment,
    update_medical_history,
    get_medical_history_summary,
    
    # Health check
    health_check as agent_health_check,
)

from rest_framework.decorators import api_view
from rest_framework.response import Response

# Clinical Guidelines views
from api.views.medical.clinical_guidelines_views import (
    ClinicalGuidelineViewSet,
    GuidelineAccessViewSet, 
    GuidelineBookmarkViewSet
)
from api.views.medical.guideline_upload_views import (
    GuidelineFileUploadView,
    GuidelineFileUpdateView
)



router = DefaultRouter()
router.register(r'hospitals', HospitalLocationViewSet, basename='hospital')
router.register(r'appointments', AppointmentViewSet, basename='appointment')
router.register(r'notifications', InAppNotificationViewSet, basename='notification')
router.register(r'admissions', PatientAdmissionViewSet, basename='admission')
router.register(r'clinical-guidelines', ClinicalGuidelineViewSet, basename='clinical-guideline')
router.register(r'guideline-access', GuidelineAccessViewSet, basename='guideline-access')
router.register(r'guideline-bookmarks', GuidelineBookmarkViewSet, basename='guideline-bookmark')

@api_view(['GET'])
def health_check(request):
    return Response({"status": "healthy"})

# Staff management endpoints
staff_patterns = [
    path('staff/', StaffManagementView.as_view(), name='staff-management'),
]


urlpatterns = [
    # ============= HOSPITAL REGISTRATION ENDPOINTS =============
    # IMPORTANT: These endpoints are for users to register with EXISTING hospitals.
    # They do NOT create new hospitals. Hospitals must be pre-created in the system.
    # NOTE: These MUST come before router.urls to avoid conflicts with r'hospitals' pattern
    
    # Get all hospitals that the current user is registered with
    # Returns empty list if user has no registrations
    path('hospitals/registrations/', 
         UserHospitalRegistrationsView.as_view(), 
         name='user-hospital-registrations'),
    
    # Register a user with an existing hospital - requires hospital_id in the request
    # POST data should include hospital ID, not hospital creation data
    path('hospitals/register/', 
         HospitalRegistrationViewSet.as_view({'post': 'create'}), 
         name='hospital-register'),
    
    # Approve hospital registration endpoint -- This is the endpoint for the hospital admins to approve the hospital registrations.
    # Only hospital admins can approve registrations for their own hospital
    path('hospitals/registrations/<int:registration_id>/approve/',
         ApproveHospitalRegistrationView.as_view(),
         name='approve-hospital-registration'),
    
    # Set primary hospital endpoint -- This is the endpoint for the users to set their primary hospital.
    # Users must be registered with the hospital first before setting it as primary
    path('hospitals/<int:hospital_id>/set-primary/', 
         SetPrimaryHospitalView.as_view(), 
         name='set-primary-hospital'),
    
    # Department endpoints
    path('hospitals/departments/', 
         departments,
         name='hospital-departments'),
    # Hospital admin registration endpoint -- This is the endpoint for the users to register as a hospital admin.
    # Can convert existing users to admins using existing_user=True and user_email parameters
    path('hospitals/admin/register/', 
         HospitalAdminRegistrationView.as_view(), 
         name='hospital-admin-register'),
    
    # Hospital admin auth endpoints
    path('hospitals/admin/login/', 
         HospitalAdminLoginView.as_view(), 
         name='hospital-admin-login'),
    path('hospitals/admin/verify-2fa/', 
         VerifyHospitalAdmin2FAView.as_view(), 
         name='hospital-admin-verify-2fa'),
    path('hospitals/admin/change-password/', 
          HospitalAdminPasswordChangeView.as_view(), 
          name='hospital-admin-change-password'),
    path('hospitals/admin/reset-password/request/',
         HospitalAdminResetRequestView.as_view(),
         name='hospital-admin-reset-request'),
    path('hospitals/admin/reset-password/verify/',
         HospitalAdminResetVerifyView.as_view(),
         name='hospital-admin-reset-verify'),
    path('hospitals/admin/reset-password/complete/',
         HospitalAdminResetCompleteView.as_view(),
         name='hospital-admin-reset-complete'),
    path('hospitals/admin/check-user/', 
         check_user_exists,
         name='check-user-exists'),
    
    # Other hospital endpoints
    path('hospitals/', hospital_list, name='hospital-list'),
    path('hospitals/pending/<int:registration_id>/', approve_registration, name='approve-registration'),
    path('hospitals/pending-registrations/', 
         pending_hospital_registrations, 
         name='pending-hospital-registrations'),
    
    # Hospital appointments endpoint for admins
    path('hospitals/appointments/', hospital_appointments, name='hospital-appointments'),

    # Clinical Guidelines upload endpoints
    path('clinical-guidelines/upload/', GuidelineFileUploadView.as_view(), name='guideline-upload'),
    path('clinical-guidelines/<uuid:guideline_id>/update-file/', GuidelineFileUpdateView.as_view(), name='guideline-file-update'),

    # Now include router URLs - hospital router will handle /api/hospitals/<id>/ patterns
    path('', include(router.urls)),
    path('profile/', UserProfileUpdateView.as_view(), name='profile-update'),
    path('password/reset/', PasswordResetRequestView.as_view(), name='password-reset-request'),
    path('password/reset/confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    path('password/change/', ChangePasswordView.as_view(), name='password-change'),
    path('onboarding/update/', UpdateOnboardingStatusView.as_view(), 
         name='update-onboarding-status'),
    
    # Has primary hospital endpoint -- This is the endpoint for the users to check if they have a primary hospital.
    path('user/has-primary-hospital/', has_primary_hospital, name='has-primary-hospital'),
    
    path('health-check/', health_check, name='health-check'),
    
    # New endpoints for appointment booking
    path('appointment-types/', appointment_types, name='appointment-types'),
    path('departments/', departments, name='departments'),
    path('doctor-assignment/', DoctorAssignmentView.as_view(), name='doctor-assignment'),
    
    # New endpoint for patient medical records - secure access
    path('patient/medical-record/', PatientMedicalRecordView.as_view(), name='patient-medical-record'),
    path('patient/medical-record/request-otp/', RequestMedicalRecordOTPView.as_view(), name='request-medical-record-otp'),
    path('patient/medical-record/verify-otp/', VerifyMedicalRecordOTPView.as_view(), name='verify-medical-record-otp'),
    
    # Medical record sharing during appointments
    path('appointments/<str:appointment_id>/request-medical-access/', 
         DoctorMedicalAccessRequestView.as_view(), 
         name='request-medical-access'),
    path('appointments/<str:appointment_id>/access-status/', 
         get_appointment_access_status, 
         name='appointment-access-status'),
    path('appointments/<str:appointment_id>/medical-records/', 
         DoctorMedicalRecordAccessView.as_view(), 
         name='appointment-medical-records'),
    
    # Alternative endpoints that the frontend might be calling
    path('professional/patient/<str:appointment_id>/request-access/', 
         DoctorMedicalAccessRequestView.as_view(), 
         name='professional-request-access'),
    path('professional/patient/<str:appointment_id>/consents/', 
         get_appointment_access_status, 
         name='professional-consents'),
    path('professional/patient/<str:appointment_id>/access-logs/', 
         get_patient_active_accesses, 
         name='professional-access-logs'),
    path('professional/patient/<str:appointment_id>/medical-access/<str:appointment_id2>/', 
         DoctorMedicalRecordAccessView.as_view(), 
         name='professional-medical-access'),
    path('patient/medical-access-requests/', 
         PatientMedicalAccessControlView.as_view(), 
         name='patient-medical-access-requests'),
    path('patient/medical-access-requests/<int:access_request_id>/', 
         PatientMedicalAccessControlView.as_view(), 
         name='patient-medical-access-control'),
    path('patient/active-medical-accesses/', 
         get_patient_active_accesses, 
         name='patient-active-medical-accesses'),
    
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
    
    # Patient search endpoint
    path('patients/search/', search_patients, name='patient-search'),
    
    # Doctors endpoint
    path('doctors/', DoctorListView.as_view(), name='doctor-list'),
    
    # Appointment notes endpoint
    path('appointments/<str:appointment_id>/notes/', get_appointment_notes, name='get-appointment-notes'),
    path('appointments/<str:appointment_id>/notes/edit/', edit_appointment_notes, name='edit-appointment-notes'),
    path('appointments/<str:appointment_id>/notes/delete/', delete_appointment_notes, name='delete-appointment-notes'),

    # Appointment refer endpoint
    path('api/appointments/<int:pk>/refer/', 
         AppointmentViewSet.as_view({'post': 'refer'}), 
         name='appointment-refer'),
    
    # Department endpoints
    path('departments/<str:hospital_id>/', get_departments_for_doctor, name='get-departments-for-doctor'),

    # Hospital departments endpoint
    path('hospitals/departments/<str:hospital_id>', get_hospital_departments, name='hospital-departments'),

    # Get doctors based on department
    path('doctors/department/<str:department_id>', get_doctor_based_on_department, name='doctor-based-on-department'),
    
    # 🛡️ MEDICAL VAULT 3.0 - Secure file upload endpoints
    path('secure/', include('api.views.security.urls')),

    # Hospital appointments endpoint for admins
    path('hospitals/appointments/', hospital_appointments, name='hospital-appointments'),

    # Staff management endpoints
    path('', include(staff_patterns)),

    # Create department endpoint
    path('hospitals/departments/create/', create_department, name='create-department'),
    
    # 💰 PAYMENT ENDPOINTS - PHB Payment Integration
    path('payments/initialize/', PaymentInitializeView.as_view(), name='payment-initialize'),
    path('payments/verify/<str:reference>/', PaymentVerifyView.as_view(), name='payment-verify'),
    path('payments/history/', PaymentHistoryView.as_view(), name='payment-history'),
    path('payments/webhook/', PaymentWebhookView.as_view(), name='payment-webhook'),
    path('payments/stats/', PaymentStatsView.as_view(), name='payment-stats'),
    path('payments/status/', PaymentStatusView.as_view(), name='payment-status'),
    
    # 🛡️ APPOINTMENT CONFLICT CHECK - Pre-validation endpoint
    path('appointments/check-conflict/', check_appointment_conflict, name='check-appointment-conflict'),
    
    # 🩺 WOMEN'S HEALTH ENDPOINTS - Comprehensive women's health management
    # Verification endpoints
    path('womens-health/verification/', WomensHealthVerificationView.as_view(), name='womens-health-verification'),
    path('womens-health/verification/verify/', WomensHealthVerifyOTPView.as_view(), name='womens-health-verify-otp'),
    
    # Dashboard
    path('womens-health/dashboard/', womens_health_dashboard_data, name='womens-health-dashboard'),
    
    # Profile management
    path('womens-health/profile/', WomensHealthProfileView.as_view(), name='womens-health-profile'),
    
    # Menstrual cycle tracking
    path('womens-health/cycles/', MenstrualCycleView.as_view(), name='womens-health-cycles'),
    path('womens-health/cycles/<int:cycle_id>/', MenstrualCycleDetailView.as_view(), name='womens-health-cycle-detail'),
    
    # Pregnancy records
    path('womens-health/pregnancy/', PregnancyRecordView.as_view(), name='womens-health-pregnancy'),
    
    # Fertility tracking
    path('womens-health/fertility/', FertilityTrackingView.as_view(), name='womens-health-fertility'),
    
    # Health goals
    path('womens-health/goals/', HealthGoalView.as_view(), name='womens-health-goals'),
    
    # Daily health logs
    path('womens-health/logs/', DailyHealthLogView.as_view(), name='womens-health-logs'),
    
    # Health screenings
    path('womens-health/screenings/', HealthScreeningView.as_view(), name='womens-health-screenings'),
    
    # 🤖 WOMEN'S HEALTH AGENTS - AI-powered health management system
    # Health check endpoint
    path('agents/health/', agent_health_check, name='agent_health_check'),
    
    # Analytics Agent URLs
    path('agents/analytics/status/', analytics_agent_status, name='analytics_status'),
    path('agents/analytics/cycle-irregularities/', analyze_cycle_irregularities, name='cycle_irregularities'),
    path('agents/analytics/predict-period/', predict_next_period, name='predict_period'),
    path('agents/analytics/predict-fertility/', predict_fertility_window, name='predict_fertility'),
    path('agents/analytics/health-insights/', generate_health_insights, name='health_insights'),
    path('agents/analytics/recommendations/', get_personalized_recommendations, name='recommendations'),
    path('agents/analytics/health-risks/', assess_health_risks, name='health_risks'),
    path('agents/analytics/analyze-patterns/', analyze_patterns, name='analyze_patterns'),
    
    # Performance Agent URLs (Admin only)
    path('agents/performance/status/', performance_agent_status, name='performance_status'),
    path('agents/performance/optimize-database/', optimize_database_queries, name='optimize_database'),
    path('agents/performance/refresh-cache/', refresh_cache_layer, name='refresh_cache'),
    path('agents/performance/monitor-performance/', monitor_system_performance, name='monitor_performance'),
    
    # Clinical Agent URLs
    path('agents/clinical/status/', clinical_agent_status, name='clinical_status'),
    path('agents/clinical/screening-recommendations/', get_health_screening_recommendations, name='screening_recommendations'),
    path('agents/clinical/schedule-appointment/', schedule_medical_appointment, name='schedule_appointment'),
    path('agents/clinical/update-medical-history/', update_medical_history, name='update_medical_history'),
    path('agents/clinical/medical-history-summary/', get_medical_history_summary, name='medical_history_summary'),
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
#  POST /api/appointments/<id>/refer/ - Refer an appointment to another hospital
# POST /api/appointments/<id>/complete/ - Mark an appointment as completed
# GET /api/appointments/upcoming/ - Get upcoming appointments
# GET /api/appointments/today/ - Get today's appointments

# Prescription endpoints:
# POST /api/appointments/<id>/prescriptions/ - Create prescriptions for a specific appointment
# POST /api/prescriptions/ - Create prescriptions with appointment_id in the request body
# GET /api/appointments/<id>/prescriptions/view/ - View prescriptions for a specific appointment
# GET /api/prescriptions/view/ - View all prescriptions for the current user