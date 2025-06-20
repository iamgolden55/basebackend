#!/usr/bin/env python
"""
Test script to verify appointment creation from payment-first approach
"""
import os
import sys
import django
import json
from datetime import datetime, timedelta
from django.utils import timezone

# Setup Django
sys.path.append('/Users/new/Newphb/basebackend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from api.models.medical.payment_transaction import PaymentTransaction
from api.models.medical.appointment import Appointment
from api.models.medical.department import Department
from api.models import CustomUser, Hospital

def test_payment_first_appointment_creation():
    """Test the payment-first appointment creation functionality"""
    print("🧪 Starting Payment-First Appointment Creation Test")
    print("=" * 60)
    
    try:
        # Find a test user
        user = CustomUser.objects.filter(role='patient').first()
        if not user:
            print("❌ No patient users found")
            return False
            
        print(f"✅ Using test user: {user.email} (ID: {user.id})")
        
        # Find a test department and hospital
        department = Department.objects.first()
        hospital = Hospital.objects.first()
        
        if not department or not hospital:
            print("❌ No department or hospital found")
            return False
            
        print(f"✅ Using department: {department.name} (ID: {department.id})")
        print(f"✅ Using hospital: {hospital.name} (ID: {hospital.id})")
        
        # Create booking details for payment-first approach
        booking_details = {
            'department_id': department.id,
            'appointment_date': (timezone.now() + timedelta(days=1)).isoformat(),
            'appointment_type': 'consultation',
            'priority': 'normal',
            'chief_complaint': 'Test payment-first booking',
            'symptoms': 'Test symptoms',
            'medical_history': 'Test history',
            'allergies': '',
            'current_medications': '',
            'hospital_id': hospital.id,
            'duration': 30,
            'is_insurance_based': False,
            'insurance_details': {},
        }
        
        print(f"✅ Created booking details: {booking_details}")
        
        # Create a payment transaction with booking details (payment-first approach)
        payment = PaymentTransaction.objects.create(
            patient=user,
            amount=100.00,
            payment_method='card',
            payment_provider='paystack',
            currency='NGN',
            created_by=user,
            last_modified_by=user,
            hospital=hospital,
            description=json.dumps({
                'type': 'payment_first_booking',
                'booking_details': booking_details
            })
        )
        
        print(f"✅ Created payment: {payment.transaction_id}")
        print(f"   - Amount: {payment.amount}")
        print(f"   - Patient: {payment.patient.email}")
        print(f"   - Hospital: {payment.hospital.name if payment.hospital else 'None'}")
        print(f"   - Appointment: {payment.appointment}")
        print(f"   - Description length: {len(payment.description) if payment.description else 0}")
        
        # Check that no appointment exists yet
        if payment.appointment:
            print("❌ Appointment should not exist before payment completion")
            return False
            
        print("✅ Confirmed no appointment exists before payment completion")
        
        # Simulate payment completion
        print("\n🎯 Simulating payment completion...")
        payment.mark_as_completed(
            gateway_response={'status': 'success', 'reference': payment.transaction_id},
            user=user
        )
        
        # Refresh payment from database
        payment.refresh_from_db()
        
        print(f"✅ Payment status after completion: {payment.payment_status}")
        print(f"✅ Payment completed at: {payment.completed_at}")
        print(f"✅ Linked appointment: {payment.appointment}")
        
        # Check if appointment was created
        if not payment.appointment:
            print("❌ Appointment was not created after payment completion")
            return False
            
        appointment = payment.appointment
        print(f"✅ Appointment created successfully!")
        print(f"   - Appointment ID: {appointment.appointment_id}")
        print(f"   - Patient: {appointment.patient.email}")
        print(f"   - Hospital: {appointment.hospital.name}")
        print(f"   - Department: {appointment.department.name}")
        print(f"   - Date: {appointment.appointment_date}")
        print(f"   - Type: {appointment.appointment_type}")
        print(f"   - Status: {appointment.status}")
        print(f"   - Payment Status: {appointment.payment_status}")
        print(f"   - Chief Complaint: {appointment.chief_complaint}")
        
        # Verify appointment details match booking details
        if appointment.department.id != booking_details['department_id']:
            print(f"❌ Department mismatch: {appointment.department.id} != {booking_details['department_id']}")
            return False
            
        if appointment.appointment_type != booking_details['appointment_type']:
            print(f"❌ Type mismatch: {appointment.appointment_type} != {booking_details['appointment_type']}")
            return False
            
        if appointment.chief_complaint != booking_details['chief_complaint']:
            print(f"❌ Chief complaint mismatch: {appointment.chief_complaint} != {booking_details['chief_complaint']}")
            return False
            
        print("✅ All appointment details match booking details")
        
        # Check notifications were created
        from api.models.medical.appointment_notification import AppointmentNotification
        notifications = AppointmentNotification.objects.filter(appointment=appointment)
        print(f"✅ {notifications.count()} notifications created for appointment")
        
        for notification in notifications:
            print(f"   - {notification.notification_type} to {notification.recipient.email}: {notification.subject}")
        
        print("\n🎉 Payment-First Appointment Creation Test PASSED!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        print(f"❌ Full traceback: {traceback.format_exc()}")
        return False

if __name__ == '__main__':
    success = test_payment_first_appointment_creation()
    if success:
        print("\n✅ ALL TESTS PASSED - Appointment saving issue is FIXED!")
    else:
        print("\n❌ TESTS FAILED - Appointment saving issue persists")
    
    sys.exit(0 if success else 1)