# Appointment System Documentation

## Overview

The appointment system manages medical appointments between patients and doctors. It handles scheduling, notifications, reminders, and status management.

## Core Components

### 1. Appointment Model

```python
class Appointment:
    # Core Fields
    appointment_id        # Unique identifier (APT-YYYYMMDD-XXX)
    patient              # ForeignKey to Patient
    doctor              # ForeignKey to Doctor
    department          # ForeignKey to Department
    appointment_type    # Choice: consultation, follow_up, emergency, etc.
    priority           # Choice: normal, urgent, emergency
    status             # Choice: scheduled, completed, cancelled, etc.
    
    # Timing Fields
    appointment_date    # Date of appointment
    appointment_time    # Time slot
    duration           # Duration in minutes
    
    # Additional Info
    symptoms           # Text description
    diagnosis         # Text field (filled after appointment)
    prescription      # Text field (filled after appointment)
    notes             # Additional notes
    
    # Tracking Fields
    created_at        # Creation timestamp
    updated_at        # Last update timestamp
    created_by        # User who created the appointment
    updated_by        # User who last updated the appointment
```

### 2. Status Types

```python
APPOINTMENT_STATUS_CHOICES = [
    'scheduled',      # Initial state
    'confirmed',      # After patient confirms
    'in_progress',    # During appointment
    'completed',      # After completion
    'cancelled',      # Cancelled by either party
    'no_show',        # Patient didn't show up
    'rescheduled'     # Moved to new time
]
```

### 3. Priority Levels

```python
PRIORITY_CHOICES = [
    'normal',         # Regular appointment
    'urgent',         # Needs quick attention
    'emergency'       # Immediate attention required
]
```

### 4. Appointment Types

```python
APPOINTMENT_TYPE_CHOICES = [
    'consultation',   # First visit
    'follow_up',      # Follow-up visit
    'emergency',      # Emergency case
    'routine_check',  # Regular checkup
    'procedure',      # Medical procedure
    'test',          # Medical test
    'vaccination'     # Vaccination
]
```

## Key Methods

### 1. Appointment Creation

```python
def create_appointment(patient, doctor, date, time, **kwargs):
    """
    Creates a new appointment with validation.
    
    Args:
        patient: Patient object
        doctor: Doctor object
        date: Appointment date
        time: Appointment time
        **kwargs: Additional fields
    
    Returns:
        Appointment object
    
    Raises:
        ValidationError: If validation fails
    """
    # 1. Validate doctor availability
    # 2. Check for conflicting appointments
    # 3. Create appointment
    # 4. Send notifications
    # 5. Create reminders
```

### 2. Status Changes

```python
def update_status(new_status, reason=None):
    """
    Updates appointment status with notifications.
    
    Args:
        new_status: New status value
        reason: Optional reason for change
    """
    # 1. Validate status transition
    # 2. Update status
    # 3. Send notifications
    # 4. Update related records
```

### 3. Notification System

The appointment system uses a comprehensive notification system that sends:

1. **Booking Confirmations**
   - Email + SMS to patient
   - Email to doctor
   - Contains appointment details

2. **Reminders**
   - 7 days before (email)
   - 2 days before (email)
   - 1 day before (SMS)
   - 2 hours before (SMS)

3. **Status Updates**
   - Cancellations
   - Rescheduling
   - Completion notifications

4. **Emergency Updates**
   - Immediate notifications
   - High priority delivery

### 4. Validation Rules

1. **Time Slot Validation**
   ```python
   def validate_time_slot(doctor, date, time):
       """
       Validates if the time slot is available.
       
       Args:
           doctor: Doctor object
           date: Proposed date
           time: Proposed time
       
       Returns:
           bool: True if valid
       """
       # Check doctor's schedule
       # Check existing appointments
       # Validate working hours
       # Check holiday calendar
   ```

2. **Doctor Availability**
   ```python
   def check_doctor_availability(doctor, date):
       """
       Checks if doctor is available on date.
       
       Args:
           doctor: Doctor object
           date: Date to check
       
       Returns:
           bool: True if available
       """
       # Check doctor's schedule
       # Check leave calendar
       # Check department roster
   ```

### 5. Payment Integration

```python
def process_payment(appointment):
    """
    Processes appointment payment.
    
    Args:
        appointment: Appointment object
    
    Returns:
        Payment object
    """
    # Calculate fees
    # Process payment
    # Send receipt
    # Update appointment status
```

## Error Handling

1. **Validation Errors**
   - Double booking
   - Invalid time slots
   - Doctor unavailability

2. **Status Transition Errors**
   - Invalid transitions
   - Missing requirements

3. **Notification Errors**
   - Failed deliveries
   - Invalid contact info

## Best Practices

1. **Scheduling**
   - Always validate time slots
   - Check doctor availability
   - Consider department load
   - Respect priority levels

2. **Notifications**
   - Use templates for consistency
   - Include all relevant details
   - Handle delivery failures
   - Track notification status

3. **Status Management**
   - Validate transitions
   - Keep audit trail
   - Notify all parties
   - Handle edge cases

4. **Emergency Handling**
   - Prioritize emergency cases
   - Fast-track processing
   - Immediate notifications
   - Override normal rules

## Integration Points

1. **Electronic Health Records (EHR)**
   - Patient history
   - Previous appointments
   - Test results
   - Prescriptions

2. **Payment System**
   - Fee calculation
   - Payment processing
   - Receipt generation
   - Refund handling

3. **Notification Service**
   - Email delivery
   - SMS gateway
   - Push notifications
   - WhatsApp integration

4. **Analytics System**
   - Appointment metrics
   - Doctor utilization
   - Patient patterns
   - Department load

## Security Considerations

1. **Data Protection**
   - Encrypt sensitive data
   - Mask personal information
   - Secure transmission
   - Access control

2. **Audit Trail**
   - Log all changes
   - Track user actions
   - Record timestamps
   - Maintain history

3. **Access Control**
   - Role-based access
   - Permission levels
   - Action logging
   - Session management 