# ML-Based Doctor Assignment System 🤖

## Overview 🎯
Welcome to the magical world of ML-based doctor assignments! Think of this system as a super-smart matchmaker that pairs patients with the perfect doctor. It's like a dating app, but for healthcare! 💉

## Table of Contents 📑
- [System Architecture](#system-architecture)
- [Feature Engineering](#feature-engineering)
- [Scoring System](#scoring-system)
- [ML Models](#ml-models)
- [Training Process](#training-process)
- [Real-time Assignment](#real-time-assignment)
- [Performance Monitoring](#performance-monitoring)
- [Code Examples](#code-examples)
- [Best Practices](#best-practices)
- [Language Preference Handling](#language-preference-handling)
- [Continuity of Care](#continuity-of-care)

## System Architecture 🏗️

### High-Level Overview
```python
class MLDoctorAssigner:
    """Main class for ML-based doctor assignment"""
    def __init__(self):
        self.feature_extractor = FeatureExtractor()
        self.scoring_model = ScoringModel()
        self.assignment_optimizer = AssignmentOptimizer()
        
    def assign_doctor(self, appointment_data):
        features = self.feature_extractor.extract(appointment_data)
        scores = self.scoring_model.predict(features)
        return self.assignment_optimizer.optimize(scores, appointment_data)
```

### Core Components
1. **Feature Extractor**: Processes raw data into ML features
2. **Scoring Model**: Calculates compatibility scores
3. **Assignment Optimizer**: Makes final assignment decisions
4. **Performance Monitor**: Tracks and improves system accuracy

## Feature Engineering 🔧

### Patient Features
```python
class PatientFeatureExtractor:
    """Extract patient-related features"""
    def extract(self, patient):
        return {
            'patient_id': patient.id,  # Added for continuity of care
            'age': self.normalize_age(patient.age),
            'gender': self.encode_gender(patient.gender),
            'medical_history': self.encode_conditions(patient.conditions),
            'language_preferences': self.encode_language_preferences(patient),
            'location': self.encode_location(patient.address),
            'previous_visits': self.get_visit_history(patient),
            'preferred_gender': patient.doctor_gender_preference,
            'special_needs': self.encode_special_needs(patient.special_needs),
            'past_appointments': self.get_past_appointments(patient)  # Added for continuity
        }
        
    def encode_language_preferences(self, patient):
        """Extract and encode patient language preferences"""
        languages = set()
        
        # Add preferred language with higher weight
        if patient.preferred_language:
            if patient.preferred_language != 'other':
                languages.add((patient.preferred_language, 3))  # Higher weight
            elif patient.custom_language:
                languages.add((patient.custom_language, 3))     # Higher weight
        
        # Add secondary languages with normal weight
        if patient.secondary_languages:
            for lang in patient.secondary_languages.split(','):
                languages.add((lang.strip(), 2))
        
        # Add legacy languages for backward compatibility
        if hasattr(patient, 'languages') and patient.languages:
            for lang in patient.languages.split(','):
                languages.add((lang.strip(), 2))
                
        return languages
        
    def get_past_appointments(self, patient):
        """Get patient's past appointments for continuity analysis"""
        from api.models import Appointment
        
        past_appointments = Appointment.objects.filter(
            patient=patient,
            status='completed'
        ).select_related('doctor', 'department').order_by('-appointment_date')
        
        # Return structured data about past appointments
        return [{
            'doctor_id': apt.doctor.id,
            'department_id': apt.department.id,
            'date': apt.appointment_date,
            'days_ago': (timezone.now().date() - apt.appointment_date.date()).days
        } for apt in past_appointments]
```

### Doctor Features
```python
class DoctorFeatureExtractor:
    """Extract doctor-related features"""
    def extract(self, doctor):
        return {
            'doctor_id': doctor.id,  # Added for continuity of care
            'specialization': self.encode_specialization(doctor.specialization),
            'experience_years': self.normalize_experience(doctor.years_of_experience),
            'languages': self.encode_languages(doctor.languages_spoken),
            'gender': self.encode_gender(doctor.gender),
            'rating': self.get_normalized_rating(doctor),
            'success_rate': self.calculate_success_rate(doctor),
            'workload': self.calculate_current_workload(doctor),
            'expertise_areas': self.encode_expertise(doctor.expertise_areas),
            'patient_continuity': self.get_patient_continuity(doctor)  # Added for continuity
        }
        
    def get_patient_continuity(self, doctor):
        """Get doctor's patient continuity metrics"""
        from api.models import Appointment
        from django.db.models import Count
        
        # Get count of repeat patients (patients with multiple appointments)
        repeat_patients = Appointment.objects.filter(
            doctor=doctor,
            status='completed'
        ).values('patient').annotate(
            count=Count('patient')
        ).filter(count__gt=1).count()
        
        # Get total unique patients
        total_patients = Appointment.objects.filter(
            doctor=doctor,
            status='completed'
        ).values('patient').distinct().count()
        
        # Calculate continuity ratio (percentage of repeat patients)
        continuity_ratio = repeat_patients / max(1, total_patients)
        
        return {
            'repeat_patients': repeat_patients,
            'total_patients': total_patients,
            'continuity_ratio': continuity_ratio
        }
```

### Appointment Context Features
```python
class AppointmentFeatureExtractor:
    """Extract appointment-specific features"""
    def extract(self, appointment):
        return {
            'department_id': appointment.department.id,  # Added for continuity of care
            'urgency': self.encode_urgency(appointment.priority),
            'appointment_type': self.encode_type(appointment.type),
            'time_slot': self.encode_time(appointment.datetime),
            'department': self.encode_department(appointment.department),
            'is_followup': appointment.is_followup,
            'required_equipment': self.encode_equipment(appointment.required_equipment)
        }
```

## Scoring System 💯

### Base Scoring Model
```python
class DoctorScoring:
    """Calculate compatibility scores between doctors and appointments"""
    
    def calculate_score(self, doctor_features, patient_features, appointment_features):
        # Base scores (0-1 scale)
        specialty_match = self.calculate_specialty_match(
            doctor_features['specialization'],
            patient_features['medical_history']
        )
        
        experience_score = self.calculate_experience_score(
            doctor_features['experience_years'],
            appointment_features['urgency']
        )
        
        language_match = self.calculate_language_match(
            doctor_features['languages'],
            patient_features['language_preferences']
        )
        
        workload_score = self.calculate_workload_score(
            doctor_features['workload']
        )
        
        # Continuity of care score
        continuity_score = self.calculate_continuity_score(
            doctor_features['doctor_id'],
            patient_features['patient_id'],
            appointment_features['department_id']
        )
        
        # Weighted combination
        weights = self.get_dynamic_weights(appointment_features)
        final_score = (
            weights['specialty'] * specialty_match +
            weights['experience'] * experience_score +
            weights['language'] * language_match +
            weights['workload'] * workload_score +
            weights['continuity'] * continuity_score
        )
        
        return self.normalize_score(final_score)
```

### Dynamic Weight Calculation
```python
def get_dynamic_weights(self, appointment_features):
    """Calculate dynamic weights based on appointment context"""
    base_weights = {
        'specialty': 0.4,
        'experience': 0.3,
        'language': 0.2,
        'workload': 0.1,
        'continuity': 0.25  # Continuity of care weight
    }
    
    if appointment_features['urgency'] == 'emergency':
        return {
            'specialty': 0.5,
            'experience': 0.4,
            'language': 0.05,
            'workload': 0.05,
            'continuity': 0.0  # No continuity weight for emergencies
        }
    
    if appointment_features['is_followup']:
        return {
            'specialty': 0.3,
            'experience': 0.2,
            'language': 0.2,
            'workload': 0.1,
            'continuity': 0.5  # Higher continuity weight for follow-ups
        }
    
    return base_weights
```

### Language Matching
```python
def calculate_language_match(self, doctor_languages, patient_language_preferences):
    """Calculate language compatibility between patient and doctor"""
    if not doctor_languages:
        return 0
        
    # Convert doctor languages to lowercase set
    doctor_langs = set(lang.strip().lower() for lang in doctor_languages.split(','))
    
    # Initialize score
    total_score = 0
    
    # Calculate score based on weighted patient language preferences
    for lang, weight in patient_language_preferences:
        if lang.strip().lower() in doctor_langs:
            total_score += weight
    
    # Normalize score (0-1 scale)
    return min(1.0, total_score / 10.0)
```

### Specialty Matching
```python
def calculate_specialty_match(self, doctor_specialization, patient_conditions):
    """Calculate how well doctor's specialty matches patient's needs"""
    base_score = self.specialty_matching_matrix[doctor_specialization][
        self.get_primary_condition(patient_conditions)
    ]
    
    # Boost score for relevant subspecialties
    subspecialty_bonus = self.calculate_subspecialty_bonus(
        doctor_specialization,
        patient_conditions
    )
    
    return min(1.0, base_score + subspecialty_bonus)
```

### Continuity of Care Scoring
```python
def calculate_continuity_score(self, doctor_id, patient_id, department_id):
    """Calculate continuity of care score based on past appointments
    
    This function evaluates the patient's history with the doctor to promote
    continuity of care. It considers:
    1. Number of past appointments with this doctor
    2. Recency of past appointments (more recent = higher score)
    3. Department match (continuity within same department is valued higher)
    
    Returns:
    - Float: A score between 0.0 (no continuity) and 1.0 (strong continuity)
    """
    # Get past appointments for this patient-doctor pair
    past_appointments = Appointment.objects.filter(
        patient_id=patient_id,
        doctor_id=doctor_id,
        status='completed'
    ).order_by('-appointment_date')
    
    if not past_appointments.exists():
        return 0.0
    
    # Calculate base score from appointment count
    appointment_count = past_appointments.count()
    count_score = min(1.0, appointment_count / 5.0)  # Max out at 5 appointments
    
    # Calculate recency score
    most_recent = past_appointments.first().appointment_date
    days_since = (timezone.now().date() - most_recent.date()).days
    recency_score = max(0.0, 1.0 - (days_since / 365.0))  # Decay over a year
    
    # Calculate department match score
    department_match = past_appointments.filter(department_id=department_id).exists()
    department_score = 1.0 if department_match else 0.5
    
    # Combine scores with weights
    final_score = (
        0.3 * count_score +    # 30% weight for number of appointments
        0.5 * recency_score +  # 50% weight for recency
        0.2 * department_score # 20% weight for department match
    )
    
    return final_score
```

## ML Models 🧠

### Feature Preprocessing
```python
class FeaturePreprocessor:
    """Prepare features for ML models"""
    
    def preprocess(self, features):
        # Normalize numerical features
        numerical = self.normalize_numerical_features(features)
        
        # Encode categorical features
        categorical = self.encode_categorical_features(features)
        
        # Handle missing values
        complete = self.handle_missing_values(numerical, categorical)
        
        return complete
```

### Model Architecture
```python
class DoctorAssignmentModel:
    """ML model for doctor assignment"""
    
    def __init__(self):
        self.feature_preprocessor = FeaturePreprocessor()
        self.model = self.build_model()
    
    def build_model(self):
        model = tf.keras.Sequential([
            tf.keras.layers.Dense(128, activation='relu'),
            tf.keras.layers.Dropout(0.3),
            tf.keras.layers.Dense(64, activation='relu'),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.Dense(32, activation='relu'),
            tf.keras.layers.Dense(1, activation='sigmoid')
        ])
        return model
```

## Training Process 📚

### Data Collection
```python
class TrainingDataCollector:
    """Collect and prepare training data"""
    
    def collect_successful_assignments(self):
        """Get data from successful past appointments"""
        return Appointment.objects.filter(
            status='completed',
            patient_satisfaction__gte=4.0
        ).prefetch_related('doctor', 'patient')
    
    def collect_unsuccessful_assignments(self):
        """Get data from problematic appointments"""
        return Appointment.objects.filter(
            Q(status='cancelled') |
            Q(patient_satisfaction__lt=3.0)
        ).prefetch_related('doctor', 'patient')
```

### Model Training
```python
class ModelTrainer:
    """Train the ML model"""
    
    def train(self, training_data):
        X_train, y_train = self.prepare_training_data(training_data)
        
        self.model.fit(
            X_train,
            y_train,
            epochs=100,
            batch_size=32,
            validation_split=0.2,
            callbacks=[
                tf.keras.callbacks.EarlyStopping(patience=5),
                tf.keras.callbacks.ModelCheckpoint(
                    'best_model.h5',
                    save_best_only=True
                )
            ]
        )
```

## Real-time Assignment 🚀

### Assignment Process
```python
class RealTimeAssigner:
    """Handle real-time doctor assignments"""
    
    def assign(self, appointment_request):
        # Get available doctors
        available_doctors = self.get_available_doctors(
            appointment_request.datetime,
            appointment_request.department
        )
        
        # Calculate scores for each doctor
        scores = []
        for doctor in available_doctors:
            score = self.calculate_assignment_score(
                doctor,
                appointment_request
            )
            scores.append((doctor, score))
        
        # Sort by score and return best match
        best_match = sorted(scores, key=lambda x: x[1], reverse=True)[0]
        return best_match[0]
```

### Score Calculation
```python
def calculate_assignment_score(self, doctor, appointment):
    """Calculate comprehensive assignment score"""
    
    # Get all features
    features = self.feature_extractor.extract_all(
        doctor=doctor,
        appointment=appointment
    )
    
    # Get base ML score
    ml_score = self.ml_model.predict(features)
    
    # Apply business rules
    final_score = self.apply_business_rules(
        ml_score,
        doctor,
        appointment
    )
    
    return final_score
```

## Performance Monitoring 📊

### Metrics Tracking
```python
class PerformanceMonitor:
    """Monitor and track assignment performance"""
    
    def track_assignment(self, appointment):
        metrics = {
            'patient_satisfaction': appointment.patient_satisfaction,
            'completed_successfully': appointment.status == 'completed',
            'wait_time': self.calculate_wait_time(appointment),
            'doctor_workload': self.get_doctor_workload(appointment.doctor),
            'ml_score': appointment.ml_score
        }
        
        self.store_metrics(metrics)
        self.update_model_if_needed(metrics)
```

### Feedback Loop
```python
class FeedbackProcessor:
    """Process appointment feedback for model improvement"""
    
    def process_feedback(self, appointment):
        # Collect feedback data
        feedback_data = self.collect_feedback(appointment)
        
        # Update training dataset
        self.update_training_data(feedback_data)
        
        # Retrain model if necessary
        if self.should_retrain_model():
            self.trigger_model_retraining()
```

## Language Preference Handling 🗣️

Our system handles patient language preferences in a comprehensive way to ensure optimal doctor-patient communication. The language matching algorithm considers multiple language fields with different priorities:

### Language Fields
1. **Preferred Language**: The patient's primary language preference
   - Standard language codes (e.g., "en", "es", "fr")
   - Special value "other" for custom languages
   
2. **Custom Language**: Used when preferred_language is set to "other"
   - Allows for languages not in the standard list
   - Examples: "Yoruba", "Calabar", "Igbo"
   
3. **Secondary Languages**: Additional languages the patient speaks
   - Comma-separated list of language codes
   - Lower priority than preferred language
   
4. **Legacy Language Field**: For backward compatibility
   - Used when the new fields are not set
   - Simple comma-separated list of languages

### Matching Algorithm
```python
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
    preferred_match = 0
    if hasattr(patient, 'preferred_language') and patient.preferred_language:
        if patient.preferred_language != 'other':
            preferred_lang = patient.preferred_language.strip().lower()
            patient_languages.add(preferred_lang)
            if preferred_lang in doctor_languages:
                preferred_match = 3  # Higher weight for preferred language
        elif hasattr(patient, 'custom_language') and patient.custom_language:
            custom_lang = patient.custom_language.strip().lower()
            patient_languages.add(custom_lang)
            if custom_lang in doctor_languages:
                preferred_match = 3  # Higher weight for preferred language
    
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
    
    # Return weighted score
    return matching_languages * 2 + preferred_match
```

### Scoring Weights
- **Preferred Language Match**: 3 points
- **Secondary/Legacy Language Match**: 2 points per match
- **No Language Match**: 0 points

### Example Scenarios

1. **Preferred Language Match**
   ```
   Patient: preferred_language="spanish"
   Doctor: languages_spoken="English,Spanish,French"
   Score: 3 (preferred match)
   ```

2. **Custom Language Match**
   ```
   Patient: preferred_language="other", custom_language="Calabar"
   Doctor: languages_spoken="English,Yoruba,Calabar"
   Score: 3 (preferred match)
   ```

3. **Secondary Languages Match**
   ```
   Patient: preferred_language="english", secondary_languages="french,spanish"
   Doctor: languages_spoken="English,French"
   Score: 5 (3 for preferred + 2 for secondary)
   ```

4. **Legacy Language Match**
   ```
   Patient: languages="Spanish"
   Doctor: languages_spoken="English,Spanish"
   Score: 2 (legacy match)
   ```

5. **Multiple Matches**
   ```
   Patient: preferred_language="spanish", secondary_languages="french,english"
   Doctor: languages_spoken="English,Spanish,French"
   Score: 7 (3 for preferred + 2*2 for secondary)
   ```

## Best Practices 📝

1. **Feature Engineering**
   - Regularly update feature importance analysis
   - Monitor feature distribution shifts
   - Handle missing data appropriately

2. **Model Training**
   - Use cross-validation for robust evaluation
   - Implement early stopping to prevent overfitting
   - Maintain separate validation set

3. **Assignment Logic**
   - Balance ML scores with business rules
   - Handle edge cases gracefully
   - Maintain fallback options

4. **Performance Monitoring**
   - Track key metrics in real-time
   - Set up automated alerts for issues
   - Regular model retraining

## Code Examples 💻

### Complete Assignment Flow
```python
def handle_new_appointment(appointment_request):
    """Handle new appointment request with ML assignment"""
    
    # Initialize components
    assigner = MLDoctorAssigner()
    monitor = PerformanceMonitor()
    
    try:
        # Get ML assignment
        assigned_doctor = assigner.assign_doctor(appointment_request)
        
        # Create appointment
        appointment = Appointment.objects.create(
            patient=appointment_request.patient,
            doctor=assigned_doctor,
            datetime=appointment_request.datetime,
            department=appointment_request.department,
            ml_score=assigned_doctor.ml_score
        )
        
        # Start monitoring
        monitor.track_assignment(appointment)
        
        return appointment
        
    except Exception as e:
        # Handle failures gracefully
        logger.error(f"Assignment failed: {str(e)}")
        return handle_assignment_failure(appointment_request)
```

### Model Retraining
```python
def retrain_model():
    """Retrain ML model with latest data"""
    
    # Collect new training data
    collector = TrainingDataCollector()
    training_data = collector.collect_all_data()
    
    # Prepare data
    preprocessor = FeaturePreprocessor()
    processed_data = preprocessor.preprocess(training_data)
    
    # Train model
    trainer = ModelTrainer()
    new_model = trainer.train(processed_data)
    
    # Validate and deploy
    if validate_model(new_model):
        deploy_model(new_model)
        notify_model_update()
```

## Related Documentation 📚
- Appointment Flow Documentation
- Doctor Management System
- Patient Registration System
- Performance Monitoring System
- Model Training Guidelines 

## Detailed System Explanations 🔍

### Understanding the Scoring System 🎯

Think of our scoring system like a matchmaking game show! Each doctor gets rated on multiple factors to find the perfect match for each patient.

#### Base Score Components
```python
# Each doctor gets points in 4 main categories (0-1 scale):

1. Specialty Match (40%):
   - Primary specialty alignment
   - Subspecialty bonuses
   - Relevant experience with condition
   
2. Experience Score (30%):
   - Years of practice (normalized)
   - Success rate with similar cases
   - Complexity handling history
   
3. Language Match (20%):
   - Primary language match
   - Secondary language capabilities
   - Communication style rating
   
4. Workload Score (10%):
   - Current patient load
   - Daily appointment distribution
   - Time slot availability
```

#### Dynamic Weight Adjustments
```python
class DynamicWeightCalculator:
    """Calculate weights based on appointment context"""
    
    def get_weights(self, appointment_type):
        if appointment_type == 'emergency':
            return {
                'specialty': 0.50,  # Increased priority
                'experience': 0.40, # Higher importance
                'language': 0.05,   # Less critical
                'workload': 0.05    # Less critical
            }
            
        elif appointment_type == 'follow_up':
            return {
                'specialty': 0.30,  # Reduced (already validated)
                'experience': 0.20, # Reduced
                'language': 0.40,   # Increased for better communication
                'workload': 0.10    # Standard
            }
            
        return {
            'specialty': 0.40,  # Standard weight
            'experience': 0.30, # Standard weight
            'language': 0.20,   # Standard weight
            'workload': 0.10    # Standard weight
        }
```

### Model Training Deep Dive 📚

Our training process ensures the model learns from both successful and unsuccessful appointments.

#### Data Collection Strategy
```python
class TrainingDataStrategy:
    """Collect and prepare training data"""
    
    def collect_positive_examples(self):
        """Successful appointments"""
        return Appointment.objects.filter(
            status='completed',
            patient_satisfaction__gte=4.0,
            doctor_rating__gte=4.0,
            completed_on_time=True
        )
    
    def collect_negative_examples(self):
        """Problematic appointments"""
        return Appointment.objects.filter(
            Q(status='cancelled') |
            Q(patient_satisfaction__lt=3.0) |
            Q(doctor_rating__lt=3.0) |
            Q(no_show=True)
        )
    
    def prepare_training_batch(self):
        """Prepare balanced training data"""
        positive = self.collect_positive_examples()
        negative = self.collect_negative_examples()
        
        # Balance dataset
        min_size = min(positive.count(), negative.count())
        return self.balance_dataset(positive, negative, min_size)
```

#### Training Pipeline
```python
class ModelTrainingPipeline:
    """Complete training pipeline"""
    
    def train_model(self):
        # 1. Data Collection
        data = TrainingDataStrategy().prepare_training_batch()
        
        # 2. Feature Extraction
        features = FeatureExtractor().extract_all(data)
        
        # 3. Data Preprocessing
        processed_data = self.preprocess_features(features)
        
        # 4. Model Training
        history = self.model.fit(
            processed_data.X,
            processed_data.y,
            epochs=100,
            batch_size=32,
            validation_split=0.2,
            callbacks=[
                EarlyStopping(patience=5),
                ModelCheckpoint('best_model.h5')
            ]
        )
        
        # 5. Validation
        self.validate_model(history)
        
        return history
```

### Real-time Assignment Process ⚡

The real-time assignment system works like a high-speed matchmaking service!

#### Assignment Workflow
```python
class RealTimeAssignmentManager:
    """Manage real-time doctor assignments"""
    
    def process_appointment_request(self, request):
        # 1. Initial Filtering
        available_doctors = self.get_available_doctors(
            time=request.preferred_time,
            department=request.department
        )
        
        # 2. Score Calculation
        scored_doctors = []
        for doctor in available_doctors:
            score = self.calculate_comprehensive_score(
                doctor=doctor,
                patient=request.patient,
                appointment_type=request.type
            )
            scored_doctors.append((doctor, score))
        
        # 3. Optimization
        best_match = self.optimize_assignment(scored_doctors)
        
        # 4. Validation
        if self.validate_assignment(best_match):
            return self.create_appointment(best_match)
        else:
            return self.handle_no_match()
```

#### Example Assignment Flow
```python
# Sample appointment request
request = AppointmentRequest(
    patient_id="P123",
    department="Cardiology",
    preferred_time="2024-03-10 10:00",
    type="regular_checkup"
)

# Assignment process
1. Find Available Doctors:
   - Check schedule availability
   - Verify department match
   - Consider workload limits

2. Score Each Doctor:
   Dr. Smith:
   - Specialty Match: 0.95
   - Experience Score: 0.88
   - Language Match: 0.90
   - Workload Score: 0.85
   Final Score: 0.92

   Dr. Jones:
   - Specialty Match: 0.85
   - Experience Score: 0.92
   - Language Match: 0.80
   - Workload Score: 0.75
   Final Score: 0.85

3. Select Best Match:
   → Dr. Smith selected (highest score)

4. Validate & Confirm:
   - Verify final score > threshold
   - Check business rules
   - Confirm availability
```

### Common Scenarios and Solutions 🎯

1. **Emergency Appointments**
   ```python
   # Priority override
   if appointment.is_emergency:
       weights.update({
           'specialty': 0.5,    # Highest priority
           'experience': 0.4,   # Critical
           'response_time': 0.1 # Quick response needed
       })
   ```

2. **Follow-up Visits**
   ```python
   # Prefer previous doctor
   if appointment.is_followup:
       previous_doctor = get_previous_doctor(patient)
       if previous_doctor.is_available():
           return assign_to_previous_doctor()
   ```

3. **No High-Score Matches**
   ```python
   # Handle low-score scenarios
   if max_score < MIN_ACCEPTABLE_SCORE:
       if is_emergency:
           return assign_best_available()
       else:
           return trigger_manual_review()
   ```

### Quick Quiz! 🤔

Test your understanding:

1. What's the highest weighted factor in emergency cases?
   - a) Experience
   - b) Specialty ✅
   - c) Language

2. How often does the model retrain?
   - a) Every day
   - b) When performance drops ✅
   - c) Never

3. What happens if no doctor scores above 0.7?
   - a) Appointment rejected
   - b) Manual review triggered ✅
   - c) Random assignment

Answers:
1. b) Specialty (50% weight in emergencies)
2. b) When performance drops below threshold
3. b) System triggers manual review for proper handling 

