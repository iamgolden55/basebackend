from django.test import TestCase
from django.utils import timezone
from api.models.medical.doctor_assignment import doctor_assigner
from api.models.medical_staff.doctor import Doctor
from api.models.user.custom_user import CustomUser
from api.models.medical.department import Department
from api.models.medical.appointment import Appointment
from api.models.medical.hospital import Hospital
from datetime import timedelta, date, datetime
import numpy as np
from api.models.medical.hospital_registration import HospitalRegistration

class TestMLDoctorAssignment(TestCase):
    def setUp(self):
        """Set up test data"""
        # Create a hospital first
        self.hospital = Hospital.objects.create(
            name="Test Hospital",
            address="123 Test St",
            city="Test City",
            state="Test State",
            country="Test Country",
            postal_code="12345",
            phone="1234567890",
            email="test@hospital.com",
            registration_number="TEST001",
            hospital_type="public",
            bed_capacity=100
        )
        
        # Create a department with all required fields
        self.department = Department.objects.create(
            name="Cardiology",
            code="CARD01",
            description="Heart related treatments",
            department_type="medical",
            hospital=self.hospital,
            floor_number="3",
            wing="north",
            extension_number="1234",
            emergency_contact="911",
            email="cardio@test.com",
            minimum_staff_required=2,
            current_staff_count=5,  # Set higher than minimum_staff_required
            total_beds=20,
            occupied_beds=0,
            icu_beds=5,
            occupied_icu_beds=0,
            bed_capacity=25
        )
        
        # Create doctor users first
        self.doctor1_user = CustomUser.objects.create(
            username="doctor1",
            email="doctor1@test.com",
            first_name="John",
            last_name="Doe",
            role="doctor"
        )
        
        self.doctor2_user = CustomUser.objects.create(
            username="doctor2",
            email="doctor2@test.com",
            first_name="Jane",
            last_name="Smith",
            role="doctor"
        )
        
        # Create doctor profiles
        self.doctor1 = Doctor.objects.create(
            user=self.doctor1_user,
            department=self.department,
            hospital=self.hospital,
            years_of_experience=5,
            languages_spoken="English,Spanish",
            specialization="Cardiology",
            medical_license_number="ML001",
            license_expiry_date=date(2025, 12, 31),
            consultation_days="Mon,Tue,Wed,Thu,Fri",
            consultation_hours_start=timezone.now().time().replace(hour=9, minute=0),
            consultation_hours_end=timezone.now().time().replace(hour=17, minute=0),
            is_active=True,
            available_for_appointments=True,
            status='active',
            is_verified=True
        )
        
        self.doctor2 = Doctor.objects.create(
            user=self.doctor2_user,
            department=self.department,
            hospital=self.hospital,
            years_of_experience=10,
            languages_spoken="English,French",
            specialization="Cardiology",
            medical_license_number="ML002",
            license_expiry_date=date(2025, 12, 31),
            consultation_days="Mon,Tue,Wed,Thu,Fri",
            consultation_hours_start=timezone.now().time().replace(hour=9, minute=0),
            consultation_hours_end=timezone.now().time().replace(hour=17, minute=0),
            is_active=True,
            available_for_appointments=True,
            status='active',
            is_verified=True
        )
        
        # Create a doctor who speaks Calabar
        self.doctor3_user = CustomUser.objects.create(
            username="doctor3",
            email="doctor3@test.com",
            first_name="Emeka",
            last_name="Okafor",
            role="doctor"
        )
        
        self.doctor3 = Doctor.objects.create(
            user=self.doctor3_user,
            department=self.department,
            hospital=self.hospital,
            years_of_experience=8,
            languages_spoken="English,Yoruba,Calabar",
            specialization="Cardiology",
            medical_license_number="ML003",
            license_expiry_date=date(2025, 12, 31),
            consultation_days="Mon,Tue,Wed,Thu,Fri",
            consultation_hours_start=timezone.now().time().replace(hour=9, minute=0),
            consultation_hours_end=timezone.now().time().replace(hour=17, minute=0),
            is_active=True,
            available_for_appointments=True,
            status='active',
            is_verified=True
        )
        
        # Create a patient using CustomUser
        self.patient = CustomUser.objects.create(
            username="patient1",
            email="patient1@test.com",
            first_name="Bob",
            last_name="Johnson",
            role="patient",
            gender="male"
        )
        
        # Register patient with the hospital
        self.registration = HospitalRegistration.objects.create(
            user=self.patient,
            hospital=self.hospital,
            status='approved',  # Set as approved
            is_primary=True
        )
        
        # Find the next Monday (to ensure it's a consultation day)
        today = timezone.now().date()
        days_until_monday = (7 - today.weekday()) % 7  # 0 = Monday, 1 = Tuesday, etc.
        if days_until_monday == 0:  # If today is Monday, use next Monday
            days_until_monday = 7
        next_monday = today + timedelta(days=days_until_monday)
        
        # Set appointment time to 2 PM on next Monday
        appointment_time = timezone.now().time().replace(hour=14, minute=0)  # 2 PM
        self.appointment_data = {
            'patient': self.patient,
            'department': self.department,
            'hospital': self.hospital,
            'appointment_type': 'regular',
            'priority': 'normal',
            'appointment_date': timezone.make_aware(datetime.combine(next_monday, appointment_time))
        }
    
    def test_doctor_assignment_without_training(self):
        """Test doctor assignment without ML training"""
        # Test initial assignment (should use simple scoring)
        assigned_doctor = doctor_assigner.assign_doctor(self.appointment_data)
        self.assertIsNotNone(assigned_doctor)
        self.assertIn(assigned_doctor, [self.doctor1, self.doctor2, self.doctor3])
        
        # Create the appointment with the assigned doctor
        self.appointment_data['doctor'] = assigned_doctor
        appointment = Appointment.objects.create(**self.appointment_data)
        self.assertEqual(appointment.doctor, assigned_doctor)
    
    def test_doctor_assignment_with_training(self):
        """Test doctor assignment with ML training"""
        # Create sample training data
        training_data = {
            'features': [],
            'outcomes': []
        }
        
        # Generate some synthetic training data
        for _ in range(100):
            features = np.random.rand(10)  # 10 features as defined in our model
            outcome = np.random.randint(0, 2)  # Binary outcome (0 or 1)
            training_data['features'].append(features)
            training_data['outcomes'].append(outcome)
        
        # Train the model
        success = doctor_assigner.train_model(training_data)
        self.assertTrue(success)
        
        # Test assignment after training
        assigned_doctor = doctor_assigner.assign_doctor(self.appointment_data)
        self.assertIsNotNone(assigned_doctor)
        self.assertIn(assigned_doctor, [self.doctor1, self.doctor2, self.doctor3])
        
        # Create the appointment with the assigned doctor
        self.appointment_data['doctor'] = assigned_doctor
        appointment = Appointment.objects.create(**self.appointment_data)
        self.assertEqual(appointment.doctor, assigned_doctor)
    
    def test_doctor_assignment_with_workload(self):
        """Test doctor assignment considering workload"""
        # Create some existing appointments for doctor1
        appointment_date = self.appointment_data['appointment_date']
        for hour in range(9, 14):  # Create appointments from 9 AM to 1 PM
            Appointment.objects.create(
                patient=self.patient,
                doctor=self.doctor1,
                hospital=self.hospital,
                department=self.department,
                appointment_type='regular',
                priority='normal',
                appointment_date=appointment_date.replace(hour=hour),
                chief_complaint='Regular checkup',
                status='confirmed'
            )
        
        # Create appointment data for 2 PM
        self.appointment_data['appointment_date'] = appointment_date.replace(hour=14)
        
        # Test assignment (should prefer doctor2 or doctor3 due to lower workload)
        assigned_doctor = doctor_assigner.assign_doctor(self.appointment_data)
        self.assertIsNotNone(assigned_doctor)
        self.assertNotEqual(assigned_doctor, self.doctor1)
        
        # Create the appointment with the assigned doctor
        self.appointment_data['doctor'] = assigned_doctor
        appointment = Appointment.objects.create(**self.appointment_data)
        self.assertEqual(appointment.doctor, assigned_doctor)
    
    def test_doctor_assignment_with_legacy_language_match(self):
        """Test doctor assignment considering legacy language match"""
        # Update patient to speak only Spanish using legacy field
        self.patient.languages = "Spanish"
        # Make sure preferred_language is set to something else to test legacy field
        self.patient.preferred_language = "en"
        self.patient.save()
        
        # Make sure doctor1 speaks Spanish
        self.doctor1.languages_spoken = "English,Spanish"
        self.doctor1.save()
        
        # Make sure doctor2 doesn't speak Spanish
        self.doctor2.languages_spoken = "English,French"
        self.doctor2.save()
        
        # Make sure doctor3 doesn't speak Spanish
        self.doctor3.languages_spoken = "English,Yoruba,Calabar"
        self.doctor3.save()
        
        # Test assignment (should prefer doctor1 who speaks Spanish)
        assigned_doctor = doctor_assigner.assign_doctor(self.appointment_data)
        self.assertIsNotNone(assigned_doctor)
        
        # Check that the assigned doctor speaks Spanish
        self.assertIn("spanish", assigned_doctor.languages_spoken.lower())
        self.assertEqual(assigned_doctor, self.doctor1)
        
        # Create the appointment with the assigned doctor
        self.appointment_data['doctor'] = assigned_doctor
        appointment = Appointment.objects.create(**self.appointment_data)
        self.assertEqual(appointment.doctor, assigned_doctor)
    
    def test_doctor_assignment_with_preferred_language(self):
        """Test doctor assignment with preferred language field"""
        # Update patient to prefer French
        self.patient.preferred_language = "french"
        self.patient.save()
        
        # Test assignment (should prefer doctor2 who speaks French)
        assigned_doctor = doctor_assigner.assign_doctor(self.appointment_data)
        self.assertIsNotNone(assigned_doctor)
        self.assertEqual(assigned_doctor, self.doctor2)
        
        # Create the appointment with the assigned doctor
        self.appointment_data['doctor'] = assigned_doctor
        appointment = Appointment.objects.create(**self.appointment_data)
        self.assertEqual(appointment.doctor, self.doctor2)
    
    def test_doctor_assignment_with_custom_language(self):
        """Test doctor assignment with custom language field"""
        # Update patient to prefer "other" language (Calabar)
        self.patient.preferred_language = "other"
        self.patient.custom_language = "Calabar"
        self.patient.save()
        
        # Test assignment (should prefer doctor3 who speaks Calabar)
        assigned_doctor = doctor_assigner.assign_doctor(self.appointment_data)
        self.assertIsNotNone(assigned_doctor)
        self.assertEqual(assigned_doctor, self.doctor3)
        
        # Create the appointment with the assigned doctor
        self.appointment_data['doctor'] = assigned_doctor
        appointment = Appointment.objects.create(**self.appointment_data)
        self.assertEqual(appointment.doctor, self.doctor3)
    
    def test_doctor_assignment_with_secondary_languages(self):
        """Test doctor assignment with secondary languages field"""
        # Update patient with preferred and secondary languages
        self.patient.preferred_language = "english"
        self.patient.secondary_languages = "spanish,yoruba"
        self.patient.save()
        
        # Test assignment (should prefer doctor1 or doctor3 who speak Spanish or Yoruba)
        assigned_doctor = doctor_assigner.assign_doctor(self.appointment_data)
        self.assertIsNotNone(assigned_doctor)
        self.assertIn(assigned_doctor, [self.doctor1, self.doctor3])
        
        # Create the appointment with the assigned doctor
        self.appointment_data['doctor'] = assigned_doctor
        appointment = Appointment.objects.create(**self.appointment_data)
        self.assertEqual(appointment.doctor, assigned_doctor)
    
    def test_preferred_language_priority(self):
        """Test that preferred language gets higher priority than secondary languages"""
        # Update patient with Spanish as preferred and French as secondary
        self.patient.preferred_language = "spanish"
        self.patient.secondary_languages = "french"
        self.patient.save()
        
        # Test assignment (should prefer doctor1 who speaks Spanish over doctor2 who speaks French)
        assigned_doctor = doctor_assigner.assign_doctor(self.appointment_data)
        self.assertIsNotNone(assigned_doctor)
        self.assertEqual(assigned_doctor, self.doctor1)
        
        # Create the appointment with the assigned doctor
        self.appointment_data['doctor'] = assigned_doctor
        appointment = Appointment.objects.create(**self.appointment_data)
        self.assertEqual(appointment.doctor, self.doctor1)
    
    def test_emergency_appointment_assignment(self):
        """Test doctor assignment for emergency appointments"""
        # Create an emergency appointment data
        appointment_data = {
            'patient': self.patient,
            'hospital': self.hospital,
            'department': self.department,
            'appointment_type': 'emergency',
            'priority': 'emergency',
            'appointment_date': timezone.now() + timedelta(days=1),
            'chief_complaint': 'Emergency heart condition',
            'status': 'confirmed'
        }
        
        # Get assigned doctor first
        assigned_doctor = doctor_assigner.assign_doctor(appointment_data)
        
        # Emergency appointments should get a doctor assigned
        self.assertIsNotNone(assigned_doctor)
        self.assertTrue(isinstance(assigned_doctor, Doctor))
        
        # Create appointment with the assigned doctor
        appointment_data['doctor'] = assigned_doctor
        appointment = Appointment.objects.create(**appointment_data)
        
        # Verify the appointment was created successfully
        self.assertEqual(appointment.doctor, assigned_doctor)
        self.assertEqual(appointment.priority, 'emergency')
    
    def test_no_available_doctors(self):
        """Test assignment when no doctors are available"""
        # Make all doctors inactive
        Doctor.objects.all().update(is_active=False)
        
        # Test assignment (should return None)
        assigned_doctor = doctor_assigner.assign_doctor(self.appointment_data)
        self.assertIsNone(assigned_doctor) 