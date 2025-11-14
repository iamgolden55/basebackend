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
    LogoutView,
    VerifyEmailToken,
)
from api.views.user_profile_view import UserProfileView
from api.views.auth.token_refresh import CookieTokenRefreshView

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
    hospital_analytics,
    hospital_occupancy_data,
    hospital_licenses_data,
    add_hospital_license,
    update_hospital_license,
    delete_hospital_license,
    approve_hospital,
    reject_hospital,
    get_my_hospital_licenses,
    upload_my_hospital_license,
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
    check_appointment_conflict,
    create_hospital
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

# Pharmacy views
from api.views.pharmacy_views import (
    PharmacyListView,
    PharmacyDetailView,
    NominatedPharmacyView,
    NominationHistoryView,
    NearbyPharmaciesView,
    create_pharmacy,
    get_hospital_pharmacies,
    update_pharmacy,
    delete_pharmacy
)

# Pharmacy prescription views
from api.views.pharmacy_prescription_views import (
    get_prescriptions_by_hpn
)

# Prescription verification views
from api.views.prescription_verification_views import (
    verify_prescription_qr,
    dispense_prescription,
    regenerate_prescription_signature,
    get_prescription_verification_log
)

# Prescription request views
from api.views.prescription_requests_views import (
    create_prescription_request,
    get_prescription_requests,
    get_doctor_prescription_requests,
    get_prescription_request_details,
    approve_prescription_request,
    reject_prescription_request
)

# Pharmacist triage views
from api.views.pharmacist_triage_views import (
    get_assigned_prescription_requests,
    get_prescription_request_detail,
    approve_prescription_request as pharmacist_approve_prescription,
    escalate_prescription_request,
    reject_prescription_request as pharmacist_reject_prescription,
    get_pharmacist_triage_statistics
)