## Continuity of Care 🔄

### Overview
Continuity of care is a critical aspect of our doctor assignment system that ensures patients maintain relationships with their healthcare providers over time. This section details how our ML system implements and prioritizes continuity of care.

### Benefits of Continuity
Research shows that continuity of care leads to:
- Better patient outcomes
- Increased patient satisfaction
- Improved treatment adherence
- More efficient appointments
- Reduced healthcare costs
- Enhanced doctor-patient communication

### Implementation in ML Pipeline

#### Feature Extraction
Our ML system extracts continuity-related features during the feature extraction phase:

```python
def extract_continuity_features(self, patient, doctor):
    """Extract features related to continuity of care"""
    # Get past appointments for this patient-doctor pair
    past_appointments = Appointment.objects.filter(
        patient=patient,
        doctor=doctor,
        status='completed'
    ).order_by('-appointment_date')
    
    if not past_appointments.exists():
        return {
            'has_past_appointments': 0,
            'appointment_count': 0,
            'days_since_last': 365,  # Default to 1 year
            'same_department_ratio': 0
        }
    
    # Calculate features
    appointment_count = past_appointments.count()
    most_recent = past_appointments.first().appointment_date
    days_since = (timezone.now().date() - most_recent.date()).days
    
    # Calculate department match ratio
    department_matches = 0
    current_department = self.appointment_data.get('department')
    
    if current_department:
        department_matches = past_appointments.filter(
            department=current_department
        ).count()
    
    same_department_ratio = department_matches / appointment_count if appointment_count > 0 else 0
    
    return {
        'has_past_appointments': 1,
        'appointment_count': min(appointment_count, 5) / 5.0,  # Normalize to 0-1
        'days_since_last': min(days_since, 365) / 365.0,  # Normalize to 0-1
        'same_department_ratio': same_department_ratio
    }
```

