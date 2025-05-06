from django.test import TestCase, Client
from django.urls import reverse
from api.models import CustomUser, MedicalRecord
from api.views import PatientMedicalRecordView
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
import json

class MedicalRecordAPITest(TestCase):
    def setUp(self):
        """Set up test data"""
        # Create a test user
        self.user = CustomUser.objects.create_user(
            email='testpatient@example.com',
            password='testpassword123',
            first_name='Test',
            last_name='Patient'
        )
        self.user.is_email_verified = True
        self.user.save()
        
        # Create a medical record for the user
        self.medical_record = MedicalRecord.objects.create(
            user=self.user,
            hpn='TEST12345',
            blood_type='O+',
            allergies='Peanuts, Penicillin',
            chronic_conditions='Hypertension',
            emergency_contact_name='Emergency Contact',
            emergency_contact_phone='+1234567890'
        )
        
        # Create a client
        self.client = APIClient()
        
        # Get token
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        
    def test_medical_record_access_authenticated(self):
        """Test accessing medical record with authentication"""
        # Set up auth
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        
        # Make request
        url = reverse('patient-medical-record')
        response = self.client.get(url)
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        
        # Verify response data
        data = response.json()
        self.assertEqual(data['hpn'], self.medical_record.hpn)
        self.assertEqual(data['blood_type'], self.medical_record.blood_type)
        self.assertEqual(data['allergies'], self.medical_record.allergies)
        self.assertEqual(data['chronic_conditions'], self.medical_record.chronic_conditions)
        self.assertEqual(data['emergency_contact_name'], self.medical_record.emergency_contact_name)
        
        print("✅ Authenticated medical record access test passed")
        
    def test_medical_record_access_unauthenticated(self):
        """Test accessing medical record without authentication"""
        # No credentials
        url = reverse('patient-medical-record')
        response = self.client.get(url)
        
        # Should require authentication
        self.assertEqual(response.status_code, 401)
        print("✅ Unauthenticated medical record access test passed")
        
    def test_medical_record_other_user(self):
        """Test that a user cannot access another user's medical record"""
        # Create another user
        other_user = CustomUser.objects.create_user(
            email='otheruser@example.com',
            password='testpassword123'
        )
        
        # Get token for other user
        refresh = RefreshToken.for_user(other_user)
        other_token = str(refresh.access_token)
        
        # Set credentials for other user
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {other_token}')
        
        # Make request
        url = reverse('patient-medical-record')
        response = self.client.get(url)
        
        # Should get not found since other user has no medical record
        self.assertEqual(response.status_code, 404)
        print("✅ Other user medical record access test passed")

# Run the test directly if executed as a script
if __name__ == '__main__':
    import django
    import os
    
    # Setup Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
    django.setup()
    
    # Create test case and run tests
    test_case = MedicalRecordAPITest()
    test_case.setUp()
    
    try:
        test_case.test_medical_record_access_authenticated()
        test_case.test_medical_record_access_unauthenticated()
        test_case.test_medical_record_other_user()
        print("\n✅ All tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
    finally:
        # Clean up
        if hasattr(test_case, 'user'):
            test_case.user.delete() 