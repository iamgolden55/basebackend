# Patient Prescription Journey - Complete Implementation Plan

**Date**: January 11, 2025  
**Purpose**: Implement complete patient flow from hospital registration to prescription dispensing  
**Status**: Implementation Ready

---

## Executive Summary

This document outlines the complete implementation of the patient prescription journey, integrating:
1. Hospital registration and primary hospital selection
2. Appointment booking with hospital doctors
3. Prescription creation after appointments
4. Pharmacist triage system
5. Doctor authorization workflow
6. Prescription verification and dispensing

---

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     PATIENT JOURNEY FLOW                         │
└─────────────────────────────────────────────────────────────────┘

PHASE 1: HOSPITAL REGISTRATION
┌──────────────────────┐
│  Patient registers   │
│  on PHB platform     │
└──────────┬───────────┘
           │
           v
┌──────────────────────┐
│ Select primary       │
│ hospital from list   │
└──────────┬───────────┘
           │
           v
┌──────────────────────┐
│ HospitalRegistration │
│ record created       │
│ (status: pending)    │
└──────────┬───────────┘
           │
           v
┌──────────────────────┐
│ Hospital admin       │
│ approves patient     │
└──────────┬───────────┘
           │
           v
┌──────────────────────┐
│ Registration status  │
│ → approved           │
│ is_primary → true    │
└──────────┬───────────┘

PHASE 2: APPOINTMENT BOOKING
           │
           v
┌──────────────────────┐
│ Patient searches for │
│ doctors at hospital  │
└──────────┬───────────┘
           │
           v
┌──────────────────────┐
│ Book appointment     │
│ with doctor          │
│ (select date/time)   │
└──────────┬───────────┘
           │
           v
┌──────────────────────┐
│ Appointment created  │
│ status: pending      │
└──────────┬───────────┘
           │
           v
┌──────────────────────┐
│ Doctor confirms      │
│ appointment          │
└──────────┬───────────┘
           │
           v
┌──────────────────────┐
│ Patient attends      │
│ appointment          │
│ status: completed    │
└──────────┬───────────┘

PHASE 3: PRESCRIPTION REQUEST
           │
           v
┌──────────────────────┐
│ Patient requests     │
│ prescription refill  │
│ OR                   │
│ Doctor prescribes    │
│ from appointment     │
└──────────┬───────────┘
           │
           v
┌──────────────────────┐
│ PrescriptionRequest  │
│ created              │
│ status: REQUESTED    │
└──────────┬───────────┘
           │
           v
┌──────────────────────────────────────┐
│ AUTOMATIC TRIAGE ASSIGNMENT           │
│                                       │
│ analyze_prescription_request()        │
│ ├─ Check medication complexity        │
│ ├─ Check controlled substances        │
│ ├─ Check patient history              │
│ └─ Assign to pharmacist OR doctor     │
└──────────┬────────────────────────────┘

PHASE 4A: PHARMACIST REVIEW PATH (90% of cases)
           │
           v
┌──────────────────────┐
│ Assigned to          │
│ pharmacist           │
└──────────┬───────────┘
           │
           v
┌──────────────────────┐
│ Pharmacist reviews   │
│ - Drug interactions  │
│ - Dosage             │
│ - Patient history    │
└──────────┬───────────┘
           │
           v
  ┌────────┴────────┐
  │                 │
  v                 v
APPROVE          ESCALATE
  │                 │
  │                 v
  │            ┌─────────────────┐
  │            │ Send to doctor  │
  │            │ for review      │
  │            └────────┬────────┘
  │                     │
  └─────────────────────┘
           │
           v
PHASE 5: DOCTOR AUTHORIZATION
           │
           v
┌──────────────────────┐
│ Doctor reviews       │
│ pharmacist notes     │
└──────────┬───────────┘
           │
           v
  ┌────────┴────────┐
  │                 │
  v                 v
APPROVE          REJECT
  │                 │
  v                 v
┌──────────────────────┐
│ Create Medication    │
│ record with QR code  │
│ Send to pharmacy     │
└──────────┬───────────┘

PHASE 6: PRESCRIPTION DISPENSING
           │
           v
