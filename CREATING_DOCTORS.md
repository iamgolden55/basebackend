# Creating Doctor Accounts

## The Two-Model System

PHB uses a two-model system for doctors:

1. **CustomUser** - Handles authentication (login, password, OTP)
2. **Doctor** - Handles professional information (hospital, department, specialization)

**IMPORTANT**: Both models must exist for a doctor to work properly. Missing the Doctor record will cause the error: *"You are not registered as a doctor in the system"*

---

## Method 1: Using Management Command (Recommended)

The safest way to create a doctor is using the management command, which creates BOTH records in a single transaction.

### Basic Example

```bash
python manage.py create_doctor \
  --email dr.john.doe@hospital.com \
  --password SecurePassword123! \
  --first-name John \
  --last-name Doe \
  --hospital-id 27 \
  --department-id 32 \
  --specialization "General Medicine" \
  --phone "+2348012345678"
```

### With OTP Disabled (For Testing)

```bash
python manage.py create_doctor \
  --email dr.test@hospital.com \
  --password TestDoctor123! \
  --first-name Test \
  --last-name Doctor \
  --hospital-id 27 \
  --department-id 32 \
  --specialization "General Medicine" \
  --phone "+2348012345678" \
  --skip-otp
```

### Full Example with All Options

```bash
python manage.py create_doctor \
  --email dr.ada.nwosu@hospital.com \
  --password SecurePass123! \
  --first-name Ada \
  --last-name Nwosu \
  --hospital-id 27 \
  --department-id 32 \
  --specialization "Cardiology" \
  --phone "+2348098765432" \
  --country "Nigeria" \
  --state "Lagos" \
  --city "Lagos" \
  --years-experience 15 \
  --skip-otp
```

---

## Method 2: Manual Creation (Advanced)

If you need to create doctors manually (e.g., in Django shell), follow this pattern:

### Step 1: Find Hospital and Department IDs

```python
from api.models.medical.hospital import Hospital
from api.models.medical.department import Department

# List hospitals
for h in Hospital.objects.all():
    print(f"ID: {h.id}, Name: {h.name}")

# List departments for a hospital
hospital = Hospital.objects.get(id=27)
for d in Department.objects.filter(hospital=hospital):
    print(f"ID: {d.id}, Name: {d.name}, Hospital: {d.hospital.name}")
```

### Step 2: Create CustomUser

```python
from api.models.user.custom_user import CustomUser

user = CustomUser.objects.create_user(
    email='dr.example@hospital.com',
    password='SecurePassword123!',
    first_name='Example',
    last_name='Doctor',
    role='doctor',  # CRITICAL: Must be 'doctor'
    phone='+2348012345678',
    country='Nigeria',
    state='Delta',
    city='Asaba',
    is_email_verified=True,
    has_completed_onboarding=True,
    otp_required_for_login=False  # Set to True for production
)
```

### Step 3: Create Doctor Record

```python
from api.models.medical_staff.doctor import Doctor
from datetime import date, timedelta

doctor = Doctor.objects.create(
    user=user,
    hospital=hospital,
    department=department,
    specialization='General Medicine',
    medical_license_number=f'MD-{user.id}-NG-2024',
    license_expiry_date=date.today() + timedelta(days=1825),  # 5 years
    years_of_experience=10,
    qualifications=['MBBS', 'MD General Medicine'],
    is_active=True,
    status='active',
    available_for_appointments=True,
    consultation_days='Mon,Tue,Wed,Thu,Fri',
    max_daily_appointments=20,
    appointment_duration=30
)
```

---

## Required Fields Reference

### CustomUser (Step 2)
- `email` - Unique email address
- `password` - Secure password
- `first_name` - Doctor's first name
- `last_name` - Doctor's last name
- `role` - Must be `'doctor'`
- `phone` - Contact phone number
- `country`, `state`, `city` - Location
- `is_email_verified` - Set to `True` for staff
- `has_completed_onboarding` - Set to `True` for staff
- `otp_required_for_login` - `True` (production) or `False` (testing)

