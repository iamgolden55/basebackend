from django.db import models
from django.utils import timezone
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import numpy as np
import joblib
import os
from datetime import datetime, timedelta
from django.conf import settings
from api.models.medical.appointment import Appointment
from api.models.medical_staff.doctor import Doctor
from api.models.user.custom_user import CustomUser
from django.core.cache import cache

class MLDoctorAssignment:
    MODEL_PATH = os.path.join(settings.BASE_DIR, 'ml_models', 'doctor_assignment.joblib')
    SCALER_PATH = os.path.join(settings.BASE_DIR, 'ml_models', 'doctor_assignment_scaler.joblib')
    
    def __init__(self):
        self._ensure_model_directory()
        self.model = self._load_or_create_model()
        self.scaler = self._load_or_create_scaler()
    
    def _ensure_model_directory(self):
        """Ensure the ml_models directory exists"""
        os.makedirs(os.path.dirname(self.MODEL_PATH), exist_ok=True)
    
    def _load_or_create_model(self):
        """Load existing model or create a new one"""
        try:
            return joblib.load(self.MODEL_PATH)
        except (FileNotFoundError, EOFError):
            model = RandomForestClassifier(
                n_estimators=100,
                random_state=42,
                class_weight='balanced'
            )
            joblib.dump(model, self.MODEL_PATH)
            return model
    
    def _load_or_create_scaler(self):
        """Load existing scaler or create a new one"""
        try:
            return joblib.load(self.SCALER_PATH)
        except (FileNotFoundError, EOFError):
            scaler = StandardScaler()
            joblib.dump(scaler, self.SCALER_PATH)
            return scaler
    
    def _calculate_language_match(self, patient, doctor):
        """Calculate language compatibility between patient and doctor"""
        # Check if doctor has languages specified
        if not doctor.languages_spoken:
            return 0
            
        # Get doctor languages as a set
        doctor_languages = set(lang.strip().lower() for lang in doctor.languages_spoken.split(','))
        
        # Initialize patient languages set
        patient_languages = set()
        
        # Add preferred language if available (with higher weight)
        preferred_language_match = 0
        if hasattr(patient, 'preferred_language') and patient.preferred_language:
            if patient.preferred_language != 'other':
                preferred_lang = patient.preferred_language.strip().lower()
                patient_languages.add(preferred_lang)
                if preferred_lang in doctor_languages:
                    preferred_language_match = 3  # Higher weight for preferred language
            elif hasattr(patient, 'custom_language') and patient.custom_language:
                custom_lang = patient.custom_language.strip().lower()
                patient_languages.add(custom_lang)
                if custom_lang in doctor_languages:
                    preferred_language_match = 3  # Higher weight for preferred language
        
        # Add secondary languages if available
        if hasattr(patient, 'secondary_languages') and patient.secondary_languages:
            if isinstance(patient.secondary_languages, str):
                for lang in patient.secondary_languages.split(','):
                    patient_languages.add(lang.strip().lower())
            elif isinstance(patient.secondary_languages, list):
                for lang in patient.secondary_languages:
                    patient_languages.add(lang.strip().lower())
        
        # Fallback to old 'languages' field if it exists
        if hasattr(patient, 'languages') and patient.languages:
            legacy_languages = set(lang.strip().lower() for lang in patient.languages.split(','))
            patient_languages.update(legacy_languages)
        
        # Calculate the number of matching languages (excluding preferred match)
        matching_languages = len(patient_languages & doctor_languages)
        
        # Log for debugging
        print(f"Language match: Patient speaks {patient_languages}, Doctor speaks {doctor_languages}")
        print(f"Matching languages: {matching_languages}, Preferred match bonus: {preferred_language_match}")
        
        return matching_languages * 2 + preferred_language_match  # Return weighted score
    
    def _extract_medical_features(self, patient):
        """Extract medical record features for ML model"""
        # Try to get medical record
        try:
            medical_record = patient.medical_record
        except:
            # No medical record found
            return {
                'diagnosis_codes': [],
                'chronic_count': 0,
                'comorbidity_score': 0,
                'severity_score': 0,
                'medication_complexity': 0,
                'care_plan_complexity': 0,
                'hospitalization_history': 0
            }
            
        # Get diagnosis codes
        diagnosis_codes = []
        chronic_conditions = 0
        severity_sum = 0
        
        try:
            # Get active diagnoses
            diagnoses = medical_record.diagnoses.filter(is_active=True)
            
            for diagnosis in diagnoses:
                if diagnosis.diagnosis_code:
                    diagnosis_codes.append(diagnosis.diagnosis_code)
                if diagnosis.is_chronic:
                    chronic_conditions += 1
                severity_sum += diagnosis.severity_rating
                
            # Calculate complexity metrics
            comorbidity_score = len(diagnosis_codes) / 10.0  # Normalize
            severity_avg = severity_sum / max(1, len(diagnoses))
            
            # Get medication complexity
            medications = medical_record.treatments.filter(
                treatment_type='medication',
                is_active=True
            ).count()
            medication_complexity = min(1.0, medications / 10.0)
            
            # Get hospitalization history
            hospitalization_score = min(1.0, medical_record.hospitalization_count / 5.0)
            
            # Use pre-calculated care plan complexity
            care_plan_complexity = medical_record.care_plan_complexity / 10.0  # Normalize to 0-1
            
            return {
                'diagnosis_codes': diagnosis_codes,
                'chronic_count': chronic_conditions,
                'comorbidity_score': comorbidity_score,
                'severity_score': severity_avg / 5.0,  # Normalize to 0-1
                'medication_complexity': medication_complexity,
                'care_plan_complexity': care_plan_complexity,
                'hospitalization_history': hospitalization_score
            }
        except Exception as e:
            print(f"Error extracting medical features: {e}")
            return {
                'diagnosis_codes': [],
                'chronic_count': 0,
                'comorbidity_score': 0,
                'severity_score': 0,
                'medication_complexity': 0,
                'care_plan_complexity': 0,
                'hospitalization_history': 0
            }
    
    def _extract_features(self, patient, doctor, appointment_type):
        """Extract relevant features for ML model"""
        # Get cached success rate or calculate
        cache_key = f'doctor_success_rate_{doctor.id}'
        success_rate = cache.get(cache_key)
        if success_rate is None:
            success_rate = self._calculate_doctor_success_rate(doctor)
            cache.set(cache_key, success_rate, timeout=3600)  # Cache for 1 hour
        
        # Calculate age from date_of_birth if available
        age = 0
        if patient.date_of_birth:
            today = timezone.now().date()
            age = today.year - patient.date_of_birth.year - ((today.month, today.day) < (patient.date_of_birth.month, patient.date_of_birth.day))
        
        # Calculate language match
        language_match = self._calculate_language_match(patient, doctor)
        
        # Calculate current workload
        current_workload = self._calculate_current_workload(doctor)
        
        # Extract medical features
        medical_features = self._extract_medical_features(patient)
        
        # Calculate specialty match
        specialty_match = self._calculate_specialty_match(patient, doctor, medical_features['diagnosis_codes'])
        
        # Calculate continuity score
        continuity_score = self._calculate_continuity_score(patient, doctor)
        
        features = [
            age / 100.0,  # Normalize age
            1 if patient.gender == 'male' else 0,
            min(10, Appointment.objects.filter(patient=patient).count()) / 10.0,  # Normalize previous visits
            min(doctor.years_of_experience, 30) / 30.0,  # Normalize experience
            success_rate,
            current_workload,  # Don't normalize workload - keep raw value
            1 if appointment_type == 'emergency' else 0,
            timezone.now().hour / 24.0,  # Normalize time
            language_match,
            specialty_match,
            medical_features['comorbidity_score'],
            medical_features['severity_score'],
            medical_features['medication_complexity'],
            medical_features['care_plan_complexity'],
            medical_features['hospitalization_history'],
            continuity_score
        ]
        
        return np.array(features).reshape(1, -1)
    
    def _calculate_doctor_success_rate(self, doctor):
        """Calculate doctor's success rate based on completed appointments"""
        completed_appointments = Appointment.objects.filter(
            doctor=doctor,
            status='completed'
        ).count()
        total_appointments = Appointment.objects.filter(doctor=doctor).count()
        return completed_appointments / total_appointments if total_appointments > 0 else 0
    
    def _calculate_current_workload(self, doctor, appointment_date=None):
        """Calculate current workload for a doctor on a given date"""
        if appointment_date is None:
            appointment_date = timezone.now()
        
        # Convert to date if datetime was provided
        if isinstance(appointment_date, datetime):
            appointment_date = appointment_date.date()
        
        # Count confirmed and pending appointments for the date
        workload = Appointment.objects.filter(
            doctor=doctor,
            appointment_date__date=appointment_date,
            status__in=['confirmed', 'pending']
        ).count()
        
        print(f"Calculating workload for {doctor} on {appointment_date}:")
        print(f"Found {workload} appointments")
        
        return workload
    
    def _calculate_specialty_match(self, patient, doctor, diagnosis_codes):
        """Calculate specialty match based on diagnosis codes"""
        if not diagnosis_codes:
            # Fallback to department-based matching if no diagnosis codes
            if hasattr(doctor, 'department') and doctor.department:
                department = doctor.department.name.lower()
                if hasattr(patient, 'medical_history') and patient.medical_history:
                    medical_history = patient.medical_history.lower()
                    # Simple keyword matching
                    keywords = {
                        'heart': ['cardiology', 'cardiac'],
                        'blood pressure': ['cardiology'],
                        'diabetes': ['endocrinology'],
                        'thyroid': ['endocrinology'],
                        'lung': ['pulmonology', 'respiratory'],
                        'breathing': ['pulmonology', 'respiratory'],
                        'kidney': ['nephrology'],
                        'liver': ['gastroenterology'],
                        'stomach': ['gastroenterology'],
                        'joint': ['orthopedic', 'rheumatology'],
                        'bone': ['orthopedic'],
                        'skin': ['dermatology'],
                        'brain': ['neurology'],
                        'nerve': ['neurology'],
                        'mental': ['psychiatry'],
                        'depression': ['psychiatry'],
                        'anxiety': ['psychiatry'],
                        'cancer': ['oncology'],
                        'tumor': ['oncology']
                    }
                    
                    for keyword, related_departments in keywords.items():
                        if keyword in medical_history:
                            if any(dept in department for dept in related_departments):
                                return 0.8  # Good match based on keywords
                    
                    return 0.5  # Neutral match
            return 0.5  # Default match
            
        # Use doctor's diagnosis match score method
        match_score = doctor.calculate_diagnosis_match_score(diagnosis_codes)
        
        # Normalize to 0-1 range
        return min(1.0, match_score / 10.0)
    
    def _calculate_continuity_score(self, patient, doctor):
        """Calculate continuity of care score"""
        # Check previous appointments with this doctor
        previous_appointments = Appointment.objects.filter(
            patient=patient,
            doctor=doctor,
            status='completed'
        ).count()
        
        # Simple continuity bonus that grows with each visit but has diminishing returns
        if previous_appointments > 0:
            continuity_score = min(1.0, previous_appointments / 5.0)
            return continuity_score
        
        return 0.0
    
    def _calculate_simple_score(self, features):
        """Calculate a simple score when model is not trained"""
        # Extract key features
        workload = features[0][5]  # Raw workload value
        language_match = features[0][8]  # Language match score
        experience = features[0][3] * 30  # De-normalize experience
        specialty_match = features[0][9] * 10  # De-normalize specialty match
        
        # Medical complexity features
        comorbidity_score = features[0][10] * 10  # De-normalize
        severity_score = features[0][11] * 5  # De-normalize
        medication_complexity = features[0][12] * 10  # De-normalize
        care_plan_complexity = features[0][13] * 10  # De-normalize
        hospitalization_history = features[0][14] * 5  # De-normalize
        continuity_score = features[0][15] * 10  # De-normalize
        
        # Calculate complexity factor (0-1)
        case_complexity = (comorbidity_score + severity_score + medication_complexity + 
                          care_plan_complexity + hospitalization_history) / 40.0
        
        # Base score starts with experience and success rate
        base_score = experience * 0.3 + features[0][4] * 0.2
        
        # Add language match bonus (significant boost for matches)
        base_score += language_match * 2.0
        
        # Add specialty match bonus
        base_score += specialty_match * 3.0
        
        # Add continuity bonus
        base_score += continuity_score * 2.5
        
        # For complex cases, strongly favor experienced doctors
        if case_complexity > 0.7:  # High complexity threshold
            experience_bonus = doctor.years_of_experience * 0.5
            base_score += experience_bonus
            
            # Also favor doctors with high complex case rating
            if hasattr(doctor, 'complex_case_rating'):
                base_score += doctor.complex_case_rating * 0.3
        
        # Add workload penalty (exponential penalty for high workload)
        workload_penalty = workload ** 3 * 0.2  # Cubic penalty with stronger multiplier
        base_score -= workload_penalty
        
        # Emergency priority
        if features[0][6] == 1:  # If emergency
            base_score += 1000.0  # High priority for emergencies
        
        print(f"Score breakdown - Experience: {experience * 0.3:.2f}, Language: {language_match * 2.0:.2f}, " +
              f"Specialty: {specialty_match * 3.0:.2f}, Continuity: {continuity_score * 2.5:.2f}, " +
              f"Complexity: {case_complexity:.2f}, Workload: {workload}, Penalty: {workload_penalty:.2f}, " +
              f"Final: {base_score:.2f}")
        
        return base_score
    
    def assign_doctor(self, appointment_data):
        """Assign the most suitable doctor for an appointment"""
        patient = appointment_data.get('patient')
        department = appointment_data.get('department')
        hospital = appointment_data.get('hospital')
        appointment_type = appointment_data.get('appointment_type', 'regular')
        appointment_date = appointment_data.get('appointment_date')

        print("\nDoctor Assignment Debug:")
        print(f"Emergency: {appointment_type == 'emergency'}")
        
        # Debug language preferences
        preferred_lang = getattr(patient, 'preferred_language', None)
        custom_lang = getattr(patient, 'custom_language', None)
        secondary_langs = getattr(patient, 'secondary_languages', None)
        
        print(f"Patient preferred language: {preferred_lang}")
        if preferred_lang == 'other':
            print(f"Patient custom language: {custom_lang}")
        print(f"Patient secondary languages: {secondary_langs}")
        
        # Legacy field
        legacy_langs = getattr(patient, 'languages', None)
        if legacy_langs:
            print(f"Patient legacy languages: {legacy_langs}")

        # Get active doctors in the department
        doctors = Doctor.objects.filter(
            department=department,
            hospital=hospital,
            is_active=True,
            status='active'
        )

        if not doctors:
            return None

        best_doctor = None
        best_score = float('-inf')
        best_experience = 0
        
        # Extract medical features once
        medical_features = self._extract_medical_features(patient)
        print(f"Medical features: {medical_features}")

        for doctor in doctors:
            if not doctor.can_practice:
                continue

            # Check availability unless it's an emergency
            if appointment_type != 'emergency' and not doctor.is_available_at(appointment_date):
                continue

            # Extract features and calculate score
            features = self._extract_features(patient, doctor, appointment_type)
            score = self._calculate_simple_score(features)

            # Update best doctor if:
            # 1. Current score is higher
            # 2. Scores are equal but current doctor has more experience
            if score > best_score or (abs(score - best_score) < 0.01 and doctor.years_of_experience > best_experience):
                best_doctor = doctor
                best_score = score
                best_experience = doctor.years_of_experience

        return best_doctor
    
    def train_model(self, training_data):
        """Train the ML model with historical appointment data"""
        if not training_data['features'] or not training_data['outcomes']:
            return False
            
        X = np.array(training_data['features'])
        y = np.array(training_data['outcomes'])
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train model
        self.model.fit(X_scaled, y)
        
        # Save model and scaler
        joblib.dump(self.model, self.MODEL_PATH)
        joblib.dump(self.scaler, self.SCALER_PATH)
        
        return True

# Create a singleton instance
doctor_assigner = MLDoctorAssignment() 