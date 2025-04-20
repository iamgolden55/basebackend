# Continuity of Care in Doctor Assignment 🔄

## Overview 🎯
Continuity of care is a critical aspect of healthcare delivery that ensures patients maintain relationships with their healthcare providers over time. This document explains how our system implements and prioritizes continuity of care in the doctor assignment process.

## Table of Contents 📑
- [Continuity of Care in Doctor Assignment 🔄](#continuity-of-care-in-doctor-assignment-)
  - [Overview 🎯](#overview-)
  - [Table of Contents 📑](#table-of-contents-)
  - [Benefits of Continuity 🌟](#benefits-of-continuity-)
  - [Implementation Details 🛠️](#implementation-details-)
    - [Past Appointment Analysis](#past-appointment-analysis)
    - [Continuity Score Calculation](#continuity-score-calculation)
    - [Score Integration](#score-integration)
  - [Continuity Factors 📊](#continuity-factors-)
    - [Appointment Count](#appointment-count)
    - [Recency](#recency)
    - [Department Match](#department-match)
  - [Appointment Type Impact 📝](#appointment-type-impact-)
    - [Follow-up Appointments](#follow-up-appointments)
    - [Regular Appointments](#regular-appointments)
    - [Emergency Appointments](#emergency-appointments)
  - [Balancing with Other Factors ⚖️](#balancing-with-other-factors-)
  - [Testing Continuity of Care 🧪](#testing-continuity-of-care-)
    - [Basic Continuity Test](#basic-continuity-test)
    - [Multiple Appointments Test](#multiple-appointments-test)
    - [Recency Test](#recency-test)
    - [Cross-Department Test](#cross-department-test)
  - [Code Examples 💻](#code-examples-)
    - [Continuity Score Calculation](#continuity-score-calculation-1)
    - [Doctor Score Integration](#doctor-score-integration)
    - [Testing Continuity](#testing-continuity)
  - [Future Enhancements 🚀](#future-enhancements-)

## Benefits of Continuity 🌟

Research shows that continuity of care leads to:

1. **Improved Patient Outcomes**: Patients with consistent providers have better health outcomes.
2. **Increased Patient Satisfaction**: Patients prefer seeing the same doctor who knows their history.
3. **Improved Treatment Adherence**: Patients are more likely to follow treatment plans from doctors they trust.
4. **More Efficient Appointments**: Less time spent reviewing history means more time addressing current issues.
5. **Reduced Healthcare Costs**: Fewer duplicate tests and more efficient care reduces overall costs.
6. **Enhanced Doctor-Patient Communication**: Established relationships lead to better communication.

## Implementation Details 🛠️

Our system implements continuity of care through the following steps:

### Past Appointment Analysis

When a new appointment is created, the system analyzes the patient's appointment history:

```python
def get_past_appointments(patient, department=None):
    """Get patient's past completed appointments"""
    query = Appointment.objects.filter(
        patient=patient,
        status='completed'
    ).select_related('doctor', 'department').order_by('-appointment_date')
    
    if department:
        query = query.filter(department=department)
        
    return query
```

### Continuity Score Calculation

The system calculates a continuity score for each doctor based on past appointments:

```python
def calculate_continuity_score(patient, doctor, department):
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
    appointment_type = appointment_data.get('appointment_type', 'regular')
    if appointment_type == 'follow_up':
        return final_score * 15.0  # Higher weight for follow-ups
    else:
        return final_score * 5.0
```

### Score Integration

The continuity score is integrated into the overall doctor score calculation:

```python
def calculate_doctor_score(doctor, patient, department, appointment_type):
    """Calculate overall score for a doctor"""
    # Base scores
    experience_score = calculate_experience_score(doctor)
    language_score = calculate_language_match(patient, doctor)
    specialty_score = calculate_specialty_match(doctor, patient)
    continuity_score = calculate_continuity_score(patient, doctor, department)
    complexity_score = calculate_complexity_match(doctor, patient)
    workload_penalty = calculate_workload_penalty(doctor)
    
    # Calculate final score
    final_score = (
        experience_score +
        language_score +
        specialty_score +
        continuity_score +
        complexity_score +
        workload_penalty
    )
    
    # Debug logging
    if settings.DEBUG:
        print(f"Score breakdown - Experience: {experience_score:.2f}, "
              f"Language: {language_score:.2f}, "
              f"Specialty: {specialty_score:.2f}, "
              f"Continuity: {continuity_score:.2f}, "
              f"Complexity: {complexity_score:.2f}, "
              f"Workload: {workload_penalty:.1f}, "
              f"Penalty: {0.00:.2f}, "
              f"Final: {final_score:.2f}")
    
    return final_score
```

## Continuity Factors 📊

The continuity score is calculated based on three main factors:

### Appointment Count

The number of past appointments between the patient and doctor:
- More appointments = higher score
- Score maxes out at 5 appointments
- Weight: 30% of continuity score

```python
appointment_count = past_appointments.count()
count_score = min(1.0, appointment_count / 5.0)  # Max out at 5 appointments
```

### Recency

How recently the patient has seen the doctor:
- More recent appointments receive higher scores
- Score decays over a one-year period
- Weight: 50% of continuity score

```python
most_recent = past_appointments.first().appointment_date
days_since = (timezone.now().date() - most_recent.date()).days
recency_score = max(0.0, 1.0 - (days_since / 365.0))  # Decay over a year
```

### Department Match

Whether past appointments were in the same department:
- Same department = full score
- Different department = half score
- Weight: 20% of continuity score

```python
department_match = past_appointments.filter(department=department).exists()
department_score = 1.0 if department_match else 0.5
```

## Appointment Type Impact 📝

The importance of continuity varies based on appointment type:

### Follow-up Appointments

Continuity is given the highest weight for follow-up appointments:
- 3x normal weight
- Ensures patients see the same doctor for ongoing treatment

```python
if appointment_type == 'follow_up':
    continuity_weight = 3.0  # Higher weight for follow-ups
```

### Regular Appointments

Continuity has standard weight for regular appointments:
- 1x normal weight
- Balances continuity with other factors

```python
else:
    continuity_weight = 1.0  # Normal weight for regular appointments
```

### Emergency Appointments

Continuity is not considered for emergency appointments:
- 0x weight (not considered)
- Prioritizes immediate availability and experience

```python
elif appointment_type == 'emergency':
    continuity_weight = 0.0  # No continuity weight for emergencies
```

## Balancing with Other Factors ⚖️

While continuity is important, it's balanced against other factors:

1. **Specialty Match**: For specialized care, matching the doctor's expertise to the patient's condition may outweigh continuity.

2. **Emergency Care**: In emergencies, doctor availability and experience take precedence over continuity.

3. **Language Compatibility**: Effective communication may sometimes be prioritized over continuity.

4. **Workload**: A doctor with a very high workload might not be assigned even if they have continuity with the patient.

## Testing Continuity of Care 🧪

Our system includes comprehensive tests to ensure continuity of care is properly implemented:

### Basic Continuity Test

Tests if a patient is assigned to a doctor they've seen before:

```python
def test_basic_continuity(self):
    """Test basic continuity of care"""
    # Create a past appointment
    past_appointment = Appointment.objects.create(
        patient=self.patient1,
        doctor=self.cardio_doctor,
        department=self.cardiology_dept,
        status='completed',
        appointment_date=timezone.now() - timedelta(days=30)
    )
    
    # Test assignment for a new appointment
    appointment_data = {
        'patient': self.patient1,
        'department': self.cardiology_dept,
        'hospital': self.hospital,
        'appointment_type': 'regular'
    }
    
    # Verify doctor assignment respects continuity
    assigned_doctor = doctor_assigner.assign_doctor(appointment_data)
    self.assertEqual(assigned_doctor, self.cardio_doctor, 
                    "Patient should be assigned to previous doctor")
```

### Multiple Appointments Test

Tests if multiple past appointments increase the continuity score:

```python
def test_multiple_appointments_continuity(self):
    """Test continuity with multiple past appointments"""
    # Create multiple past appointments
    for days_ago in [90, 60, 30]:
        Appointment.objects.create(
            patient=self.patient3,
            doctor=self.endo_doctor,
            department=self.endocrinology_dept,
            status='completed',
            appointment_date=timezone.now() - timedelta(days=days_ago)
        )
    
    # Test assignment
    appointment_data = {
        'patient': self.patient3,
        'department': self.endocrinology_dept,
        'hospital': self.hospital,
        'appointment_type': 'regular'
    }
    
    assigned_doctor = doctor_assigner.assign_doctor(appointment_data)
    self.assertEqual(assigned_doctor, self.endo_doctor,
                    "Patient should be assigned to doctor with multiple past appointments")
```

### Recency Test

Tests if more recent appointments have stronger continuity weight:

```python
def test_recency_continuity(self):
    """Test recency factor in continuity"""
    # Create an older appointment with doctor A
    Appointment.objects.create(
        patient=self.patient2,
        doctor=self.doctor_a,
        department=self.cardiology_dept,
        status='completed',
        appointment_date=timezone.now() - timedelta(days=180)
    )
    
    # Create a more recent appointment with doctor B
    Appointment.objects.create(
        patient=self.patient2,
        doctor=self.doctor_b,
        department=self.cardiology_dept,
        status='completed',
        appointment_date=timezone.now() - timedelta(days=30)
    )
    
    # Test assignment
    appointment_data = {
        'patient': self.patient2,
        'department': self.cardiology_dept,
        'hospital': self.hospital,
        'appointment_type': 'regular'
    }
    
    assigned_doctor = doctor_assigner.assign_doctor(appointment_data)
    self.assertEqual(assigned_doctor, self.doctor_b,
                    "Patient should be assigned to doctor with more recent appointments")
```

### Cross-Department Test

Tests if continuity across departments is handled correctly:

```python
def test_cross_department_continuity(self):
    """Test continuity across different departments"""
    # Create a past appointment in cardiology
    Appointment.objects.create(
        patient=self.patient1,
        doctor=self.cardio_doctor,
        department=self.cardiology_dept,
        status='completed',
        appointment_date=timezone.now() - timedelta(days=30)
    )
    
    # Test assignment in neurology
    appointment_data = {
        'patient': self.patient1,
        'department': self.neurology_dept,  # Different department
        'hospital': self.hospital,
        'appointment_type': 'regular'
    }
    
    assigned_doctor = doctor_assigner.assign_doctor(appointment_data)
    self.assertNotEqual(assigned_doctor, self.cardio_doctor,
                       "Patient should not be assigned to doctor from different department")
```

## Code Examples 💻

### Continuity Score Calculation

```python
def _calculate_continuity_score(self, patient, doctor, department):
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

### Doctor Score Integration

```python
def _calculate_doctor_score(self, doctor, patient, department):
    """Calculate overall score for a doctor"""
    # Base scores
    experience_score = self._calculate_experience_score(doctor)
    language_score = self._calculate_language_match(patient, doctor)
    specialty_score = self._calculate_specialty_match(doctor, patient)
    continuity_score = self._calculate_continuity_score(patient, doctor, department)
    complexity_score = self._calculate_complexity_match(doctor, patient)
    workload_penalty = self._calculate_workload_penalty(doctor)
    
    # Calculate final score
    final_score = (
        experience_score +
        language_score +
        specialty_score +
        continuity_score +
        complexity_score +
        workload_penalty
    )
    
    # Debug logging
    if settings.DEBUG:
        print(f"Score breakdown - Experience: {experience_score:.2f}, "
              f"Language: {language_score:.2f}, "
              f"Specialty: {specialty_score:.2f}, "
              f"Continuity: {continuity_score:.2f}, "
              f"Complexity: {complexity_score:.2f}, "
              f"Workload: {workload_penalty:.1f}, "
              f"Penalty: {0.00:.2f}, "
              f"Final: {final_score:.2f}")
    
    return final_score
```

### Testing Continuity

```python
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
    
    # Verify our expectations
    self.assertEqual(assigned_doctor1, self.cardio_doctor, "Patient 1 should be assigned to cardio_doctor due to continuity")
```

## Future Enhancements 🚀

Planned enhancements to our continuity of care system include:

1. **Patient Preference**: Allow patients to explicitly request continuity with specific doctors.

2. **Team-Based Continuity**: Extend continuity to include care teams, not just individual doctors.

3. **Outcome-Based Weighting**: Adjust continuity weight based on past treatment outcomes.

4. **AI-Driven Optimization**: Use machine learning to dynamically adjust continuity weights based on patient outcomes.

5. **Specialty-Specific Continuity**: Different continuity weights for different specialties based on research.

6. **Family Continuity**: Consider family relationships to promote continuity across family members. 