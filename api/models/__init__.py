# api/models/__init__.py

# First, import the user models
from .user.custom_user import CustomUser
from .user.manager import CustomUserManager

# Then import other models
from .medical.hospital import Hospital, GPPractice
from .medical.department import Department
from .medical.department_emergency import DepartmentEmergency
from .medical.medical_record import MedicalRecord
from .medical.staff_transfer import StaffTransfer
from .medical.hospital_auth import HospitalAdminManager, HospitalAdmin
from .medical.hospital_registration import HospitalRegistration

from .medical_staff.doctor import Doctor
from .medical_staff.general_practitioner import GeneralPractitioner

# Import signals
from . import signals

__all__ = [
    'CustomUser',
    'CustomUserManager',
    'Hospital',
    'GPPractice',
    'Department',
    'DepartmentEmergency',
    'MedicalRecord',
    'StaffTransfer',
    'HospitalAdminManager',
    'HospitalAdmin',
    'Doctor',
    'GeneralPractitioner',
    'HospitalRegistration',
]