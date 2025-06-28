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

#=============medical_staff folder==================================
from .medical_staff.doctor import Doctor
from .medical_staff.general_practitioner import GeneralPractitioner

#=============notification folder==================================
from .notifications.in_app_notification import InAppNotification

#=============security folder==================================
from .secure_documents import SecureDocument, DocumentAccessLog, DocumentShare

#=============payment folder==================================
from .payment_providers.base import BasePaymentProvider

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
    
    # Medical Staff models
    'Doctor',
    'GeneralPractitioner',
    
    # Notification models
    'InAppNotification',
    
    # Security models
    'SecureDocument',
    'DocumentAccessLog', 
    'DocumentShare',
    
    # Payment models
    'BasePaymentProvider',
]