┌──────────────────────┐
│ Patient receives     │
│ printable QR code    │
└──────────┬───────────┘
           │
           v
┌──────────────────────┐
│ Patient visits       │
│ nominated pharmacy   │
└──────────┬───────────┘
           │
           v
┌──────────────────────┐
│ Pharmacist scans     │
│ QR code              │
│ - Verifies signature │
│ - Checks expiry      │
│ - Checks ID (if      │
│   controlled drug)   │
└──────────┬───────────┘
           │
           v
┌──────────────────────┐
│ Dispense medication  │
│ status: DISPENSED    │
└──────────────────────┘
```

---

## Backend Implementation Status

### ✅ ALREADY IMPLEMENTED

#### 1. **Hospital Registration System**
**Files**: 
- `/api/models/medical/hospital_registration.py`
- `/api/models/user/custom_user.py`

**Models**:
```python
class HospitalRegistration(models.Model):
    user = ForeignKey(CustomUser)
    hospital = ForeignKey(Hospital)
    status = CharField(choices=['pending', 'approved', 'rejected'])
    is_primary = BooleanField(default=False)
    created_at = DateTimeField()
    approved_date = DateTimeField()
```

**Methods**:
- `approve_registration()` - Approves hospital registration
- `set_primary_hospital(hospital)` - Sets hospital as primary for user

#### 2. **Appointment System**
**Files**: 
- `/api/models/medical/appointment.py`

**Models**:
```python
class Appointment(models.Model):
    appointment_id = CharField(unique=True)
    patient = ForeignKey(CustomUser)
    hospital = ForeignKey(Hospital)
    department = ForeignKey(Department)
    doctor = ForeignKey(Doctor)
    appointment_type = CharField(choices=[...])
    status = CharField(choices=['pending', 'confirmed', ...])
    appointment_date = DateTimeField()
    chief_complaint = TextField()
```

#### 3. **Prescription Request System**
**Files**:
- `/api/models/medical/prescription_request.py`
- `/api/views/prescription_requests_views.py`

**Models**:
```python
class PrescriptionRequest(models.Model):
    # Basic fields
    id = UUIDField(primary_key=True)
    request_reference = CharField(unique=True)  # REQ-ABC123
    patient = ForeignKey(CustomUser)
    hospital = ForeignKey(Hospital)
    status = CharField(choices=['REQUESTED', 'APPROVED', ...])
    
    # Triage fields
    triage_category = CharField()  # ROUTINE_REPEAT, URGENT_NEW, etc.
    assigned_to_role = CharField(choices=['pharmacist', 'doctor'])
    assigned_to_pharmacist = ForeignKey(Pharmacist)
    assigned_to_doctor = ForeignKey(Doctor)
    
    # Pharmacist review
    pharmacist_reviewed_by = ForeignKey(Pharmacist)
    pharmacist_review_action = CharField(choices=[
        'approved', 'escalated', 'rejected', 'consultation'
    ])
    pharmacist_notes = TextField()
    escalation_reason = TextField()
    
    # Doctor review
    reviewed_by = ForeignKey(Doctor)
    reviewed_date = DateTimeField()
    rejection_reason = TextField()
```

**API Endpoints**:
```python
POST /api/prescriptions/requests/  
    - Create prescription request
    - Auto-assigns to pharmacist/doctor via triage
    - Sends email notifications

GET /api/prescriptions/requests/
    - List patient's prescription requests

GET /api/prescriptions/requests/{id}/
    - Get detailed request status
