from django.test import TestCase
from django.utils import timezone
from datetime import timedelta, date
from api.models.medical.medical_record import MedicalRecord, PatientDiagnosis, PatientTreatment, DoctorInteraction
from api.models.medical_staff.doctor import Doctor
from api.models.user.custom_user import CustomUser
from api.models.medical.department import Department
from api.models.medical.hospital import Hospital
from api.models.medical.appointment import Appointment
from api.models.medical.doctor_assignment import doctor_assigner
from api.models.medical.hospital_registration import HospitalRegistration

class TestMedicalRecordsData(TestCase):
    """Test case for creating realistic medical records data and testing doctor assignment"""
    
    def setUp(self):
        """Set up test data with hospitals, departments, doctors, and patients"""
        # Create a hospital
        self.hospital = Hospital.objects.create(
            name="General Hospital",
            address="123 Main St",
            city="Lagos",
            state="Lagos State",
            country="Nigeria",
            postal_code="100001",
            phone="1234567890",
            email="info@generalhospital.com",
            registration_number="GH001",
            hospital_type="general",
            bed_capacity=500
        )
        
        # Create departments
        self.cardiology_dept = Department.objects.create(
            name="Cardiology",
            code="CARD01",
            description="Heart and cardiovascular system",
            department_type="medical",
            hospital=self.hospital,
            floor_number="3",
            wing="east",
            extension_number="3001",
            emergency_contact="3000",
            email="cardiology@generalhospital.com",
            minimum_staff_required=5,
            current_staff_count=8,
            total_beds=30,
            occupied_beds=15,
            icu_beds=10,
            occupied_icu_beds=5,
            bed_capacity=40
        )
        
        self.endocrinology_dept = Department.objects.create(
            name="Endocrinology",
            code="ENDO01",
            description="Hormonal and metabolic disorders",
            department_type="medical",
            hospital=self.hospital,
            floor_number="4",
            wing="west",
            extension_number="4001",
            emergency_contact="4000",
            email="endocrinology@generalhospital.com",
            minimum_staff_required=3,
            current_staff_count=5,
            total_beds=20,
            occupied_beds=10,
            icu_beds=5,
            occupied_icu_beds=2,
            bed_capacity=25
        )
        
        self.neurology_dept = Department.objects.create(
            name="Neurology",
            code="NEUR01",
            description="Brain and nervous system",
            department_type="medical",
            hospital=self.hospital,
            floor_number="5",
            wing="north",
            extension_number="5001",
            emergency_contact="5000",
            email="neurology@generalhospital.com",
            minimum_staff_required=4,
            current_staff_count=6,
            total_beds=25,
            occupied_beds=12,
            icu_beds=8,
            occupied_icu_beds=3,
            bed_capacity=33
        )
        
        # Create doctor users
        self.cardio_doctor_user = CustomUser.objects.create(
            username="cardiodoc",
            email="cardio@example.com",
            first_name="John",
            last_name="Heart",
            role="doctor"
        )
        
        self.endo_doctor_user = CustomUser.objects.create(
            username="endodoc",
            email="endo@example.com",
            first_name="Emma",
            last_name="Diabetes",
            role="doctor"
        )
        
        self.neuro_doctor_user = CustomUser.objects.create(
            username="neurodoc",
            email="neuro@example.com",
            first_name="Nancy",
            last_name="Brain",
            role="doctor"
        )
        
        # Create doctor profiles with expertise codes
        self.cardio_doctor = Doctor.objects.create(
            user=self.cardio_doctor_user,
            department=self.cardiology_dept,
            hospital=self.hospital,
            specialization="Cardiology",
            medical_license_number="CARD123",
            license_expiry_date=date(2025, 12, 31),
            years_of_experience=15,
            languages_spoken="English,Yoruba",
            consultation_days="Mon,Tue,Wed,Thu,Fri",
            consultation_hours_start=timezone.now().time().replace(hour=8, minute=0),
            consultation_hours_end=timezone.now().time().replace(hour=16, minute=0),
            is_active=True,
            available_for_appointments=True,
            status='active',
            is_verified=True,
            expertise_codes=["I10", "I11", "I20", "I21", "I25", "I50"],
            primary_expertise_codes=["I21", "I25"],
            chronic_care_experience=True,
            complex_case_rating=8.5,
            continuity_of_care_rating=9.0
        )
        
        self.endo_doctor = Doctor.objects.create(
            user=self.endo_doctor_user,
            department=self.endocrinology_dept,
            hospital=self.hospital,
            specialization="Endocrinology",
            medical_license_number="ENDO456",
            license_expiry_date=date(2025, 12, 31),
            years_of_experience=10,
            languages_spoken="English,Hausa",
            consultation_days="Mon,Tue,Wed,Thu,Fri",
            consultation_hours_start=timezone.now().time().replace(hour=9, minute=0),
            consultation_hours_end=timezone.now().time().replace(hour=17, minute=0),
            is_active=True,
            available_for_appointments=True,
            status='active',
            is_verified=True,
            expertise_codes=["E10", "E11", "E14", "E21", "E05", "E06"],
            primary_expertise_codes=["E11", "E05"],
            chronic_care_experience=True,
            complex_case_rating=7.5,
            continuity_of_care_rating=8.0
        )
        
        self.neuro_doctor = Doctor.objects.create(
            user=self.neuro_doctor_user,
            department=self.neurology_dept,
            hospital=self.hospital,
            specialization="Neurology",
            medical_license_number="NEURO789",
            license_expiry_date=date(2025, 12, 31),
            years_of_experience=12,
            languages_spoken="English,Igbo,French",
            consultation_days="Mon,Tue,Wed,Thu,Fri",
            consultation_hours_start=timezone.now().time().replace(hour=10, minute=0),
            consultation_hours_end=timezone.now().time().replace(hour=18, minute=0),
            is_active=True,
            available_for_appointments=True,
            status='active',
            is_verified=True,
            expertise_codes=["G20", "G35", "G40", "G43", "G44", "G45", "G47"],
            primary_expertise_codes=["G40", "G43"],
            chronic_care_experience=True,
            complex_case_rating=9.0,
            continuity_of_care_rating=7.5
        )
        
        # Create patients
        self.patient1 = CustomUser.objects.create(
            username="patient1",
            email="patient1@example.com",
            first_name="Ade",
            last_name="Johnson",
            role="patient",
            gender="male",
            date_of_birth=date(1975, 5, 15),
            preferred_language="english"
        )
        
        self.patient2 = CustomUser.objects.create(
            username="patient2",
            email="patient2@example.com",
            first_name="Ngozi",
            last_name="Okafor",
            role="patient",
            gender="female",
            date_of_birth=date(1982, 8, 22),
            preferred_language="igbo",
            secondary_languages="english,french"
        )
        
        self.patient3 = CustomUser.objects.create(
            username="patient3",
            email="patient3@example.com",
            first_name="Mohammed",
            last_name="Ibrahim",
            role="patient",
            gender="male",
            date_of_birth=date(1968, 3, 10),
            preferred_language="hausa",
            secondary_languages="english"
        )
        
        # Register patients with hospital
        for patient in [self.patient1, self.patient2, self.patient3]:
            HospitalRegistration.objects.create(
                user=patient,
                hospital=self.hospital,
                status='approved',
                is_primary=True
            )
        
        # Delete any existing medical records for these patients to avoid IntegrityError
        MedicalRecord.objects.filter(user__in=[self.patient1, self.patient2, self.patient3]).delete()
        
        # Create medical records
        self.record1 = MedicalRecord.objects.create(
            user=self.patient1,
            hpn="HPN10001",
            blood_type="O+",
            allergies="Penicillin",
            chronic_conditions="Hypertension, Diabetes",
            is_high_risk=True,
            last_visit_date=timezone.now() - timedelta(days=30)
        )
        
        self.record2 = MedicalRecord.objects.create(
            user=self.patient2,
            hpn="HPN10002",
            blood_type="A-",
            allergies="None",
            chronic_conditions="Migraine",
            is_high_risk=False,
            last_visit_date=timezone.now() - timedelta(days=45)
        )
        
        self.record3 = MedicalRecord.objects.create(
            user=self.patient3,
            hpn="HPN10003",
            blood_type="B+",
            allergies="Sulfa drugs",
            chronic_conditions="Type 2 Diabetes",
            is_high_risk=True,
            last_visit_date=timezone.now() - timedelta(days=15)
        )
    
    def test_create_medical_data(self):
        """Create realistic medical data for patients and test doctor assignment"""
        # Add diagnoses for Patient 1 (Hypertension and Diabetes)
        diagnosis1_1 = PatientDiagnosis.objects.create(
            medical_record=self.record1,
            diagnosis_code="I10",
            diagnosis_name="Essential (primary) hypertension",
            diagnosis_date=timezone.now() - timedelta(days=365),
            diagnosed_by=self.cardio_doctor,
            is_chronic=True,
            is_active=True,
            severity_rating=3,
            notes="Patient has family history of hypertension"
        )
        
        diagnosis1_2 = PatientDiagnosis.objects.create(
            medical_record=self.record1,
            diagnosis_code="E11",
            diagnosis_name="Type 2 diabetes mellitus",
            diagnosis_date=timezone.now() - timedelta(days=300),
            diagnosed_by=self.endo_doctor,
            is_chronic=True,
            is_active=True,
            severity_rating=4,
            notes="Poor glycemic control, HbA1c: 8.5%"
        )
        
        diagnosis1_3 = PatientDiagnosis.objects.create(
            medical_record=self.record1,
            diagnosis_code="I25.1",
            diagnosis_name="Atherosclerotic heart disease",
            diagnosis_date=timezone.now() - timedelta(days=180),
            diagnosed_by=self.cardio_doctor,
            is_chronic=True,
            is_active=True,
            severity_rating=3,
            notes="Moderate coronary artery disease"
        )
        
        # Add treatments for Patient 1
        treatment1_1 = PatientTreatment.objects.create(
            medical_record=self.record1,
            treatment_type="medication",
            treatment_name="Lisinopril",
            treatment_code="ACE-I",
            prescribed_by=self.cardio_doctor,
            start_date=timezone.now() - timedelta(days=365),
            is_active=True,
            dosage="10mg",
            frequency="Once daily",
            notes="For hypertension"
        )
        
        treatment1_2 = PatientTreatment.objects.create(
            medical_record=self.record1,
            treatment_type="medication",
            treatment_name="Metformin",
            treatment_code="BIG",
            prescribed_by=self.endo_doctor,
            start_date=timezone.now() - timedelta(days=300),
            is_active=True,
            dosage="1000mg",
            frequency="Twice daily",
            notes="For diabetes"
        )
        
        treatment1_3 = PatientTreatment.objects.create(
            medical_record=self.record1,
            treatment_type="medication",
            treatment_name="Aspirin",
            treatment_code="ASA",
            prescribed_by=self.cardio_doctor,
            start_date=timezone.now() - timedelta(days=180),
            is_active=True,
            dosage="81mg",
            frequency="Once daily",
            notes="For heart disease"
        )
        
        # Add doctor interactions for Patient 1
        interaction1_1 = DoctorInteraction.objects.create(
            medical_record=self.record1,
            doctor=self.cardio_doctor,
            interaction_date=timezone.now() - timedelta(days=365),
            interaction_type="appointment",
            patient_rating=4,
            doctor_notes="Initial diagnosis of hypertension"
        )
        
        interaction1_2 = DoctorInteraction.objects.create(
            medical_record=self.record1,
            doctor=self.endo_doctor,
            interaction_date=timezone.now() - timedelta(days=300),
            interaction_type="appointment",
            patient_rating=5,
            doctor_notes="Initial diagnosis of diabetes"
        )
        
        interaction1_3 = DoctorInteraction.objects.create(
            medical_record=self.record1,
            doctor=self.cardio_doctor,
            interaction_date=timezone.now() - timedelta(days=180),
            interaction_type="appointment",
            patient_rating=4,
            doctor_notes="Diagnosis of coronary artery disease"
        )
        
        # Add diagnoses for Patient 2 (Migraine)
        diagnosis2_1 = PatientDiagnosis.objects.create(
            medical_record=self.record2,
            diagnosis_code="G43.9",
            diagnosis_name="Migraine, unspecified",
            diagnosis_date=timezone.now() - timedelta(days=400),
            diagnosed_by=self.neuro_doctor,
            is_chronic=True,
            is_active=True,
            severity_rating=3,
            notes="Frequent episodes, 2-3 times per month"
        )
        
        diagnosis2_2 = PatientDiagnosis.objects.create(
            medical_record=self.record2,
            diagnosis_code="G44.2",
            diagnosis_name="Tension-type headache",
            diagnosis_date=timezone.now() - timedelta(days=400),
            diagnosed_by=self.neuro_doctor,
            is_chronic=False,
            is_active=True,
            severity_rating=2,
            notes="Often co-occurs with migraines"
        )
        
        # Add treatments for Patient 2
        treatment2_1 = PatientTreatment.objects.create(
            medical_record=self.record2,
            treatment_type="medication",
            treatment_name="Sumatriptan",
            treatment_code="TRIP",
            prescribed_by=self.neuro_doctor,
            start_date=timezone.now() - timedelta(days=400),
            is_active=True,
            dosage="50mg",
            frequency="As needed for migraine",
            notes="Take at first sign of migraine"
        )
        
        treatment2_2 = PatientTreatment.objects.create(
            medical_record=self.record2,
            treatment_type="medication",
            treatment_name="Propranolol",
            treatment_code="BB",
            prescribed_by=self.neuro_doctor,
            start_date=timezone.now() - timedelta(days=350),
            is_active=True,
            dosage="40mg",
            frequency="Twice daily",
            notes="For migraine prevention"
        )
        
        treatment2_3 = PatientTreatment.objects.create(
            medical_record=self.record2,
            treatment_type="therapy",
            treatment_name="Biofeedback",
            prescribed_by=self.neuro_doctor,
            start_date=timezone.now() - timedelta(days=300),
            is_active=True,
            notes="Non-pharmacological approach to migraine management"
        )
        
        # Add doctor interactions for Patient 2
        interaction2_1 = DoctorInteraction.objects.create(
            medical_record=self.record2,
            doctor=self.neuro_doctor,
            interaction_date=timezone.now() - timedelta(days=400),
            interaction_type="appointment",
            patient_rating=5,
            doctor_notes="Initial diagnosis of migraine"
        )
        
        interaction2_2 = DoctorInteraction.objects.create(
            medical_record=self.record2,
            doctor=self.neuro_doctor,
            interaction_date=timezone.now() - timedelta(days=350),
            interaction_type="follow_up",
            patient_rating=4,
            doctor_notes="Started preventive medication"
        )
        
        interaction2_3 = DoctorInteraction.objects.create(
            medical_record=self.record2,
            doctor=self.neuro_doctor,
            interaction_date=timezone.now() - timedelta(days=300),
            interaction_type="follow_up",
            patient_rating=5,
            doctor_notes="Added biofeedback therapy"
        )
        
        # Add diagnoses for Patient 3 (Diabetes)
        diagnosis3_1 = PatientDiagnosis.objects.create(
            medical_record=self.record3,
            diagnosis_code="E11.9",
            diagnosis_name="Type 2 diabetes mellitus without complications",
            diagnosis_date=timezone.now() - timedelta(days=500),
            diagnosed_by=self.endo_doctor,
            is_chronic=True,
            is_active=True,
            severity_rating=3,
            notes="Family history of diabetes"
        )
        
        diagnosis3_2 = PatientDiagnosis.objects.create(
            medical_record=self.record3,
            diagnosis_code="E11.2",
            diagnosis_name="Type 2 diabetes mellitus with kidney complications",
            diagnosis_date=timezone.now() - timedelta(days=200),
            diagnosed_by=self.endo_doctor,
            is_chronic=True,
            is_active=True,
            severity_rating=4,
            notes="Early signs of diabetic nephropathy"
        )
        
        # Add treatments for Patient 3
        treatment3_1 = PatientTreatment.objects.create(
            medical_record=self.record3,
            treatment_type="medication",
            treatment_name="Metformin",
            treatment_code="BIG",
            prescribed_by=self.endo_doctor,
            start_date=timezone.now() - timedelta(days=500),
            is_active=True,
            dosage="1000mg",
            frequency="Twice daily",
            notes="For diabetes"
        )
        
        treatment3_2 = PatientTreatment.objects.create(
            medical_record=self.record3,
            treatment_type="medication",
            treatment_name="Glimepiride",
            treatment_code="SU",
            prescribed_by=self.endo_doctor,
            start_date=timezone.now() - timedelta(days=400),
            is_active=True,
            dosage="2mg",
            frequency="Once daily",
            notes="Added as second agent for diabetes"
        )
        
        treatment3_3 = PatientTreatment.objects.create(
            medical_record=self.record3,
            treatment_type="medication",
            treatment_name="Lisinopril",
            treatment_code="ACE-I",
            prescribed_by=self.endo_doctor,
            start_date=timezone.now() - timedelta(days=200),
            is_active=True,
            dosage="5mg",
            frequency="Once daily",
            notes="For kidney protection"
        )
        
        # Add doctor interactions for Patient 3
        interaction3_1 = DoctorInteraction.objects.create(
            medical_record=self.record3,
            doctor=self.endo_doctor,
            interaction_date=timezone.now() - timedelta(days=500),
            interaction_type="appointment",
            patient_rating=4,
            doctor_notes="Initial diagnosis of diabetes"
        )
        
        interaction3_2 = DoctorInteraction.objects.create(
            medical_record=self.record3,
            doctor=self.endo_doctor,
            interaction_date=timezone.now() - timedelta(days=400),
            interaction_type="follow_up",
            patient_rating=3,
            doctor_notes="Added second medication"
        )
        
        interaction3_3 = DoctorInteraction.objects.create(
            medical_record=self.record3,
            doctor=self.endo_doctor,
            interaction_date=timezone.now() - timedelta(days=200),
            interaction_type="follow_up",
            patient_rating=4,
            doctor_notes="Diagnosed kidney complications"
        )
        
        # Update complexity metrics for all patients
        self.record1.update_complexity_metrics()
        self.record2.update_complexity_metrics()
        self.record3.update_complexity_metrics()
        
        # Print medical record statistics
        print("\n📊 Medical Record Statistics:")
        print(f"Patient 1 (HPN: {self.record1.hpn}):")
        print(f"  - Comorbidity count: {self.record1.comorbidity_count}")
        print(f"  - Medication count: {self.record1.medication_count}")
        print(f"  - Care plan complexity: {self.record1.care_plan_complexity}")
        
        print(f"\nPatient 2 (HPN: {self.record2.hpn}):")
        print(f"  - Comorbidity count: {self.record2.comorbidity_count}")
        print(f"  - Medication count: {self.record2.medication_count}")
        print(f"  - Care plan complexity: {self.record2.care_plan_complexity}")
        
        print(f"\nPatient 3 (HPN: {self.record3.hpn}):")
        print(f"  - Comorbidity count: {self.record3.comorbidity_count}")
        print(f"  - Medication count: {self.record3.medication_count}")
        print(f"  - Care plan complexity: {self.record3.care_plan_complexity}")
        
        # Test doctor assignment for each patient
        self._test_doctor_assignment(self.patient1, "Patient with hypertension and diabetes")
        self._test_doctor_assignment(self.patient2, "Patient with migraine")
        self._test_doctor_assignment(self.patient3, "Patient with diabetes and kidney complications")
    
    def test_continuity_of_care(self):
        """Test continuity of care in doctor assignment by creating past appointments"""
        # First create all the medical data
        self.test_create_medical_data()
        
        # Generate unique appointment IDs
        appointment_id1 = Appointment.generate_appointment_id()
        appointment_id2 = Appointment.generate_appointment_id()
        appointment_id3 = Appointment.generate_appointment_id()
        
        # Get consultation hours for each doctor
        cardio_start_time = self.cardio_doctor.consultation_hours_start
        cardio_end_time = self.cardio_doctor.consultation_hours_end
        endo_start_time = self.endo_doctor.consultation_hours_start
        endo_end_time = self.endo_doctor.consultation_hours_end
        
        # Helper function to ensure date is a weekday (Monday-Friday)
        def ensure_weekday(date_obj):
            # If it's Saturday (5) or Sunday (6), move to Monday
            if date_obj.weekday() >= 5:
                days_to_add = 7 - date_obj.weekday()  # Days until Monday
                return date_obj + timedelta(days=days_to_add)
            return date_obj
        
        # Create past appointment dates within consultation hours
        # For cardio doctor (8:00 - 16:00)
        cardio_past_date = timezone.now() - timedelta(days=60)
        cardio_past_date = cardio_past_date.replace(
            hour=cardio_start_time.hour + 1,  # 1 hour after start time
            minute=0, 
            second=0, 
            microsecond=0
        )
        cardio_past_date = ensure_weekday(cardio_past_date)
        
        # For endo doctor (9:00 - 17:00)
        endo_past_date = timezone.now() - timedelta(days=60)
        endo_past_date = endo_past_date.replace(
            hour=endo_start_time.hour + 1,  # 1 hour after start time
            minute=0, 
            second=0, 
            microsecond=0
        )
        endo_past_date = ensure_weekday(endo_past_date)
        
        # Create past appointments for Patient 1 with Cardiology
        past_appointment1 = Appointment.objects.create(
            appointment_id=appointment_id1,
            patient=self.patient1,
            hospital=self.hospital,
            department=self.cardiology_dept,
            doctor=self.cardio_doctor,
            appointment_type='follow_up',
            priority='normal',
            status='completed',
            appointment_date=cardio_past_date,
            duration=30,
            chief_complaint="Chest pain and shortness of breath",
            completed_at=cardio_past_date
        )
        
        # Create past appointments for Patient 2 with Cardiology
        # Make sure it's on a weekday
        cardio_past_date2 = ensure_weekday(cardio_past_date + timedelta(days=15))
        past_appointment2 = Appointment.objects.create(
            appointment_id=appointment_id2,
            patient=self.patient2,
            hospital=self.hospital,
            department=self.cardiology_dept,  # Intentionally using cardiology
            doctor=self.cardio_doctor,        # Using cardio doctor instead of neuro
            appointment_type='follow_up',
            priority='normal',
            status='completed',
            appointment_date=cardio_past_date2,
            duration=30,
            chief_complaint="Headache consultation",
            completed_at=cardio_past_date2
        )
        
        # Create multiple past appointments for Patient 3 with Endocrinology
        # This should result in a strong continuity score
        for i, days_ago in enumerate([90, 60, 30]):
            appointment_id = Appointment.generate_appointment_id()
            # Ensure it's a weekday
            appointment_date = ensure_weekday(endo_past_date + timedelta(days=30-days_ago))
            past_appointment3 = Appointment.objects.create(
                appointment_id=appointment_id,
                patient=self.patient3,
                hospital=self.hospital,
                department=self.endocrinology_dept,
                doctor=self.endo_doctor,
                appointment_type='follow_up',
                priority='normal',
                status='completed',
                appointment_date=appointment_date,
                duration=30,
                chief_complaint="Diabetes follow-up",
                completed_at=appointment_date
            )
        
        print("\n🔄 Testing Continuity of Care:")
        
        # Create future appointment dates within consultation hours
        # For testing doctor assignment
        future_cardio_date = timezone.now() + timedelta(days=7)
        future_cardio_date = future_cardio_date.replace(
            hour=cardio_start_time.hour + 1,
            minute=0, 
            second=0, 
            microsecond=0
        )
        future_cardio_date = ensure_weekday(future_cardio_date)
        
        future_endo_date = timezone.now() + timedelta(days=7)
        future_endo_date = future_endo_date.replace(
            hour=endo_start_time.hour + 1,
            minute=0, 
            second=0, 
            microsecond=0
        )
        future_endo_date = ensure_weekday(future_endo_date)
        
        # Test assignment for Patient 1 in Cardiology (should prefer cardio_doctor due to continuity)
        appointment_data1 = {
            'patient': self.patient1,
            'department': self.cardiology_dept,
            'hospital': self.hospital,
            'appointment_type': 'regular',
            'appointment_date': future_cardio_date
        }
        
        assigned_doctor1 = doctor_assigner.assign_doctor(appointment_data1)
        print(f"\nPatient 1 (Cardiology): Assigned to {assigned_doctor1.user.get_full_name()}")
        
        # Test assignment for Patient 2 in Cardiology (should prefer cardio_doctor due to continuity)
        appointment_data2 = {
            'patient': self.patient2,
            'department': self.cardiology_dept,
            'hospital': self.hospital,
            'appointment_type': 'regular',
            'appointment_date': future_cardio_date
        }
        
        assigned_doctor2 = doctor_assigner.assign_doctor(appointment_data2)
        print(f"Patient 2 (Cardiology): Assigned to {assigned_doctor2.user.get_full_name()}")
        
        # Test assignment for Patient 3 in Endocrinology (should strongly prefer endo_doctor)
        appointment_data3 = {
            'patient': self.patient3,
            'department': self.endocrinology_dept,
            'hospital': self.hospital,
            'appointment_type': 'regular',
            'appointment_date': future_endo_date
        }
        
        assigned_doctor3 = doctor_assigner.assign_doctor(appointment_data3)
        print(f"Patient 3 (Endocrinology): Assigned to {assigned_doctor3.user.get_full_name()}")
        
        # Test if continuity overrides specialty match
        # Patient 1 has diabetes (E11) which matches endo_doctor's expertise
        # But has continuity with cardio_doctor
        # Let's see which factor wins in Endocrinology department
        appointment_data4 = {
            'patient': self.patient1,
            'department': self.endocrinology_dept,
            'hospital': self.hospital,
            'appointment_type': 'regular',
            'appointment_date': future_endo_date
        }
        
        assigned_doctor4 = doctor_assigner.assign_doctor(appointment_data4)
        print(f"Patient 1 (Endocrinology - Continuity vs Specialty): Assigned to {assigned_doctor4.user.get_full_name()}")
        
        # Verify our expectations
        self.assertEqual(assigned_doctor1, self.cardio_doctor, "Patient 1 should be assigned to cardio_doctor due to continuity")
        self.assertEqual(assigned_doctor2, self.cardio_doctor, "Patient 2 should be assigned to cardio_doctor due to continuity")
        self.assertEqual(assigned_doctor3, self.endo_doctor, "Patient 3 should be assigned to endo_doctor due to strong continuity")
    
    def _test_doctor_assignment(self, patient, description):
        """Test doctor assignment for a patient and print results"""
        # Create appointment data
        appointment_date = timezone.now() + timedelta(days=7)
        appointment_date = appointment_date.replace(hour=10, minute=0, second=0, microsecond=0)
        
        # Test assignment for each department
        departments = [self.cardiology_dept, self.endocrinology_dept, self.neurology_dept]
        
        print(f"\n🧪 Testing doctor assignment for {description} ({patient.get_full_name()}):")
        
        for department in departments:
            appointment_data = {
                'patient': patient,
                'department': department,
                'hospital': self.hospital,
                'appointment_type': 'regular',
                'appointment_date': appointment_date
            }
            
            # Assign doctor
            assigned_doctor = doctor_assigner.assign_doctor(appointment_data)
            
            if assigned_doctor:
                print(f"  - For {department.name} department: Assigned to {assigned_doctor.user.get_full_name()}")
            else:
                print(f"  - For {department.name} department: No doctor assigned")
        
        # Test emergency assignment
        emergency_data = {
            'patient': patient,
            'department': self.cardiology_dept,  # Use cardiology for emergency
            'hospital': self.hospital,
            'appointment_type': 'emergency',
            'appointment_date': timezone.now()  # Immediate appointment
        }
        
        emergency_doctor = doctor_assigner.assign_doctor(emergency_data)
        if emergency_doctor:
            print(f"  - For emergency: Assigned to {emergency_doctor.user.get_full_name()}")
        else:
            print(f"  - For emergency: No doctor assigned") 