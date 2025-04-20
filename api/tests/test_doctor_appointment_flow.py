from django.test import TestCase
from django.utils import timezone
from datetime import timedelta, time
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from api.models import (
    Hospital,
    Department,
    Doctor,
    Appointment,
    AppointmentFee,
    AppointmentNotification,
    PaymentTransaction,
    AppointmentDocument,
    HospitalRegistration
)

class DoctorAppointmentFlowTest(TestCase):
    """Test the doctor's appointment flow including approval and fee handling"""

    def setUp(self):
        """Set up test data"""
        # Create users
        self.patient_user = get_user_model().objects.create_user(
            email='patient@test.com',
            password='password123',
            username='patient'
        )
        self.doctor_user = get_user_model().objects.create_user(
            email='doctor@test.com',
            password='password123',
            username='doctor'
        )
        
        # Create permissions
        appointment_content_type = ContentType.objects.get_for_model(Appointment)
        approve_permission, _ = Permission.objects.get_or_create(
            codename='can_approve_appointments',
            name='Can approve appointments',
            content_type=appointment_content_type,
        )
        refer_permission, _ = Permission.objects.get_or_create(
            codename='can_refer_appointments',
            name='Can refer appointments',
            content_type=appointment_content_type,
        )
        
        # Assign permissions to doctor
        self.doctor_user.user_permissions.add(approve_permission)
        self.doctor_user.user_permissions.add(refer_permission)
        
        # Create hospital and department
        self.hospital = Hospital.objects.create(
            name='Test Hospital',
            address='123 Test St',
            phone='1234567890',
            hospital_type='public',
            is_verified=True
        )
        
        self.department = Department.objects.create(
            name='General Medicine',
            hospital=self.hospital,
            code='GEN',
            minimum_staff_required=1,
            current_staff_count=1
        )
        
        # Create doctor
        self.doctor = Doctor.objects.create(
            user=self.doctor_user,
            hospital=self.hospital,
            department=self.department,
            specialization='General Medicine',
            medical_license_number='12345',
            license_expiry_date=timezone.now().date() + timezone.timedelta(days=365),
            years_of_experience=5,
            is_active=True,
            is_verified=True,
            status='active',
            consultation_hours_start=time(9, 0),  # 9 AM
            consultation_hours_end=time(17, 0),   # 5 PM
            consultation_days='Mon,Tue,Wed,Thu,Fri'
        )
        
        # Register patient with hospital
        self.hospital_registration, _ = HospitalRegistration.objects.get_or_create(
            user=self.patient_user,
            hospital=self.hospital,
            defaults={
                'status': 'approved',
                'is_primary': True,
                'approved_date': timezone.now()
            }
        )
        
        # Create appointment fee
        self.appointment_fee = AppointmentFee.objects.create(
            hospital=self.hospital,
            fee_type='general',
            base_fee=Decimal('100.00'),
            valid_from=timezone.now().date()
        )

    def test_doctor_appointment_approval_flow(self):
        """Test the complete doctor's appointment approval flow"""
        # Create an appointment for tomorrow at 10 AM
        tomorrow = timezone.now() + timezone.timedelta(days=1)
        appointment_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
        
        appointment = Appointment.objects.create(
            patient=self.patient_user,
            hospital=self.hospital,
            department=self.department,
            doctor=self.doctor,
            appointment_type='consultation',
            priority='normal',
            appointment_date=appointment_time,
            fee=self.appointment_fee
        )
        
        # Doctor approves the appointment
        appointment.approve(self.doctor_user, notes='Approved for consultation')
        
        # Check if appointment was approved
        self.assertEqual(appointment.status, 'confirmed')
        self.assertEqual(appointment.approved_by, self.doctor_user)
        self.assertIsNotNone(appointment.approval_date)
        self.assertEqual(appointment.approval_notes, 'Approved for consultation')

    def test_doctor_appointment_rejection(self):
        """Test doctor's ability to reject appointments"""
        # Create an appointment for tomorrow at 10 AM
        tomorrow = timezone.now() + timezone.timedelta(days=1)
        appointment_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
        
        appointment = Appointment.objects.create(
            patient=self.patient_user,
            hospital=self.hospital,
            department=self.department,
            doctor=self.doctor,
            appointment_type='consultation',
            priority='normal',
            appointment_date=appointment_time,
            fee=self.appointment_fee
        )
        
        # Doctor rejects the appointment
        appointment.status = 'rejected'
        appointment.save()
        
        # Create rejection notification
        AppointmentNotification.objects.create(
            appointment=appointment,
            notification_type='email',
            event_type='appointment_rejected',
            recipient=self.patient_user,
            subject=f"Appointment Rejected - {appointment.appointment_id}",
            message="Your appointment has been rejected.",
            template_name='appointment_rejected'
        )
        
        # Check if appointment was rejected
        self.assertEqual(appointment.status, 'rejected')
        notification = AppointmentNotification.objects.filter(
            appointment=appointment,
            event_type='appointment_rejected'
        ).first()
        self.assertIsNotNone(notification)

    def test_doctor_appointment_referral(self):
        """Test doctor's ability to refer appointments"""
        # Create an appointment for tomorrow at 10 AM
        tomorrow = timezone.now() + timezone.timedelta(days=1)
        appointment_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
        
        appointment = Appointment.objects.create(
            patient=self.patient_user,
            hospital=self.hospital,
            department=self.department,
            doctor=self.doctor,
            appointment_type='consultation',
            priority='normal',
            appointment_date=appointment_time,
            fee=self.appointment_fee
        )
        
        # Create target hospital and department
        target_hospital = Hospital.objects.create(
            name='Target Hospital',
            address='456 Target St',
            phone='0987654321',
            hospital_type='public',
            is_verified=True
        )
        
        target_department = Department.objects.create(
            name='General Medicine',
            hospital=target_hospital,
            code='GEN2',
            minimum_staff_required=1,
            current_staff_count=1
        )

        # Register patient with target hospital
        HospitalRegistration.objects.get_or_create(
            user=self.patient_user,
            hospital=target_hospital,
            defaults={
                'status': 'approved',
                'is_primary': False,
                'approved_date': timezone.now()
            }
        )

        # Create target doctor's user
        target_doctor_user = get_user_model().objects.create_user(
            email='target_doctor@test.com',
            password='password123',
            username='target_doctor'
        )
        
        # Create target doctor
        target_doctor = Doctor.objects.create(
            user=target_doctor_user,  # Using the new user
            hospital=target_hospital,
            department=target_department,
            specialization='General Medicine',
            medical_license_number='TGT123456',
            license_expiry_date=timezone.now().date() + timezone.timedelta(days=365),
            years_of_experience=5,
            consultation_hours_start=time(9, 0),
            consultation_hours_end=time(17, 0),
            consultation_days='Mon,Tue,Wed,Thu,Fri',
            is_verified=True,
            is_active=True
        )
        
        # Doctor refers the appointment
        new_appointment = appointment.refer(
            target_hospital=target_hospital,
            reason='Specialized care needed',
            referred_by=self.doctor_user
        )
        
        # Check if appointment was referred
        self.assertEqual(appointment.status, 'referred')
        self.assertEqual(appointment.referred_to_hospital, target_hospital)
        self.assertEqual(appointment.referral_reason, 'Specialized care needed')
        self.assertIsNotNone(appointment.referral_date)
        
        # Check if new appointment was created at target hospital
        self.assertEqual(new_appointment.hospital, target_hospital)
        self.assertEqual(new_appointment.status, 'pending')
        
        # Check if referral notification was created
        notification = AppointmentNotification.objects.filter(
            appointment=appointment,
            event_type='referral_notification'
        ).first()
        self.assertIsNotNone(notification)

    def test_emergency_appointment_handling(self):
        """Test doctor handling emergency appointments"""
        # Create appointment
        appointment = Appointment.objects.create(
            patient=self.patient_user,
            doctor=self.doctor,
            hospital=self.hospital,
            department=self.department,
            appointment_type='consultation',
            priority='emergency',
            appointment_date=timezone.now() + timezone.timedelta(hours=1),
            fee=self.appointment_fee
        )
        
        # Doctor approves the emergency appointment
        appointment.approve(self.doctor_user, notes='Emergency consultation approved')
        
        # Check if appointment was approved
        self.assertEqual(appointment.status, 'confirmed')
        self.assertEqual(appointment.approved_by, self.doctor_user)
        self.assertIsNotNone(appointment.approval_date)
        self.assertEqual(appointment.approval_notes, 'Emergency consultation approved') 