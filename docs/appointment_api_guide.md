# 🏥 PHB Management Appointment API Guide

## Table of Contents
- [Overview](#overview)
- [Authentication](#authentication)
- [Endpoints](#endpoints)
- [Models](#models)
- [Error Handling](#error-handling)
- [Examples](#examples)

## Overview 🌟

The PHB Management Appointment API provides a comprehensive system for managing medical appointments. This guide details the endpoints, models, and workflows for integrating with the appointment system.

## Authentication 🔐

All endpoints require authentication using JWT tokens. Include the token in the Authorization header:

```http
Authorization: Bearer <your_access_token>
```

## Endpoints 🛣️

### 1. Create Appointment

**Endpoint:** `POST /api/appointments/`

**Request Body:**
```json
{
    "doctor_id": 1,
    "hospital": 1,
    "department": 1,
    "appointment_date": "2025-02-27T15:00:00Z",
    "appointment_type": "consultation",
    "priority": "normal",
    "chief_complaint": "Regular checkup",
    "symptoms": "None",
    "medical_history": "No significant history",
    "allergies": "None",
    "current_medications": "None",
    "is_insurance_based": false,
    "notes": "First visit",
    "fee_id": 1
}
```

**Required Fields:**
- `doctor_id`: ID of the doctor
- `hospital`: ID of the hospital
- `department`: ID of the department
- `appointment_date`: DateTime in ISO format
- `fee_id`: ID of the appointment fee structure

### 2. List Appointments

**Endpoint:** `GET /api/appointments/`

**Query Parameters:**
- `status`: Filter by status (pending, confirmed, completed, etc.)
- `appointment_type`: Filter by type
- `priority`: Filter by priority
- `hospital`: Filter by hospital ID
- `department`: Filter by department ID
- `search`: Search in doctor name or chief complaint
- `ordering`: Order by fields (appointment_date, created_at, priority)

### 3. Get Appointment Details

**Endpoint:** `GET /api/appointments/{id}/`

### 4. Update Appointment

**Endpoint:** `PUT/PATCH /api/appointments/{id}/`

### 5. Cancel Appointment

**Endpoint:** `POST /api/appointments/{id}/cancel/`

**Request Body:**
```json
{
    "cancellation_reason": "Unable to attend"
}
```

### 6. Approve Appointment (Doctor/Admin)

**Endpoint:** `POST /api/appointments/{id}/approve/`

**Request Body:**
```json
{
    "approval_notes": "Approved for consultation"
}
```

### 7. Refer Appointment

**Endpoint:** `POST /api/appointments/{id}/refer/`

**Request Body:**
```json
{
    "referred_to_hospital": 2,
    "referral_reason": "Specialist consultation required"
}
```

## Models 📊

### Appointment Status Flow
```
pending → confirmed → in_progress → completed
       → cancelled
       → rejected
       → referred
```

### Appointment Types
- `first_visit`: First Visit
- `follow_up`: Follow Up
- `consultation`: Consultation
- `procedure`: Procedure
- `test`: Medical Test
- `vaccination`: Vaccination
- `therapy`: Therapy

### Priority Levels
- `normal`: Normal
- `urgent`: Urgent
- `emergency`: Emergency

### Payment Status
- `pending`: Payment Pending
- `partial`: Partial Payment
- `completed`: Payment Completed
- `waived`: Payment Waived
- `insurance`: Insurance Processing
- `refunded`: Refunded

## Error Handling ⚠️

Common error responses:

- `400 Bad Request`: Invalid input data
- `401 Unauthorized`: Invalid or missing authentication
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `409 Conflict`: Scheduling conflict
- `422 Unprocessable Entity`: Validation error

Example error response:
```json
{
    "error": "Doctor is not available at this time",
    "code": "doctor_unavailable",
    "details": {
        "appointment_date": ["Doctor is not available at the requested time"]
    }
}
```

## Examples 🎯

### 1. Creating a New Appointment

```javascript
// Example using fetch
const response = await fetch('http://api.example.com/api/appointments/', {
    method: 'POST',
    headers: {
        'Authorization': 'Bearer your_token',
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        "doctor_id": 1,
        "hospital": 1,
        "department": 1,
        "appointment_date": "2025-02-27T15:00:00Z",
        "appointment_type": "consultation",
        "priority": "normal",
        "chief_complaint": "Regular checkup",
        "fee_id": 1
    })
});

const data = await response.json();
```

### 2. Checking Doctor Availability

Before creating an appointment, check doctor's availability:

- Doctor must be available on the requested day (consultation_days)
- Time must be within consultation hours
- No overlapping appointments
- Doctor must be able to practice
- Appointment must be in the future

### 3. Handling Appointment Fees

The fee structure includes:
- Base fee
- Registration fee (if applicable)
- Medical card fee (if applicable)
- Insurance coverage (if applicable)
- Senior citizen discounts (if applicable)

## Best Practices 💡

1. **Validation**
   - Always validate appointment dates are in the future
   - Check doctor availability before scheduling
   - Verify patient registration with hospital
   - Handle timezone differences appropriately

2. **Error Handling**
   - Implement proper error handling for all API calls
   - Display user-friendly error messages
   - Handle network errors gracefully

3. **User Experience**
   - Show loading states during API calls
   - Implement proper form validation
   - Provide clear feedback on success/failure
   - Include appointment confirmation details

4. **Security**
   - Always use HTTPS
   - Include proper authentication headers
   - Validate user permissions
   - Sanitize input data

## Testing 🧪

Test scenarios to implement:

1. **Appointment Creation**
   - Create with valid data
   - Handle validation errors
   - Check doctor availability
   - Verify fee calculation

2. **Appointment Management**
   - Update appointment details
   - Cancel appointments
   - Handle appointment approval
   - Process referrals

3. **Error Cases**
   - Invalid dates
   - Unavailable time slots
   - Missing required fields
   - Permission issues

## Support 🆘

For additional support or questions:
- Email: support@phbmanagement.com
- Documentation: [Full API Documentation](https://docs.phbmanagement.com)
- Status Page: [System Status](https://status.phbmanagement.com) 