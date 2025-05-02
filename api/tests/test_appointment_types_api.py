from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from api.models.medical.appointment import AppointmentType
from api.models.medical.department import Department
from api.models.medical.hospital_auth import Hospital
from django.contrib.auth import get_user_model

class AppointmentTypesDepartmentsAPITests(TestCase):
    """Test the appointment types and departments API endpoints"""

    def setUp(self):
        """Set up test client and test data"""
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

        # Create test appointment types
        self.appointment_types = [
            AppointmentType.objects.create(id='test_visit', name='Test Visit'),
            AppointmentType.objects.create(id='test_consult', name='Test Consultation')
        ]

        # Create a test hospital
        self.hospital = Hospital.objects.create(
            name='Test Hospital',
            address='123 Test St',
            phone='1234567890',
            hospital_type='public',
            bed_capacity=100,
            emergency_unit=True
        )

        # Create test departments
        self.departments = [
            Department.objects.create(
                name='Test Department',
                code='TEST001',
                hospital=self.hospital,
                department_type='medical',
                minimum_staff_required=1,
                current_staff_count=1,
                floor_number='1',
                wing='test',
                extension_number='123',
                emergency_contact='123',
                email='test@example.com'
            )
        ]

    def test_appointment_types_endpoint(self):
        """Test retrieving appointment types"""
        url = '/api/appointment-types/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) >= 2)  # At least our test types
        
        # Verify our test types are in the response
        type_ids = [item['id'] for item in response.data]
        self.assertIn('test_visit', type_ids)
        self.assertIn('test_consult', type_ids)

    def test_departments_endpoint(self):
        """Test retrieving departments"""
        url = '/api/departments/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) >= 1)  # At least our test department
        
        # Verify our test department is in the response
        department_names = [item['name'] for item in response.data]
        self.assertIn('Test Department', department_names) 