# Stream Chat views
from api.views.stream_chat import (
    generate_stream_token,
    get_hospital_users,
    create_department_channel
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

# Drug Database views
from api.views.drug_views import (
    search_drugs,
    get_drug_detail,
    get_drug_statistics
)

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

# Messaging views
from api.views import messaging

# Practice page views
from api.views import practice_page_views



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
    path('hospitals/create/', create_hospital, name='hospital-create'),
    path('hospitals/analytics/', hospital_analytics, name='hospital-analytics'),
    path('hospitals/occupancy/', hospital_occupancy_data, name='hospital-occupancy'),
    path('hospitals/licenses/', hospital_licenses_data, name='hospital-licenses'),
    path('hospitals/<int:hospital_id>/licenses/add/', add_hospital_license, name='add-hospital-license'),
    path('hospitals/<int:hospital_id>/licenses/<int:license_id>/update/', update_hospital_license, name='update-hospital-license'),
    path('hospitals/<int:hospital_id>/licenses/<int:license_id>/delete/', delete_hospital_license, name='delete-hospital-license'),
    path('hospitals/<int:hospital_id>/approve/', approve_hospital, name='approve-hospital'),
    path('hospitals/<int:hospital_id>/reject/', reject_hospital, name='reject-hospital'),
    # Hospital admin license management (for hospital admins to manage their own licenses)
    path('my-hospital/licenses/', get_my_hospital_licenses, name='my-hospital-licenses'),
    path('my-hospital/licenses/upload/', upload_my_hospital_license, name='upload-my-hospital-license'),
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

    # Authentication endpoints
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', CookieTokenRefreshView.as_view(), name='token-refresh-cookie'),

    # Profile and password management
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('password/reset/', PasswordResetRequestView.as_view(), name='password-reset-request'),
    path('password/reset/confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    path('password/change/', ChangePasswordView.as_view(), name='password-change'),

    # Email verification
    path('email/verify/<uuid:email_verification_token>/', VerifyEmailToken.as_view(), name='verify-email'),

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

    # Prescription request endpoints (patient prescription requests) - MUST come before generic prescription patterns
    path('prescriptions/requests/', create_prescription_request, name='create-prescription-request'),
    path('prescriptions/requests/history/', get_prescription_requests, name='get-prescription-requests'),

    # Prescription verification endpoints (for pharmacy security) - MUST come before generic prescription patterns
    path('prescriptions/verify/', verify_prescription_qr, name='verify-prescription-qr'),
    path('prescriptions/dispense/', dispense_prescription, name='dispense-prescription'),
    path('prescriptions/<int:prescription_id>/regenerate-signature/', regenerate_prescription_signature, name='regenerate-prescription-signature'),
    path('prescriptions/<int:prescription_id>/verification-log/', get_prescription_verification_log, name='prescription-verification-log'),

    # Pharmacist triage endpoints (clinical pharmacist prescription review) - MUST come BEFORE generic doctor prescription patterns
    path('provider/prescriptions/triage/', get_assigned_prescription_requests, name='pharmacist-assigned-requests'),
    path('provider/prescriptions/triage/stats/', get_pharmacist_triage_statistics, name='pharmacist-triage-stats'),
    path('provider/prescriptions/triage/<str:request_id>/', get_prescription_request_detail, name='pharmacist-prescription-detail'),
    path('provider/prescriptions/triage/<str:request_id>/approve/', pharmacist_approve_prescription, name='pharmacist-approve-prescription'),
    path('provider/prescriptions/triage/<str:request_id>/escalate/', escalate_prescription_request, name='pharmacist-escalate-prescription'),
    path('provider/prescriptions/triage/<str:request_id>/reject/', pharmacist_reject_prescription, name='pharmacist-reject-prescription'),

    # Professional prescription endpoints (doctor prescription management) - Generic patterns come AFTER specific pharmacist patterns
    path('provider/prescriptions/', get_doctor_prescription_requests, name='get-doctor-prescription-requests'),
    path('provider/prescriptions/<str:request_id>/', get_prescription_request_details, name='get-prescription-request-details'),
    path('provider/prescriptions/<str:request_id>/approve/', approve_prescription_request, name='approve-prescription-request'),
    path('provider/prescriptions/<str:request_id>/reject/', reject_prescription_request, name='reject-prescription-request'),

    # Generic prescription endpoints - MUST come last to avoid capturing specific paths
    path('prescriptions/', patient_prescriptions, name='patient-prescriptions'),
    path('prescriptions/<str:appointment_id>/', patient_prescriptions, name='patient-prescriptions-by-appointment'),

    # Pharmacy endpoints
    path('pharmacies/', PharmacyListView.as_view(), name='pharmacy-list'),
    path('pharmacies/nearby/', NearbyPharmaciesView.as_view(), name='nearby-pharmacies'),
    path('pharmacies/nominated/', NominatedPharmacyView.as_view(), name='nominated-pharmacy'),
    path('pharmacies/nomination-history/', NominationHistoryView.as_view(), name='nomination-history'),
    path('pharmacies/<int:pk>/', PharmacyDetailView.as_view(), name='pharmacy-detail'),

    # Pharmacy prescription access endpoints (authenticated pharmacists only)
    path('pharmacy/prescriptions/search/', get_prescriptions_by_hpn, name='pharmacy-prescriptions-by-hpn'),

    # Admin pharmacy management endpoints
    path('pharmacies/create/', create_pharmacy, name='create-pharmacy'),
    path('pharmacies/<int:pharmacy_id>/update/', update_pharmacy, name='update-pharmacy'),
    path('pharmacies/<int:pharmacy_id>/delete/', delete_pharmacy, name='delete-pharmacy'),
    path('hospitals/<int:hospital_id>/pharmacies/', get_hospital_pharmacies, name='hospital-pharmacies'),

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
    
    # 👑 PLATFORM ADMIN ENDPOINTS - Platform owner dashboard and management
    path('admin/', include('api.views.admin.urls')),

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
    
    # 💬 MESSAGING ENDPOINTS - WhatsApp-style secure healthcare messaging  
    path('messaging/', include([
        # Conversation management
        path('conversations/', messaging.get_conversations, name='get_conversations'),
        path('conversations/create/', messaging.create_conversation, name='create_conversation'),
        path('conversations/emergency/', messaging.create_emergency_conversation, name='create_emergency_conversation'),
        path('conversations/<str:conversation_id>/participants/', messaging.get_conversation_participants, name='get_conversation_participants'),
        
        # Message management
        path('conversations/<str:conversation_id>/messages/', messaging.get_messages, name='get_messages'),
        path('conversations/<str:conversation_id>/send/', messaging.send_message, name='send_message'),
        
        # System information
        path('storage/info/', messaging.get_storage_info, name='get_storage_info'),
    ])),
    
    # ============= STREAM CHAT ENDPOINTS =============
    # Stream Chat token generation and user management
    path('stream-chat/', include([
        path('token/', generate_stream_token, name='stream_chat_token'),
        path('users/', get_hospital_users, name='stream_chat_users'),
        path('channels/create/', create_department_channel, name='stream_chat_create_channel'),
    ])),

    # ============= PROFESSIONAL REGISTRY ENDPOINTS =============
    # PHB National Professional Registry (separate microservice namespace)
    # Nigerian healthcare professional licensing and credentialing
    # Can be extracted to separate Django app/service in future
    path('registry/', include('api.registry_urls')),

    # ============= DRUG DATABASE ENDPOINTS =============
    # Drug classification and search (505+ medications)
    path('drugs/', include([
        path('search/', search_drugs, name='search_drugs'),
        path('statistics/', get_drug_statistics, name='drug_statistics'),
        path('<uuid:drug_id>/', get_drug_detail, name='drug_detail'),
    ])),

    # ============= PROFESSIONAL PRACTICE PAGE ENDPOINTS =============
    # Professional practice pages for approved healthcare professionals
    path('practice-pages/', include([
        # Public endpoints
        path('', practice_page_views.public_practice_pages, name='public_practice_pages'),
        
        # Professional endpoints (requires authentication) - MUST come before <slug:slug>/
        path('check-eligibility/', practice_page_views.check_eligibility, name='check_eligibility'),
        path('create/', practice_page_views.create_practice_page, name='create_practice_page'),
        path('my-page/', practice_page_views.my_practice_page, name='my_practice_page'),
        path('my-page/preview/', practice_page_views.preview_my_practice_page, name='preview_my_practice_page'),
        path('my-page/update/', practice_page_views.update_practice_page, name='update_practice_page'),
        path('my-page/publish/', practice_page_views.toggle_publish, name='toggle_publish'),
        path('my-page/analytics/', practice_page_views.page_analytics, name='page_analytics'),

        # Patient endpoints (requires authentication)
        path('nominatable-pharmacies/', practice_page_views.nominatable_pharmacies, name='nominatable_pharmacies'),

        # Admin endpoints (requires admin authentication)
        path('admin/pages/', practice_page_views.admin_list_pages, name='admin_list_pages'),
        path('admin/pages/<uuid:page_id>/', practice_page_views.admin_page_detail, name='admin_page_detail'),
        path('admin/pages/<uuid:page_id>/verify/', practice_page_views.admin_verify_page, name='admin_verify_page'),
        
        # Public detail view - MUST come last to avoid catching specific paths
        path('<slug:slug>/', practice_page_views.public_practice_page_detail, name='public_practice_page_detail'),
    ])),
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