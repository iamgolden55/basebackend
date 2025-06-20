#!/usr/bin/env python
"""
Debug script to test appointment creation with symptoms_data field
"""
import os
import sys
import django
from datetime import datetime, timedelta
from django.utils import timezone

# Setup Django
sys.path.append('/Users/new/Newphb/basebackend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from api.models.medical.appointment import Appointment
from api.models.medical.department import Department
from api.models import CustomUser, Hospital

def test_symptoms_data_field():
    """Test the symptoms_data field behavior"""
    print("🧪 Testing symptoms_data field behavior")
    print("=" * 50)
    
    try:
        # Get test data
        user = CustomUser.objects.first()
        department = Department.objects.first()
        hospital = Hospital.objects.first()
        
        print(f"Using user: {user.email}")
        print(f"Using department: {department.name}")
        print(f"Using hospital: {hospital.name}")
        
        # Test 1: Create appointment with symptoms_data=[]
        print("\n🧪 Test 1: Creating appointment with symptoms_data=[]")
        try:
            appointment1 = Appointment(
                appointment_id=Appointment.generate_appointment_id(),
                patient=user,
                hospital=hospital,
                department=department,
                appointment_date=timezone.now() + timedelta(days=1),
                symptoms_data=[]
            )
            appointment1.full_clean()  # This should trigger validation
            print("✅ Test 1 PASSED: symptoms_data=[] is valid")
        except Exception as e:
            print(f"❌ Test 1 FAILED: {e}")
        
        # Test 2: Create appointment without symptoms_data (let default apply)
        print("\n🧪 Test 2: Creating appointment without symptoms_data (default)")
        try:
            appointment2 = Appointment(
                appointment_id=Appointment.generate_appointment_id(),
                patient=user,
                hospital=hospital,
                department=department,
                appointment_date=timezone.now() + timedelta(days=1)
                # No symptoms_data specified - should use default
            )
            appointment2.full_clean()  # This should trigger validation
            print("✅ Test 2 PASSED: Default symptoms_data is valid")
        except Exception as e:
            print(f"❌ Test 2 FAILED: {e}")
        
        # Test 3: Create appointment with symptoms_data=None
        print("\n🧪 Test 3: Creating appointment with symptoms_data=None")
        try:
            appointment3 = Appointment(
                appointment_id=Appointment.generate_appointment_id(),
                patient=user,
                hospital=hospital,
                department=department,
                appointment_date=timezone.now() + timedelta(days=1),
                symptoms_data=None
            )
            appointment3.full_clean()  # This should trigger validation
            print("✅ Test 3 PASSED: symptoms_data=None is valid")
        except Exception as e:
            print(f"❌ Test 3 FAILED: {e}")
        
        # Test 4: Create appointment using the same pattern as payment-first
        print("\n🧪 Test 4: Creating appointment using payment-first pattern")
        try:
            appointment4 = Appointment.objects.create(
                appointment_id=Appointment.generate_appointment_id(),
                patient=user,
                hospital=hospital,
                department=department,
                appointment_date=timezone.now() + timedelta(days=1),
                appointment_type='consultation',
                priority='normal',
                chief_complaint='Test payment-first booking',
                symptoms='Test symptoms',
                medical_history='Test history',
                allergies='',
                current_medications='',
                duration=30,
                is_insurance_based=False,
                insurance_details={},
                status='pending',
                payment_status='completed'
            )
            print(f"✅ Test 4 PASSED: Created appointment {appointment4.appointment_id}")
            print(f"   symptoms_data value: {appointment4.symptoms_data}")
            print(f"   symptoms_data type: {type(appointment4.symptoms_data)}")
        except Exception as e:
            print(f"❌ Test 4 FAILED: {e}")
            import traceback
            print(f"❌ Full traceback: {traceback.format_exc()}")
        
        print("\n" + "=" * 50)
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        import traceback
        print(f"❌ Full traceback: {traceback.format_exc()}")

if __name__ == '__main__':
    test_symptoms_data_field()