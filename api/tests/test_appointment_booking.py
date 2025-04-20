from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from datetime import timedelta
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

class AppointmentBookingTest(TestCase):
    """Test appointment booking functionality 🏥"""

    def setUp(self):
        """Set up test data 🔧"""
        # Create a test user (patient)
        self.patient_user = get_user_model().objects.create_user(
            username='testpatient',
            email='patient@test.com',
            password='testpass123',
            role='patient'
        )

        # Create a hospital
        self.hospital = Hospital.objects.create(
            name='Test Hospital',
            address='123 Test St',
            phone='1234567890',
            hospital_type='public',
            bed_capacity=100,
            emergency_unit=True
        )

        # Create a department with required staff count
        self.department = Department.objects.create(
            name='Cardiology',
            code='CARD001',
            hospital=self.hospital,
            department_type='medical',
            minimum_staff_required=1,
            current_staff_count=1,
            floor_number='3',
            wing='north',
            extension_number='1234',
            emergency_contact='1234567890',
            email='cardiology@test.com'
        )

        # Create a doctor user
        self.doctor_user = get_user_model().objects.create_user(
            username='testdoctor',
            email='doctor@test.com',
            password='testpass123',
            role='doctor'
        )

        # Create test doctor with all required fields
        self.doctor = Doctor.objects.create(
            user=self.doctor_user,
            department=self.department,
            hospital=self.hospital,
            specialization='Cardiology',
            medical_license_number='MED123',
            license_expiry_date=timezone.now().date() + timezone.timedelta(days=365),
            years_of_experience=5,
            consultation_days='Mon,Tue,Wed,Thu,Fri',
            consultation_hours_start=timezone.datetime.strptime('09:00', '%H:%M').time(),
            consultation_hours_end=timezone.datetime.strptime('17:00', '%H:%M').time(),
            qualifications=['MBBS', 'MD'],
            is_verified=True
        )

        # Create hospital registration for the patient
        self.hospital_registration = HospitalRegistration.objects.create(
            user=self.patient_user,
            hospital=self.hospital,
            status='approved',
            is_primary=True,
            approved_date=timezone.now()
        )

        # Create appointment fee
        self.fee = AppointmentFee.objects.create(
            hospital=self.hospital,
            department=self.department,
            doctor=self.doctor,
            fee_type='general',
            base_fee=Decimal('50.00'),
            currency='NGN',
            valid_from=timezone.now().date()
        )

    def test_basic_appointment_creation(self):
        """Test creating a basic appointment 📅"""
        # Get tomorrow at 10 AM
        tomorrow = timezone.now() + timedelta(days=1)
        appointment_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)

        appointment = Appointment.objects.create(
            patient=self.patient_user,
            hospital=self.hospital,
            department=self.department,
            doctor=self.doctor,
            appointment_date=appointment_time,
            appointment_type='consultation',
            priority='normal',
            fee=self.fee
        )

        self.assertEqual(appointment.status, 'pending')
        self.assertEqual(appointment.patient, self.patient_user)
        self.assertEqual(appointment.doctor, self.doctor)

    def test_appointment_in_past(self):
        """Test that appointments can't be created in the past ⏰"""
        yesterday = timezone.now() - timedelta(days=1)
        
        with self.assertRaises(ValidationError):
            Appointment.objects.create(
                patient=self.patient_user,
                hospital=self.hospital,
                department=self.department,
                doctor=self.doctor,
                appointment_date=yesterday,
                appointment_type='consultation',
                priority='normal',
                fee=self.fee
            )

    def test_overlapping_appointments(self):
        """Test that overlapping appointments are not allowed 🔄"""
        # Create first appointment
        tomorrow = timezone.now() + timedelta(days=1)
        appointment_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)

        Appointment.objects.create(
            patient=self.patient_user,
            hospital=self.hospital,
            department=self.department,
            doctor=self.doctor,
            appointment_date=appointment_time,
            appointment_type='consultation',
            priority='normal',
            fee=self.fee
        )

        # Try to create overlapping appointment
        with self.assertRaises(ValidationError):
            Appointment.objects.create(
                patient=self.patient_user,
                hospital=self.hospital,
                department=self.department,
                doctor=self.doctor,
                appointment_date=appointment_time + timedelta(minutes=15),
                appointment_type='consultation',
                priority='normal',
                fee=self.fee
            )

    def test_emergency_appointment(self):
        """Test emergency appointment creation 🚨"""
        # Emergency appointments should bypass normal validation
        appointment_time = timezone.now() + timedelta(hours=1)

        appointment = Appointment.objects.create(
            patient=self.patient_user,
            hospital=self.hospital,
            department=self.department,
            doctor=self.doctor,
            appointment_date=appointment_time,
            appointment_type='consultation',
            priority='emergency',
            fee=self.fee
        )

        self.assertEqual(appointment.status, 'pending')
        self.assertEqual(appointment.priority, 'emergency')

    def test_appointment_notifications(self):
        """Test that notifications are created for appointments 📧"""
        tomorrow = timezone.now() + timedelta(days=1)
        appointment_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)

        appointment = Appointment.objects.create(
            patient=self.patient_user,
            hospital=self.hospital,
            department=self.department,
            doctor=self.doctor,
            appointment_date=appointment_time,
            appointment_type='consultation',
            priority='normal',
            fee=self.fee
        )

        # Check if booking confirmation notifications were created
        notifications = AppointmentNotification.objects.filter(
            appointment=appointment,
            event_type='booking_confirmation'
        )
        
        # Should have both email and SMS notifications
        self.assertEqual(notifications.count(), 2)
        self.assertTrue(notifications.filter(notification_type='email').exists())
        self.assertTrue(notifications.filter(notification_type='sms').exists())

    def test_appointment_outside_hours(self):
        """Test that appointments can't be made outside consultation hours ⏰"""
        tomorrow = timezone.now() + timedelta(days=1)
        # Try to book at 8 AM (before consultation hours)
        early_time = tomorrow.replace(hour=8, minute=0, second=0, microsecond=0)

        with self.assertRaises(ValidationError):
            Appointment.objects.create(
                patient=self.patient_user,
                hospital=self.hospital,
                department=self.department,
                doctor=self.doctor,
                appointment_date=early_time,
                appointment_type='consultation',
                priority='normal',
                fee=self.fee
            )

    def test_unregistered_patient(self):
        """Test that unregistered patients can't book appointments 🚫"""
        # Create unregistered user
        unregistered_user = get_user_model().objects.create_user(
            email='unregistered@test.com',
            password='testpass123'
        )

        tomorrow = timezone.now() + timedelta(days=1)
        appointment_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)

        with self.assertRaises(ValidationError):
            Appointment.objects.create(
                patient=unregistered_user,
                hospital=self.hospital,
                department=self.department,
                doctor=self.doctor,
                appointment_date=appointment_time,
                appointment_type='consultation',
                priority='normal',
                fee=self.fee
            )

    def test_appointment_status_transitions(self):
        """Test appointment status transitions ⚡"""
        tomorrow = timezone.now() + timedelta(days=1)
        appointment_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)

        appointment = Appointment.objects.create(
            patient=self.patient_user,
            hospital=self.hospital,
            department=self.department,
            doctor=self.doctor,
            appointment_date=appointment_time,
            appointment_type='consultation',
            priority='normal',
            fee=self.fee
        )

        # Test valid transitions
        appointment.status = 'confirmed'
        appointment.save()
        self.assertEqual(appointment.status, 'confirmed')

        appointment.status = 'in_progress'
        appointment.save()
        self.assertEqual(appointment.status, 'in_progress')

        appointment.status = 'completed'
        appointment.save()
        self.assertEqual(appointment.status, 'completed')

        # Test invalid transition
        appointment.status = 'pending'
        with self.assertRaises(ValidationError):
            appointment.save() 