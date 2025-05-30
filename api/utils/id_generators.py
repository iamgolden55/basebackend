# api/utils/id_generators.py

import random
import string
import uuid
from datetime import datetime

def generate_admission_id():
    """Generate a unique admission ID in format ADM-YYMMDD-XXXX"""
    timestamp = datetime.now().strftime("%y%m%d")
    random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"ADM-{timestamp}-{random_suffix}"

def generate_hpn_number(user, hospital):
    """Generate a unique Hospital Patient Number (HPN) in format HPN-HOSPITAL_CODE-YY-XXXXXX"""
    year = datetime.now().strftime('%y')
    hospital_code = hospital.code if hasattr(hospital, 'code') else 'GEN'
    unique_id = str(uuid.uuid4())[:6].upper()
    
    return f"HPN-{hospital_code}-{year}-{unique_id}"

def generate_temp_patient_id():
    """Generate a temporary patient ID for emergency admissions in format TEMP-YYMMDD-XXXX"""
    date_str = datetime.now().strftime('%y%m%d')
    random_part = str(uuid.uuid4())[:4].upper()
    return f"TEMP-{date_str}-{random_part}"
