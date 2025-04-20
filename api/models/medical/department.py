# api/models/medical/department.py

from django.db import models
from django.core.exceptions import ValidationError
from django.db import transaction
from datetime import datetime, time
from django.utils import timezone
from ..base import TimestampedModel

class Department(TimestampedModel):
    """
    Department model representing different medical departments within a hospital.
    """
    DEPARTMENT_TYPES = [
        # Clinical Departments
        ('medical', 'Medical Department'),
        ('surgical', 'Surgical Department'),
        ('emergency', 'Emergency Department'),
        ('critical_care', 'Critical Care'),
        ('outpatient', 'Outpatient Clinic'),
        
        # Support Departments
        ('laboratory', 'Laboratory'),
        ('radiology', 'Radiology'),
        ('pharmacy', 'Pharmacy'),
        ('physiotherapy', 'Physiotherapy'),
        
        # Administrative Departments
        ('admin', 'Administration'),
        ('records', 'Medical Records'),
        ('it', 'Information Technology')
    ]

    WING_CHOICES = [
        ('north', 'North Wing'),
        ('south', 'South Wing'),
        ('east', 'East Wing'),
        ('west', 'West Wing'),
        ('central', 'Central Wing'),
    ]

    # Basic Information
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    department_type = models.CharField(
        max_length=20,
        choices=DEPARTMENT_TYPES,
        help_text="Type/Category of the department"
    )
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    # Contact and Location
    floor_number = models.CharField(
        max_length=10,
        help_text="Floor number where the department is located"
    )
    wing = models.CharField(
        max_length=50,
        choices=WING_CHOICES,
        help_text="Hospital wing where the department is located"
    )
    extension_number = models.CharField(
        max_length=10,
        help_text="Internal telephone extension"
    )
    emergency_contact = models.CharField(
        max_length=20,
        help_text="Emergency contact number"
    )
    email = models.EmailField(
        help_text="Department email address"
    )
    
    # Operational Details
    is_24_hours = models.BooleanField(
        default=False,
        help_text="Whether the department operates 24/7"
    )
    operating_hours = models.JSONField(
        default=dict,
        help_text="Operating hours for each day of the week"
    )
    
    # Capacity Management
    total_beds = models.PositiveIntegerField(
        default=0,
        help_text="Total number of regular beds"
    )
    occupied_beds = models.PositiveIntegerField(
        default=0,
        help_text="Number of occupied regular beds"
    )
    icu_beds = models.PositiveIntegerField(
        default=0,
        help_text="Total number of ICU beds"
    )
    occupied_icu_beds = models.PositiveIntegerField(
        default=0,
        help_text="Number of occupied ICU beds"
    )
    bed_capacity = models.PositiveIntegerField(
        default=0,
        help_text="Total bed capacity including regular and ICU beds"
    )
    current_patient_count = models.PositiveIntegerField(
        default=0,
        help_text="Current number of patients in the department"
    )
    
    # Staff Requirements
    minimum_staff_required = models.PositiveIntegerField(
        default=1,
        help_text="Minimum number of staff required for safe operation"
    )
    current_staff_count = models.PositiveIntegerField(
        default=0,
        help_text="Current number of active staff in the department"
    )
    recommended_staff_ratio = models.FloatField(
        default=1.0,
        help_text="Recommended staff to patient ratio"
    )
    
    # Budget and Resources
    annual_budget = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Annual budget allocation for the department"
    )
    budget_year = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Fiscal year for the budget"
    )
    budget_utilized = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Amount of budget utilized so far"
    )
    equipment_budget = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Budget allocated for equipment and maintenance"
    )
    staff_budget = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Budget allocated for staff salaries and benefits"
    )
    
    # Appointment Settings
    appointment_duration = models.PositiveIntegerField(
        default=30,
        help_text="Default appointment duration in minutes"
    )
    max_daily_appointments = models.PositiveIntegerField(
        default=50,
        help_text="Maximum number of appointments per day"
    )
    requires_referral = models.BooleanField(
        default=False,
        help_text="Whether this department requires referral for appointments"
    )
    
    # Use string reference to avoid circular import
    hospital = models.ForeignKey(
        'api.Hospital',
        on_delete=models.CASCADE,
        related_name='departments'
    )

    class Meta:
        ordering = ['name']
        unique_together = ['hospital', 'name']
        indexes = [
            # Primary lookup fields
            models.Index(fields=['code'], name='dept_code_idx'),  # For quick department code lookups
            models.Index(fields=['department_type'], name='dept_type_idx'),  # For filtering by department type
            
            # Operational status fields
            models.Index(fields=['is_active'], name='dept_active_idx'),  # For filtering active/inactive departments
            models.Index(fields=['is_24_hours'], name='dept_24hr_idx'),  # For filtering 24-hour departments
            
            # Location-based lookup
            models.Index(fields=['wing'], name='dept_wing_idx'),  # For location-based queries
            
            # Composite indexes for common query patterns
            models.Index(fields=['hospital', 'department_type'], name='dept_hosp_type_idx'),  # For filtering departments by type within a hospital
            models.Index(fields=['hospital', 'is_active'], name='dept_hosp_active_idx'),  # For filtering active departments within a hospital
            
            # Budget and capacity monitoring
            models.Index(fields=['current_patient_count'], name='dept_patient_count_idx'),  # For capacity monitoring
            models.Index(fields=['current_staff_count'], name='dept_staff_count_idx'),  # For staffing queries
        ]

    def __str__(self):
        return f"{self.name} - {self.hospital.name} ({self.get_department_type_display()})"

    def clean(self):
        """Validate department data"""
        super().clean()
        
        # Validate bed counts
        if self.occupied_beds > self.total_beds:
            raise ValidationError("Occupied beds cannot exceed total beds")
            
        if self.occupied_icu_beds > self.icu_beds:
            raise ValidationError("Occupied ICU beds cannot exceed total ICU beds")
            
        # Validate total capacity
        if self.current_patient_count > (self.total_beds + self.icu_beds):
            raise ValidationError("Current patient count cannot exceed total capacity")
            
        # Validate staff counts
        if self.current_staff_count < 0:
            raise ValidationError("Current staff count cannot be negative")
            
        if self.minimum_staff_required < 1:
            raise ValidationError("Minimum staff required must be at least 1")
            
        if self.current_staff_count < self.minimum_staff_required:
            raise ValidationError("Current staff count is below minimum required")
            
        # Validate budget
        if self.annual_budget and self.annual_budget < 0:
            raise ValidationError("Annual budget cannot be negative")
            
        if self.budget_utilized < 0:
            raise ValidationError("Budget utilized cannot be negative")
            
        if self.annual_budget and self.budget_utilized > self.annual_budget:
            raise ValidationError("Budget utilized cannot exceed annual budget")
            
        # Validate category budgets
        if self.equipment_budget and self.equipment_budget < 0:
            raise ValidationError("Equipment budget cannot be negative")
            
        if self.staff_budget and self.staff_budget < 0:
            raise ValidationError("Staff budget cannot be negative")
            
        # Validate total of category budgets doesn't exceed annual budget
        if self.annual_budget and self.equipment_budget and self.staff_budget:
            if (self.equipment_budget + self.staff_budget) > self.annual_budget:
                raise ValidationError("Sum of category budgets cannot exceed annual budget")
                
        # Validate operating hours
        if self.is_24_hours and self.operating_hours:
            for day, hours in self.operating_hours.items():
                if not isinstance(hours, dict) or 'start' not in hours or 'end' not in hours:
                    raise ValidationError(f"Invalid operating hours format for {day}")
                if hours['start'] != '00:00' or hours['end'] != '23:59':
                    raise ValidationError("24-hour departments must have full day operating hours")
        elif self.operating_hours:
            for day, hours in self.operating_hours.items():
                if not isinstance(hours, dict) or 'start' not in hours or 'end' not in hours:
                    raise ValidationError(f"Invalid operating hours format for {day}")
                try:
                    start = datetime.strptime(hours['start'], '%H:%M').time()
                    end = datetime.strptime(hours['end'], '%H:%M').time()
                    if start >= end:
                        raise ValidationError(f"End time must be after start time for {day}")
                except ValueError:
                    raise ValidationError(f"Invalid time format for {day}. Use HH:MM format")

    def save(self, *args, **kwargs):
        # Update total bed capacity
        self.bed_capacity = self.total_beds + self.icu_beds
        
        # Ensure 24-hour departments have correct operating hours
        if self.is_24_hours:
            self.operating_hours = {
                day: {'start': '00:00', 'end': '23:59'}
                for day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
            }
            
        self.clean()
        super().save(*args, **kwargs)

    @property
    def available_beds(self):
        """Get number of available regular beds"""
        return self.total_beds - self.occupied_beds

    @property
    def available_icu_beds(self):
        """Get number of available ICU beds"""
        return self.icu_beds - self.occupied_icu_beds

    @property
    def total_available_beds(self):
        """Get total number of available beds"""
        return self.available_beds + self.available_icu_beds

    @property
    def bed_utilization_rate(self):
        """Calculate bed utilization rate"""
        total_capacity = self.total_beds + self.icu_beds
        if total_capacity == 0:
            return 0
        total_occupied = self.occupied_beds + self.occupied_icu_beds
        return (total_occupied / total_capacity) * 100

    @property
    def utilization_rate(self):
        """Calculate department utilization rate"""
        if self.bed_capacity == 0:
            return 0
        return (self.current_patient_count / self.bed_capacity) * 100

    @property
    def is_clinical(self):
        """Check if department is a clinical department"""
        return self.department_type in ['medical', 'surgical', 'emergency', 'critical_care', 'outpatient']

    @property
    def is_support(self):
        """Check if department is a support department"""
        return self.department_type in ['laboratory', 'radiology', 'pharmacy', 'physiotherapy']

    @property
    def is_administrative(self):
        """Check if department is an administrative department"""
        return self.department_type in ['admin', 'records', 'it']

    @property
    def is_available_for_appointments(self):
        """Check if department can accept new appointments"""
        # Administrative departments don't accept appointments
        if self.is_administrative:
            return False
            
        # Get current day and time
        now = timezone.now()
        current_day = now.strftime('%A').lower()
        
        # Check operating hours
        if not self.operating_hours.get(current_day):
            return False
            
        # Check if within operating hours
        hours = self.operating_hours[current_day]
        current_time = now.strftime('%H:%M')
        return (hours['start'] <= current_time <= hours['end'] and 
                self.is_active)

    def get_available_slots(self, date):
        """Get available appointment slots for a given date"""
        # Administrative departments don't have appointment slots
        if self.is_administrative:
            return []
            
        from api.models import Appointment
        
        # Get operating hours for the day
        day_name = date.strftime('%A').lower()
        if not self.operating_hours.get(day_name):
            return []
            
        hours = self.operating_hours[day_name]
        
        # Calculate total slots
        start_time = timezone.datetime.strptime(hours['start'], '%H:%M').time()
        end_time = timezone.datetime.strptime(hours['end'], '%H:%M').time()
        
        # Generate all possible slots
        slots = []
        current_time = start_time
        while current_time < end_time:
            slot_datetime = timezone.datetime.combine(date, current_time)
            
            # Check if slot is already booked
            is_booked = Appointment.objects.filter(
                department=self,
                appointment_date=slot_datetime
            ).exists()
            
            if not is_booked:
                slots.append(slot_datetime)
                
            # Move to next slot
            current_time = (timezone.datetime.combine(date, current_time) + 
                          timezone.timedelta(minutes=self.appointment_duration)).time()
        
        return slots

    def get_staff_count(self):
        """Get total number of staff in department"""
        return self.doctors.filter(is_active=True).count()

    def is_adequately_staffed(self):
        """Check if department has minimum required staff"""
        return self.get_staff_count() >= self.minimum_staff_required

    # Resource Management Methods
    def assign_bed(self, is_icu=False):
        """Assign a bed to a patient"""
        if not self.is_clinical:
            raise ValidationError("Only clinical departments can assign beds")
            
        if is_icu:
            if self.occupied_icu_beds >= self.icu_beds:
                raise ValidationError("No ICU beds available")
            self.occupied_icu_beds += 1
        else:
            if self.occupied_beds >= self.total_beds:
                raise ValidationError("No regular beds available")
            self.occupied_beds += 1
        self.save()

    def release_bed(self, is_icu=False):
        """Release a bed"""
        if not self.is_clinical:
            raise ValidationError("Only clinical departments can release beds")
            
        if is_icu:
            if self.occupied_icu_beds > 0:
                self.occupied_icu_beds -= 1
        else:
            if self.occupied_beds > 0:
                self.occupied_beds -= 1
        self.save()

    def update_staff_count(self):
        """Update current staff count"""
        self.current_staff_count = self.get_all_staff().count()
        self.save()

    # Emergency Handling
    def declare_emergency(self, reason):
        """Declare department emergency (e.g., mass casualty)"""
        if not self.is_clinical:
            raise ValidationError("Only clinical departments can declare emergencies")
            
        from .department_emergency import DepartmentEmergency
        
        return DepartmentEmergency.objects.create(
            department=self,
            reason=reason,
            required_staff=self.minimum_staff_required * 2  # Double staff during emergency
        )

    @property
    def staff_utilization_rate(self):
        """Calculate staff utilization rate based on recommended ratio"""
        if self.current_patient_count == 0 or self.recommended_staff_ratio == 0:
            return 0
        recommended_staff = self.current_patient_count * self.recommended_staff_ratio
        return (self.current_staff_count / recommended_staff) * 100

    @property
    def is_understaffed(self):
        """Check if department is understaffed"""
        return self.current_staff_count < self.minimum_staff_required

    @property
    def budget_utilization_rate(self):
        """Calculate budget utilization rate"""
        if not self.annual_budget:
            return 0
        return (self.budget_utilized / self.annual_budget) * 100

    @property
    def remaining_budget(self):
        """Calculate remaining budget"""
        if not self.annual_budget:
            return 0
        return self.annual_budget - self.budget_utilized

    def update_budget_utilization(self, amount, category=None):
        """Update budget utilization"""
        if not self.annual_budget:
            raise ValidationError("No annual budget set for this department")
            
        if self.budget_utilized + amount > self.annual_budget:
            raise ValidationError("Budget utilization would exceed annual budget")
            
        self.budget_utilized += amount
        
        # Update category-specific budget if provided
        if category == 'equipment' and self.equipment_budget:
            if amount > self.equipment_budget:
                raise ValidationError("Amount exceeds equipment budget")
        elif category == 'staff' and self.staff_budget:
            if amount > self.staff_budget:
                raise ValidationError("Amount exceeds staff budget")
                
        self.save()