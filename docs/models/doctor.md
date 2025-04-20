# Doctor Model Documentation 👨‍⚕️

## Overview
The Doctor model represents medical professionals within the hospital system. It manages doctor information, availability, appointments, and professional credentials.

## Model Structure

### Basic Information
| Field | Type | Description |
|-------|------|-------------|
| `user` | OneToOneField | Link to User model |
| `department` | ForeignKey | Department where doctor works |
| `hospital` | ForeignKey | Primary hospital affiliation |
| `specialization` | CharField | Medical specialization |

### Professional Credentials
| Field | Type | Description |
|-------|------|-------------|
| `medical_license_number` | CharField | Unique license number |
| `license_expiry_date` | DateField | License expiry date |
| `years_of_experience` | PositiveIntegerField | Years of practice |
| `qualifications` | JSONField | Academic qualifications |
| `board_certifications` | TextField | Medical board certifications |
| `surgical_subspecialty` | CharField | Required for surgical departments |

### Availability Management
| Field | Type | Description |
|-------|------|-------------|
| `is_active` | BooleanField | Current practice status |
| `status` | CharField | Working status (active/leave/suspended/retired) |
| `available_for_appointments` | BooleanField | Accepting new appointments |
| `consultation_hours_start` | TimeField | Daily start time |
| `consultation_hours_end` | TimeField | Daily end time |
| `consultation_days` | CharField | Available days (comma-separated) |
| `max_daily_appointments` | PositiveIntegerField | Maximum appointments per day |
| `appointment_duration` | PositiveIntegerField | Minutes per appointment |

### Additional Information
| Field | Type | Description |
|-------|------|-------------|
| `research_interests` | TextField | Research areas |
| `publications` | TextField | Published works |
| `languages_spoken` | CharField | Languages (comma-separated) |
| `medical_school` | CharField | Education institution |
| `graduation_year` | PositiveIntegerField | Year of graduation |

### Continuity of Care Metrics
| Field | Type | Description |
|-------|------|-------------|
| `continuity_of_care_rating` | FloatField | Rating (0-10) for continuity effectiveness |
| `repeat_patient_ratio` | FloatField | Ratio of repeat to new patients |
| `patient_retention_rate` | FloatField | Percentage of patients who return |
| `avg_appointments_per_patient` | FloatField | Average number of appointments per patient |
| `long_term_patient_count` | IntegerField | Patients with >5 appointments |
| `continuity_preference_weight` | FloatField | Doctor's preference for continuity (0-1) |

### Contact Information
| Field | Type | Description |
|-------|------|-------------|
| `office_phone` | CharField | Office contact |
| `office_location` | CharField | Location in hospital |
| `emergency_contact` | CharField | Emergency number |

### Verification
| Field | Type | Description |
|-------|------|-------------|
| `is_verified` | BooleanField | Credential verification status |
| `verification_documents` | FileField | Supporting documents |

## Key Properties

### Status Properties
```python
@property
def can_practice(self):
    """Check if doctor can practice"""
    return (self.is_active and self.is_verified and 
            self.is_license_valid and self.status == 'active')

@property
def is_license_valid(self):
    """Check license validity"""
    return self.license_expiry_date > timezone.now().date()

@property
def days_until_license_expires(self):
    """Days until license expiry"""
    return (self.license_expiry_date - timezone.now().date()).days
```

### Professional Information
```python
@property
def full_name(self):
    """Full name with title"""
    return f"Dr. {self.user.get_full_name()}"

def get_expertise_summary(self):
    """Comprehensive expertise summary"""
    # Returns formatted string with specialization,
    # subspecialty, certifications, etc.
```

## Appointment Management

### Availability Checking
```python
def is_available_on_day(self, day):
    """Check availability for specific day"""
    if not self.can_practice:
        return False
    return day.lower()[:3] in [d.strip().lower() for d in self.consultation_days.split(',')]

def is_available_at(self, datetime):
    """Check availability for specific datetime"""
    # Checks practice status, consultation hours,
    # and existing appointments
```

### Appointment Slots
```python
def get_available_slots(self, date):
    """Get all available slots for a date"""
    # Returns list of available datetime slots
    # considering consultation hours and existing appointments

def get_appointments_for_date(self, date):
    """Get all appointments for a date"""
    # Returns QuerySet of appointments ordered by time

def can_accept_appointment(self, date):
    """Check if can accept more appointments"""
    return (self.get_appointment_count_for_date(date) < 
            self.max_daily_appointments)
```

## Business Rules and Validations

### Department Rules
1. Surgical departments require subspecialty
2. Department must belong to doctor's hospital

### Availability Rules
1. Consultation end time must be after start time
2. Consultation days must be valid weekday names
3. Cannot exceed maximum daily appointments

### License Rules
1. License must be valid for active status
2. Automatic validation on expiry date

### Status Rules
1. Must be active, verified, and licensed to practice
2. Status changes affect appointment availability

## Database Indexes
The model includes optimized indexes for:
1. License number lookups
2. Department and hospital queries
3. Status checks
4. Availability filtering

## Permissions
The model includes permissions for:
- Prescribing medications
- Viewing/updating patient records
- Performing surgical procedures
- Admitting/discharging patients
- Ordering/viewing tests

## Usage Examples

### Creating a Doctor
```python
doctor = Doctor.objects.create(
    user=user,
    department=department,
    specialization="Cardiology",
    medical_license_number="MD12345",
    license_expiry_date=expiry_date
)
```

### Checking Availability
```python
# Check if doctor can take appointment
if doctor.is_available_at(appointment_datetime):
    slots = doctor.get_available_slots(appointment_date)
```

### Managing Appointments
```python
# Get doctor's schedule
schedule = doctor.get_weekly_schedule()

# Check appointment capacity
if doctor.can_accept_appointment(date):
    appointments = doctor.get_appointments_for_date(date)
```

## Best Practices
1. Always check `can_practice` before scheduling
2. Validate department-subspecialty consistency
3. Use provided methods for availability checks
4. Keep license information updated
5. Maintain verification documents

## Security Considerations
1. Protect sensitive contact information
2. Verify credential documents
3. Audit status changes
4. Control permission assignments
5. Validate hospital affiliations

## Performance Considerations
1. Use provided indexes for queries
2. Cache availability calculations
3. Batch update operations
4. Use select_related for user/department queries

## Related Models
- User (OneToOne relationship)
- Department (ForeignKey)
- Hospital (ForeignKey)
- Appointment (Related name: appointments)

## Future Enhancements
1. Telemedicine support
2. Multiple hospital affiliations
3. Advanced scheduling rules
4. Specialty-based permissions
5. Performance metrics tracking 