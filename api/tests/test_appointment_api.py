from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from api.models import (
    Appointment,
    Doctor,
    Hospital,
    Department,
    AppointmentNotification,
    HospitalRegistration,
    AppointmentFee
)
from decimal import Decimal
from datetime import timedelta, time
from rest_framework import status
from django.db import connection

APPOINTMENTS_URL = '/api/appointments/'

class AppointmentAPITest(APITestCase):
    """Test the appointment booking API endpoints 🏥"""

    def setUp(self):
        """Set up test data 🔧"""
        # Create test users
        self.patient_user = get_user_model().objects.create_user(
            username='testpatient',
            email='patient@test.com',
            password='testpass123',
            first_name='Test',
            last_name='Patient'
        )
        
        self.admin_user = get_user_model().objects.create_user(
            username='testadmin',
            email='admin@test.com',
            password='testpass123',
            first_name='Test',
            last_name='Admin',
            is_staff=True
        )
        
        # Add appointment approval permission to admin
        content_type = ContentType.objects.get_for_model(Appointment)
        permission = Permission.objects.get(
            codename='can_approve_appointments',
            content_type=content_type,
        )
        self.admin_user.user_permissions.add(permission)
        
        # Create hospital and department
        self.hospital = Hospital.objects.create(
            name='Test Hospital',
            address='123 Test St',
            phone='1234567890',
            hospital_type='public',
            bed_capacity=100,
            emergency_unit=True
        )
        
        self.department = Department.objects.create(
            hospital=self.hospital,
            name='Test Department',
            code='TEST001',
            department_type='medical',
            floor_number='1',
            wing='north',
            extension_number='123',
            emergency_contact='911',
            email='test@hospital.com',
            minimum_staff_required=1,
            current_staff_count=1
        )
        
        # Create doctor user and doctor profile
        self.doctor_user = get_user_model().objects.create_user(
            username='testdoctor',
            email='doctor@test.com',
            password='testpass123',
            first_name='Test',
            last_name='Doctor'
        )
        
        self.doctor = Doctor.objects.create(
            user=self.doctor_user,
            hospital=self.hospital,
            department=self.department,
            specialization='Cardiology',
            consultation_days='Mon,Tue,Wed,Thu,Fri',
            consultation_hours_start='09:00:00',
            consultation_hours_end='17:00:00',
            medical_license_number='12345',
            license_expiry_date=timezone.now().date() + timezone.timedelta(days=365),
            years_of_experience=5,
            is_verified=True
        )
        
        # Create appointment fee for the doctor
        self.fee = AppointmentFee.objects.create(
            hospital=self.hospital,
            department=self.department,
            doctor=self.doctor,
            fee_type='consultation',
            base_fee=Decimal('100.00'),
            currency='USD',
            is_active=True,
            valid_from=timezone.now().date()
        )
        
        # Create hospital registration for patient
        self.registration = HospitalRegistration.objects.create(
            user=self.patient_user,
            hospital=self.hospital,
            status='approved',
            is_primary=True
        )
        
        # Set up appointment time for tests (10:00 AM next day)
        next_day = timezone.now() + timezone.timedelta(days=1)
        self.appointment_time = next_day.replace(hour=10, minute=0, second=0, microsecond=0)
        
        # Set up API client
        self.client = APIClient()
        self.client.force_authenticate(user=self.patient_user)

    def test_list_appointments_unauthenticated(self):
        """Test that unauthenticated users cannot list appointments"""
        self.client.force_authenticate(user=None)  # Ensure no user is authenticated
        response = self.client.get(APPOINTMENTS_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_appointments_authenticated(self):
        """Test that authenticated users can list their appointments 📋"""
        self.client.force_authenticate(user=self.patient_user)
        url = '/api/appointments/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_create_appointment(self):
        """Test creating a new appointment"""
        appointment_id = f"APT-{self.appointment_time.strftime('%Y%m%d')}-001"
        
        data = {
            'doctor_id': self.doctor.id,
            'hospital': self.hospital.id,
            'department': self.department.id,
            'appointment_date': self.appointment_time,
            'appointment_type': 'consultation',
            'priority': 'normal',
            'chief_complaint': 'Test complaint',
            'fee_id': self.fee.id,
            'appointment_id': appointment_id
        }
        
        response = self.client.post(APPOINTMENTS_URL, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        appointment = Appointment.objects.get(id=response.data['id'])
        self.assertEqual(appointment.doctor.id, self.doctor.id)
        self.assertEqual(appointment.fee.id, self.fee.id)
        self.assertEqual(appointment.patient, self.patient_user)
        
        # Check if notifications were created
        notifications = AppointmentNotification.objects.filter(
            appointment=appointment,
            event_type='booking_confirmation'
        )
        self.assertEqual(notifications.count(), 3)  # Email and SMS for patient, Email for doctor
        
        # Verify notification types and recipients
        patient_notifications = notifications.filter(recipient=self.patient_user)
        doctor_notifications = notifications.filter(recipient=self.doctor_user)
        
        self.assertEqual(set(patient_notifications.values_list('notification_type', flat=True)), {'email', 'sms'})
        self.assertEqual(doctor_notifications.count(), 1)
        self.assertEqual(doctor_notifications.first().notification_type, 'email')

    def test_create_appointment_invalid_time(self):
        """Test creating an appointment with invalid time"""
        past_date = timezone.now() - timezone.timedelta(days=1)
        past_date = past_date.replace(hour=10, minute=0, second=0, microsecond=0)
        appointment_id = f"APT-{past_date.strftime('%Y%m%d')}-002"
        
        data = {
            'doctor_id': self.doctor.id,
            'hospital': self.hospital.id,
            'department': self.department.id,
            'appointment_date': past_date,
            'appointment_type': 'consultation',
            'priority': 'normal',
            'chief_complaint': 'Test complaint',
            'fee_id': self.fee.id,
            'appointment_id': appointment_id
        }
        
        response = self.client.post(APPOINTMENTS_URL, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response.data)
        self.assertEqual(
            response.data['non_field_errors'][0],
            "Cannot create appointments in the past."
        )

    def test_update_appointment_status(self):
        """Test updating appointment status"""
        # Create an appointment
        appointment = Appointment.objects.create(
            doctor=self.doctor,
            patient=self.patient_user,
            hospital=self.hospital,
            department=self.department,
            appointment_date=self.appointment_time,
            appointment_type='consultation',
            priority='normal',
            fee=self.fee,
            appointment_id=f'APT-{self.appointment_time.strftime("%Y%m%d")}-003'
        )
        
        # Update status to confirmed
        data = {'status': 'confirmed'}
        response = self.client.patch(
            f'{APPOINTMENTS_URL}{appointment.id}/',
            data
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        appointment.refresh_from_db()
        self.assertEqual(appointment.status, 'confirmed')

    def test_cancel_appointment(self):
        """Test canceling an appointment"""
        # Create an appointment
        appointment = Appointment.objects.create(
            doctor=self.doctor,
            patient=self.patient_user,
            hospital=self.hospital,
            department=self.department,
            appointment_date=self.appointment_time,
            appointment_type='consultation',
            priority='normal',
            fee=self.fee,
            appointment_id=f'APT-{self.appointment_time.strftime("%Y%m%d")}-004'
        )
        
        # Cancel the appointment
        data = {
            'status': 'cancelled',
            'cancellation_reason': 'Schedule conflict'
        }
        response = self.client.patch(
            f'{APPOINTMENTS_URL}{appointment.id}/',
            data
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        appointment.refresh_from_db()
        self.assertEqual(appointment.status, 'cancelled')
        self.assertEqual(appointment.cancellation_reason, 'Schedule conflict')

    def test_list_upcoming_appointments(self):
        """Test listing upcoming appointments"""
        # Create a past appointment using raw SQL to bypass validation
        past_date = timezone.now() - timezone.timedelta(days=1)
        past_date = past_date.replace(hour=10, minute=0, second=0, microsecond=0)
        
        # First create the appointment with current date
        past_appointment = Appointment.objects.create(
            patient=self.patient_user,
            doctor=self.doctor,
            hospital=self.hospital,
            department=self.department,
            appointment_date=self.appointment_time,
            status='completed',
            fee=self.fee,
            appointment_type='consultation',
            priority='normal'
        )
        
        # Then update its date to past using raw SQL
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE api_appointment 
                SET appointment_date = %s 
                WHERE id = %s
                """,
                [past_date, past_appointment.id]
            )
        
        # Create an upcoming appointment
        upcoming_appointment = Appointment.objects.create(
            patient=self.patient_user,
            doctor=self.doctor,
            hospital=self.hospital,
            department=self.department,
            appointment_date=self.appointment_time,
            status='pending',
            fee=self.fee,
            appointment_type='consultation',
            priority='normal'
        )
        
        # Make the request
        self.client.force_authenticate(user=self.patient_user)
        response = self.client.get(f'{APPOINTMENTS_URL}?upcoming=true')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], upcoming_appointment.id)

    def test_doctor_appointment_list(self):
        """Test listing doctor's appointments"""
        # Create an appointment for our doctor
        appointment = Appointment.objects.create(
            patient=self.patient_user,
            doctor=self.doctor,
            hospital=self.hospital,
            department=self.department,
            appointment_date=self.appointment_time,
            status='pending',
            fee=self.fee,
            appointment_type='consultation',
            priority='normal'
        )
        
        # Create another doctor and appointment
        other_doctor_user = get_user_model().objects.create_user(
            username='otherdoctor',
            email='other@example.com',
            password='testpass123',
            first_name='Other',
            last_name='Doctor'
        )
        
        other_doctor = Doctor.objects.create(
            user=other_doctor_user,
            specialization='Cardiology',
            medical_license_number='54321',
            license_expiry_date=timezone.now().date() + timezone.timedelta(days=365),
            years_of_experience=5,
            hospital=self.hospital,
            department=self.department,
            consultation_hours_start=time(9, 0),
            consultation_hours_end=time(17, 0),
            consultation_days='Mon,Tue,Wed,Thu,Fri',
            is_verified=True
        )
        
        # Create appointment for other doctor on a weekday (Monday-Friday)
        next_day = self.appointment_time
        
        # Ensure the day is a weekday by checking if the day is in consultation_days
        day_name = next_day.strftime('%a')  # Get short day name (Mon, Tue, etc.)
        
        # If not a weekday in doctor's consultation days, find the next available day
        consultation_days = other_doctor.consultation_days.split(',')
        while day_name not in consultation_days:
            next_day = next_day + timezone.timedelta(days=1)
            day_name = next_day.strftime('%a')
            
        print(f"Creating test appointment on {day_name} for doctor with consultation days: {other_doctor.consultation_days}")
        
        other_appointment = Appointment.objects.create(
            patient=self.patient_user,
            doctor=other_doctor,
            hospital=self.hospital,
            department=self.department,
            appointment_date=next_day,
            status='pending',
            fee=self.fee,
            appointment_type='consultation',
            priority='normal'
        )
        
        # Refresh the doctor user instance to ensure the relationship is loaded
        doctor_user = get_user_model().objects.get(id=self.doctor_user.id)
        self.assertTrue(hasattr(doctor_user, 'doctor_profile'))
        self.assertEqual(doctor_user.doctor_profile, self.doctor)
        
        # Make the request as the doctor
        self.client.force_authenticate(user=doctor_user)
        response = self.client.get(APPOINTMENTS_URL)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], appointment.id) 