#### Continuity Score Calculation
The continuity score is calculated based on three main factors:

1. **Appointment Count**: The number of past appointments between the patient and doctor.
   - More appointments = higher score
   - Score maxes out at 5 appointments
   - Weight: 30% of continuity score

2. **Recency**: How recently the patient has seen the doctor.
   - More recent appointments receive higher scores
   - Score decays over a one-year period
   - Weight: 50% of continuity score

3. **Department Match**: Whether past appointments were in the same department.
   - Same department = full score
   - Different department = half score
   - Weight: 20% of continuity score

```python
def calculate_continuity_score(self, patient, doctor, department):
    """Calculate continuity of care score for a patient-doctor pair"""
    # Get past appointments for this patient with this doctor
    past_appointments = Appointment.objects.filter(
        patient=patient,
        doctor=doctor,
        status='completed'
    ).order_by('-appointment_date')
    
    if not past_appointments.exists():
        return 0.0
    
    # Calculate base score from appointment count
    appointment_count = past_appointments.count()
    count_score = min(1.0, appointment_count / 5.0)  # Max out at 5 appointments
    
    # Calculate recency score
    most_recent = past_appointments.first().appointment_date
    days_since = (timezone.now().date() - most_recent.date()).days
    recency_score = max(0.0, 1.0 - (days_since / 365.0))  # Decay over a year
    
    # Calculate department match score
    department_match = past_appointments.filter(department=department).exists()
    department_score = 1.0 if department_match else 0.5
    
    # Combine scores with weights
    final_score = (
        0.3 * count_score +    # 30% weight for number of appointments
        0.5 * recency_score +  # 50% weight for recency
        0.2 * department_score # 20% weight for department match
    )
    
    # Scale the final score based on appointment type
    appointment_type = self.appointment_data.get('appointment_type', 'regular')
    if appointment_type == 'follow_up':
        return final_score * 15.0  # Higher weight for follow-ups
    else:
        return final_score * 5.0
```