```

#### 4. **Triage System**
**Files**:
- `/api/utils/prescription_triage.py`

**Function**: `assign_prescription_request(prescription_request)`

**Logic**:
1. Analyzes medications requested
2. Checks for controlled substances
3. Reviews patient history
4. Determines complexity level
5. Assigns to:
   - **Pharmacist** (90% of cases): Routine refills, simple medications
   - **Doctor** (10% of cases): New controlled drugs, complex cases

**Triage Categories**:
- `ROUTINE_REPEAT` → Pharmacist
- `URGENT_NEW` → Pharmacist first review
- `CONTROLLED_SUBSTANCE` → Pharmacist + Doctor
- `COMPLEX_CASE` → Direct to Doctor
- `SPECIALIST_REQUIRED` → Direct to Doctor

#### 5. **Email Notification System**
**Files**: `/api/utils/email.py`

**Functions**:
- `send_prescription_request_confirmation()` - To patient
- `send_prescription_request_to_pharmacist()` - To assigned pharmacist
- `send_prescription_escalation_to_physician()` - When pharmacist escalates
- `send_prescription_approved_notification()` - When approved
- `send_prescription_rejected_notification()` - When rejected

#### 6. **Prescription Verification & Dispensing**
**Files**:
- `/api/views/prescription_verification_views.py`
- `/api/utils/prescription_security.py`

**API Endpoints**:
```python
POST /api/prescriptions/verify/
    - Verify prescription QR code signature
    - Check expiry
    - Check dispensing status

POST /api/prescriptions/dispense/
    - Record medication dispensing
    - Require patient ID for controlled substances
    - Log to audit trail
```

---

## ⚠️ MISSING / NEEDS IMPLEMENTATION

### Frontend Implementation (All Missing)

#### 1. **Hospital Registration UI**

**File to Create**: `/phbfrontend/src/pages/account/RegisterHospitalPage.tsx`

**Features Needed**:
- Search hospitals by name/location
- Display hospital details (address, departments, services)
- "Register with Hospital" button
- Show registration status (pending/approved/rejected)
- Set as primary hospital option

**API Calls**:
```typescript
// Get available hospitals
GET /api/hospitals/?search=Lagos&type=general

// Register with hospital
POST /api/hospital-registrations/
{
  "hospital_id": 5,
  "is_primary": true
}

// Get user's hospital registrations
GET /api/hospital-registrations/
```

#### 2. **Appointment Booking UI**

**File to Create**: `/phbfrontend/src/pages/account/BookAppointmentPage.tsx`

**Features Needed**:
- Display user's primary hospital
- List departments at hospital
- Search doctors by department/specialty
- View doctor availability calendar
- Select date/time slot
- Enter chief complaint
- Submit appointment request

**API Calls**:
```typescript
// Get hospital departments
GET /api/hospitals/{hospital_id}/departments/

// Get doctors in department
GET /api/departments/{dept_id}/doctors/

// Get doctor availability
GET /api/doctors/{doctor_id}/availability/?date=2025-01-15

// Create appointment
POST /api/appointments/
{
  "doctor_id": 10,
  "hospital_id": 5,
  "department_id": 3,
  "appointment_date": "2025-01-15T10:00:00Z",
  "chief_complaint": "Annual checkup",
  "appointment_type": "consultation"
}
```

#### 3. **My Appointments Page**

**File to Create**: `/phbfrontend/src/pages/account/MyAppointmentsPage.tsx`

**Features Needed**:
- List upcoming appointments
- List past appointments
- View appointment details
- Cancel appointment
- Reschedule appointment
- Request prescription from completed appointment

**API Calls**:
```typescript
// Get user appointments
GET /api/appointments/?status=pending

// Cancel appointment
POST /api/appointments/{id}/cancel/

// Request prescription after appointment
POST /api/prescriptions/requests/
{
  "appointment_id": 123,  // Link to appointment
  "medications": [...]
}
```

#### 4. **Prescription Request UI (Patient)**

**File**: `/phbfrontend/src/pages/account/RequestPrescriptionPage.tsx` *(Already exists)*

**Features to Add**:
- Link prescription request to appointment (if applicable)
- Show triage status clearly
- Display assigned pharmacist/doctor name
- Show expected processing time based on triage category

**Update API Response Display**:
```typescript
// Current response includes:
{
  "request_reference": "REQ-ABC123",
  "status": "REQUESTED",
  "triage_category": "ROUTINE_REPEAT",
  "triage_reason": "Simple repeat prescription",
  "assigned_to_role": "pharmacist",
  "assigned_pharmacist_name": "Dr. Ahmed Ibrahim",
  "expected_days": "2-3"
}
```

#### 5. **Pharmacist Triage Dashboard**

**File to Create**: `/phbfrontend/src/pages/professional/PharmacistTriageDashboard.tsx`

**Features Needed**:
- List assigned prescription requests
- Filter by urgency, triage category, status
- View patient details, medication history
- Check drug interactions
- Review pharmacist decision form:
  - ✅ Approve (create prescription)
  - 🔺 Escalate to physician (with reason)
  - ❌ Reject (with reason)
  - 💬 Request patient consultation
- Add clinical notes
- Submit review

**API Calls**:
```typescript
// Get assigned prescription requests
GET /api/pharmacist/prescription-requests/?status=REQUESTED

