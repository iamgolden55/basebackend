# Appointment Flow Documentation

## Overview 🎯
This document explains the complete appointment flow in our healthcare system, from creation to completion. The flow includes hospital registration, ML-based doctor assignment, doctor availability checks, payment processing, document management, and status transitions.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Appointment Creation](#appointment-creation)
- [ML-Based Doctor Assignment](#ml-based-doctor-assignment)
- [Language Preference Handling](#language-preference-handling)
- [Validation Rules](#validation-rules)
- [Status Flow](#status-flow)
- [Payment Processing](#payment-processing)
- [Document Management](#document-management)
- [Notifications](#notifications) this
- [Emergency Appointments](#emergency-appointments)
- [Code Examples](#code-examples)
- [API Endpoints](#api-endpoints)
- [Authentication & Authorization](#authentication-authorization)
- [Rate Limiting & Throttling](#rate-limiting-throttling)
- [Error Handling & Response Formats](#error-handling-response-formats)
- [Testing Guide](#testing-guide)
- [Frontend Integration Guide](#frontend-integration-guide)

## Prerequisites
Before creating an appointment, ensure:
1. Patient is registered with the hospital (except for emergencies)
2. Doctors exist and are active in the system
3. Doctor availability is properly configured
4. Hospital and department are properly configured

## Appointment Creation

### Basic Flow
1. Patient registration check
2. Doctor assignment (manual or ML-based)
3. Doctor availability verification
4. Appointment slot allocation
5. Initial status set to 'pending'
6. Payment requirement check
7. Notification dispatch

### Example Code
```python
# Standard appointment creation
appointment = Appointment.objects.create(
    patient=patient,
    doctor=doctor,
    hospital=hospital,
    department=department,
    appointment_date=appointment_date,
    appointment_type='general',
    status='pending',
    priority='normal',
    fee=fee
)

# ML-based appointment creation
appointment_data = {
    'patient': patient,
    'hospital': hospital,
    'department': department,
    'appointment_type': 'regular',
    'priority': 'normal',
    'appointment_date': appointment_date
}

# Get ML-assigned doctor
assigned_doctor = doctor_assigner.assign_doctor(appointment_data)

appointment = Appointment.objects.create(
    patient=patient,
    doctor=assigned_doctor,
    hospital=hospital,
    department=department,
    appointment_date=appointment_date,
    appointment_type='regular',
    status='pending',
    priority='normal',
    fee=fee
)
```

## ML-Based Doctor Assignment and Availability 🤖

### Overview
Our system uses a sophisticated machine learning approach to match patients with the most suitable doctors. This ensures optimal healthcare delivery while maintaining continuity of care and considering various factors like doctor expertise, patient preferences, and scheduling constraints.

### Key Features
1. **Smart Doctor Selection** 🎯
   - Experience matching
   - Language compatibility
   - Specialty alignment
   - Workload balancing
   - Patient history consideration

2. **Availability Management** ⏰
   - Real-time schedule tracking
   - Conflict prevention
   - Emergency slot allocation
   - Buffer time management

### Scoring System
The ML system calculates doctor scores based on weighted factors:

```python
Experience: 30%
Success Rate: 20%
Language Match: Bonus of 2.0
Specialty Match: Bonus of 3.0
Continuity of Care: Bonus of 2.5
Workload: Penalty based on current load
```

### Doctor Availability Controls
Doctors have granular control over their schedules:
```python
available_for_appointments = models.BooleanField(
    default=True,
    help_text="Whether accepting new appointments"
)
consultation_hours_start = models.TimeField(
    help_text="Start time of consultation hours"
)
consultation_hours_end = models.TimeField(
    help_text="End time of consultation hours"
)
consultation_days = models.CharField(
    max_length=100,
    help_text="Comma-separated days, e.g., 'Mon,Tue,Wed'"
)
max_daily_appointments = models.PositiveIntegerField(
    default=20,
    help_text="Maximum appointments per day"
)
appointment_duration = models.PositiveIntegerField(
    default=30,
    help_text="Default appointment duration in minutes"
)
```

### Assignment Process Flow 🔄

1. **Initial Screening**
   - Check doctor availability
   - Verify consultation hours
   - Validate appointment slots
   - Check maximum daily limit

2. **Score Calculation**
   ```python
   final_score = (
       experience_score * 0.3 +
       success_rate * 0.2 +
       language_match_bonus +
       specialty_match_bonus +
       continuity_bonus -
       workload_penalty
   )
   ```

3. **Assignment Rules**
   - Highest scoring available doctor is selected
   - Emergency cases bypass normal scoring
   - Follow-ups prioritize previous doctors
   - Workload distribution is considered

4. **Validation Steps**
   - Verify doctor's schedule
   - Check for conflicts
   - Validate time slots
   - Ensure doctor permissions

### Example Assignment Code
```python
def assign_doctor(appointment_data):
    """Assign the most suitable doctor for an appointment"""
    config = DoctorAssignmentConfig.objects.get(
        hospital=appointment_data['hospital']
    )
    
    best_doctor = None
    best_score = float('-inf')
    
    for doctor in available_doctors:
        # Extract features
        features = [
            doctor.years_of_experience / 30.0,  # Normalize experience
            calculate_language_match(patient, doctor),
            calculate_current_workload(doctor),
            calculate_success_rate(doctor),
            calculate_continuity_score(patient, doctor),
            1 if appointment_data['priority'] == 'emergency' else 0
        ]
        
        # Calculate score
        score = calculate_doctor_score(features)
        
        # Update best doctor if current score is higher
        if score > best_score and doctor.is_available_at(appointment_date):
            best_doctor = doctor
            best_score = score
    
    return {
        'doctor': best_doctor,
        'score': best_score,
        'can_auto_approve': best_score >= config.min_doctor_score
    }
```

### Best Practices 🌟

1. **Availability Management**
   - Regular schedule updates
   - Buffer time between appointments
   - Emergency slot reservations
   - Holiday calendar integration

2. **Assignment Optimization**
   - Regular model retraining
   - Performance monitoring
   - Feedback integration
   - Load balancing

3. **Error Handling**
   - Graceful fallbacks
   - Conflict resolution
   - Emergency override protocols
   - Notification system

### Future Improvements 🚀

1. **Enhanced ML Features**
   - Patient feedback integration
   - Treatment success rate
   - Specialty-based routing
   - Dynamic scheduling

2. **Availability Management**
   - Real-time calendar sync
   - Mobile app integration
   - Automated schedule optimization
   - Smart break scheduling

3. **System Integration**
   - EMR system integration
   - Insurance verification
   - Payment processing
   - Document management

## Language Preference Handling

The system considers patient language preferences when assigning doctors to ensure effective communication. This is particularly important for international patients or in multilingual regions.

### Language Fields
The system uses several fields to determine language compatibility:

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

### Language Matching Algorithm
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

### Admin Approval Interface
```python
def admin_approve_assignment(appointment, approved_doctor=None):
    """Admin approval for doctor assignment"""
    if approved_doctor:
        appointment.doctor = approved_doctor
    
    appointment.status = 'confirmed'
    appointment.admin_approved_at = timezone.now()
    appointment.save()
    
    # Send notifications after admin approval
    notify_doctor_assignment(appointment)
    notify_patient_confirmation(appointment)
```

## Validation Rules

### Hospital Registration
```python
def _validate_hospital_registration(self):
    """Check if patient is registered with the hospital"""
    registrations = self.patient.get_registered_hospitals()
    
    # Skip check for emergencies
    if self.priority == 'emergency':
        return True
        
    return registrations.filter(hospital=self.hospital).exists()
```

### Doctor Availability
Doctor availability is checked based on:
1. Consultation days (e.g., 'Mon,Tue,Wed,Thu,Fri')
2. Consultation hours (e.g., 9 AM - 5 PM)
3. Existing appointments
4. Maximum daily appointment limit
5. Current appointment context (for updates)

```python
def is_available_at(self, datetime, is_emergency=False, current_appointment=None):
    """Check if doctor is available at a specific datetime"""
    if not self.can_practice:
        return False
        
    # Emergency appointments bypass normal checks
    if is_emergency:
        return True
        
    # Check consultation day
    if not self.is_available_on_day(datetime.strftime('%A')):
        return False
        
    # Check consultation hours
    time = datetime.time()
    if not (self.consultation_hours_start <= time <= self.consultation_hours_end):
        return False
        
    # Check existing appointments
    query = Appointment.objects.filter(
        doctor=self,
        appointment_date=datetime,
        status__in=['confirmed', 'pending']
    )
    
    # Exclude current appointment if provided
    if current_appointment and current_appointment.pk:
        query = query.exclude(pk=current_appointment.pk)
        
    return not query.exists()
```

### Same Specialty, Same Day Validation
The system prevents patients from scheduling multiple appointments in the same specialty on the same day:

```python
# Check for existing appointments with the same specialty on the same day
if not is_emergency:  # Skip for emergency appointments
    same_specialty_appointments = Appointment.objects.filter(
        patient=self.patient,
        appointment_date__date=self.appointment_date.date(),
        department=self.department,  # Same department/specialty
        status__in=['pending', 'confirmed', 'in_progress']
    )
    
    # Exclude current appointment if it's being updated
    if self.pk:
        same_specialty_appointments = same_specialty_appointments.exclude(pk=self.pk)
    
    if same_specialty_appointments.exists():
        raise ValidationError({
            'appointment_date': ["You already have an appointment in this specialty on this date. Please choose another date or specialty."]
        })
```

This validation:
- Prevents patients from booking multiple appointments in the same specialty on the same day
- Allows booking in different specialties on the same day
- Bypasses the check for emergency appointments
- Excludes the current appointment when updating existing appointments
- Provides a clear error message suggesting alternatives

## Status Flow

### Valid Status Transitions
```python
valid_transitions = {
    'pending': ['confirmed', 'cancelled', 'rejected', 'referred', 'pending_admin_approval'],
    'pending_admin_approval': ['confirmed', 'cancelled', 'rejected'],
    'confirmed': ['in_progress', 'cancelled', 'no_show', 'referred'],
    'in_progress': ['completed', 'referred'],
    'completed': [],  # No further transitions
    'cancelled': [],  # No further transitions
    'no_show': [],    # No further transitions
    'rejected': [],   # No further transitions
    'referred': ['pending'],  # Can start new process
    'rescheduled': ['pending']
}
```

### Status Transition Validation
```python
def _is_valid_status_transition(self, old_status, new_status):
    """Check if status transition is valid"""
    return new_status in valid_transitions.get(old_status, [])
```

## Payment Processing

### Payment States
1. pending: Initial state
2. partial: Partial payment received
3. completed: Full payment received
4. waived: Payment requirement waived
5. insurance: Being processed by insurance
6. refunded: Payment refunded

### Example Payment Flow
```python
# Create payment transaction
payment = PaymentTransaction.objects.create(
    appointment=appointment,
    amount_display=fee.base_fee,
    currency='NGN',
    payment_method='card',
    payment_status='pending'
)

# Complete payment
payment.mark_as_completed(user=patient)
```

## Document Management

### Document Types
- prescription
- lab_report
- medical_certificate
- referral_letter
- consent_form
- insurance_claim
- medical_history
- test_result
- x_ray
- scan
- other

### Document Creation and Signing
```python
# Create document
document = AppointmentDocument.objects.create(
    appointment=appointment,
    document_type='prescription',
    title='Test Prescription',
    file=file_object,
    requires_signature=True
)

# Sign document
document.sign_document(patient)
```

## Notifications

### Notification Types
```python
NOTIFICATION_TYPE_CHOICES = [
    'email',        # Email notifications
    'sms',          # SMS notifications
    'in_app',       # In-app notifications
    'whatsapp'      # WhatsApp notifications
]

EVENT_TYPE_CHOICES = [
    'booking_confirmation',       # New booking
    'appointment_reminder',       # Upcoming appointment
    'appointment_update',         # Any changes
    'appointment_cancellation',   # Cancellation
    'appointment_rescheduled',    # New date/time
    'payment_reminder',          # Payment needed
    'payment_confirmation',      # Payment received
    'doctor_unavailable',        # Doctor cancellation
    'referral_notification',     # Referral info
    'follow_up_reminder',        # Follow-up needed
    'emergency_notification',    # Urgent matters
    'test_results_available',    # Test results ready
    'pre_appointment_instructions'  # Preparation info
]
```

### Notification Flow

1. **Booking Confirmation**
```python
def _send_appointment_confirmation(self, appointment):
    """Send appointment confirmation with error handling"""
    try:
        # Create email notification for the patient
        AppointmentNotification.objects.create(
            appointment=appointment,
            recipient=appointment.patient,
            notification_type='email',
            event_type='booking_confirmation',
            subject='Appointment Confirmation',
            message=f'Your appointment with Dr. {appointment.doctor.user.get_full_name()} '
                    f'has been scheduled for {appointment.appointment_date.strftime("%B %d, %Y at %I:%M %p")}.',
            scheduled_time=timezone.now()
        )
        
        # Create SMS notification for the patient
        AppointmentNotification.objects.create(
            appointment=appointment,
            recipient=appointment.patient,
            notification_type='sms',
            event_type='booking_confirmation',
            subject='Appointment Confirmation',
            message=f'Your appointment with Dr. {appointment.doctor.user.get_full_name()} '
                    f'has been scheduled for {appointment.appointment_date.strftime("%B %d, %Y at %I:%M %p")}.',
            scheduled_time=timezone.now()
        )
        
        # Create notification for the doctor
        AppointmentNotification.objects.create(
            appointment=appointment,
            recipient=appointment.doctor.user,
            notification_type='email',
            event_type='booking_confirmation',
            subject='New Appointment',
            message=f'New appointment scheduled with {appointment.patient.get_full_name()} '
                    f'on {appointment.appointment_date.strftime("%B %d, %Y at %I:%M %p")}.',
            scheduled_time=timezone.now()
        )
        
        # Create reminders
        appointment.create_reminders()
        
    except Exception as e:
        logger.error(f"Error sending appointment confirmation: {str(e)}")
        # Don't raise the error - appointment creation should succeed even if notification fails
```

2. **Appointment Reminders**
```python
def create_reminders(self):
    """Create reminders for the appointment"""
    reminder_schedule = [
        {'days_before': 7, 'type': 'email'},  # 1 week before
        {'days_before': 2, 'type': 'email'},  # 2 days before
        {'days_before': 1, 'type': 'sms'},    # 1 day before
        {'hours_before': 2, 'type': 'sms'}    # 2 hours before
    ]
    
    AppointmentNotification.create_reminders(self, reminder_schedule)
    
    # Update fields directly in the database to avoid recursive save
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute(
            "UPDATE api_appointment SET reminder_sent = %s, last_reminder_sent = %s WHERE id = %s",
            [True, timezone.now(), self.id]
        )
```

3. **Status Change Notifications**
```python
def cancel(self, reason=None):
    """Cancel the appointment"""
    if self.status not in ['pending', 'confirmed']:
        raise ValidationError("Only pending or confirmed appointments can be cancelled")
        
    self.status = 'cancelled'
    self.cancelled_at = timezone.now()
    self.cancellation_reason = reason
    self.save()
    
    # Send cancellation notification
    AppointmentNotification.objects.create(
        appointment=self,
        notification_type='email',
        event_type='appointment_cancellation',
        recipient=self.patient,
        subject=f"Appointment Cancelled - {self.appointment_id}",
        message=(
            f"Dear {self.patient.get_full_name()},\n\n"
            f"Your appointment has been cancelled.\n"
            f"Reason: {reason or 'No reason provided'}"
        ),
        template_name='appointment_cancellation'
    )
```

4. **Emergency Notifications**
```python
def create_emergency_notification(self, message):
    """Create emergency notification"""
    # Send SMS to patient
    AppointmentNotification.objects.create(
        appointment=self,
        notification_type='sms',
        event_type='emergency_notification',
        recipient=self.patient,
        subject='Urgent: Appointment Update',
        message=message,
        scheduled_time=timezone.now()
    )
    
    # Send email to patient
    AppointmentNotification.objects.create(
        appointment=self,
        notification_type='email',
        event_type='emergency_notification',
        recipient=self.patient,
        subject='Urgent: Appointment Update',
        message=message,
        template_name='emergency_notification',
        scheduled_time=timezone.now()
    )
```

### Notification Delivery

Each notification:
- Uses HTML templates for emails
- Sends SMS for urgent communications
- Creates in-app notifications
- Supports WhatsApp messages
- Tracks delivery status
- Includes error handling and logging

### Templates Location
```
api/templates/email/
├── appointment_booking_confirmation.html
├── appointment_reminder.html
├── appointment_cancellation.html
├── payment_confirmation.html
├── payment_reminder.html
├── doctor_unavailable.html
├── referral_notification.html
├── follow_up_reminder.html
├── emergency_notification.html
├── test_results_available.html
└── pre_appointment_instructions.html
```

## Emergency Appointments

Emergency appointments have special handling:
1. Bypass hospital registration check
2. Bypass doctor availability check
3. Bypass appointment limit check
4. Higher priority in scheduling

```python
appointment = Appointment.objects.create(
    patient=patient,
    doctor=doctor,
    hospital=hospital,
    department=department,
    appointment_date=appointment_date,
    status='pending',
    priority='emergency'  # Bypasses normal validation
)
```

## Code Examples

### Complete Appointment Flow with ML Assignment
```python
# 1. Prepare appointment data
appointment_data = {
    'patient': patient,
    'hospital': hospital,
    'department': department,
    'appointment_type': 'regular',
    'priority': 'normal',
    'appointment_date': appointment_date
}

# 2. Get ML-assigned doctor
assigned_doctor = doctor_assigner.assign_doctor(appointment_data)

# 3. Create appointment
appointment = Appointment.objects.create(
    patient=patient,
    doctor=assigned_doctor,
    hospital=hospital,
    department=department,
    appointment_date=appointment_date,
    status='pending'
)

# 4. Create notification
AppointmentNotification.create_booking_confirmation(appointment)

# 5. Process payment
payment = PaymentTransaction.objects.create(
    appointment=appointment,
    amount=fee.base_fee,
    status='pending'
)
payment.mark_as_completed(user=patient)

# 6. Create and sign document
document = AppointmentDocument.objects.create(
    appointment=appointment,
    document_type='prescription',
    file=file_object
)
document.sign_document(patient)

# 7. Status transitions
appointment.status = 'confirmed'
appointment.save()

appointment.status = 'in_progress'
appointment.save()

appointment.status = 'completed'
appointment.save()
```

### Testing the Flow
See `api/tests/test_appointment_flow.py` for complete test cases demonstrating both standard and ML-based appointment flows.

## Best Practices
1. Always use the model's clean() method for validation
2. Handle emergency appointments appropriately
3. Validate status transitions
4. Create appropriate notifications
5. Maintain proper document trail
6. Handle payments securely
7. Use transactions where appropriate
8. Use ML assignment for optimal doctor allocation
9. Handle concurrent appointment creation properly
10. Validate doctor availability thoroughly

## Common Issues and Solutions
1. **Invalid Status Transition**
   - Check valid_transitions dictionary
   - Ensure proper status flow

2. **Doctor Unavailable**
   - Verify consultation days and hours
   - Check existing appointments
   - Consider emergency override
   - Handle concurrent bookings properly
   - Exclude current appointment when updating

3. **ML Assignment Issues**
   - Verify doctor scoring factors
   - Check availability before assignment
   - Handle edge cases (no available doctors)
   - Consider workload distribution
   - Verify admin approval requirements
   - Handle auto-approval conditions properly

4. **Payment Issues**
   - Verify payment amount
   - Check payment status
   - Handle insurance cases

5. **Document Signing**
   - Ensure proper file upload
   - Verify signature requirements
   - Handle multiple signers if needed

6. **Language Matching Issues**
   - Ensure doctor languages are properly formatted
   - Verify patient language preferences are set correctly
   - Check that the language matching algorithm is considering all relevant fields
   - Test with various language combinations to ensure proper matching

## Future Improvements
1. Add support for recurring appointments
2. Implement waitlist functionality
3. Add support for group appointments
4. Enhance notification system
5. Improve emergency handling
6. Enhance ML doctor assignment algorithm
7. Add real-time availability updates
8. Implement smart rescheduling
9. Add predictive appointment duration
10. Implement load balancing for doctor assignments
11. Expand language preference options and matching algorithm

## Related Documentation
- Doctor Availability System
- ML-Based Doctor Assignment
- Payment Processing
- Document Management
- Notification System
- Hospital Registration 

## Continuity of Care

### Overview
Continuity of care is a key factor in our doctor assignment system. It ensures patients see the same doctor for related issues over time, which has been shown to improve patient outcomes and satisfaction.

### Benefits of Continuity of Care
- Improved patient outcomes
- Enhanced patient satisfaction
- Better treatment adherence
- More efficient appointments
- Reduced healthcare costs

### Implementation in Appointment Flow
Our system implements continuity of care through the following steps:

1. **Past Appointment Analysis**: When a new appointment is created, the system analyzes the patient's appointment history.

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

2. **Continuity Score Calculation**: The system calculates a continuity score for each doctor based on past appointments.

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

3. **Score Integration**: The continuity score is integrated into the overall doctor score calculation.

```python
def calculate_doctor_score(doctor, patient, department, appointment_type):
    """Calculate overall score for a doctor"""
    # Base scores
    experience_score = calculate_experience_score(doctor)
    language_score = calculate_language_match(patient, doctor)
    specialty_score = calculate_specialty_match(doctor, patient)
    continuity_score = calculate_continuity_score(patient, doctor, department)
    workload_penalty = calculate_workload_penalty(doctor)
    
    # Adjust weights based on appointment type
    if appointment_type == 'follow_up':
        continuity_weight = 3.0  # Higher weight for follow-ups
    elif appointment_type == 'emergency':
        continuity_weight = 0.0  # No continuity weight for emergencies
    else:
        continuity_weight = 1.0  # Normal weight for regular appointments
    
    # Calculate final score
    final_score = (
        experience_score +
        language_score +
        specialty_score +
        (continuity_score * continuity_weight) +
        workload_penalty
    )
    
    return final_score
```

### Continuity Factors
The continuity score is calculated based on three main factors:

1. **Appointment Count**: The number of past appointments between the patient and doctor.
   - More appointments = higher score
   - Score maxes out at 5 appointments

2. **Recency**: How recently the patient has seen the doctor.
   - More recent appointments receive higher scores
   - Score decays over a one-year period

3. **Department Match**: Whether past appointments were in the same department.
   - Same department = full score
   - Different department = half score

### Appointment Type Impact
The importance of continuity varies based on appointment type:

1. **Follow-up Appointments**: Continuity is given the highest weight (3x normal)
   ```python
   if appointment_type == 'follow_up':
       continuity_weight = 3.0
   ```

2. **Regular Appointments**: Continuity has standard weight
   ```python
   else:
       continuity_weight = 1.0
   ```

3. **Emergency Appointments**: Continuity is not considered
   ```python
   elif appointment_type == 'emergency':
       continuity_weight = 0.0
   ```

### Balancing with Other Factors
While continuity is important, it's balanced against other factors:

1. **Specialty Match**: For specialized care, matching the doctor's expertise to the patient's condition may outweigh continuity.

2. **Emergency Care**: In emergencies, doctor availability and experience take precedence over continuity.

3. **Language Compatibility**: Effective communication may sometimes be prioritized over continuity.

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

## API Endpoints 🌐

### Appointment Management
```python
# Base URL: /api/v1

# Appointments
POST    /appointments/              # Create appointment
GET     /appointments/              # List appointments
GET     /appointments/{id}/         # Get appointment details
PATCH   /appointments/{id}/         # Update appointment
DELETE  /appointments/{id}/         # Cancel appointment

# Doctor Management
GET     /doctors/                   # List available doctors
GET     /doctors/{id}/             # Get doctor details
GET     /doctors/{id}/schedule/    # Get doctor's schedule

# Availability
GET     /doctors/{id}/availability/  # Check doctor's availability
POST    /doctors/{id}/block-time/   # Block time slot
```

### Request/Response Examples

1. **Create Appointment**
```json
// Request
POST /api/v1/appointments/
{
    "doctor_id": 2,
    "hospital_id": 1,
    "department_id": 1,
    "appointment_date": "2025-03-03T11:00:00Z",
    "appointment_type": "consultation",
    "priority": "normal"
}

// Success Response (201 Created)
{
    "id": "APT-AB481952",
    "status": "pending",
    "doctor": {
        "id": 2,
        "name": "Dr. John Doe",
        "department": "General Medicine"
    },
    "appointment_date": "2025-03-03T11:00:00Z",
    "created_at": "2025-02-26T04:16:48Z"
}
```

2. **Get Appointment**
```json
// Response (200 OK)
{
    "id": "APT-AB481952",
    "status": "confirmed",
    "patient": {
        "id": 1,
        "name": "Jane Smith"
    },
    "doctor": {
        "id": 2,
        "name": "Dr. John Doe"
    },
    "hospital": {
        "id": 1,
        "name": "General Hospital"
    },
    "department": {
        "id": 1,
        "name": "General Medicine"
    },
    "appointment_date": "2025-03-03T11:00:00Z",
    "appointment_type": "consultation",
    "priority": "normal",
    "fee": {
        "amount": 150.00,
        "currency": "USD",
        "status": "pending"
    }
}
```

## Authentication & Authorization 🔐

### JWT Authentication
```python
# Get access token
POST /api/token/
{
    "username": "user@example.com",
    "password": "secure_password"
}

# Response
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1..."
}
```

### Permission Levels
```python
class AppointmentPermissions(permissions.BasePermission):
    def has_permission(self, request, view):
        # Admin can do everything
        if request.user.is_staff:
            return True
            
        # Doctors can view their appointments
        if request.user.is_doctor:
            return request.method in ['GET', 'PATCH']
            
        # Patients can create and view their appointments
        return request.method in ['GET', 'POST']
```

## Rate Limiting & Throttling ⚡

### Configuration
```python
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/day',
        'user': '1000/day',
        'appointment_creation': '10/hour'
    }
}
```

### Custom Throttling
```python
class AppointmentThrottle(UserRateThrottle):
    rate = '10/hour'
    scope = 'appointment_creation'

    def get_cache_key(self, request, view):
        if request.user.is_authenticated:
            return f'appointment_throttle_{request.user.pk}'
        return None
```

## Error Handling & Response Formats ❌

### Standard Error Responses
```json
// 400 Bad Request
{
    "error": {
        "code": "invalid_request",
        "message": "Invalid appointment data",
        "details": {
            "appointment_date": ["Date cannot be in the past"],
            "doctor_id": ["Doctor is not available"]
        }
    }
}

// 401 Unauthorized
{
    "error": {
        "code": "authentication_failed",
        "message": "Invalid or expired token"
    }
}

// 403 Forbidden
{
    "error": {
        "code": "permission_denied",
        "message": "You don't have permission to perform this action"
    }
}

// 404 Not Found
{
    "error": {
        "code": "not_found",
        "message": "Appointment not found"
    }
}

// 429 Too Many Requests
{
    "error": {
        "code": "rate_limit_exceeded",
        "message": "Too many requests",
        "retry_after": 3600
    }
}
```

### Error Handling Middleware
```python
class APIErrorHandler:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        if 400 <= response.status_code < 600:
            response.data = {
                'error': {
                    'code': self._get_error_code(response),
                    'message': response.data.get('detail', str(response.data)),
                    'details': self._get_error_details(response)
                }
            }
        
        return response
```

## Testing Guide 🧪

### Unit Tests
```python
class AppointmentTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.doctor = Doctor.objects.create(...)
        self.patient = Patient.objects.create(...)
        
    def test_create_appointment(self):
        data = {
            "doctor_id": self.doctor.id,
            "appointment_date": "2025-03-03T11:00:00Z",
            "appointment_type": "consultation"
        }
        response = self.client.post('/api/appointments/', data)
        self.assertEqual(response.status_code, 201)
        
    def test_doctor_availability(self):
        # Test doctor availability check
        response = self.client.get(f'/api/doctors/{self.doctor.id}/availability/')
        self.assertEqual(response.status_code, 200)
```

### Integration Tests
```python
class AppointmentFlowTests(TestCase):
    def test_complete_appointment_flow(self):
        # 1. Create appointment
        appointment = self.create_appointment()
        
        # 2. Confirm appointment
        self.confirm_appointment(appointment.id)
        
        # 3. Process payment
        self.process_payment(appointment.id)
        
        # 4. Complete appointment
        self.complete_appointment(appointment.id)
        
        # 5. Verify final status
        appointment.refresh_from_db()
        self.assertEqual(appointment.status, 'completed')
```

### Performance Tests
```python
class AppointmentLoadTests(TestCase):
    def test_concurrent_appointments(self):
        """Test system handling multiple concurrent appointment requests"""
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(self.create_appointment)
                for _ in range(10)
            ]
            results = [f.result() for f in futures]
            
        # Verify all appointments were created
        self.assertEqual(len(results), 10)
        self.assertTrue(all(r.status_code == 201 for r in results))
```

## Frontend Integration Guide 🎨

### API Client Setup
```typescript
// appointment.service.ts
export class AppointmentService {
    async createAppointment(data: AppointmentCreate): Promise<Appointment> {
        const response = await this.http.post('/api/appointments/', data);
        return response.data;
    }
    
    async getAppointment(id: string): Promise<Appointment> {
        const response = await this.http.get(`/api/appointments/${id}/`);
        return response.data;
    }
}
```

### Error Handling
```typescript
// error.interceptor.ts
export class ErrorInterceptor {
    intercept(error: HttpErrorResponse) {
        switch (error.status) {
            case 401:
                // Handle authentication error
                this.authService.logout();
                break;
            case 403:
                // Handle permission error
                this.notificationService.error('Permission denied');
                break;
            case 429:
                // Handle rate limiting
                this.notificationService.warning('Please try again later');
                break;
            default:
                // Handle other errors
                this.notificationService.error('An error occurred');
        }
    }
}
```

### State Management
```typescript
// appointment.store.ts
export class AppointmentStore {
    private appointments = new BehaviorSubject<Appointment[]>([]);
    
    async createAppointment(data: AppointmentCreate) {
        try {
            const appointment = await this.appointmentService.createAppointment(data);
            this.appointments.next([...this.appointments.value, appointment]);
            return appointment;
        } catch (error) {
            this.handleError(error);
            throw error;
        }
    }
}
```