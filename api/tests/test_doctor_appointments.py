import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.utils import timezone
from api.models.medical.appointment import Appointment
from api.models.medical_staff.doctor import Doctor
from api.models.hospital import Hospital, Department
from django.contrib.auth import get_user_model
from datetime import timedelta

User = get_user_model()

class DoctorAppointmentSummaryTests(APITestCase):
    """Tests for the doctor appointment summary endpoint"""
    
    def setUp(self):
        # Create a doctor user
        self.doctor_user = User.objects.create_user(
            username='doctor@example.com',
            email='doctor@example.com',
            password='password123',
            first_name='John',
            last_name='Doe'
        )
        
        # Create hospital and department
        self.hospital = Hospital.objects.create(
            name='Test Hospital',
            address='123 Test Street',
            city='Test City',
            state='Test State',
            postal_code='12345',
            country='Test Country'
        )
        
        self.department = Department.objects.create(
            name='Cardiology',
            description='Heart department',
            hospital=self.hospital
        )
        
        # Create doctor profile
        self.doctor = Doctor.objects.create(
            user=self.doctor_user,
            hospital=self.hospital,
            department=self.department,
            specialty='Cardiology',
            license_number='12345'
        )
        
        # Create patient user
        self.patient = User.objects.create_user(
            username='patient@example.com',
            email='patient@example.com',
            password='password123',
            first_name='Jane',
            last_name='Smith'
        )
        
        # Create appointments with different statuses
        now = timezone.now()
        
        # Create pending appointment (today)
        self.pending_appointment = Appointment.objects.create(
            appointment_id='APT-00000001',
            patient=self.patient,
            hospital=self.hospital,
            department=self.department,
            doctor=self.doctor,
            appointment_type='consultation',
            priority='normal',
            status='pending',
            appointment_date=now + timedelta(hours=2)
        )
        
        # Create confirmed appointment (tomorrow)
        self.confirmed_appointment = Appointment.objects.create(
            appointment_id='APT-00000002',
            patient=self.patient,
            hospital=self.hospital,
            department=self.department,
            doctor=self.doctor,
            appointment_type='follow_up',
            priority='normal',
            status='confirmed',
            appointment_date=now + timedelta(days=1)
        )
        
        # Create completed appointment (yesterday)
        self.completed_appointment = Appointment.objects.create(
            appointment_id='APT-00000003',
            patient=self.patient,
            hospital=self.hospital,
            department=self.department,
            doctor=self.doctor,
            appointment_type='first_visit',
            priority='normal',
            status='completed',
            appointment_date=now - timedelta(days=1),
            completed_at=now - timedelta(days=1)
        )
        
        # Create cancelled appointment (2 days ago)
        self.cancelled_appointment = Appointment.objects.create(
            appointment_id='APT-00000004',
            patient=self.patient,
            hospital=self.hospital,
            department=self.department,
            doctor=self.doctor,
            appointment_type='consultation',
            priority='normal',
            status='cancelled',
            appointment_date=now - timedelta(days=2),
            cancelled_at=now - timedelta(days=3)
        )
        
        # Login as doctor
        self.client.force_authenticate(user=self.doctor_user)
    
    def test_doctor_appointments_summary(self):
        """Test getting the doctor appointment summary"""
        url = reverse('doctor-appointment-appointments-summary')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Check that all required fields are present in the response
        self.assertIn('total_appointments', data)
        self.assertIn('counts', data)
        self.assertIn('by_status', data['counts'])
        self.assertIn('by_type', data['counts'])
        self.assertIn('by_time_period', data['counts'])
        self.assertIn('by_department', data['counts'])
        self.assertIn('recent_appointments', data)
        self.assertIn('upcoming_appointments', data)
        self.assertIn('trends', data)
        
        # Check appointment counts
        self.assertEqual(data['total_appointments'], 4)
        self.assertEqual(data['counts']['by_status']['pending'], 1)
        self.assertEqual(data['counts']['by_status']['confirmed'], 1)
        self.assertEqual(data['counts']['by_status']['completed'], 1)
        self.assertEqual(data['counts']['by_status']['cancelled'], 1)
        
        # Check appointment types
        self.assertEqual(data['counts']['by_type']['consultation'], 2)
        self.assertEqual(data['counts']['by_type']['follow_up'], 1)
        self.assertEqual(data['counts']['by_type']['first_visit'], 1)
        
        # Check recent and upcoming appointments
        self.assertEqual(len(data['recent_appointments']), 2)  # completed and cancelled
        self.assertEqual(len(data['upcoming_appointments']), 2)  # pending and confirmed
        
    def test_doctor_appointments_summary_no_doctor_profile(self):
        """Test getting the doctor appointment summary without a doctor profile"""
        # Create a non-doctor user
        non_doctor_user = User.objects.create_user(
            username='nodoc@example.com',
            email='nodoc@example.com',
            password='password123'
        )
        
        # Login as non-doctor user
        self.client.force_authenticate(user=non_doctor_user)
        
        url = reverse('doctor-appointment-appointments-summary')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.json()['message'], 'You are not registered as a doctor in the system') 