// Review prescription request
POST /api/pharmacist/prescription-requests/{id}/review/
{
  "action": "approved",  // approved | escalated | rejected | consultation
  "clinical_notes": "Verified patient history, no drug interactions",
  "drug_interactions_checked": "No interactions found",
  "monitoring_requirements": "Monitor blood pressure",
  "pharmacist_recommendation": "Approve as requested"
}

// Escalate to physician
POST /api/pharmacist/prescription-requests/{id}/escalate/
{
  "escalation_reason": "Patient has renal impairment, dosage adjustment needed",
  "clinical_concerns": "eGFR < 60 ml/min",
  "pharmacist_recommendation": "Reduce dose to 50mg BID"
}
```

#### 6. **Doctor Prescription Authorization Dashboard**

**File to Create**: `/phbfrontend/src/pages/professional/DoctorPrescriptionDashboard.tsx`

**Features Needed**:
- Two tabs:
  1. **Direct Assignments** (complex cases from triage)
  2. **Pharmacist Escalations** (cases escalated by pharmacists)
  
- For each request show:
  - Patient demographics, medical history
  - Requested medications
  - Pharmacist notes (if escalated)
  - Triage category and reason
  
- Doctor decision form:
  - ✅ Approve prescription
  - ✏️ Modify dosage/quantity
  - ❌ Reject with clinical reason
  - 📅 Require follow-up appointment
  
- Generate Medication record with QR code
- Send to patient's nominated pharmacy

**API Calls**:
```typescript
// Get prescription requests assigned to doctor
GET /api/doctor/prescription-requests/?assigned_to_me=true

// Get pharmacist escalations
GET /api/doctor/prescription-requests/?escalated=true

// Approve prescription
POST /api/prescriptions/requests/{id}/approve/
{
  "approval_type": "as_requested",  // as_requested | modified | partial
  "approved_medications": [
    {
      "medication_id": 1,
      "approved_quantity": 30,
      "approved_dosage": "Take 1 tablet daily",
      "refills_allowed": 2
    }
  ],
  "clinical_notes": "Approved for 3 months therapy",
  "requires_followup": false,
  "followup_days": null
}

// Reject prescription
POST /api/prescriptions/requests/{id}/reject/
{
  "rejection_reason": "Patient has contraindication (pregnancy)",
  "requires_followup": true,
  "followup_days": 7,
  "alternative_recommendation": "Consider alternative therapy"
}
```

#### 7. **Prescription Status Tracking (Patient)**

**File to Create**: `/phbfrontend/src/pages/account/MyPrescriptionsPage.tsx`

**Features Needed**:
- Timeline view of prescription journey:
  ```
  ✅ Requested (Jan 10, 10:30 AM)
  ✅ Assigned to Pharmacist (Jan 10, 10:31 AM)
  ✅ Pharmacist Reviewed (Jan 10, 2:00 PM)
  ⏳ Awaiting Doctor Authorization (Jan 10, 2:05 PM)
  ⏳ Doctor Approval Pending...
  ```
  
- Show current status clearly
- Display assigned pharmacist/doctor
- Show expected completion date
- Download prescription PDF when approved
- Print QR code for pharmacy

**API Calls**:
```typescript
// Get prescription request status
GET /api/prescriptions/requests/{id}/

