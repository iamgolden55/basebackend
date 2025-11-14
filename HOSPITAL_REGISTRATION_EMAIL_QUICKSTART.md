# Hospital Registration Email - Quick Start Guide

## What Was Implemented

✅ **Automatic email notifications** sent to patients when hospitals approve their registration requests.

Previously, patients received NO email notification when approved. Now they get a professional, informative email with hospital details, next steps, and dashboard links.

---

## Quick Test

### 1. Test with Sample Data (No Database Required)

```bash
cd /Users/new/Newphb/basebackend
python manage.py shell
```

```python
exec(open('api/tests/test_hospital_registration_email.py').read())
```

**Change the email in the test script** to your real email to see the actual email:
- Edit: `api/tests/test_hospital_registration_email.py`
- Line 30: Change `'test.patient@example.com'` to your email
- Run the test again

### 2. Test with Real Registration

```python
# In Django shell
from api.tests.test_hospital_registration_email import test_with_real_registration
test_with_real_registration()
```

**Requirements**: At least one approved hospital registration in the database

---

## What Gets Sent

**Subject**: `Hospital Registration Approved ✅ - {Hospital Name}`

**Email Includes**:
- Approval confirmation message
- Hospital name, address, contact information
- Patient's Health Profile Number (HPN)
- List of available services (appointments, prescriptions, etc.)
- Call-to-action buttons (Go to My Account, View Hospital Profile)
- Support information
- Professional responsive design

---

## Files Created

1. **Email Template**:
   `/Users/new/Newphb/basebackend/api/templates/email/hospital_registration_approved.html`

2. **Email Function**:
   `/Users/new/Newphb/basebackend/api/utils/email.py` (lines 3974-4041)

3. **Test Script**:
   `/Users/new/Newphb/basebackend/api/tests/test_hospital_registration_email.py`

4. **Documentation**:
   `/Users/new/Newphb/basebackend/docs/HOSPITAL_REGISTRATION_EMAIL_IMPLEMENTATION.md`

---

## Files Modified

1. **Views** (to send email on approval):
   `/Users/new/Newphb/basebackend/api/views/hospital/hospital_views.py`
   - Added import (line 31)
   - Added email sending logic (lines 211-255)

---

## Environment Variables Required

Make sure these are set in your `.env` file:

```bash
# Email Configuration
EMAIL_HOST='smtp.gmail.com'  # For testing
EMAIL_PORT=587
EMAIL_HOST_USER='your-email@gmail.com'
EMAIL_HOST_PASSWORD='your-app-password'
DEFAULT_FROM_EMAIL='noreply@phb.ng'

# Frontend URL (for email links)
NEXTJS_URL='http://localhost:3001'  # Development
# NEXTJS_URL='https://phb.ng'  # Production
```

**Gmail Note**: Use App Password, not your regular password.
Generate at: https://myaccount.google.com/apppasswords

---

## How It Works

### Patient Side
1. Patient selects a hospital on `/account/link-phb`
2. Patient submits registration request
3. Status shows as "pending"

### Hospital Admin Side
1. Admin logs into hospital dashboard
2. Admin navigates to `/organization/user-registrations`
3. Admin clicks "Approve Patient" button
4. **✨ Email automatically sent to patient**
5. Patient receives email notification

### Patient Experience
1. Receives email: "Hospital Registration Approved ✅"
2. Views hospital details and contact information
3. Learns about available services
4. Clicks "Go to My Account" button
5. Can now book appointments, request prescriptions, etc.

---

## Monitoring

### Check Logs for Email Status

```bash
# Backend logs
tail -f /path/to/logs/django.log | grep "Hospital registration"

# Look for:
# ✅ Hospital registration approval email sent to patient@example.com for St. Nicholas Hospital
# ❌ Failed to send hospital registration approval email: [error]
```

### Django Shell Monitoring

