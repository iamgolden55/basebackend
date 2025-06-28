# api/models/medical/__init__.py
from .hospital_auth import HospitalAdminManager, HospitalAdmin
from .hospital import Hospital, GPPractice
from .department import Department
from .medical_record import MedicalRecord
from .staff_transfer import StaffTransfer
from .department_emergency import DepartmentEmergency
from .hospital_registration import HospitalRegistration
from .appointment_document import AppointmentDocument
from .appointment_fee import AppointmentFee
from .appointment_notification import AppointmentNotification
from .appointment_reminder import AppointmentReminder
from .appointment import Appointment
from .appointment_medical_access import AppointmentMedicalAccess, MedicalAccessAuditLog
from .payment_transaction import PaymentTransaction
from .laboratory import LaboratoryTestType, LaboratoryResult
from .vital_signs import VitalSign
from .medical_history import FamilyMedicalHistory, SurgicalHistory, Immunization, GeneticInformation
from .medication import MedicationCatalog, Medication
from .medical_imaging import ImagingType, MedicalImage
from .clinical_notes import ClinicalNote, HealthcareProviderNote, NursingNote
from .lifestyle import LifestyleInformation
from .clinical_guideline import ClinicalGuideline, GuidelineAccess, GuidelineBookmark





