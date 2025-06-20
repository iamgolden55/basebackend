#!/usr/bin/env python
"""
Debug script to test appointment creation bypassing validation
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

def test_bypass_validation():
    """Test appointment creation bypassing validation"""
    print("🧪 Testing appointment creation bypassing validation")
    print("=" * 50)
    
    try:
        # Get test data
        user = CustomUser.objects.first()
        department = Department.objects.first()
        hospital = Hospital.objects.first()
        
        print(f"Using user: {user.email}")
        print(f"Using department: {department.name}")
        print(f"Using hospital: {hospital.name}")
        
        # Test: Create appointment bypassing validation
        print("\n🧪 Creating appointment bypassing validation")
        try:
            appointment = Appointment(
                appointment_id=Appointment.generate_appointment_id(),
                patient=user,
                hospital=hospital,
                department=department,
                appointment_date=timezone.now() + timedelta(days=1),
                appointment_type='consultation',
                priority='normal',
                chief_complaint='Test payment-first booking',
                symptoms='Test symptoms',
                symptoms_data=[],  # Empty list
                medical_history='Test history',
                allergies='',
                current_medications='',
                duration=30,
                is_insurance_based=False,
                insurance_details={},
                status='pending',
                payment_status='completed'
            )
            
            # Save without calling full_clean() to bypass validation
            appointment.save(bypass_validation=True)
            
            print(f"✅ BYPASSED VALIDATION: Created appointment {appointment.appointment_id}")
            print(f"   symptoms_data value: {appointment.symptoms_data}")
            print(f"   symptoms_data type: {type(appointment.symptoms_data)}")
            
            # Try to read it back
            saved_appointment = Appointment.objects.get(pk=appointment.pk)
            print(f"✅ Successfully read back appointment {saved_appointment.appointment_id}")
            print(f"   symptoms_data from DB: {saved_appointment.symptoms_data}")
            
        except Exception as e:
            print(f"❌ BYPASS FAILED: {e}")
            import traceback
            print(f"❌ Full traceback: {traceback.format_exc()}")
        
        print("\n" + "=" * 50)
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        import traceback
        print(f"❌ Full traceback: {traceback.format_exc()}")

if __name__ == '__main__':
    test_bypass_validation()