Response:
{
  "request_reference": "REQ-ABC123",
  "status": "REQUESTED",
  "timeline": [
    {
      "event": "requested",
      "timestamp": "2025-01-10T10:30:00Z",
      "description": "Prescription request submitted"
    },
    {
      "event": "triage_assigned",
      "timestamp": "2025-01-10T10:31:00Z",
      "description": "Assigned to Pharmacist - Dr. Ahmed Ibrahim",
      "assigned_to": "Dr. Ahmed Ibrahim (Pharmacist)"
    },
    {
      "event": "pharmacist_reviewed",
      "timestamp": "2025-01-10T14:00:00Z",
      "description": "Pharmacist approved and sent to physician"
    },
    {
      "event": "awaiting_physician",
      "timestamp": "2025-01-10T14:05:00Z",
      "description": "Awaiting physician authorization"
    }
  ],
  "current_step": "awaiting_physician",
  "assigned_pharmacist": {
    "name": "Dr. Ahmed Ibrahim",
    "pcn_license": "PCN-123456"
  },
  "assigned_doctor": {
    "name": "Dr. Jane Smith",
    "mdcn_license": "MDCN-98765"
  },
  "expected_completion": "2025-01-12"
}
```

---

## Database Schema Additions Needed

### ⚠️ Need to Add Missing Endpoints

#### 1. **Hospital Registration Endpoints**

**File to Create**: `/api/views/hospital_registration_views.py`

```python
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def register_with_hospital(request):
    """
    Register user with a hospital
    
    POST /api/hospital-registrations/
    {
        "hospital_id": 5,
        "is_primary": true
    }
    """
    hospital_id = request.data.get('hospital_id')
    is_primary = request.data.get('is_primary', False)
    
    # Validate hospital exists
    hospital = Hospital.objects.get(id=hospital_id)
    
    # Create or update registration
    registration, created = HospitalRegistration.objects.get_or_create(
        user=request.user,
        hospital=hospital,
        defaults={'is_primary': is_primary}
    )
    
    return Response({
        'id': registration.id,
        'hospital': hospital.name,
        'status': registration.status,
        'is_primary': registration.is_primary,
        'message': 'Hospital registration submitted. Awaiting approval.'
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_user_hospital_registrations(request):
    """
    List user's hospital registrations
    
    GET /api/hospital-registrations/
    """
    registrations = HospitalRegistration.objects.filter(
        user=request.user
    ).select_related('hospital')
    
    return Response([
        {
            'id': reg.id,
            'hospital': {
                'id': reg.hospital.id,
                'name': reg.hospital.name,
                'city': reg.hospital.city,
                'state': reg.hospital.state
            },
            'status': reg.status,
            'is_primary': reg.is_primary,
            'created_at': reg.created_at,
            'approved_date': reg.approved_date
        }
        for reg in registrations
    ])
```

#### 2. **Appointment Booking Endpoints**

**File to Create**: `/api/views/appointment_booking_views.py`

```python
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_hospital_departments(request, hospital_id):
    """
    Get departments at a hospital
    
    GET /api/hospitals/{hospital_id}/departments/
    """
    departments = Department.objects.filter(
        hospital_id=hospital_id,
        is_active=True
    )
    
    return Response([
        {
            'id': dept.id,
            'name': dept.name,
            'description': dept.description,
            'doctor_count': dept.doctors.count()
        }
        for dept in departments
    ])


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_department_doctors(request, department_id):
    """
    Get doctors in a department
    
    GET /api/departments/{department_id}/doctors/
    """
    doctors = Doctor.objects.filter(
        department_id=department_id,
        is_active=True
    ).select_related('user')
    
    return Response([
        {
            'id': doctor.id,
            'name': doctor.get_full_name(),
            'specialty': doctor.specialty,
            'qualification': doctor.qualification,
            'years_experience': doctor.years_of_experience,
            'available_days': doctor.available_days
        }
        for doctor in doctors
    ])


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def book_appointment(request):
    """
    Book an appointment
    
    POST /api/appointments/
    {
        "doctor_id": 10,
        "hospital_id": 5,
        "department_id": 3,
        "appointment_date": "2025-01-15T10:00:00Z",
        "chief_complaint": "Annual checkup",
        "appointment_type": "consultation"
    }
    """
    # Validate user has approved hospital registration
    if not HospitalRegistration.objects.filter(
        user=request.user,
        hospital_id=request.data['hospital_id'],
        status='approved'
    ).exists():
        return Response(
            {'error': 'You must be registered with this hospital'},
            status=400
        )
    
    # Create appointment
    appointment = Appointment.objects.create(
        patient=request.user,
        hospital_id=request.data['hospital_id'],
        department_id=request.data['department_id'],
        doctor_id=request.data['doctor_id'],
        appointment_date=request.data['appointment_date'],
        chief_complaint=request.data['chief_complaint'],
        appointment_type=request.data['appointment_type'],
        status='pending'
    )
    
    # Send confirmation email
    send_appointment_confirmation_email(appointment)
    
    return Response({
        'id': appointment.id,
        'appointment_id': appointment.appointment_id,
        'status': 'pending',
        'message': 'Appointment request submitted successfully'
    })
```

#### 3. **Pharmacist Review Endpoints**

**File to Create**: `/api/views/pharmacist_prescription_review_views.py`

```python
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_assigned_prescription_requests(request):
    """
    Get prescription requests assigned to pharmacist
    
    GET /api/pharmacist/prescription-requests/
    """
    # Get pharmacist profile
    pharmacist = Pharmacist.objects.get(user=request.user)
    
    # Get assigned requests
    requests = PrescriptionRequest.objects.filter(
        assigned_to_pharmacist=pharmacist,
        status='REQUESTED'
    ).select_related('patient', 'hospital').prefetch_related('medications')
    
    return Response([
        {
            'id': req.id,
            'request_reference': req.request_reference,
            'patient_name': req.patient.get_full_name(),
            'patient_hpn': req.patient.hpn,
            'triage_category': req.triage_category,
            'urgency': req.urgency,
            'request_date': req.request_date,
            'medications': [
                {
                    'name': med.medication_name,
                    'strength': med.strength,
                    'quantity': med.quantity,
                    'is_repeat': med.is_repeat
                }
                for med in req.medications.all()
            ]
        }
        for req in requests
    ])


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def review_prescription_request(request, request_id):
    """
    Pharmacist reviews prescription request
    
    POST /api/pharmacist/prescription-requests/{request_id}/review/
    {
        "action": "approved",
        "clinical_notes": "...",
        "drug_interactions_checked": "...",
        "pharmacist_recommendation": "..."
    }
    """
    pharmacist = Pharmacist.objects.get(user=request.user)
    prescription_request = PrescriptionRequest.objects.get(id=request_id)
    
    # Validate pharmacist is assigned
    if prescription_request.assigned_to_pharmacist != pharmacist:
        return Response({'error': 'Not authorized'}, status=403)
    
    # Update review fields
    prescription_request.pharmacist_reviewed_by = pharmacist
    prescription_request.pharmacist_review_date = timezone.now()
    prescription_request.pharmacist_review_action = request.data['action']
    prescription_request.pharmacist_notes = request.data['clinical_notes']
    prescription_request.drug_interactions_checked = request.data.get('drug_interactions_checked')
    prescription_request.pharmacist_recommendation = request.data.get('pharmacist_recommendation')
    prescription_request.save()
    
    # Send notification based on action
    if request.data['action'] == 'approved':
        # Notify doctor for final authorization
        send_prescription_approved_by_pharmacist_email(prescription_request)
    elif request.data['action'] == 'escalated':
        # Escalate to physician
        prescription_request.escalation_reason = request.data.get('escalation_reason')
        prescription_request.save()
        send_prescription_escalation_to_physician(prescription_request)
    
    return Response({
        'success': True,
        'message': f'Prescription request {request.data["action"]}'
    })
```

---

## Implementation Roadmap

### **WEEK 1: Backend Endpoints**

**Day 1-2**: Hospital Registration Endpoints
- Create `hospital_registration_views.py`
- Add URL routes
- Test with Postman

**Day 3-4**: Appointment Booking Endpoints
- Create `appointment_booking_views.py`
- Add doctor availability logic
- Add URL routes
- Test appointment flow

**Day 5**: Pharmacist Review Endpoints
- Create `pharmacist_prescription_review_views.py`
- Add review workflow
- Test triage → pharmacist → doctor flow

---

### **WEEK 2: Frontend - Patient Journey**

**Day 1-2**: Hospital Registration UI
- Create `RegisterHospitalPage.tsx`
- Hospital search and list
- Registration form
- Status display

**Day 3-4**: Appointment Booking UI
- Create `BookAppointmentPage.tsx`
- Doctor search
- Date/time picker
- Appointment form

**Day 5**: Prescription Request Enhancement
- Update `RequestPrescriptionPage.tsx`
- Show triage status
- Link to appointments
- Display assigned pharmacist

---

### **WEEK 3: Frontend - Professional Dashboards**

**Day 1-3**: Pharmacist Triage Dashboard
- Create `PharmacistTriageDashboard.tsx`
- Request list with filters
- Review form
- Drug interaction checker UI
- Approve/Escalate/Reject workflow

**Day 4-5**: Doctor Authorization Dashboard
- Create `DoctorPrescriptionDashboard.tsx`
- Two tabs: Direct assignments & Escalations
- Review pharmacist notes
- Approve/Modify/Reject form
- Generate Medication record

---

### **WEEK 4: Testing & Polish**

**Day 1-2**: End-to-End Testing
- Test complete patient journey
- Test triage assignment
- Test pharmacist review
- Test doctor authorization
- Test prescription dispensing

**Day 3-4**: UI/UX Improvements
- Add loading states
- Add error handling
- Improve mobile responsiveness
- Add success animations

**Day 5**: Documentation & Deployment
- Update API documentation
- Create user guides
- Deploy to staging
- QA testing

---

## Key Decision Points

### 1. **Auto-Approve Simple Requests?**

**Question**: Should pharmacist-approved routine refills be auto-approved without doctor review?

**Recommendation**: **YES** for:
- Routine refills (patient has active prescription)
- Simple medications (non-controlled, non-specialized)
- Pharmacist confidence level = HIGH

**Require Doctor Authorization** for:
- New medications
- Controlled substances
- Dosage changes
- Pharmacist escalations

### 2. **Appointment Required for Prescription?**

**Question**: Must patient have an appointment to request prescription?

**Recommendation**: **NO**
- Allow prescription requests without appointment (NHS model)
- But link to appointment if one exists
- Doctors can create prescriptions during appointments

### 3. **Multiple Hospitals?**

**Question**: Can user register with multiple hospitals?

**Recommendation**: **YES**
- Allow multiple hospital registrations
- Only ONE can be primary
- Prescriptions default to primary hospital
- Can request from any approved hospital

---

## Success Metrics

### **Phase 1: Hospital Registration**
- ✅ 100% of users able to find and register with hospital
- ✅ Hospital approval time < 24 hours
- ✅ Clear status communication

### **Phase 2: Appointment Booking**
- ✅ 95% appointment booking success rate
- ✅ Doctor availability clearly displayed
- ✅ Confirmation emails sent

### **Phase 3: Prescription Triage**
- ✅ 90% requests assigned to pharmacist
- ✅ 10% complex cases to doctor
- ✅ < 5% triage assignment errors

### **Phase 4: Pharmacist Review**
- ✅ 80% approved by pharmacist
- ✅ 15% escalated to physician
- ✅ 5% rejected
- ✅ Average review time < 2 hours

### **Phase 5: Doctor Authorization**
- ✅ 95% approval rate
- ✅ Average authorization time < 4 hours
- ✅ Clear rejection reasons

### **Phase 6: Prescription Dispensing**
- ✅ 100% QR code verification success
- ✅ Controlled substance ID verification compliance
- ✅ Complete audit trail

---

## Next Steps

1. **Review this document** with team
2. **Prioritize features** - which phase first?
3. **Assign developers** - backend vs frontend
4. **Set sprint goals** - 4-week timeline?
5. **Begin Week 1** - Hospital registration endpoints

**Questions for Discussion**:
1. Should we implement all phases or start with Phase 1-3?
2. Do we need additional pharmacist training before rollout?
3. What's the approval process for hospital registration?
4. How do we handle emergency prescriptions?

---

**Document Status**: Ready for Implementation  
**Next Update**: After team review meeting
