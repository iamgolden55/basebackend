# api/models/medical_staff/doctor.py

from django.db import models
from django.core.exceptions import ValidationError
from ..user.custom_user import CustomUser
from ..medical.hospital import Hospital


class Doctor(models.Model):
    # Department choices organized by categories
    DEPARTMENTS = [
        # Core Medical Specialties
        ('general_medicine', 'General Medicine'),
        ('cardiology', 'Cardiology'),
        ('neurology', 'Neurology'),
        ('pediatrics', 'Pediatrics'),
        ('psychiatry', 'Psychiatry'),
        ('dermatology', 'Dermatology'),
        ('oncology', 'Oncology'),
        ('emergency_medicine', 'Emergency Medicine'),
        ('gastroenterology', 'Gastroenterology'),
        ('endocrinology', 'Endocrinology'),
        ('nephrology', 'Nephrology'),
        ('pulmonology', 'Pulmonology'),
        ('rheumatology', 'Rheumatology'),
        ('hematology', 'Hematology'),
        ('infectious_diseases', 'Infectious Diseases'),
        ('geriatrics', 'Geriatrics'),
        ('allergy_immunology', 'Allergy & Immunology'),
        
        # Surgical Specialties
        ('general_surgery', 'General Surgery'),
        ('orthopedic_surgery', 'Orthopedic Surgery'),
        ('neurosurgery', 'Neurosurgery'),
        ('cardiothoracic_surgery', 'Cardiothoracic Surgery'),
        ('pediatric_surgery', 'Pediatric Surgery'),
        ('plastic_surgery', 'Plastic Surgery'),
        ('trauma_surgery', 'Trauma Surgery'),
        ('vascular_surgery', 'Vascular Surgery'),
        
        # Women's Health
        ('obstetrics_gynecology', 'Obstetrics & Gynecology'),
        ('reproductive_medicine', 'Reproductive Medicine'),
        
        # Diagnostic & Support Specialties
        ('radiology', 'Radiology'),
        ('pathology', 'Pathology'),
        ('anesthesiology', 'Anesthesiology'),
        ('nuclear_medicine', 'Nuclear Medicine'),
        
        # Special Senses & ENT
        ('ophthalmology', 'Ophthalmology'),
        ('ent', 'ENT (Otolaryngology)'),
        
        # Other Specialties
        ('urology', 'Urology'),
        ('palliative_care', 'Palliative Care'),
        ('sports_medicine', 'Sports Medicine'),
        ('pain_management', 'Pain Management'),
        ('rehabilitation_medicine', 'Rehabilitation Medicine'),
        ('neonatology', 'Neonatal-Perinatal Medicine'),
    ]

    # Surgical subspecialties for surgeons
    SURGICAL_SUBSPECIALTIES = [
        ('minimally_invasive', 'Minimally Invasive Surgery'),
        ('robotic_surgery', 'Robotic Surgery'),
        ('transplant_surgery', 'Transplant Surgery'),
        ('bariatric_surgery', 'Bariatric Surgery'),
        ('oncologic_surgery', 'Oncologic Surgery'),
        ('pediatric_surgery', 'Pediatric Surgery'),
        ('cosmetic_surgery', 'Cosmetic Surgery'),
    ]

    # Your existing fields
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='doctor_profile'
    )
    
    # Department and specialization fields
    department = models.CharField(
        max_length=50,
        choices=DEPARTMENTS,
        default='general_medicine'
    )
    surgical_subspecialty = models.CharField(
        max_length=50,
        choices=SURGICAL_SUBSPECIALTIES,
        null=True,
        blank=True,
        help_text="Required only for surgical departments"
    )
    
    # Add validation for surgical subspecialty
    def clean(self):
        if 'surgery' in self.department and not self.surgical_subspecialty:
            raise ValidationError({
                'surgical_subspecialty': 'Surgical subspecialty is required for surgical departments'
            })
        super().clean()

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
  # Medical Credentials (existing fields plus new ones)
    medical_license_number = models.CharField(max_length=50, unique=True)
    license_expiry_date = models.DateField()
    specialization = models.CharField(max_length=100)
    years_of_experience = models.PositiveIntegerField()
    
    # Hospital Affiliation
    hospital = models.ForeignKey(
        Hospital,
        on_delete=models.SET_NULL,
        null=True,
        related_name='doctors'
    )
    
    # Status and Verification
    is_verified = models.BooleanField(default=False)
    verification_documents = models.FileField(
        upload_to='doctor_verifications/',
        null=True,
        blank=True
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ('active', 'Active'),
            ('on_leave', 'On Leave'),
            ('suspended', 'Suspended'),
            ('retired', 'Retired')
        ],
        default='active'
    )
    
    # Contact and Location
    office_phone = models.CharField(max_length=20, null=True, blank=True)
    office_location = models.CharField(max_length=100, null=True, blank=True)
    emergency_contact = models.CharField(max_length=20, null=True, blank=True)
    
    # Availability Settings
    available_for_appointments = models.BooleanField(default=True)
    consultation_hours_start = models.TimeField(null=True, blank=True)
    consultation_hours_end = models.TimeField(null=True, blank=True)
    consultation_days = models.CharField(
        max_length=100,
        help_text="Comma-separated days, e.g., 'Mon,Tue,Wed'"
    )
    
    # Additional Professional Info
    medical_school = models.CharField(max_length=200, null=True, blank=True)
    graduation_year = models.PositiveIntegerField(null=True, blank=True)
    board_certifications = models.TextField(null=True, blank=True)
    research_interests = models.TextField(null=True, blank=True)
    publications = models.TextField(null=True, blank=True)
    languages_spoken = models.CharField(
        max_length=200,
        help_text="Comma-separated languages",
        null=True,
        blank=True
    )

    class Meta:
        permissions = [
            ("can_prescribe", "Can prescribe medications"),
            ("can_view_patient_records", "Can view patient records"),
            ("can_update_patient_records", "Can update patient records"),
            ("can_perform_surgery", "Can perform surgical procedures"),
            ("can_admit_patients", "Can admit patients to hospital"),
            ("can_discharge_patients", "Can discharge patients"),
            ("can_order_tests", "Can order medical tests"),
            ("can_view_test_results", "Can view test results"),
        ]
        indexes = [
            models.Index(fields=['medical_license_number']),
            models.Index(fields=['department']),
            models.Index(fields=['status']),
            models.Index(fields=['hospital']),
        ]

