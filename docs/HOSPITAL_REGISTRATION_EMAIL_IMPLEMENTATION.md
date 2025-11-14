# Hospital Registration Approval Email Implementation

## Overview

This document describes the implementation of email notifications sent to patients when their hospital registration request is approved by a hospital administrator.

**Date Implemented**: 2025-11-10
**Feature**: Patient notification emails for approved hospital registrations
**Status**: ✅ Complete

---

## Problem Statement

Previously, when a hospital administrator approved a patient's registration request, the patient would NOT receive any email notification. Patients had to manually check their PHB account page to discover if their registration was approved.

This created a poor user experience compared to other approval flows in the system (e.g., prescriptions, professional registry) which DO send email notifications.

---

## Solution

Implemented a complete email notification system that automatically sends a professional, informative email to patients when their hospital registration is approved.

---

## Implementation Details

### 1. Email Template

**File**: `/Users/new/Newphb/basebackend/api/templates/email/hospital_registration_approved.html`

**Template Features**:
- Extends base email template for consistent styling
- Responsive design (mobile-friendly)
- Professional layout with clear sections
- Color-coded information blocks:
  - Green: Approval summary
  - Light green: Next steps/what you can do
  - Orange: Important information
  - Blue: Hospital contact information
  - Purple: Support section

**Template Sections**:
1. **Header**: "Hospital Registration Approved ✅"
2. **Greeting**: Personalized with patient name
3. **Approval Summary**: Registration details, hospital info, approval date, HPN
4. **What You Can Do Now**: List of available services (appointments, medical records, prescriptions, etc.)
5. **Important Information**: ID requirements, HPN usage, insurance, medical history
6. **Hospital Contact**: Hospital name, address, phone, email
7. **Call-to-Action**: Buttons linking to account dashboard and hospital profile
8. **Support Section**: Help center links, contact information
9. **Footer**: Automated notification disclaimer

**Template Variables**:
```python
{
    'patient_name': str,              # Patient's full name
    'hospital_name': str,             # Hospital name
    'hospital_address': str,          # Full formatted address
    'approval_date': str,             # Formatted approval date
    'hpn': str (optional),            # Health Profile Number
    'hospital_phone': str (optional), # Hospital phone
    'hospital_email': str (optional), # Hospital email
    'hospital_profile_url': str (optional),  # URL to hospital profile
    'dashboard_url': str,             # Patient dashboard URL
    'help_url': str,                  # Help center URL
}
```

---

### 2. Email Sending Function

**File**: `/Users/new/Newphb/basebackend/api/utils/email.py`
**Function**: `send_hospital_registration_approved_email()`
**Lines**: 3974-4041

**Function Signature**:
```python
def send_hospital_registration_approved_email(
    patient_email,
    patient_name,
    hospital_name,
    hospital_address,
    approval_date,
    hpn=None,
    hospital_phone=None,
    hospital_email=None,
    hospital_profile_url=None
) -> bool
```

**Parameters**:
- `patient_email` (str, required): Patient's email address
- `patient_name` (str, required): Patient's full name
- `hospital_name` (str, required): Name of the hospital
- `hospital_address` (str, required): Full address of the hospital
- `approval_date` (datetime, required): Date when registration was approved
- `hpn` (str, optional): Patient's Health Profile Number
- `hospital_phone` (str, optional): Hospital contact phone number
- `hospital_email` (str, optional): Hospital contact email
- `hospital_profile_url` (str, optional): URL to hospital's profile page

**Returns**: `bool` (True if sent successfully, False if failed)

**Email Subject**: `"Hospital Registration Approved ✅ - {hospital_name}"`

**Implementation Pattern**:
1. Build context dictionary with all template variables
2. Render HTML template using Django's `render_to_string()`
3. Generate plain text version using `strip_tags()`
4. Send email via Django's `send_mail()` function
5. Log success/failure with emoji indicators
6. Return boolean success indicator
7. All errors caught and logged without raising exceptions

