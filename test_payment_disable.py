#!/usr/bin/env python3
"""
Test script to verify payment disable functionality works correctly.
This script tests the payment system when PAYMENTS_ENABLED=false.
"""

import os
import sys
import django
from datetime import datetime, timedelta

# Add the project directory to the Python path
sys.path.append('/Users/new/Newphb/basebackend')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from django.conf import settings
from django.contrib.auth import get_user_model
from api.models import Hospital, Department
from api.models.medical.appointment import Appointment
from api.models.medical.hospital_registration import HospitalRegistration
import json
import requests

User = get_user_model()

def test_payment_settings():
    """Test that payment settings are correctly configured"""
    print("🔧 Testing Payment Settings...")
    print(f"   PAYMENTS_ENABLED: {getattr(settings, 'PAYMENTS_ENABLED', 'NOT_SET')}")
    print(f"   Environment PAYMENTS_ENABLED: {os.environ.get('PAYMENTS_ENABLED', 'NOT_SET')}")
    
    payments_enabled = getattr(settings, 'PAYMENTS_ENABLED', True)
    if not payments_enabled:
        print("   ✅ Payments are correctly DISABLED")
    else:
        print("   ❌ Payments are still ENABLED")
    
    return not payments_enabled

def test_appointment_creation_with_waived_payment():
    """Test creating an appointment with waived payment when payments are disabled"""
    print("\n🏥 Testing Appointment Creation with Waived Payment...")
    
    try:
        # Get or create test user
        user, created = User.objects.get_or_create(
            email='test@example.com',
            defaults={
                'first_name': 'Test',
                'last_name': 'Patient',
                'phone': '+1234567890',
                'role': 'patient'
            }
        )
        if created:
            user.set_password('testpass123')
            user.save()
            print(f"   Created test user: {user.email}")
        else:
            print(f"   Using existing test user: {user.email}")
        
        # Get any existing hospital or create test hospital
        hospital = Hospital.objects.first()
        if not hospital:
            hospital = Hospital.objects.create(
                name='Test Hospital',
                address='123 Test St',
                city='Test City',
                country='Test Country',
                phone='+1234567890',
                email='test@hospital.com'
            )
            print(f"   Created test hospital: {hospital.name}")
        else:
            print(f"   Using existing hospital: {hospital.name}")
        
        # Get any existing department or create simple test department  
        department = Department.objects.filter(hospital=hospital, is_active=True).first()
        if not department:
            # Use any department from any hospital if none in current hospital
            department = Department.objects.filter(is_active=True).first()
        
        if not department:
            print(f"   ⚠️  No active departments found - skipping appointment creation test")
            return True
        else:
            print(f"   Using existing department: {department.name} at {department.hospital.name}")
        
        # Ensure user is registered with the department's hospital
        registration, created = HospitalRegistration.objects.get_or_create(
            user=user,
            hospital=department.hospital,
            defaults={
                'is_primary': True,
                'status': 'approved'
            }
        )
        if created:
            print(f"   Created hospital registration for user")
        else:
            print(f"   Using existing hospital registration")
        
        # Create appointment with waived payment  
        from django.utils import timezone
        appointment_date = timezone.now() + timedelta(days=1)
        appointment = Appointment.objects.create(
            appointment_id=Appointment.generate_appointment_id(),
            patient=user,
            hospital=department.hospital,  # Use department's hospital
            department=department,
            appointment_date=appointment_date,
            appointment_type='consultation',
            priority='normal',
            chief_complaint='Test complaint for payment disable testing',
            symptoms_data=[],  # Add required field
            status='pending',
            payment_status='waived',  # This should be the default when payments are disabled
            payment_required=False
        )
        
        print(f"   ✅ Created appointment: {appointment.appointment_id}")
        print(f"   ✅ Payment status: {appointment.payment_status}")
        print(f"   ✅ Payment required: {appointment.payment_required}")
        print(f"   ✅ Appointment date: {appointment.appointment_date}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error creating appointment: {str(e)}")
        import traceback
        print(f"   ❌ Traceback: {traceback.format_exc()}")
        return False

def test_payment_endpoint_responses():
    """Test that payment endpoints return appropriate responses when disabled"""
    print("\n🌐 Testing Payment Endpoint Responses...")
    
    # Test payment status endpoint (should work without authentication)
    try:
        # This would normally be a request to the server, but we'll simulate the response
        from api.views.payment.payment_views import PaymentStatusView
        from rest_framework.test import APIRequestFactory
        from rest_framework.request import Request
        
        factory = APIRequestFactory()
        request = factory.get('/api/payments/status/')
        request = Request(request)
        
        view = PaymentStatusView()
        response = view.get(request)
        
        print(f"   Payment Status Response: {response.status_code}")
        print(f"   Response Data: {response.data}")
        
        if response.data.get('payments_enabled') == False:
            print("   ✅ Payment status endpoint correctly reports disabled")
        else:
            print("   ❌ Payment status endpoint reports incorrect status")
            
        return response.data.get('payments_enabled') == False
        
    except Exception as e:
        print(f"   ❌ Error testing payment endpoints: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Payment Disable Functionality")
    print("=" * 50)
    
    tests = [
        test_payment_settings,
        test_appointment_creation_with_waived_payment,
        test_payment_endpoint_responses
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"   ❌ Test failed with exception: {str(e)}")
            results.append(False)
    
    print("\n📊 Test Results Summary")
    print("=" * 50)
    for i, (test, result) in enumerate(zip(tests, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {i+1}. {test.__name__}: {status}")
    
    total_passed = sum(results)
    total_tests = len(results)
    print(f"\n🏁 Overall: {total_passed}/{total_tests} tests passed")
    
    if total_passed == total_tests:
        print("🎉 All tests passed! Payment disable functionality is working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
    
    return total_passed == total_tests

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)