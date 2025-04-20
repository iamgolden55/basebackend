# api/models/medical_staff/doctor.py

from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth import get_user_model
from ..user.custom_user import CustomUser
from ..medical.hospital import Hospital
from ..medical.department import Department
from ..base import TimestampedModel

User = get_user_model()

class Doctor(TimestampedModel):
    """
    Doctor model representing medical professionals in the hospital.
    Handles doctor information, availability, and appointment management.
    """
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

    # Basic Information
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='doctor_profile',
        help_text="User account associated with this doctor"
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        related_name='doctors',
        help_text="Department where the doctor primarily works"
    )
    hospital = models.ForeignKey(
        Hospital,
        on_delete=models.SET_NULL,
        null=True,
        related_name='doctors',
        help_text="Primary hospital affiliation"
    )
    
    # Professional Information
    specialization = models.CharField(
        max_length=100,
        help_text="Doctor's medical specialization"
    )
    medical_license_number = models.CharField(
        max_length=50,
        unique=True,
        help_text="Medical license registration number"
    )
    license_expiry_date = models.DateField(
        help_text="Medical license expiry date"
    )
    years_of_experience = models.PositiveIntegerField(
        help_text="Years of professional experience"
    )
    qualifications = models.JSONField(
        default=list,
        help_text="List of academic and professional qualifications"
    )
    board_certifications = models.TextField(
        null=True,
        blank=True,
        help_text="Medical board certifications"
    )
    
    # Availability Management
    is_active = models.BooleanField(
        default=True,
        help_text="Whether the doctor is currently practicing"
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ('active', 'Active'),
            ('on_leave', 'On Leave'),
            ('suspended', 'Suspended'),
            ('retired', 'Retired')
        ],
        default='active',
        help_text="Current working status"
    )
    available_for_appointments = models.BooleanField(
        default=True,
        help_text="Whether accepting new appointments"
    )
    consultation_hours_start = models.TimeField(
        null=True,
        blank=True,
        help_text="Start time of consultation hours"
    )
    consultation_hours_end = models.TimeField(
        null=True,
        blank=True,
        help_text="End time of consultation hours"
    )
    consultation_days = models.CharField(
        max_length=100,
        help_text="Comma-separated days, e.g., 'Mon,Tue,Wed'"
    )
    max_daily_appointments = models.PositiveIntegerField(
        default=20,
        help_text="Maximum appointments per day"
    )
    appointment_duration = models.PositiveIntegerField(
        default=30,
        help_text="Default appointment duration in minutes"
    )
    
    # Additional Professional Info
    surgical_subspecialty = models.CharField(
        max_length=50,
        choices=SURGICAL_SUBSPECIALTIES,
        null=True,
        blank=True,
        help_text="Required only for surgical departments"
    )
    research_interests = models.TextField(
        null=True,
        blank=True,
        help_text="Areas of research interest"
    )
    publications = models.TextField(
        null=True,
        blank=True,
        help_text="Published research works"
    )
    languages_spoken = models.CharField(
        max_length=200,
        help_text="Comma-separated languages",
        null=True,
        blank=True
    )
    medical_school = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        help_text="Medical school attended"
    )
    graduation_year = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Year of graduation from medical school"
    )
    
    # Contact Information
    office_phone = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text="Office contact number"
    )
    office_location = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Office location within hospital"
    )
    emergency_contact = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text="Emergency contact number"
    )
    
    # Verification
    is_verified = models.BooleanField(
        default=False,
        help_text="Whether credentials are verified"
    )
    verification_documents = models.FileField(
        upload_to='doctor_verifications/',
        null=True,
        blank=True,
        help_text="Credential verification documents"
    )
    
    # New fields for ML-based doctor assignment
    expertise_codes = models.JSONField(
        default=list,
        help_text="List of ICD-10 codes the doctor specializes in"
    )
    primary_expertise_codes = models.JSONField(
        default=list,
        help_text="List of primary ICD-10 codes (highest expertise)"
    )
    chronic_care_experience = models.BooleanField(
        default=False,
        help_text="Whether doctor has experience with chronic conditions"
    )
    complex_case_rating = models.FloatField(
        default=0.0,
        help_text="Rating for handling complex cases (0-10)"
    )
    continuity_of_care_rating = models.FloatField(
        default=0.0,
        help_text="Rating for maintaining continuity of care (0-10)"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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
            models.Index(fields=['specialization']),
            models.Index(fields=['is_active', 'available_for_appointments']),
        ]

    def __str__(self):
        return f"Dr. {self.user.get_full_name()} - {self.specialization}"

    def clean(self):
        """Enhanced validation including all checks"""
        super().clean()
        
        # Validate department and surgical subspecialty
        if self.department and 'surgery' in self.department.name.lower():
            if not self.surgical_subspecialty:
                raise ValidationError({
                    'surgical_subspecialty': 'Surgical subspecialty is required for surgical departments'
                })
        
        # Validate consultation hours
        if self.consultation_hours_start and self.consultation_hours_end:
            if self.consultation_hours_start >= self.consultation_hours_end:
                raise ValidationError({
                    'consultation_hours': 'End time must be after start time'
                })
        
        # Validate consultation days format
        if self.consultation_days:
            valid_days = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
            days = [d.strip().lower()[:3] for d in self.consultation_days.split(',')]
            invalid_days = [d for d in days if d not in valid_days]
            if invalid_days:
                raise ValidationError({
                    'consultation_days': f'Invalid days found: {", ".join(invalid_days)}'
                })
        
        # Validate license expiry
        if self.license_expiry_date and self.license_expiry_date < timezone.now().date():
            raise ValidationError({
                'license_expiry_date': 'License has expired'
            })
        
        # Validate department and hospital consistency
        if self.department and self.hospital:
            if self.department.hospital != self.hospital:
                raise ValidationError({
                    'department': 'Department must belong to the selected hospital'
                })

    def save(self, *args, **kwargs):
        """Enhanced save method with additional checks"""
        self.clean()
        
        # Ensure user role is 'doctor'
        if hasattr(self.user, 'role') and self.user.role != 'doctor':
            self.user.role = 'doctor'
            self.user.save()
        
        # Convert consultation days to standard format
        if self.consultation_days:
            days = [d.strip().capitalize() for d in self.consultation_days.split(',')]
            self.consultation_days = ','.join(days)
        
        super().save(*args, **kwargs)

    # Properties
    @property
    def full_name(self):
        """Returns the doctor's full name with title"""
        return f"Dr. {self.user.get_full_name()}"

    @property
    def is_license_valid(self):
        """Check if the medical license is currently valid"""
        return self.license_expiry_date > timezone.now().date()

    @property
    def days_until_license_expires(self):
        """Calculate days remaining until license expires"""
        return (self.license_expiry_date - timezone.now().date()).days

    @property
    def can_practice(self):
        """Check if doctor can practice (active, verified, valid license)"""
        return (self.is_active and self.is_verified and 
                self.is_license_valid and self.status == 'active')

    # Appointment Management Methods
    def get_weekly_schedule(self):
        """Returns a structured weekly schedule"""
        if not self.consultation_days:
            return {}
            
        days = self.consultation_days.split(',')
        return {
            day.strip(): {
                'start': self.consultation_hours_start,
                'end': self.consultation_hours_end
            } for day in days
        }

    def is_available_on_day(self, day):
        """Check if doctor is available on a specific day"""
        if not self.can_practice:
            return False
            
        # Convert day to three-letter format (Mon, Tue, etc.)
        day_abbrev = day.strip()[:3].capitalize()
        consultation_days = [d.strip()[:3].capitalize() for d in self.consultation_days.split(',')]
        
        return day_abbrev in consultation_days

    def is_available_at(self, datetime, is_emergency=False, current_appointment=None):
        """Check if doctor is available at a specific time"""
        print(f"Checking availability for Dr. {self.user.get_full_name()} - {self.specialization} at {datetime}")
        print(f"Is emergency: {is_emergency}")
        
        if not self.can_practice:
            print("Doctor cannot practice")
            return False
            
        # For emergency appointments, only check if doctor can practice
        if is_emergency:
            print("Emergency appointment - doctor is available")
            return True
            
        # Check if it's a consultation day
        day_name = datetime.strftime('%A')[:3]  # Get first three letters of day name
        print(f"Day name: {day_name}")
        print(f"Consultation days: {self.consultation_days}")
        if not self.is_available_on_day(day_name):
            print(f"Not available on {day_name}")
            return False
            
        # Check if within consultation hours
        appointment_time = datetime.time()
        print(f"Time: {appointment_time}")
        print(f"Consultation hours: {self.consultation_hours_start} - {self.consultation_hours_end}")
        
        # Convert consultation hours to time objects if they're strings
        start_time = self.consultation_hours_start
        end_time = self.consultation_hours_end
        if isinstance(start_time, str):
            start_time = timezone.datetime.strptime(start_time, '%H:%M:%S').time()
        if isinstance(end_time, str):
            end_time = timezone.datetime.strptime(end_time, '%H:%M:%S').time()
            
        if not (start_time <= appointment_time <= end_time):
            print("Not within consultation hours")
            return False
            
        # Check if slot is already booked
        from api.models import Appointment
        
        # Calculate the end time of the requested appointment
        appointment_end = datetime + timezone.timedelta(minutes=30)  # Default duration is 30 minutes
        
        # Find any appointments that overlap with the requested time slot
        query = Appointment.objects.filter(
            doctor=self,
            status__in=['confirmed', 'pending'],
            appointment_date__date=datetime.date(),  # Only check appointments on the same day
            appointment_date__gte=datetime,  # Start time is after or at the requested time
            appointment_date__lt=appointment_end  # Start time is before the end of the requested slot
        )
        
        # Exclude current appointment if provided
        if current_appointment and current_appointment.pk:
            query = query.exclude(pk=current_appointment.pk)
            
        is_booked = query.exists()
        print(f"Slot is booked: {is_booked}")
        
        return not is_booked

    def get_available_slots(self, date):
        """Get available appointment slots for a given date"""
        if not self.can_practice:
            return []
            
        # Check if it's a consultation day
        if not self.is_available_on_day(date.strftime('%A')):
            return []
            
        from api.models import Appointment
        
        slots = []
        current_time = self.consultation_hours_start
        
        while current_time <= self.consultation_hours_end:
            slot_datetime = timezone.datetime.combine(date, current_time)
            
            # Check if slot is already booked
            is_booked = Appointment.objects.filter(
                doctor=self,
                appointment_date=slot_datetime,
                status__in=['confirmed', 'pending']
            ).exists()
            
            if not is_booked:
                slots.append(slot_datetime)
                
            # Move to next slot
            current_time = (timezone.datetime.combine(date, current_time) + 
                          timezone.timedelta(minutes=self.appointment_duration)).time()
            
        return slots

    def get_appointments_for_date(self, date):
        """Get all appointments for a specific date"""
        from api.models import Appointment
        return Appointment.objects.filter(
            doctor=self,
            appointment_date__date=date
        ).order_by('appointment_date')

    def get_appointment_count_for_date(self, date):
        """Get total number of appointments for a specific date"""
        return self.get_appointments_for_date(date).count()

    def can_accept_appointment(self, date):
        """Check if doctor can accept more appointments for a specific date"""
        if not self.can_practice:
            return False
        return (self.get_appointment_count_for_date(date) < 
                self.max_daily_appointments)

    def get_expertise_summary(self):
        """Get a summary of doctor's expertise"""
        expertise = {
            'specialization': self.specialization,
            'years_experience': self.years_of_experience,
            'board_certifications': self.board_certifications,
            'expertise_codes': self.expertise_codes,
            'primary_expertise': self.primary_expertise_codes,
            'chronic_care': self.chronic_care_experience,
            'complex_case_rating': self.complex_case_rating
        }
        return expertise
        
    def has_expertise_for_diagnosis(self, diagnosis_code):
        """Check if doctor has expertise for a specific diagnosis code"""
        # Direct match
        if diagnosis_code in self.expertise_codes:
            return True
            
        # Check for category match (first 3 characters of ICD-10)
        if len(diagnosis_code) >= 3:
            category = diagnosis_code[:3]
            for code in self.expertise_codes:
                if len(code) >= 3 and code[:3] == category:
                    return True
                    
        return False
        
    def calculate_diagnosis_match_score(self, diagnosis_codes):
        """Calculate match score for a list of diagnosis codes"""
        if not diagnosis_codes:
            return 0
            
        total_matches = 0
        primary_matches = 0
        
        for code in diagnosis_codes:
            if code in self.expertise_codes:
                total_matches += 1
                
            if code in self.primary_expertise_codes:
                primary_matches += 1
                
        # Calculate weighted score
        score = (total_matches * 1.0 + primary_matches * 2.0) / max(1, len(diagnosis_codes))
        return min(10.0, score * 3.0)  # Scale to 0-10