### Doctor (Step 3)
- `user` - ForeignKey to CustomUser (from Step 2)
- `hospital` - ForeignKey to Hospital
- `department` - ForeignKey to Department
- `specialization` - Medical specialization (e.g., "Cardiology")
- `medical_license_number` - Unique license number
- `license_expiry_date` - License expiration date
- `years_of_experience` - Years of practice
- `qualifications` - JSONField with list of degrees
- `is_active` - Boolean, set to `True`
- `status` - Choices: 'active', 'on_leave', 'suspended', 'retired'
- `available_for_appointments` - Boolean, set to `True`
- `consultation_days` - Comma-separated days (e.g., 'Mon,Tue,Wed,Thu,Fri')
- `max_daily_appointments` - Integer (default: 20)
- `appointment_duration` - Integer in minutes (default: 30)

---

## Troubleshooting

### Error: "You are not registered as a doctor in the system"

**Cause**: CustomUser exists with `role='doctor'` but no Doctor model record.

**Fix**: Create the Doctor record for the user:

```bash
python manage.py shell
```

```python
from api.models.user.custom_user import CustomUser
from api.models.medical_staff.doctor import Doctor
from api.models.medical.hospital import Hospital
from api.models.medical.department import Department
from datetime import date, timedelta

# Get the user
user = CustomUser.objects.get(email='problematic.doctor@email.com')

# Get hospital and department
hospital = Hospital.objects.get(id=27)
department = Department.objects.get(id=32)

# Create Doctor record
doctor = Doctor.objects.create(
    user=user,
    hospital=hospital,
    department=department,
    specialization='General Medicine',
    medical_license_number=f'MD-{user.id}-NG-{date.today().year}',
    license_expiry_date=date.today() + timedelta(days=1825),
    years_of_experience=5,
    qualifications=['MBBS'],
    is_active=True,
    status='active',
    available_for_appointments=True,
    consultation_days='Mon,Tue,Wed,Thu,Fri',
    max_daily_appointments=20,
    appointment_duration=30
)

print(f"✅ Doctor record created: {doctor.id}")
```

### Error: "Department does not belong to hospital"

**Cause**: The department and hospital IDs don't match.

**Fix**: Verify the department belongs to the hospital:

```python
department = Department.objects.get(id=32)
print(f"Department: {department.name}")
print(f"Hospital: {department.hospital.name}")
print(f"Hospital ID: {department.hospital.id}")
```

### Error: "UNIQUE constraint failed"

**Cause**: Trying to create a doctor for a user that already has a Doctor record.

**Fix**: Check if Doctor record exists:

```python
user = CustomUser.objects.get(email='doctor@email.com')
try:
    doctor = Doctor.objects.get(user=user)
    print(f"✅ Doctor record already exists: {doctor.id}")
except Doctor.DoesNotExist:
    print("❌ No Doctor record - can create one")
```

---

## Verifying Doctor Creation

After creating a doctor, verify both records exist:

```bash
python manage.py shell
```

```python
from api.models.user.custom_user import CustomUser
from api.models.medical_staff.doctor import Doctor

email = 'doctor@email.com'

# Check CustomUser
user = CustomUser.objects.get(email=email)
print(f"✅ CustomUser: {user.id} - {user.email} - Role: {user.role}")

# Check Doctor
doctor = Doctor.objects.get(user=user)
print(f"✅ Doctor: {doctor.id}")
print(f"   Hospital: {doctor.hospital.name}")
print(f"   Department: {doctor.department.name}")
print(f"   Specialization: {doctor.specialization}")
```

---

## Quick Reference: Test Doctor

Current test doctor in the system:

```
Email: dr.emmanuel.okonkwo@phb-test.com
Password: TestDoctor123!
Hospital: New General Central Hospital GRA Asaba (ID: 27)
Department: General Medicine (ID: 32)
OTP: Disabled
CustomUser ID: 82
Doctor ID: 12
```

---

## Best Practices

1. ✅ **Always use the management command** for creating doctors
2. ✅ **Verify hospital and department exist** before creating
3. ✅ **Use transaction.atomic()** when creating manually
4. ✅ **Enable OTP in production** (`otp_required_for_login=True`)
5. ✅ **Set is_email_verified=True** for staff accounts
6. ✅ **Use unique license numbers** (format: `MD-{user_id}-NG-{year}`)
7. ✅ **Test the account** after creation by logging in

---

## Future Improvements

Consider implementing:
- Automatic Doctor record creation when CustomUser with role='doctor' is created (using Django signals)
- API endpoint for admin to create doctors
- Bulk import command for multiple doctors
- Doctor approval workflow for registry integration
