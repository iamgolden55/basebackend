# Patient Admission System Documentation

## Overview

The Patient Admission System is a comprehensive solution for managing hospital admissions, including both registered patients and emergency admissions for unregistered patients. The system integrates with the existing hospital management framework and provides a complete workflow for patient intake, bed management, transfers, and discharges.

## Core Features

- **Complete Admission Management**: Track patient admissions, transfers, and discharges
- **Emergency Admission Flow**: Process patients without existing accounts
- **Registration Conversion**: Convert emergency patients to registered users
- **Bed Management**: Track bed assignments across departments
- **HPN Generation**: Automatic Hospital Patient Number assignment

## System Architecture

### Core Components

1. **Database Models**:
   - `PatientAdmission`: Tracks admission details, bed assignments, and clinical information
   - `PatientTransfer`: Records movements between departments
   - `CustomUser`: Existing user model with HPN generation logic
   - `HospitalRegistration`: Links users to hospitals

2. **API Endpoints**:
   - Regular admission management endpoints
   - Emergency admission endpoint for unregistered patients
   - Registration completion endpoint to convert temporary patients to users

3. **Utility Functions**:
   - Admission ID generation
   - Temporary patient ID generation

## Detailed Process Flows

### Regular Patient Admission (Registered Users)

1. **Pre-conditions**: Patient already has an account with a registered hospital
2. **Admission Creation**:
   - API call to `/admissions/` with patient ID and clinical details
   - System validates bed availability in selected department
   - Generates unique admission ID (format: ADM-YYMMDD-XXXX)
3. **Bed Assignment**:
   - Department's `assign_bed()` method allocates a bed
   - Occupied bed counter is incremented
4. **Discharge Process**:
   - API call to `/admissions/{id}/discharge/` with discharge details
   - Bed is released back to department's available pool
   - Clinical documentation is finalized

### Emergency Admission (Unregistered Patients)

1. **Initial Intake**:
   - API call to `/admissions/emergency_admission/` with temporary patient details
   - System generates temporary patient ID (format: TEMP-YYMMDD-XXXX)
   - Creates admission record with `is_registered_patient=False`
   - Records demographic and clinical data in `temp_patient_details` JSON field
   
   **Required Fields for Emergency Admission**:
   
   *Essential Personal Information:*
   - `first_name`: Patient's first name
   - `last_name`: Patient's last name
   - `gender`: Patient's gender (male/female/other)
   - `age` or `date_of_birth`: Patient's age or date of birth
   - `phone_number`: Contact number
   - `city`: City of residence (important for HPN generation)
   - `address`: Full address if available
   - `emergency_contact`: Emergency contact number
   - `emergency_contact_name`: Name of emergency contact person
   - `emergency_contact_relationship`: Relationship to patient
   
   *Medical Information:*
   - `chief_complaint`: Primary reason for visit
   - `allergies`: List of known allergies
   - `current_medications`: Current medications
   - `brief_history`: Brief medical history relevant to current issue
   
   *Optional Additional Information:*
   - `insurance_provider`: Insurance company name
   - `insurance_id`: Insurance ID number
   - `government_id`: National ID, passport, or other government ID
   - `vitals`: Initial vital signs (BP, pulse, temp, etc.)
   - `occupation`: Patient's occupation
   - `preferred_language`: Preferred communication language

2. **Clinical Care**:
   - Same bed assignment and clinical workflow as regular admissions
   - All documentation links to temporary patient record

3. **Registration Completion**:
   - API call to `/admissions/{id}/complete_registration/` with required account info
   - System creates full `CustomUser` record with email, password, etc.
   - City from temporary details is used to generate proper HPN
   - User's built-in save method creates HPN in format "XXX NNN NNN NNN" where:
     - XXX is first 3 letters of city (e.g., "LAG" for Lagos)
     - NNN NNN NNN is UUID-derived unique number
   - Creates `HospitalRegistration` record with `is_primary=True`
   - Updates admission record to link to new user

4. **Post-Registration**:
   - Patient can now access the patient portal
   - All clinical documentation remains linked and accessible

### Patient Transfer Process

1. **Transfer Initiation**:
   - API call to `/admissions/{id}/transfer/` with target department
   - Source department releases bed
   - Target department assigns new bed
   - `PatientTransfer` record created with reason and timestamps

2. **Department Updating**:
   - Bed counters updated in both departments
   - Patient record updated with new department

## Data Models

### PatientAdmission

