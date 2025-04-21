from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta, date, time, datetime
from django.db import IntegrityError
from django.contrib.auth.hashers import make_password
import random

# Import necessary models
from api.models.medical.medical_record import MedicalRecord, PatientDiagnosis, PatientTreatment, DoctorInteraction
from api.models.medical_staff.doctor import Doctor
from api.models.user.custom_user import CustomUser
from api.models.medical.department import Department
from api.models.medical.hospital import Hospital
from api.models.medical.appointment import Appointment
from api.models.medical.appointment_fee import AppointmentFee
from api.models.medical.doctor_assignment import doctor_assigner
from api.models.medical.hospital_registration import HospitalRegistration
from django.db import transaction

class Command(BaseCommand):
    help = 'Evaluates the performance of the current doctor assignment model against defined scenarios.'

    # --- Data Setup --- 
    @transaction.atomic
    def setup_test_data(self):
        """Sets up the necessary hospital, departments, doctors, fees.
           Uses atomic transaction to ensure data integrity or rollback."""
        self.stdout.write(self.style.HTTP_INFO("Setting up test data..."))

        # Use specific identifiers to avoid conflicts and allow cleanup
        eval_hospital_reg = "EVALH001"
        eval_dept_codes = {
            'cardio': "EVALCARD01",
            'endo': "EVALENDO01",
            'neuro': "EVALNEUR01",
            'genmed': "EVALGENM01"
        }
        eval_doctor_users = {
            'cardio': 'eval_cardiodoc',
            'endo': 'eval_endodoc',
            'neuro': 'eval_neurodoc',
            'gen': 'eval_gendoc'
        }

        # --- Create Hospital ---
        self.hospital, _ = Hospital.objects.get_or_create(
            registration_number=eval_hospital_reg,
            defaults={
                'name': "Evaluation Hospital", 'address': "456 Eval St", 'city': "Testville",
                'state': "Test State", 'country': "Testland", 'postal_code': "EVAL01",
                'phone': "9876543210", 'email': "info@evalhospital.com",
                'hospital_type': "general", 'bed_capacity': 200
            }
        )

        # --- Create Departments ---
        self.cardiology_dept, _ = Department.objects.get_or_create(hospital=self.hospital, code=eval_dept_codes['cardio'], defaults={'name': "CardiologyEval", 'bed_capacity': 20, 'minimum_staff_required': 1, 'current_staff_count': 1})
        self.endo_dept, _ = Department.objects.get_or_create(hospital=self.hospital, code=eval_dept_codes['endo'], defaults={'name': "EndocrinologyEval", 'bed_capacity': 15, 'minimum_staff_required': 1, 'current_staff_count': 1})
        self.neuro_dept, _ = Department.objects.get_or_create(hospital=self.hospital, code=eval_dept_codes['neuro'], defaults={'name': "NeurologyEval", 'bed_capacity': 18, 'minimum_staff_required': 1, 'current_staff_count': 1})
        self.genmed_dept, _ = Department.objects.get_or_create(hospital=self.hospital, code=eval_dept_codes['genmed'], defaults={'name': "GeneralMedicineEval", 'bed_capacity': 30, 'minimum_staff_required': 1, 'current_staff_count': 1})

        # --- Create Doctors --- 
        # Doctor 1: Cardiologist
        user1, _ = CustomUser.objects.get_or_create(email='evalcardio@example.com', defaults={'username': eval_doctor_users['cardio'], 'first_name': 'Eva', 'last_name': 'Cardio', 'role': 'doctor'})
        self.cardio_doc, _ = Doctor.objects.update_or_create(
            user=user1, hospital=self.hospital, 
            defaults={
                'department': self.cardiology_dept,
                'specialization': "Cardiology", 'medical_license_number': "EVCARD1", 'license_expiry_date': date(2026, 1, 1),
                'years_of_experience': 12, 'languages_spoken': "English,Spanish", 'consultation_days': "Mon,Wed,Fri",
                'consultation_hours_start': time(9, 0), 'consultation_hours_end': time(17, 0), 'is_verified': True, 'is_active': True, 'status': 'active',
                'expertise_codes': ["I10", "I20", "I25", "I50"], 'primary_expertise_codes': ["I25"],
                'chronic_care_experience': True, 'complex_case_rating': 8.0, 'continuity_of_care_rating': 8.5
            }
        )
        # Doctor 2: Endocrinologist
        user2, _ = CustomUser.objects.get_or_create(email='evalendo@example.com', defaults={'username': eval_doctor_users['endo'], 'first_name': 'Evan', 'last_name': 'Endo', 'role': 'doctor'})
        self.endo_doc, _ = Doctor.objects.update_or_create(
            user=user2, hospital=self.hospital, 
            defaults={
                'department': self.endo_dept,
                'specialization': "Endocrinology", 'medical_license_number': "EVENDO1", 'license_expiry_date': date(2026, 1, 1),
                'years_of_experience': 8, 'languages_spoken': "English", 'consultation_days': "Tue,Thu",
                'consultation_hours_start': time(8, 30), 'consultation_hours_end': time(16, 30), 'is_verified': True, 'is_active': True, 'status': 'active',
                'expertise_codes': ["E10", "E11", "E05", "E06"], 'primary_expertise_codes': ["E11"],
                'chronic_care_experience': True, 'complex_case_rating': 7.0, 'continuity_of_care_rating': 7.5
            }
        )
        # Doctor 3: Neurologist
        user3, _ = CustomUser.objects.get_or_create(email='evalneuro@example.com', defaults={'username': eval_doctor_users['neuro'], 'first_name': 'Eve', 'last_name': 'Neuro', 'role': 'doctor'})
        self.neuro_doc, _ = Doctor.objects.update_or_create(
            user=user3, hospital=self.hospital, 
            defaults={
                'department': self.neuro_dept,
                'specialization': "Neurology", 'medical_license_number': "EVNEUR1", 'license_expiry_date': date(2026, 1, 1),
                'years_of_experience': 15, 'languages_spoken': "English,French", 'consultation_days': "Mon,Tue,Wed,Thu,Fri",
                'consultation_hours_start': time(10, 0), 'consultation_hours_end': time(18, 0), 'is_verified': True, 'is_active': True, 'status': 'active',
                'expertise_codes': ["G20", "G35", "G40", "G43"], 'primary_expertise_codes': ["G40", "G43"],
                'chronic_care_experience': False, 'complex_case_rating': 9.0, 'continuity_of_care_rating': 7.0
            }
        )
        # Doctor 4: General Medicine
        user4, _ = CustomUser.objects.get_or_create(email='evalgen@example.com', defaults={'username': eval_doctor_users['gen'], 'first_name': 'Gene', 'last_name': 'Ral', 'role': 'doctor'})
        self.gen_doc, _ = Doctor.objects.update_or_create(
            user=user4, hospital=self.hospital, 
            defaults={
                'department': self.genmed_dept,
                'specialization': "General Medicine", 'medical_license_number': "EVGEN1", 'license_expiry_date': date(2026, 1, 1),
                'years_of_experience': 5, 'languages_spoken': "English", 'consultation_days': "Mon,Tue,Wed,Thu,Fri",
                'consultation_hours_start': time(8, 0), 'consultation_hours_end': time(17, 0), 'is_verified': True, 'is_active': True, 'status': 'active',
                'expertise_codes': ["R51", "J06", "Z00"], 'primary_expertise_codes': [],
                'chronic_care_experience': False, 'complex_case_rating': 6.0, 'continuity_of_care_rating': 6.5
            }
        )

        # --- Create Fees ---
        self.cardio_fee, _ = AppointmentFee.objects.get_or_create(doctor=self.cardio_doc, defaults={'hospital': self.hospital, 'department': self.cardiology_dept, 'fee_type': 'consultation', 'base_fee': 100, 'valid_from': timezone.now().date()})
        self.endo_fee, _ = AppointmentFee.objects.get_or_create(doctor=self.endo_doc, defaults={'hospital': self.hospital, 'department': self.endo_dept, 'fee_type': 'consultation', 'base_fee': 100, 'valid_from': timezone.now().date()})
        self.neuro_fee, _ = AppointmentFee.objects.get_or_create(doctor=self.neuro_doc, defaults={'hospital': self.hospital, 'department': self.neuro_dept, 'fee_type': 'consultation', 'base_fee': 100, 'valid_from': timezone.now().date()})
        self.gen_fee, _ = AppointmentFee.objects.get_or_create(doctor=self.gen_doc, defaults={'hospital': self.hospital, 'department': self.genmed_dept, 'fee_type': 'consultation', 'base_fee': 80, 'valid_from': timezone.now().date()})

        self.stdout.write(self.style.SUCCESS("Test data setup complete."))

    # --- Scenario Creation --- 
    @transaction.atomic
    def create_patient_scenario(self, username_suffix, first_name, last_name, dob, diagnoses_data, past_interactions=None, preferred_language='english', secondary_languages=None):
        """Creates/Updates a patient, registers, creates/updates medical record and diagnoses.
           Uses atomic transaction."""
        if past_interactions is None:
            past_interactions = []
        
        username_base = f'eval_{username_suffix}' 
        # Ensure unique email for evaluation runs
        timestamp = timezone.now().strftime('%Y%m%d%H%M%S%f') 
        email = f'{username_base}_{timestamp}@example.com' 
        # Ensure unique username as well to avoid DB constraint errors on re-runs
        username = f'{username_base}_{timestamp}' 
        user_defaults = {
            'username': username, # Use the unique, timestamped username
            'first_name': first_name, 'last_name': last_name, 
            'role': 'patient', 'date_of_birth': dob, 'preferred_language': preferred_language,
            'secondary_languages': secondary_languages
        }
        
        # Use email as the lookup key for update_or_create
        patient_user, created = CustomUser.objects.update_or_create(
            email=email,
            defaults=user_defaults
        )

        if not patient_user: # Check if creation failed and returned None
            return None
            
        HospitalRegistration.objects.get_or_create(
            user=patient_user, hospital=self.hospital, defaults={'status': 'approved', 'is_primary': True}
        )
        
        # Get or create medical record, then clear related data before adding new scenario data
        medical_record, created = MedicalRecord.objects.get_or_create(
            user=patient_user,
            defaults={'hpn': f"EVAL{username_suffix.upper()}", 'blood_type': "O+", 'last_visit_date': timezone.now().date()}
        )
        medical_record.diagnoses.all().delete()
        medical_record.doctor_interactions.all().delete()
            
        for dx_code, dx_name, is_chronic, severity, doc_attr in diagnoses_data:
            # Find the doctor object based on the attribute name string (e.g., 'cardio_doc')
            diagnosing_doctor = getattr(self, doc_attr, None)
            if not diagnosing_doctor:
                 self.stderr.write(self.style.ERROR(f"Doctor attribute '{doc_attr}' not found for diagnosis '{dx_name}' in scenario {username_suffix}"))
                 continue
            PatientDiagnosis.objects.create(
                medical_record=medical_record,
                diagnosis_code=dx_code, diagnosis_name=dx_name,
                diagnosis_date=timezone.now() - timedelta(days=90),
                diagnosed_by=diagnosing_doctor,
                is_chronic=is_chronic, is_active=True, severity_rating=severity
            )
            
        for doc_attr, days_ago in past_interactions:
             # Find the doctor object based on the attribute name string
             interaction_doctor = getattr(self, doc_attr, None)
             if not interaction_doctor:
                 self.stderr.write(self.style.ERROR(f"Doctor attribute '{doc_attr}' not found for past interaction in scenario {username_suffix}"))
                 continue
             DoctorInteraction.objects.create(
                 medical_record=medical_record,
                 doctor=interaction_doctor,
                 interaction_date=timezone.now() - timedelta(days=days_ago),
                 interaction_type="appointment"
             )
             
        medical_record.update_complexity_metrics() # Update based on new data
        return patient_user

    # --- Evaluation Logic --- 
    def find_next_available_slot(self, doctor, start_date):
        """Finds the next available date/time slot for a doctor starting from start_date."""
        consult_days = [d.strip().lower() for d in doctor.consultation_days.split(',')] 
        day_map = {'mon': 0, 'tue': 1, 'wed': 2, 'thu': 3, 'fri': 4, 'sat': 5, 'sun': 6}
        allowed_weekdays = {day_map[d] for d in consult_days if d in day_map}
        
        current_date = start_date
        while True:
            if current_date.weekday() in allowed_weekdays:
                # Check time within consultation hours (use middle of the day)
                start_hour = doctor.consultation_hours_start.hour
                end_hour = doctor.consultation_hours_end.hour
                target_hour = start_hour + max(1, (end_hour - start_hour) // 2) # Ensure at least 1 hour offset if needed
                
                # Check if target hour is valid
                if start_hour <= target_hour < end_hour:
                    # Combine date and time, then replace parts if necessary (though unlikely needed here)
                    # Use datetime.combine to create a datetime object
                    appointment_datetime = datetime.combine(current_date, time(hour=target_hour, minute=0, second=0, microsecond=0))
                    
                    # Make the datetime timezone-aware if needed (assuming settings.TIME_ZONE)
                    # This depends on how appointment dates are stored and compared.
                    # If they need to be timezone-aware, uncomment the following:
                    # from django.conf import settings
                    # import pytz
                    # current_tz = pytz.timezone(settings.TIME_ZONE)
                    # appointment_datetime = current_tz.localize(appointment_datetime)

                    # TODO: Ideally, check actual appointment clashes here if needed for accuracy
                    return appointment_datetime # Return the datetime object
                    
            current_date += timedelta(days=1)
            if (current_date - start_date).days > 30: # Avoid infinite loop, search max 30 days
                return None 

    def run_evaluation(self, scenarios):
        """Runs the evaluation for a list of scenarios."""
        results = {'correct': 0, 'incorrect': 0, 'no_assignment_correct': 0, 'no_assignment_incorrect': 0, 'details': []}
        total_scenarios = len(scenarios)

        for i, scenario in enumerate(scenarios):
            self.stdout.write(f"\nRunning scenario {i+1}/{total_scenarios}: {scenario['description']}")
            patient = scenario['patient']
            department = scenario['department']
            expected_doctor_obj = scenario['expected_doctor'] # Actual Doctor object or None
            appointment_type = scenario.get('appointment_type', 'regular')
            appointment_date = scenario.get('appointment_date')
            
            # Find a suitable appointment date if not provided
            if not appointment_date:
                # Try finding slot for expected doctor first, fallback to general doc
                target_doc_for_slot = expected_doctor_obj or self.gen_doc 
                appointment_date = self.find_next_available_slot(target_doc_for_slot, timezone.now().date() + timedelta(days=1))
            
            if not appointment_date:
                self.stdout.write(self.style.WARNING(" -> Could not find available slot for scenario, skipping assignment."))
                expected_outcome = "None (No Slot)"
                assigned_outcome = "None (No Slot)"
                result_status = "Skipped"
                 # Consider how to score skipped scenarios if needed
            else:
                self.stdout.write(f"   Using appointment date: {appointment_date.strftime('%Y-%m-%d %H:%M')}")
                appointment_data = {
                    'patient': patient,
                    'department': department,
                    'hospital': self.hospital,
                    'appointment_type': appointment_type,
                    'appointment_date': appointment_date,
                }
                
                assigned_doctor_obj = doctor_assigner.assign_doctor(appointment_data)
                
                expected_outcome = expected_doctor_obj.user.username if expected_doctor_obj else "None"
                assigned_outcome = assigned_doctor_obj.user.username if assigned_doctor_obj else "None"
                
                # Determine status
                if assigned_doctor_obj == expected_doctor_obj: # Covers both obj=obj and None=None
                    results['correct'] += 1
                    result_status = "Correct"
                    if expected_doctor_obj is None:
                        results['no_assignment_correct'] += 1
                        result_status = "Correct (No Assignment)"
                else:
                    results['incorrect'] += 1
                    result_status = "Incorrect"
                    if assigned_doctor_obj is None:
                         results['no_assignment_incorrect'] += 1
                         result_status = "Incorrect (No Assignment Made)"
            
            results['details'].append({
                'scenario': scenario['description'],
                'patient': patient.username,
                'department': department.name,
                'expected': expected_outcome,
                'assigned': assigned_outcome,
                'status': result_status
            })
            self.stdout.write(f" -> Expected: {expected_outcome}, Assigned: {assigned_outcome} ({result_status})")

        return results

    # --- Command Handler --- 
    def handle(self, *args, **options):
        self.setup_test_data()

        # --- Define Patients for Scenarios --- 
        self.stdout.write(self.style.HTTP_INFO("\nCreating patient scenarios..."))
        
        # Group 1: Standard Cases
        patient_std_cardio = self.create_patient_scenario('std_cardio', 'Std', 'Cardio', date(1970, 1, 1), [("I10", "Hypertension", True, 3, 'cardio_doc')])
        patient_std_endo = self.create_patient_scenario('std_endo', 'Std', 'Endo', date(1980, 1, 1), [("E11", "Type 2 Diabetes", True, 4, 'endo_doc')])
        patient_std_neuro = self.create_patient_scenario('std_neuro', 'Std', 'Neuro', date(1990, 1, 1), [("G43", "Migraine", True, 3, 'neuro_doc')])
        patient_std_gen = self.create_patient_scenario('std_gen', 'Std', 'Gen', date(1985, 1, 1), [("R51", "Headache", False, 1, 'gen_doc')])
        
        # Group 2: Continuity Cases
        patient_cont_cardio = self.create_patient_scenario('cont_cardio', 'Cont', 'Cardio', date(1972, 1, 1), 
                                                        [("I25", "Chronic ischemic heart disease", True, 4, 'cardio_doc')], 
                                                        past_interactions=[('cardio_doc', 30), ('cardio_doc', 90)])
        patient_cont_endo = self.create_patient_scenario('cont_endo', 'Cont', 'Endo', date(1965, 1, 1),
                                                       [("E05", "Hyperthyroidism", True, 3, 'endo_doc')], 
                                                       past_interactions=[('endo_doc', 60)])
        patient_mixed_cont = self.create_patient_scenario('mixed_cont', 'Mixed', 'Cont', date(1975, 1, 1), 
                                                        [("I10", "Hypertension", True, 3, 'cardio_doc'), ("E11", "Diabetes", True, 3, 'endo_doc')],
                                                        past_interactions=[('cardio_doc', 45)]) # Seen cardio recently

        # Group 3: Stress Test / Different Data
        patient_complex_multi = self.create_patient_scenario('complex_multi', 'Complex', 'Multi', date(1960, 1, 1), 
                                                          [ ("I50", "Heart Failure", True, 5, 'cardio_doc'),
                                                            ("E11", "Diabetes", True, 4, 'endo_doc'),
                                                            ("G20", "Parkinson's disease", True, 4, 'neuro_doc') ])
                                                            
        # Patient with no medical record (created user, ensured no record)
        # Delete existing user first to guarantee clean state for this specific eval user
        # Use email for deletion as it's the unique identifier
        norecord_email_pattern = 'eval_norecord_*.example.com' # Pattern might be too broad, be careful
        # A safer approach might be to generate the expected email if predictable, or store it.
        # For now, let's assume deletion by username is still okay if username remains unique per eval type
        # Reverting delete logic back to username as emails are timestamped and unpredictable
        CustomUser.objects.filter(username='eval_norecord').delete()
        patient_no_record, _ = CustomUser.objects.update_or_create(
            email=f'eval_norecord_{timezone.now().strftime("%Y%m%d%H%M%S%f")}@example.com', 
            defaults={'username': 'eval_norecord', 'first_name': 'No', 'last_name': 'Record', 'role': 'patient', 'date_of_birth': date(2000,1,1)}
        )
        HospitalRegistration.objects.get_or_create(user=patient_no_record, hospital=self.hospital, defaults={'status': 'approved', 'is_primary': True})
        MedicalRecord.objects.filter(user=patient_no_record).delete()
        
        # Patient with rare language
        # Delete existing user first by username
        CustomUser.objects.filter(username='eval_rarelang').delete()
        patient_rare_lang, _ = CustomUser.objects.update_or_create(
            email=f'eval_rarelang_{timezone.now().strftime("%Y%m%d%H%M%S%f")}@example.com', 
            defaults={'username': 'eval_rarelang', 'first_name': 'Rare', 'last_name': 'Lang', 'role': 'patient', 'date_of_birth': date(1995,1,1), 'preferred_language': 'klingon'}
        )
        HospitalRegistration.objects.get_or_create(user=patient_rare_lang, hospital=self.hospital, defaults={'status': 'approved', 'is_primary': True})
        MedicalRecord.objects.get_or_create(user=patient_rare_lang, defaults={'hpn': "EVALRARELANG", 'blood_type':"AB+"}) # Give basic record

        self.stdout.write(self.style.SUCCESS("Patient scenarios created."))

        # --- Define Evaluation Scenarios List --- 
        # Format: {description, patient, department, expected_doctor (obj or None), [optional: appointment_type/date] } 
        scenarios = [
            # Standard Cases - Should match specialty
            {'description': "Std Cardio patient -> Cardio Dept", 'patient': patient_std_cardio, 'department': self.cardiology_dept, 'expected_doctor': self.cardio_doc},
            {'description': "Std Endo patient -> Endo Dept", 'patient': patient_std_endo, 'department': self.endo_dept, 'expected_doctor': self.endo_doc},
            {'description': "Std Neuro patient -> Neuro Dept", 'patient': patient_std_neuro, 'department': self.neuro_dept, 'expected_doctor': self.neuro_doc},
            {'description': "Std Gen patient -> GenMed Dept", 'patient': patient_std_gen, 'department': self.genmed_dept, 'expected_doctor': self.gen_doc},
            {'description': "Std Cardio patient -> GenMed Dept (Mismatch)", 'patient': patient_std_cardio, 'department': self.genmed_dept, 'expected_doctor': self.gen_doc}, # Expect fallback to GenMed
            {'description': "Std Gen patient -> Cardio Dept (Mismatch)", 'patient': patient_std_gen, 'department': self.cardiology_dept, 'expected_doctor': self.cardio_doc}, # Expect assign specialist

            # Continuity Cases - Should prioritize past doctor
            {'description': "Cont Cardio patient -> Cardio Dept", 'patient': patient_cont_cardio, 'department': self.cardiology_dept, 'expected_doctor': self.cardio_doc},
            {'description': "Cont Endo patient -> Endo Dept", 'patient': patient_cont_endo, 'department': self.endo_dept, 'expected_doctor': self.endo_doc},
            {'description': "Mixed Hist patient -> Cardio Dept (Continuity Match)", 'patient': patient_mixed_cont, 'department': self.cardiology_dept, 'expected_doctor': self.cardio_doc},
            {'description': "Mixed Hist patient -> Endo Dept (Specialty Match, No Continuity)", 'patient': patient_mixed_cont, 'department': self.endo_dept, 'expected_doctor': self.endo_doc},

            # Stress Tests & Different Data
            {'description': "Complex Multi patient -> Cardio Dept", 'patient': patient_complex_multi, 'department': self.cardiology_dept, 'expected_doctor': self.cardio_doc}, # Match primary diagnosis?
            {'description': "Complex Multi patient -> Endo Dept", 'patient': patient_complex_multi, 'department': self.endo_dept, 'expected_doctor': self.endo_doc},
            {'description': "Complex Multi patient -> Neuro Dept", 'patient': patient_complex_multi, 'department': self.neuro_dept, 'expected_doctor': self.neuro_doc},
            {'description': "Complex Multi patient -> GenMed Dept", 'patient': patient_complex_multi, 'department': self.genmed_dept, 'expected_doctor': self.gen_doc}, # Fallback expected?
            {'description': "Patient No Record -> GenMed Dept", 'patient': patient_no_record, 'department': self.genmed_dept, 'expected_doctor': self.gen_doc}, # Simple, assign available
            {'description': "Patient No Record -> Cardio Dept", 'patient': patient_no_record, 'department': self.cardiology_dept, 'expected_doctor': self.cardio_doc}, # Assign available specialist
            {'description': "Patient Rare Lang -> GenMed Dept", 'patient': patient_rare_lang, 'department': self.genmed_dept, 'expected_doctor': self.gen_doc}, # Assign available despite lang
            {'description': "Std Cardio patient -> Cardio Dept (Emergency)", 'patient': patient_std_cardio, 'department': self.cardiology_dept, 'expected_doctor': self.cardio_doc, 'appointment_type': 'emergency'},
            
            # Scenario where Endo doc is unavailable (request on Wed)
            # {'description': "Std Endo patient -> Endo Dept (Unavailable)", 'patient': patient_std_endo, 'department': self.endo_dept, 'expected_doctor': None, 'appointment_date': self.find_next_available_slot(self.cardio_doc, timezone.now().date() + timedelta(days=1)) }, # Find next available Cardio slot as proxy for bad time for Endo
        ]

        # --- Run Evaluation --- 
        self.stdout.write(self.style.HTTP_INFO("\n--- Running Evaluation ---"))
        eval_results = self.run_evaluation(scenarios)

        # --- Report Results --- 
        self.stdout.write(self.style.HTTP_INFO("\n--- Evaluation Summary ---"))
        correct_assignments = eval_results['correct'] - eval_results['no_assignment_correct']
        incorrect_assignments = eval_results['incorrect'] - eval_results['no_assignment_incorrect']
        total_assigned_scenarios = correct_assignments + incorrect_assignments
        
        self.stdout.write(f"Total Scenarios Tested: {len(scenarios)}")
        self.stdout.write(f"  - Correct Assignments: {correct_assignments}")
        self.stdout.write(f"  - Incorrect Assignments: {incorrect_assignments}")
        self.stdout.write(f"  - Correctly Identified No Assignment Possible: {eval_results['no_assignment_correct']}")
        self.stdout.write(f"  - Incorrectly Made No Assignment: {eval_results['no_assignment_incorrect']}")

        # Calculate accuracy only on scenarios where an assignment was expected and made
        accuracy = (correct_assignments / total_assigned_scenarios) * 100 if total_assigned_scenarios > 0 else 0
        self.stdout.write(f"Accuracy (on assigned cases): {accuracy:.2f}%" if total_assigned_scenarios > 0 else "Accuracy: N/A (No assignments expected/made)") 

        self.stdout.write(self.style.HTTP_INFO("\n--- Detailed Results ---"))
        for detail in eval_results['details']:
            style = self.style.SUCCESS if 'Correct' in detail['status'] else self.style.ERROR
            self.stdout.write(style(f"  Scenario: {detail['scenario']}"))
            self.stdout.write(f"    Patient: {detail['patient']}, Dept: {detail['department']}")
            self.stdout.write(f"    Expected: {detail['expected']}, Assigned: {detail['assigned']} - Status: {detail['status']}")

        self.stdout.write(self.style.SUCCESS('\nEvaluation command finished.')) 