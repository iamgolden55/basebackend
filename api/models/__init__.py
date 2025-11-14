# api/models/__init__.py

#=============user folder=====================================
from .user.custom_user import CustomUser
from .user.manager import CustomUserManager

#=============medical folder==================================
from .medical.hospital import Hospital, GPPractice
from .medical.department import Department
from .medical.department_emergency import DepartmentEmergency
from .medical.medical_record import MedicalRecord
from .medical.staff_transfer import StaffTransfer
from .medical.hospital_auth import HospitalAdminManager, HospitalAdmin
from .medical.hospital_registration import HospitalRegistration
from .medical.appointment_document import AppointmentDocument
from .medical.appointment_fee import AppointmentFee
from .medical.appointment_notification import AppointmentNotification
from .medical.appointment_reminder import AppointmentReminder
from .medical.appointment import Appointment
from .medical.payment_transaction import PaymentTransaction

# Women's Health Models
from .medical.womens_health_profile import WomensHealthProfile
from .medical.menstrual_cycle import MenstrualCycle
from .medical.pregnancy_record import PregnancyRecord
from .medical.fertility_tracking import FertilityTracking
from .medical.health_goal import HealthGoal
from .medical.daily_health_log import DailyHealthLog
from .medical.health_screening import HealthScreening
from .medical.medical_history_extended import MedicalHistory

# Pharmacy Models
from .medical.pharmacy import Pharmacy, NominatedPharmacy, PharmacyAccessLog
from .medical.medication import Medication, MedicationCatalog

# Prescription Request Models
from .medical.prescription_request import PrescriptionRequest, PrescriptionRequestItem

#=============registry folder==================================
from .registry.professional_application import ProfessionalApplication
from .registry.application_document import ApplicationDocument, get_required_documents_for_profession
from .registry.professional_registry import PHBProfessionalRegistry

#=============professional folder==================================
from .professional.professional_practice_page import (
    ProfessionalPracticePage,
    PhysicalLocation,
    VirtualServiceOffering,
)

#=============medical_staff folder==================================
from .medical_staff.doctor import Doctor
from .medical_staff.general_practitioner import GeneralPractitioner
from .medical_staff.pharmacist import Pharmacist

#=============drug folder==================================
from .drug.drug_classification import DrugClassification
from .drug.drug_interaction import DrugInteraction

#=============notification folder==================================
from .notifications.in_app_notification import InAppNotification

#=============security folder==================================
from .secure_documents import SecureDocument, DocumentAccessLog, DocumentShare

#=============admin folder==================================
from .admin_signature import AdminSignature

#=============payment folder==================================
from .payment_providers.base import BasePaymentProvider

#=============messaging folder==================================
from .messaging.conversation import Conversation
from .messaging.message import Message
from .messaging.message_participant import MessageParticipant
from .messaging.message_attachment import MessageAttachment
from .messaging.message_audit_log import MessageAuditLog
from .messaging.message_metadata import MessageMetadata
from .messaging.auto_scaling_storage import get_auto_scaling_storage

# Import signals
from . import signals

__all__ = [
    # User models
    'CustomUser',
    'CustomUserManager',
    
    # Medical models
    'Hospital',
    'GPPractice',
    'Department',
    'DepartmentEmergency',
    'MedicalRecord',
    'StaffTransfer',
    'HospitalAdminManager',
    'HospitalAdmin',
    'HospitalRegistration',
    'AppointmentDocument',
    'AppointmentFee',
    'AppointmentNotification',
    'AppointmentReminder',
    'Appointment',
    'PaymentTransaction',
    
    # Women's Health models
    'WomensHealthProfile',
    'MenstrualCycle',
    'PregnancyRecord',
    'FertilityTracking',
    'HealthGoal',
    'DailyHealthLog',
    'HealthScreening',
    'MedicalHistory',

    # Pharmacy models
    'Pharmacy',
    'NominatedPharmacy',
    'PharmacyAccessLog',
    'Medication',
    'MedicationCatalog',

    # Prescription Request models
    'PrescriptionRequest',
    'PrescriptionRequestItem',

    # Registry models
    'ProfessionalApplication',
    'ApplicationDocument',
    'get_required_documents_for_profession',
    'PHBProfessionalRegistry',

    # Professional models
    'ProfessionalPracticePage',
    'PhysicalLocation',
    'VirtualServiceOffering',

    # Medical Staff models
    'Doctor',
    'GeneralPractitioner',
    'Pharmacist',

    # Drug models
    'DrugClassification',
    'DrugInteraction',

    # Notification models
    'InAppNotification',
    
    # Security models
    'SecureDocument',
    'DocumentAccessLog',
    'DocumentShare',

    # Admin models
    'AdminSignature',

    # Payment models
    'BasePaymentProvider',
    
    # Messaging models
    'Conversation',
    'Message',
    'MessageParticipant',
    'MessageAttachment',
    'MessageAuditLog',
    'MessageMetadata',
    'get_auto_scaling_storage',
]