### Appointment Type Impact
The importance of continuity varies based on appointment type:

1. **Follow-up Appointments**: Continuity is given the highest weight (3x normal)
2. **Regular Appointments**: Continuity has standard weight
3. **Emergency Appointments**: Continuity is not considered

```python
def get_continuity_weight(self, appointment_type):
    """Get continuity weight based on appointment type"""
    if appointment_type == 'follow_up':
        return 3.0  # Higher weight for follow-ups
    elif appointment_type == 'emergency':
        return 0.0  # No continuity weight for emergencies
    else:
        return 1.0  # Standard weight for regular appointments
```

### Integration with ML Model
The continuity score is integrated into the ML model as a feature:

```python
def prepare_features_for_model(self, patient, doctor, appointment_data):
    """Prepare all features for ML model prediction"""
    # Get basic features
    patient_features = self.extract_patient_features(patient)
    doctor_features = self.extract_doctor_features(doctor)
    appointment_features = self.extract_appointment_features(appointment_data)
    
    # Get continuity features
    continuity_features = self.extract_continuity_features(patient, doctor)
    
    # Combine all features
    all_features = {
        **patient_features,
        **doctor_features,
        **appointment_features,
        **continuity_features
    }
    
    # Preprocess for model
    return self.feature_preprocessor.preprocess(all_features)
```

