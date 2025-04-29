from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from api.models import CustomUser, Hospital, HospitalAdmin

class HospitalAdminRegistrationTests(TestCase):
    def setUp(self):
        # Create a test hospital
        self.hospital = Hospital.objects.create(
            name="Test Hospital",
            address="123 Test Street",
            city="Test City",
            state="Test State",
            country="Test Country"
        )
        
        # Create a test user
        self.existing_user = CustomUser.objects.create_user(
            email="existing@example.com",
            password="password123",
            first_name="Existing",
            last_name="User",
            date_of_birth="1990-01-01",
            gender="male",
            phone="1234567890",
            country="Nigeria",
            state="Lagos",
            city="Lagos",
            preferred_language="en",
            secondary_languages=["fr"],
            consent_terms=True,
            consent_hipaa=True,
            consent_data_processing=True
        )
        
        self.client = APIClient()
    
    def test_new_hospital_admin_registration(self):
        """Test registering a new user as a hospital admin"""
        url = reverse('hospital-admin-register')
        data = {
            "email": "newadmin@example.com",
            "full_name": "New Admin",
            "password": "password123",
            "hospital": self.hospital.id,
            "position": "Chief Administrator",
            "date_of_birth": "1985-05-15",
            "gender": "female",
            "phone": "9876543210",
            "country": "Nigeria",
            "state": "Lagos",
            "city": "Lagos",
            "preferred_language": "en",
            "secondary_languages": ["yo"],
            "consent_terms": True,
            "consent_hipaa": True,
            "consent_data_processing": True
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(HospitalAdmin.objects.count(), 1)
        self.assertEqual(CustomUser.objects.filter(email="newadmin@example.com").count(), 1)
        
        # Check that user data was properly saved
        user = CustomUser.objects.get(email="newadmin@example.com")
        self.assertEqual(user.date_of_birth.strftime('%Y-%m-%d'), "1985-05-15")
        self.assertEqual(user.gender, "female")
        self.assertEqual(user.phone, "9876543210")
        self.assertEqual(user.city, "Lagos")
        self.assertEqual(user.role, "hospital_admin")
    
    def test_existing_user_to_admin_conversion(self):
        """Test converting an existing user to a hospital admin"""
        url = reverse('hospital-admin-register')
        data = {
            "existing_user": True,
            "user_email": "existing@example.com",
            "hospital": self.hospital.id,
            "position": "Medical Director"
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(HospitalAdmin.objects.count(), 1)
        
        # Check that the existing user was properly converted
        user = CustomUser.objects.get(email="existing@example.com")
        self.assertEqual(user.role, "hospital_admin")
        self.assertTrue(hasattr(user, "hospital_admin_profile"))
        self.assertEqual(user.hospital_admin_profile.position, "Medical Director")
    
    def test_check_user_exists_endpoint(self):
        """Test the endpoint to check if a user exists"""
        url = reverse('check-user-exists')
        
        # Check existing user
        response = self.client.get(f"{url}?email=existing@example.com")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["exists"])
        self.assertFalse(response.data["is_admin"])
        
        # Check non-existing user
        response = self.client.get(f"{url}?email=nonexistent@example.com")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["exists"])
        self.assertFalse(response.data["is_admin"])
        
        # Test when email is not provided
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST) 