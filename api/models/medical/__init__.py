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
from .payment_transaction import PaymentTransaction