### Balancing with Other Factors
While continuity is important, it's balanced against other factors:

1. **Specialty Match**: For specialized care, matching the doctor's expertise to the patient's condition may outweigh continuity.

2. **Emergency Care**: In emergencies, doctor availability and experience take precedence over continuity.

3. **Language Compatibility**: Effective communication may sometimes be prioritized over continuity.

4. **Workload**: A doctor with a very high workload might not be assigned even if they have continuity with the patient.

### Testing Continuity of Care
Our system includes comprehensive tests to ensure continuity of care is properly implemented:

```python
def test_continuity_of_care(self):
    """Test continuity of care in doctor assignment"""
    # Create past appointments for patients with specific doctors
    past_appointment1 = Appointment.objects.create(
        patient=self.patient1,
        doctor=self.cardio_doctor,
        department=self.cardiology_dept,
        status='completed',
        appointment_date=timezone.now() - timedelta(days=30)
    )
    
    # Create multiple past appointments for stronger continuity
    for days_ago in [90, 60, 30]:
        Appointment.objects.create(
            patient=self.patient3,
            doctor=self.endo_doctor,
            department=self.endocrinology_dept,
            status='completed',
            appointment_date=timezone.now() - timedelta(days=days_ago)
        )
    
    # Test assignment for patients with past appointments
    appointment_data1 = {
        'patient': self.patient1,
        'department': self.cardiology_dept,
        'hospital': self.hospital,
        'appointment_type': 'regular'
    }
    
    # Verify doctor assignment respects continuity
    assigned_doctor1 = doctor_assigner.assign_doctor(appointment_data1)
    self.assertEqual(assigned_doctor1, self.cardio_doctor, 
                    "Patient should be assigned to previous doctor")
```

### Future Enhancements
Planned enhancements to our continuity of care system include:

1. **Patient Preference**: Allow patients to explicitly request continuity with specific doctors.

2. **Team-Based Continuity**: Extend continuity to include care teams, not just individual doctors.

3. **Outcome-Based Weighting**: Adjust continuity weight based on past treatment outcomes.

4. **AI-Driven Optimization**: Use machine learning to dynamically adjust continuity weights based on patient outcomes.

5. **Specialty-Specific Continuity**: Different continuity weights for different specialties based on research. 