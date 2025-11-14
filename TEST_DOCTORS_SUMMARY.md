# Test Doctors Summary

## Overview

Two test doctors have been created in the system for testing different department workflows.

---

## 🩺 Doctor 1: Dr. Emmanuel Okonkwo (General Medicine)

### Login Credentials
- **Email**: `dr.emmanuel.okonkwo@phb-test.com`
- **Password**: `TestDoctor123!`
- **OTP Required**: No ❌

### Professional Details
- **Full Name**: Emmanuel Okonkwo
- **Specialization**: General Medicine
- **Experience**: 10 years
- **License**: MD-82-NG-2024
- **License Expiry**: November 11, 2030

### Hospital & Department
- **Hospital**: New General Central Hospital GRA Asaba (ID: 27)
- **Department**: General Medicine (ID: 32)
- **Department Type**: Primary care, general consultations

### Availability
- **Status**: Active
- **Days**: Monday - Friday
- **Max Appointments/Day**: 20
- **Appointment Duration**: 30 minutes

### Database IDs
- **User ID**: 82
- **Doctor ID**: 12
- **Hospital ID**: 27
- **Department ID**: 32

### What Appointments Can They See?
✅ Pending appointments in **General Medicine** department
✅ Appointments with general health concerns
✅ Non-specialized consultations

### Current Appointments
- **Pending Department Appointments**: 0
- **My Confirmed Appointments**: 0

---

## ❤️ Doctor 2: Dr. Ada Nwosu (Cardiology)

### Login Credentials
- **Email**: `dr.ada.nwosu@phb-test.com`
- **Password**: `TestDoctor123!`
- **OTP Required**: No ❌

### Professional Details
- **Full Name**: Ada Nwosu
- **Specialization**: Cardiology
- **Experience**: 15 years
- **License**: MD-83-NG-2025
- **License Expiry**: November 11, 2030

### Hospital & Department
- **Hospital**: New General Central Hospital GRA Asaba (ID: 27)
- **Department**: Cardiology (ID: 34)
- **Department Type**: Heart-related conditions, chest pain, cardiovascular issues

### Availability
- **Status**: Active
- **Days**: Monday - Friday
- **Max Appointments/Day**: 20
- **Appointment Duration**: 30 minutes

### Database IDs
- **User ID**: 83
- **Doctor ID**: 13
- **Hospital ID**: 27
- **Department ID**: 34

### What Appointments Can They See?
✅ Pending appointments in **Cardiology** department
✅ Appointments with chest pain complaints
✅ Cardiovascular-related consultations

### Current Appointments
- **Pending Department Appointments**: 1
  - Patient: Bernard James Kamilo (HPN: ASA 289 843 1620)
  - Complaint: Chest pain
  - Appointment ID: APT-3DF00D14
  - Date: November 12, 2025 at 10:00 AM

---

## 📊 Comparison Table

| Feature | Dr. Emmanuel Okonkwo | Dr. Ada Nwosu |
|---------|---------------------|---------------|
| Email | dr.emmanuel.okonkwo@phb-test.com | dr.ada.nwosu@phb-test.com |
| Password | TestDoctor123! | TestDoctor123! |
| Department | General Medicine (ID: 32) | Cardiology (ID: 34) |
| Specialization | General Medicine | Cardiology |
| Experience | 10 years | 15 years |
| User ID | 82 | 83 |
| Doctor ID | 12 | 13 |
| OTP | Disabled | Disabled |
| Pending Appointments | 0 | 1 |

---

## 🔄 Department Routing Example

**Scenario**: Bernard James Kamilo books an appointment with complaint "Chest pain"

### Routing Process:
1. ✅ Patient fills appointment form with chief complaint: "Chest - Chest pain"
2. ✅ System routes to **Cardiology Department** (ID: 34)
3. ✅ Appointment appears in Dr. Ada Nwosu's pending list
4. ❌ Appointment does NOT appear in Dr. Emmanuel Okonkwo's pending list

### Why?
- **Dr. Emmanuel** sees only **General Medicine** appointments
- **Dr. Ada** sees only **Cardiology** appointments
- Chest pain is routed to Cardiology, not General Medicine

---

## 🧪 Testing Scenarios

### Scenario 1: Test General Medicine Workflow
1. Create a patient appointment with complaint like:
   - "General checkup"
   - "Fever"
   - "Headache"
2. Login as Dr. Emmanuel Okonkwo
3. Should see the appointment in "Pending Department Appointments"

### Scenario 2: Test Cardiology Workflow
1. Create a patient appointment with complaint like:
   - "Chest pain"
   - "Heart palpitations"
   - "Shortness of breath"
2. Login as Dr. Ada Nwosu
3. Should see the appointment in "Pending Department Appointments"

### Scenario 3: Test Department Isolation
1. Create appointment in Cardiology
2. Login as Dr. Emmanuel (General Medicine)
3. Verify appointment does NOT appear
4. Login as Dr. Ada (Cardiology)
5. Verify appointment DOES appear

---

## 🚀 Quick Access URLs

### Professional Dashboard
- **Dr. Emmanuel**: `http://localhost:5173/professional/dashboard`
- **Dr. Ada**: `http://localhost:5173/professional/dashboard`

### Professional Login
- URL: `http://localhost:5173/professional/login`
- Use the credentials from the table above

---

## 📝 Notes

### Creating More Test Doctors

Use the management command:

```bash
cd /Users/new/Newphb/basebackend

python manage.py create_doctor \
  --email doctor.email@phb-test.com \
  --password TestDoctor123! \
  --first-name FirstName \
  --last-name LastName \
  --hospital-id 27 \
  --department-id [DEPARTMENT_ID] \
  --specialization "Specialization Name" \
  --phone "+2348012345678" \
  --years-experience 10 \
  --skip-otp
```

### Available Departments at Hospital 27

Common departments you can use:
- General Medicine (ID: 32)
- Cardiology (ID: 34)
- (Run query to see all departments)

### Department Query

```python
from api.models.medical.department import Department
from api.models.medical.hospital import Hospital

hospital = Hospital.objects.get(id=27)
for dept in Department.objects.filter(hospital=hospital):
    print(f"ID: {dept.id}, Name: {dept.name}")
```

---

## ✅ Verification Checklist

After creating a doctor, verify:

- [ ] Can login with provided credentials
- [ ] Professional dashboard loads without errors
- [ ] Correct hospital name displayed
- [ ] Correct department name displayed
- [ ] Pending appointments section shows (empty or with appointments)
- [ ] Department-specific appointments appear correctly
- [ ] No errors in browser console

---

**Created**: January 11, 2025
**Last Updated**: January 11, 2025
**Status**: ✅ Both doctors active and functional