```python
# Check recent registrations
from api.models import HospitalRegistration
recent = HospitalRegistration.objects.filter(status='approved').order_by('-approved_date')[:5]
for reg in recent:
    print(f"{reg.user.email} - {reg.hospital.name} - {reg.approved_date}")
```

---

## Troubleshooting

### Email Not Sending?

1. **Check environment variables**:
   ```python
   import os
   print(f"EMAIL_HOST: {os.environ.get('EMAIL_HOST')}")
   print(f"EMAIL_HOST_USER: {os.environ.get('EMAIL_HOST_USER')}")
   print(f"DEFAULT_FROM_EMAIL: {os.environ.get('DEFAULT_FROM_EMAIL')}")
   ```

2. **Check email template exists**:
   ```bash
   ls -la api/templates/email/hospital_registration_approved.html
   ```

3. **Test email function directly**:
   ```python
   from api.utils.email import send_hospital_registration_approved_email
   from django.utils import timezone

   result = send_hospital_registration_approved_email(
       patient_email='your-email@example.com',
       patient_name='Test Patient',
       hospital_name='Test Hospital',
       hospital_address='123 Test St, Lagos',
       approval_date=timezone.now(),
       hpn='PHB-TEST-123'
   )
   print(f"Email sent: {result}")
   ```

4. **Check Django logs**:
   ```bash
   python manage.py runserver
   # Look for error messages in console
   ```

### Common Issues

**"Template not found"**:
- Ensure template file exists at correct path
- Check `TEMPLATES` setting in `settings.py`

**"SMTPAuthenticationError"**:
- Use Gmail App Password (not regular password)
- Enable "Less secure app access" (not recommended)
- Use AWS SES for production

**"Connection refused"**:
- Check `EMAIL_HOST` and `EMAIL_PORT`
- Ensure firewall allows SMTP connections
- Try different SMTP server

---

## Production Deployment

### AWS SES Configuration

1. **Verify domain** in AWS SES console
2. **Create SMTP credentials**
3. **Update environment variables**:
   ```bash
   EMAIL_HOST='email-smtp.us-east-1.amazonaws.com'
   EMAIL_PORT=587
   EMAIL_HOST_USER='<AWS_SES_SMTP_USERNAME>'
   EMAIL_HOST_PASSWORD='<AWS_SES_SMTP_PASSWORD>'
   DEFAULT_FROM_EMAIL='noreply@phb.ng'
   NEXTJS_URL='https://phb.ng'
   ```

4. **Move out of SES sandbox** (if needed):
   - Request production access in AWS console
   - Required to send to non-verified emails

### Monitoring in Production

- Set up CloudWatch alarms for email failures
- Monitor email bounce rates
- Track email delivery metrics
- Set up email forwarding for bounces

---

## Next Steps

### Recommended Enhancements

1. **Add Rejection Emails**: Notify patients when registrations are rejected
2. **Email Tracking**: Add `email_sent` field to track which registrations had emails sent
3. **Frontend Indicators**: Show "Email sent" status in admin dashboard
4. **Email Preferences**: Allow users to opt-out of notifications
5. **Internationalization**: Translate emails to multiple languages

### Optional Features

- SMS notifications via Twilio
- In-app notifications
- Email open tracking
- Link click analytics

---

## Support

**Full Documentation**: `/Users/new/Newphb/basebackend/docs/HOSPITAL_REGISTRATION_EMAIL_IMPLEMENTATION.md`

**Test Script**: `/Users/new/Newphb/basebackend/api/tests/test_hospital_registration_email.py`

**Research Document**: `/Users/new/phbfinal/phbfrontend/thoughts/shared/research/2025-11-10-hospital-acceptance-email-missing.md`

---

## Summary

✅ Feature implemented and ready to use
✅ Email template created (professional design)
✅ Email function implemented (with error handling)
✅ Approval endpoint updated (sends email automatically)
✅ Test script created (easy testing)
✅ Documentation complete (this guide + full docs)

**No breaking changes** - existing functionality still works exactly as before, but now patients get email notifications!
