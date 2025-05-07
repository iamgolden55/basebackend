# api/views/hospital/__init__.py
# This file re-exports hospital-related views

from api.views.hospital.hospital_views import (
    # Class-based views
    HospitalRegistrationViewSet,
    UserHospitalRegistrationsView,
    SetPrimaryHospitalView,
    ApproveHospitalRegistrationView,
    HospitalAdminRegistrationView,
    AppointmentViewSet,
    HospitalLocationViewSet,
    
    # Function-based views
    has_primary_hospital,
    approve_registration,
    hospital_registration,
    hospital_list,
    check_user_exists,
    appointment_types,
    departments,
    pending_hospital_registrations,
    doctor_appointments
)