```python
class PatientAdmission(TimestampedModel):
    # Status options
    STATUS_CHOICES = [
        ('pending', 'Pending Admission'),
        ('admitted', 'Currently Admitted'),
        ('discharged', 'Discharged'),
        ('transferred', 'Transferred'),
        ('deceased', 'Deceased'),
        ('left_ama', 'Left Against Medical Advice'),
    ]
    
    # Core fields
    admission_id = models.CharField(max_length=20, unique=True)
    patient = models.ForeignKey('api.CustomUser', on_delete=models.PROTECT, null=True, blank=True)
    hospital = models.ForeignKey('api.Hospital', on_delete=models.PROTECT)
    department = models.ForeignKey('api.Department', on_delete=models.PROTECT)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Emergency admission fields
    is_registered_patient = models.BooleanField(default=True)
    temp_patient_id = models.CharField(max_length=20, null=True, blank=True)
    temp_patient_details = models.JSONField(null=True, blank=True)
    registration_status = models.CharField(
        max_length=20,
        choices=[
            ('complete', 'Complete Registration'),
            ('partial', 'Partial Registration'),
            ('pending', 'Registration Pending'),
        ],
        default='complete'
    )
    
    # Clinical fields
    admission_type = models.CharField(max_length=20)
    priority = models.CharField(max_length=20)
    reason_for_admission = models.TextField()
    attending_doctor = models.ForeignKey('api.Doctor', on_delete=models.PROTECT)
    # ... additional fields omitted for brevity
```

## API Documentation

### Standard Admission Endpoints

```
GET /admissions/ - List all admissions (filtered by user role)
POST /admissions/ - Create a new admission for registered patient
GET /admissions/{id}/ - View specific admission
PUT/PATCH /admissions/{id}/ - Update admission details
DELETE /admissions/{id}/ - Delete admission (with proper permissions)
```

### Specialized Actions

```
POST /admissions/{id}/admit/ - Admit patient and assign bed
POST /admissions/{id}/discharge/ - Discharge patient
POST /admissions/{id}/transfer/ - Transfer patient to new department
```

### Emergency Flow Endpoints

```
POST /admissions/emergency_admission/ - Create admission for unregistered patient
POST /admissions/{id}/complete_registration/ - Convert temporary patient to registered user
```

## API Request/Response Examples

### Create Emergency Admission

**Request**:
```json
POST /admissions/emergency_admission/
{
  "hospital_id": 1,
  "department_id": 3,
  "reason_for_admission": "Chest pain and shortness of breath",
  "attending_doctor_id": 5,
  "priority": "urgent",
  "admission_type": "emergency",
  "assign_bed": true,
  "temp_patient_details": {
    "first_name": "John",
    "last_name": "Doe",
    "gender": "male",
    "age": 35,
    "phone_number": "+1234567890",
    "city": "Lagos",
    "address": "123 Main St, Lagos, Nigeria",
    "emergency_contact": "+1987654321",
    "emergency_contact_name": "Jane Doe",
    "chief_complaint": "Chest pain and shortness of breath",
    "allergies": ["Penicillin"]
  }
}
```

**Response**:
```json
{
  "message": "Emergency admission created successfully",
  "admission": {
    "id": 42,
    "admission_id": "ADM-250529-7P1U",
    "status": "admitted",
    "temp_patient_id": "TEMP-250529-7791",
    "department": {
      "id": 3,
      "name": "Emergency Department"
    },
    "is_registered_patient": false,
    "registration_status": "pending"
  }
}
```

### Complete Patient Registration

**Request**:
```json
POST /admissions/42/complete_registration/
{
  "email": "john.doe.unique@example.com",
  "password": "SecurePassword123",
  "date_of_birth": "1990-05-15"
}
```

**Response**:
```json
{
  "message": "Patient registration completed successfully",
  "admission": {
    "id": 42,
    "admission_id": "ADM-250529-7P1U",
    "status": "admitted",
    "patient": {
      "id": 20,
      "name": "John Doe",
      "hpn": "LAG 332 345 1480"
    },
    "is_registered_patient": true,
    "registration_status": "complete"
  }
}
```

## Security Considerations

The implementation aligns with the existing security protocols:

1. **Hospital Administrator Authentication**:
   - The system implements enhanced security with hospital code verification and 2FA for admin users
   - The admission system respects these security boundaries, ensuring only authorized staff can admit patients

2. **Data Protection**:
   - Temporary patient details are stored securely in JSON fields
   - Conversion to registered accounts follows established patterns for user creation
   - HPN numbers are generated using the standardized format for consistency

3. **Permissions**:
   - API endpoints enforce role-based access control
   - Doctors can only see their patients' admissions
   - Hospital staff can only see admissions in their facility

## Deployment and Testing

### Migration

To apply the database changes, run:

```bash
python manage.py makemigrations
python manage.py migrate
```

### Testing

Two test scripts are provided to demonstrate and validate the functionality:

1. **test_patient_admission.py** - Tests regular patient admission flow
2. **test_emergency_admission.py** - Tests emergency admission and registration conversion

Run the tests with:

```bash
python test_patient_admission.py
python test_emergency_admission.py
```

## Future Enhancements

1. **Dashboard Development**:
   - Real-time bed availability visualization
   - Department capacity metrics
   - Admission/discharge trends

2. **Electronic Health Record Integration**:
   - Automatic chart creation for new admissions
   - Document uploads for unregistered patients
   - Integration with clinical documentation system

3. **Billing Integration**:
   - Automatic billing initiation on admission
   - Payment tracking through discharge
   - Insurance verification for emergency patients

4. **Mobile Notifications**:
   - Patient status updates to family members
   - Bed availability alerts for waiting patients
   - Discharge planning notifications