def __str__(self):
    return f"Dr. {self.user.first_name} {self.user.last_name} - {self.get_department_display()}"

@property
def full_name(self):
    """Returns the doctor's full name with title"""
    return f"Dr. {self.user.first_name} {self.user.last_name}"

@property
def is_license_valid(self):
        """Check if the medical license is currently valid"""
        from datetime import date
        return self.license_expiry_date > date.today()

@property
def days_until_license_expires(self):
        """Calculate days remaining until license expires"""
        from datetime import date
        delta = self.license_expiry_date - date.today()
        return delta.days

def is_available_on_day(self, day):
    """Check if doctor is available on a specific day"""
    return day.lower()[:3] in [d.strip().lower() for d in self.consultation_days.split(',')]

def get_weekly_schedule(self):
    """Returns a structured weekly schedule"""
    days = self.consultation_days.split(',')
    return {
        day.strip(): {
            'start': self.consultation_hours_start,
            'end': self.consultation_hours_end
        } for day in days
    }

def validate_consultation_hours(self):
    """Validate consultation hours are logical"""
    if self.consultation_hours_start and self.consultation_hours_end:
        if self.consultation_hours_start >= self.consultation_hours_end:
            raise ValidationError({
                'consultation_hours': 'End time must be after start time'
            })

def clean(self):
    """Enhanced validation including all checks"""
    super().clean()
    # Check surgical subspecialty
    if 'surgery' in self.department and not self.surgical_subspecialty:
        raise ValidationError({
            'surgical_subspecialty': 'Surgical subspecialty is required for surgical departments'
        })
    
    # Validate consultation hours
    self.validate_consultation_hours()
    
    # Validate consultation days format
    if self.consultation_days:
        valid_days = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
        days = [d.strip().lower()[:3] for d in self.consultation_days.split(',')]
        invalid_days = [d for d in days if d not in valid_days]
        if invalid_days:
            raise ValidationError({
                'consultation_days': f'Invalid days found: {", ".join(invalid_days)}'
            })

def save(self, *args, **kwargs):
    """Enhanced save method with additional checks"""
    # Run all validations
    self.clean()
    
    # Ensure user role is 'doctor'
    if self.user.role != 'doctor':
        self.user.role = 'doctor'
        self.user.save()
        
    # Convert consultation days to standard format
    if self.consultation_days:
        days = [d.strip().capitalize() for d in self.consultation_days.split(',')]
        self.consultation_days = ','.join(days)
        
    super().save(*args, **kwargs)

def get_expertise_summary(self):
    """Returns a summary of doctor's expertise"""
    expertise = f"{self.get_department_display()}"
    if self.surgical_subspecialty:
        expertise += f" with specialization in {self.get_surgical_subspecialty_display()}"
    if self.board_certifications:
        expertise += f"\nBoard Certified in: {self.board_certifications}"
    return expertise

def is_available_for_appointment(self, date_time):
    """Check if doctor is available at a specific date and time"""
    if not self.available_for_appointments or self.status != 'active':
        return False
        
    # Check if it's a consultation day
    if not self.is_available_on_day(date_time.strftime('%a')):
        return False
        
    # Check if within consultation hours
    time = date_time.time()
    return self.consultation_hours_start <= time <= self.consultation_hours_end