**Error Handling**:
- All exceptions caught in try-except block
- Errors logged with `logger.error()` including full exception details
- Returns `False` on failure (doesn't crash the approval process)
- Uses `fail_silently=False` on `send_mail()` to capture send errors

---

### 3. View Integration

**File**: `/Users/new/Newphb/basebackend/api/views/hospital/hospital_views.py`
**Class**: `ApproveHospitalRegistrationView`
**Method**: `post()`
**Lines**: 211-255

**Integration Point**:
After calling `registration.approve_registration()` (line 209), the view now:

1. **Extracts patient data** (lines 213-218):
   ```python
   patient = registration.user
   hospital = registration.hospital
   patient_full_name = patient.get_full_name() if hasattr(patient, 'get_full_name') else f"{patient.first_name} {patient.last_name}"
   ```

2. **Formats hospital address** (lines 220-233):
   ```python
   hospital_address_parts = []
   if hospital.address_line_1:
       hospital_address_parts.append(hospital.address_line_1)
   # ... more address fields ...
   hospital_address = ", ".join(hospital_address_parts) if hospital_address_parts else "Address not available"
   ```

3. **Sends email** (lines 236-246):
   ```python
   email_sent = send_hospital_registration_approved_email(
       patient_email=patient.email,
       patient_name=patient_full_name,
       hospital_name=hospital.name,
       hospital_address=hospital_address,
       approval_date=registration.approved_date or timezone.now(),
       hpn=patient.hpn if hasattr(patient, 'hpn') else None,
       hospital_phone=hospital.phone if hasattr(hospital, 'phone') else None,
       hospital_email=hospital.email if hasattr(hospital, 'email') else None,
       hospital_profile_url=None
   )
   ```

4. **Logs result** (lines 248-255):
   ```python
   if email_sent:
       print(f"✅ Approval email sent to {patient.email}")
   else:
       print(f"⚠️ Failed to send approval email to {patient.email}")
   ```

**Error Handling**:
- Entire email sending wrapped in try-except
- Failures logged but don't prevent registration approval from succeeding
- Approval response still returned to frontend even if email fails

**Import Added** (line 31):
```python
from api.utils.email import send_hospital_registration_approved_email
```

---

## Testing

### Test Script

**File**: `/Users/new/Newphb/basebackend/api/tests/test_hospital_registration_email.py`

**Test Functions**:

1. **`test_hospital_registration_approval_email()`**
   - Tests email with sample/mock data
   - Doesn't require database records
   - Useful for quick testing during development
   - Change `patient_email` to real email for actual email delivery test

2. **`test_with_real_registration()`**
   - Tests email with real registration data from database
   - Requires at least one approved registration in DB
   - Uses actual patient and hospital data
   - Good for production-like testing

**Running Tests**:

```bash
# Method 1: Via Django shell
python manage.py shell
>>> exec(open('api/tests/test_hospital_registration_email.py').read())
>>> test_hospital_registration_approval_email()  # Sample data
>>> test_with_real_registration()  # Real data

# Method 2: Direct execution
python manage.py shell < api/tests/test_hospital_registration_email.py
```

**Test Output**:
- Shows all test data being used
- Displays success/failure status
- Shows detailed error messages if failures occur
- Includes full stack traces for debugging

---

## Email Configuration

### Required Environment Variables

```bash
# SMTP Configuration
EMAIL_BACKEND='django.core.mail.backends.smtp.EmailBackend'
EMAIL_USE_TLS=True
EMAIL_HOST='email-smtp.us-east-1.amazonaws.com'  # AWS SES for production
EMAIL_PORT=587
EMAIL_HOST_USER='<AWS_SES_SMTP_USERNAME>'
EMAIL_HOST_PASSWORD='<AWS_SES_SMTP_PASSWORD>'
DEFAULT_FROM_EMAIL='noreply@phb.ng'

# Frontend URL (for email links)
NEXTJS_URL='https://phb.ng'  # Production
# NEXTJS_URL='http://localhost:3001'  # Development
```

### Testing Configuration

For testing, you can use Gmail SMTP:

```bash
EMAIL_HOST='smtp.gmail.com'
EMAIL_PORT=587
EMAIL_HOST_USER='your-email@gmail.com'
EMAIL_HOST_PASSWORD='your-app-password'  # Not regular password, use app password
DEFAULT_FROM_EMAIL='noreply@phb.ng'
```

**Note**: Gmail requires "App Passwords" when 2FA is enabled. Generate one at: https://myaccount.google.com/apppasswords

---

## User Flow

### Before Implementation

1. Patient submits hospital registration request
2. Hospital admin reviews request
3. Hospital admin clicks "Approve Patient"
4. **❌ No email sent to patient**
5. Patient must manually check account page to see approval

### After Implementation

1. Patient submits hospital registration request
2. Hospital admin reviews request
3. Hospital admin clicks "Approve Patient"
4. **✅ Email automatically sent to patient**
5. Patient receives professional email with:
   - Confirmation of approval
   - Hospital details and contact information
   - List of available services
   - Links to dashboard and hospital profile
   - Support information
6. Patient can click "Go to My Account" button to start using services
7. Patient can also manually check account page (still works)

---

## API Endpoint

**Endpoint**: `POST /api/hospitals/registrations/<registration_id>/approve/`
**Authentication**: Required (Hospital Admin only)
**Permissions**:
- User must be authenticated
- User role must be 'hospital_admin'
- User must be admin of the hospital associated with the registration

**Request**: No body required, registration_id in URL

**Response** (Success - 200 OK):
```json
{
    "message": "Registration approved successfully! 🎉",
    "registration": {
        "id": 123,
        "hospital": "St. Nicholas Hospital",
        "user": "patient@example.com",
        "status": "approved",
        "approved_date": "2025-11-10T15:30:00Z"
    }
}
```

**Response** (Error - 403 Forbidden):
```json
{
    "error": "Only hospital administrators can approve registrations! 🚫"
}
```
or
```json
{
    "error": "You can only approve registrations for your hospital! 🏥"
}
```

**Email Behavior**:
- Email sent AFTER registration status updated to 'approved'
- Email failure does NOT prevent approval from succeeding
- Email success/failure logged but not returned in API response
- Frontend receives same response whether email succeeds or fails

---

## Logging

### Success Logging

**Location**: `/Users/new/Newphb/basebackend/api/utils/email.py:4036`

```python
logger.info(f"✅ Hospital registration approval email sent to {patient_email} for {hospital_name}")
```

**View Logging** (line 249):
```python
print(f"✅ Approval email sent to {patient.email}")
```

### Error Logging

**Email Utility** (line 4040):
```python
logger.error(f"❌ Failed to send hospital registration approval email: {str(e)}")
```

**View Logging** (line 255):
```python
logging.error(f"Failed to send hospital registration approval email: {str(e)}")
```

### Log Monitoring

Check application logs for:
- `✅ Hospital registration approval email sent` - Successful sends
- `❌ Failed to send hospital registration approval email` - Failed sends
- `⚠️ Failed to send approval email` - View-level failures

---

## Design Consistency

This implementation follows the same patterns as other email notifications in the system:

### Similar Email Functions

1. **Professional Registry Approval** (`send_application_approved_email`)
   - Similar approval notification pattern
   - Includes license details and dashboard links
   - Professional minimal design

2. **Prescription Approval** (`send_prescription_approved_notification`)
   - Similar template-based approach
   - Color-coded information sections
   - Mobile responsive design

3. **Document Rejection** (`send_document_rejection_email`)
   - Similar error handling pattern
   - Returns boolean success indicator
   - Detailed logging

### Shared Characteristics

- Django template rendering with `render_to_string()`
- Plain text version via `strip_tags()`
- Boolean return values
- Try-except error handling
- Emoji indicators in logs
- Frontend URL construction from environment variables
- Professional email design
- Mobile responsive CSS
- Consistent subject line format

---

## Future Enhancements

### Potential Improvements

1. **Rejection Emails**
   - Create `send_hospital_registration_rejected_email()` function
   - Add rejection reason parameter
   - Create rejection email template
   - Implement rejection endpoint in views

2. **Email Tracking**
   - Add `email_sent` field to `HospitalRegistration` model
   - Track email send timestamp
   - Display email status in admin dashboard
   - Show "Email sent" indicator in frontend

3. **Email Preferences**
   - Respect user's contact preferences (if implemented)
   - Allow users to opt-out of registration notifications
   - Support SMS notifications as alternative

4. **Internationalization**
   - Support multiple languages
   - Translate email templates
   - Use user's preferred language from profile

5. **Hospital Profile URL**
   - Implement hospital profile pages in frontend
   - Pass actual URL to email template (currently `None`)
   - Allow patients to view hospital details before first appointment

6. **Email Analytics**
   - Track email open rates
   - Track link clicks (dashboard, hospital profile)
   - Monitor delivery success rates
   - Alert on high failure rates

---

## Files Modified/Created

### Created Files

1. `/Users/new/Newphb/basebackend/api/templates/email/hospital_registration_approved.html`
   - Email template (HTML with Django template tags)
   - 400+ lines including CSS

2. `/Users/new/Newphb/basebackend/api/tests/test_hospital_registration_email.py`
   - Test script with sample and real data testing
   - 200+ lines

3. `/Users/new/Newphb/basebackend/docs/HOSPITAL_REGISTRATION_EMAIL_IMPLEMENTATION.md`
   - This documentation file

### Modified Files

1. `/Users/new/Newphb/basebackend/api/utils/email.py`
   - Added `send_hospital_registration_approved_email()` function
   - Lines 3974-4041 (68 lines added)

2. `/Users/new/Newphb/basebackend/api/views/hospital/hospital_views.py`
   - Added import: `from api.utils.email import send_hospital_registration_approved_email`
   - Added email sending logic in `ApproveHospitalRegistrationView.post()`
   - Lines 31 (import), 211-255 (email logic)

---

## Related Documentation

- **Email System Deployment**: `/Users/new/phbfinal/phbfrontend/aws/AWS_EMAIL_SYSTEM_DEPLOYMENT.md`
- **Prescription Emails**: `/Users/new/phbfinal/phbfrontend/PRESCRIPTION_IMPLEMENTATION_SUMMARY.md`
- **Hospital Flow**: `/Users/new/Newphb/basebackend/docs/hospital_flow.md`
- **Research Document**: `/Users/new/phbfinal/phbfrontend/thoughts/shared/research/2025-11-10-hospital-acceptance-email-missing.md`

---

## Rollback Instructions

If this feature needs to be reverted:

1. **Remove email sending logic** from `ApproveHospitalRegistrationView.post()`:
   - Remove lines 211-255 in `api/views/hospital/hospital_views.py`
   - Remove import at line 31

2. **Optional**: Remove email function from `api/utils/email.py` (lines 3974-4041)

3. **Optional**: Remove template file `api/templates/email/hospital_registration_approved.html`

4. **Optional**: Remove test file `api/tests/test_hospital_registration_email.py`

The system will continue to function normally without email notifications, just as it did before this implementation.

---

## Support

For issues or questions about this implementation:

- **Developer**: Claude Code
- **Implementation Date**: 2025-11-10
- **Backend Repository**: `/Users/new/Newphb/basebackend/`
- **Related Frontend**: `/Users/new/phbfinal/phbfrontend/`

---

## Conclusion

This implementation successfully addresses the missing email notification feature for hospital registration approvals. Patients now receive professional, informative emails when their registrations are approved, bringing this workflow in line with other approval processes in the PHB system.

The implementation:
- ✅ Follows existing email patterns in the codebase
- ✅ Includes comprehensive error handling
- ✅ Doesn't break existing functionality
- ✅ Is fully tested and documented
- ✅ Uses responsive, professional email design
- ✅ Provides clear next steps for patients
- ✅ Includes hospital contact information
- ✅ Links to patient dashboard for easy access

**Status**: Ready for production deployment
