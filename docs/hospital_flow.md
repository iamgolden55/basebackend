# Hospital Management Flow Documentation

## Overview 🏥
This document explains the complete hospital management flow in our healthcare system, including hospital settings, doctor assignment configurations, approval workflows, and administrative controls.

## Table of Contents 📑
- [Hospital Setup](#hospital-setup)
- [Doctor Management](#doctor-management)
- [Assignment Settings](#assignment-settings)
- [Approval Workflows](#approval-workflows)
- [Administrative Controls](#administrative-controls)
- [Notifications](#notifications)
- [Best Practices](#best-practices)
- [Code Examples](#code-examples)

## Hospital Setup 🏗️

### Basic Hospital Configuration
```python
class Hospital(models.Model):
    name = models.CharField(max_length=255)
    address = models.TextField()
    contact_number = models.CharField(max_length=20)
    email = models.EmailField()
    license_number = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    
    # Operating hours
    operating_hours_start = models.TimeField()
    operating_hours_end = models.TimeField()
    
    # Configuration flags
    allow_emergency_appointments = models.BooleanField(default=True)
    allow_online_appointments = models.BooleanField(default=True)
    require_patient_registration = models.BooleanField(default=True)
```

### Department Configuration
```python
class Department(models.Model):
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField()
    is_active = models.BooleanField(default=True)
    
    # Department-specific settings
    requires_referral = models.BooleanField(default=False)
    allow_direct_booking = models.BooleanField(default=True)
```

## Doctor Management 👨‍⚕️

### Doctor Registration
```python
class Doctor(models.Model):
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    specialization = models.CharField(max_length=100)
    license_number = models.CharField(max_length=50)
    years_of_experience = models.IntegerField()
    
    # Availability settings
    consultation_hours_start = models.TimeField()
    consultation_hours_end = models.TimeField()
    consultation_days = models.CharField(max_length=100)  # e.g., "Mon,Tue,Wed"
    max_daily_appointments = models.IntegerField(default=20)
    
    # Status
    is_active = models.BooleanField(default=True)
    can_practice = models.BooleanField(default=True)
```

### Doctor Approval Workflow
```python
class DoctorApproval(models.Model):
    doctor = models.OneToOneField(Doctor, on_delete=models.CASCADE)
    is_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True)
    approved_at = models.DateTimeField(null=True)
    approval_notes = models.TextField(blank=True)
    
    def approve(self, approved_by, notes=""):
        self.is_approved = True
        self.approved_by = approved_by
        self.approved_at = timezone.now()
        self.approval_notes = notes
        self.save()
        
        # Enable doctor to practice
        self.doctor.can_practice = True
        self.doctor.save()
        
        # Send notifications
        notify_doctor_approval(self.doctor)
```

## Assignment Settings ⚙️

### Hospital-wide Assignment Configuration
```python
class DoctorAssignmentConfig(models.Model):
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE)
    
    # Approval settings
    requires_admin_approval = models.BooleanField(default=True)
    auto_approve_emergency = models.BooleanField(default=True)
    auto_approve_followup = models.BooleanField(default=False)
    min_doctor_score = models.FloatField(default=0.7)
    
    # Assignment preferences
    prioritize_experience = models.FloatField(default=0.3)
    prioritize_workload = models.FloatField(default=0.3)
    prioritize_rating = models.FloatField(default=0.2)
    prioritize_language_match = models.FloatField(default=0.2)
    
    def get_assignment_weights(self):
        return {
            'experience': self.prioritize_experience,
            'workload': self.prioritize_workload,
            'rating': self.prioritize_rating,
            'language': self.prioritize_language_match
        }
```

### Department-specific Overrides
```python
class DepartmentAssignmentConfig(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    
    # Override hospital settings
    override_hospital_config = models.BooleanField(default=False)
    requires_admin_approval = models.BooleanField(default=True)
    
    # Department-specific rules
    require_specialist_approval = models.BooleanField(default=False)
    min_years_experience = models.IntegerField(default=0)
```

## Approval Workflows 📋

### Standard Approval Process
```python
def process_appointment_approval(appointment):
    """Process appointment approval based on hospital settings"""
    hospital_config = DoctorAssignmentConfig.objects.get(
        hospital=appointment.hospital
    )
    
    department_config = DepartmentAssignmentConfig.objects.get(
        department=appointment.department
    )
    
    # Check if department overrides hospital settings
    if department_config.override_hospital_config:
        requires_approval = department_config.requires_admin_approval
    else:
        requires_approval = hospital_config.requires_admin_approval
    
    if not requires_approval:
        auto_approve_appointment(appointment)
        return
    
    # Check auto-approval conditions
    if can_auto_approve_appointment(appointment, hospital_config):
        auto_approve_appointment(appointment)
    else:
        queue_for_admin_approval(appointment)
```

### Auto-Approval Conditions
```python
def can_auto_approve_appointment(appointment, config):
    """Check if appointment can be auto-approved"""
    # Emergency override
    if appointment.priority == 'emergency' and config.auto_approve_emergency:
        return True
    
    # Follow-up override
    if appointment.is_followup and config.auto_approve_followup:
        return True
    
    # High confidence match
    if appointment.ml_score >= config.min_doctor_score:
        return True
    
    return False
```

## Administrative Controls 🎛️

### Hospital Admin Interface
```python
class HospitalAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'allow_online_appointments']
    list_filter = ['is_active', 'allow_online_appointments']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'address', 'contact_number', 'email')
        }),
        ('Operating Hours', {
            'fields': ('operating_hours_start', 'operating_hours_end')
        }),
        ('Appointment Settings', {
            'fields': (
                'allow_emergency_appointments',
                'allow_online_appointments',
                'require_patient_registration'
            )
        })
    )
```

### Assignment Configuration Interface
```python
class DoctorAssignmentConfigAdmin(admin.ModelAdmin):
    list_display = ['hospital', 'requires_admin_approval']
    
    fieldsets = (
        ('Approval Settings', {
            'fields': (
                'requires_admin_approval',
                'auto_approve_emergency',
                'auto_approve_followup',
                'min_doctor_score'
            )
        }),
        ('Assignment Weights', {
            'fields': (
                'prioritize_experience',
                'prioritize_workload',
                'prioritize_rating',
                'prioritize_language_match'
            )
        })
    )
```

## Notifications 📬

### Admin Notifications
```python
def notify_admin_pending_approval(appointment):
    """Notify admin of pending appointment approval"""
    notification = AdminNotification.objects.create(
        hospital=appointment.hospital,
        notification_type='pending_approval',
        appointment=appointment,
        message=f"New appointment requires approval: {appointment.id}"
    )
    
    # Send email to admin
    send_admin_email(
        subject="Pending Appointment Approval",
        template="emails/pending_approval.html",
        context={
            'appointment': appointment,
            'approval_link': generate_approval_link(appointment)
        }
    )
```

### Doctor Notifications
```python
def notify_doctor_assignment(appointment):
    """Notify doctor of new assignment"""
    notification = DoctorNotification.objects.create(
        doctor=appointment.doctor,
        notification_type='new_assignment',
        appointment=appointment,
        message=f"New appointment assigned: {appointment.id}"
    )
    
    # Send email to doctor
    send_doctor_email(
        subject="New Appointment Assignment",
        template="emails/new_assignment.html",
        context={'appointment': appointment}
    )
```

## Best Practices 📝

1. **Configuration Management**
   - Keep hospital-wide settings as default
   - Use department overrides sparingly
   - Document all configuration changes

2. **Doctor Assignment**
   - Regularly review auto-approval thresholds
   - Monitor ML assignment accuracy
   - Adjust weights based on performance

3. **Continuity of Care**
   - Configure appropriate continuity weights by department
   - Set follow-up appointment continuity multipliers
   - Monitor continuity metrics and patient satisfaction
   - Balance continuity with specialty matching needs
   - Regularly review continuity exceptions

4. **Approval Workflow**
   - Set clear approval criteria
   - Maintain audit trails
   - Regular review of approval patterns

5. **Security**
   - Implement role-based access control
   - Log all configuration changes
   - Regular security audits

## Code Examples 💻

### Setting Up Hospital Configuration
```python
# Create hospital with default settings
hospital = Hospital.objects.create(
    name="General Hospital",
    address="123 Healthcare Ave",
    operating_hours_start=time(8, 0),  # 8 AM
    operating_hours_end=time(17, 0),   # 5 PM
    allow_online_appointments=True
)

# Configure doctor assignment
assignment_config = DoctorAssignmentConfig.objects.create(
    hospital=hospital,
    use_ml_assignment=True,
    auto_approve_threshold=0.85,
    emergency_auto_assign=True,
    language_match_weight=2.0,
    specialty_match_weight=3.0,
    experience_weight=0.3,
    workload_weight=0.2,
    continuity_weight=2.5,  # Base weight for continuity of care
    follow_up_continuity_multiplier=3.0,  # Higher weight for follow-ups
    emergency_continuity_weight=0.0,  # No continuity for emergencies
    max_continuity_appointments=5,  # Max appointments to consider
    continuity_decay_days=365  # Decay period for continuity score
)

# Configure continuity of care settings by department
cardiology_dept = Department.objects.get(name="Cardiology")
emergency_dept = Department.objects.get(name="Emergency")

ContinuityConfig.objects.create(
    hospital=hospital,
    department=cardiology_dept,
    base_weight=3.0,  # Higher continuity weight for cardiology
    follow_up_multiplier=3.5,
    max_appointments=7,
    decay_days=450  # Longer decay period for cardiology
)

ContinuityConfig.objects.create(
    hospital=hospital,
    department=emergency_dept,
    base_weight=0.5,  # Lower continuity weight for emergency
    follow_up_multiplier=1.5,
    max_appointments=3,
    decay_days=180  # Shorter decay period for emergency
)

# Department-specific settings
department = Department.objects.create(
    hospital=hospital,
    name="Neurology",
    requires_referral=True
)

department_config = DepartmentAssignmentConfig.objects.create(
    department=department,
    override_hospital_config=True,
    requires_admin_approval=True,
    require_specialist_approval=True
)
```

### Managing Approval Flow
```python
def handle_appointment_creation(appointment_data):
    """Handle new appointment creation with proper approval flow"""
    # Create appointment
    appointment = create_appointment_with_assignment(appointment_data)
    
    # Process approval
    process_appointment_approval(appointment)
    
    # Send notifications
    if appointment.status == 'confirmed':
        notify_doctor_assignment(appointment)
        notify_patient_confirmation(appointment)
    else:
        notify_admin_pending_approval(appointment)
    
    return appointment
```

## Related Documentation 📚
- Appointment Flow Documentation
- Doctor Management System
- Patient Registration System
- ML-Based Doctor Assignment
- Notification System 