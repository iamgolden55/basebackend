# api/models/medical/department.py

from django.db import models
from django.core.exceptions import ValidationError
from django.db import transaction
from datetime import datetime, time

class Department(models.Model):
    """
    Comprehensive model for hospital departments with resource and staff management
    """
    # Department Types and Categories
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

    # Basic Information
    hospital = models.ForeignKey(
        'Hospital',
        on_delete=models.CASCADE,
        related_name='departments'
    )
    name = models.CharField(max_length=100)
    department_type = models.CharField(
        max_length=50,
        choices=DEPARTMENT_TYPES
    )
    code = models.CharField(max_length=10, unique=True)
    
    # Department Leadership
    head_doctor = models.ForeignKey(
        'api.Doctor',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='headed_department'
    )
    assistant_head = models.ForeignKey(
        'api.Doctor',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assistant_headed_department'
    )
    
    # Contact and Location
    floor_number = models.CharField(max_length=10)
    wing = models.CharField(max_length=50)
    extension_number = models.CharField(max_length=10)
    emergency_contact = models.CharField(max_length=20)
    email = models.EmailField()
    
    # Operational Details
    is_active = models.BooleanField(default=True)
    is_24_hours = models.BooleanField(default=False)
    operating_hours_start = models.TimeField(null=True, blank=True)
    operating_hours_end = models.TimeField(null=True, blank=True)
    weekend_operating_hours_start = models.TimeField(null=True, blank=True)
    weekend_operating_hours_end = models.TimeField(null=True, blank=True)
    
    # Capacity Management
    total_beds = models.PositiveIntegerField(default=0)
    occupied_beds = models.PositiveIntegerField(default=0)
    icu_beds = models.PositiveIntegerField(default=0)
    occupied_icu_beds = models.PositiveIntegerField(default=0)
    
    # Staff Requirements
    minimum_staff_required = models.PositiveIntegerField(default=1)
    current_staff_count = models.PositiveIntegerField(default=0)
    
    # Budget and Resources
    annual_budget = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )
    equipment_count = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ['hospital', 'name']
        ordering = ['name']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['department_type']),
        ]

    def __str__(self):
        return f"{self.name} - {self.hospital.name}"

    def clean(self):
        """Validate department data"""
        if not self.is_24_hours:
            if not all([self.operating_hours_start, self.operating_hours_end]):
                raise ValidationError("Operating hours required for non-24-hour departments")

        if self.occupied_beds > self.total_beds:
            raise ValidationError("Occupied beds cannot exceed total beds")

        if self.occupied_icu_beds > self.icu_beds:
            raise ValidationError("Occupied ICU beds cannot exceed total ICU beds")

    @property
    def bed_availability(self):
        """Get current bed availability"""
        return {
            'regular_beds': {
                'total': self.total_beds,
                'occupied': self.occupied_beds,
                'available': self.total_beds - self.occupied_beds,
                'occupancy_rate': (self.occupied_beds / self.total_beds * 100 
                                 if self.total_beds > 0 else 0)
            },
            'icu_beds': {
                'total': self.icu_beds,
                'occupied': self.occupied_icu_beds,
                'available': self.icu_beds - self.occupied_icu_beds,
                'occupancy_rate': (self.occupied_icu_beds / self.icu_beds * 100 
                                 if self.icu_beds > 0 else 0)
            }
        }

    @property
    def is_currently_open(self):
        """Check if department is currently open"""
        if self.is_24_hours:
            return True
            
        current_time = datetime.now().time()
        current_day = datetime.now().strftime('%A')
        
        if current_day in ['Saturday', 'Sunday']:
            if not all([self.weekend_operating_hours_start, 
                       self.weekend_operating_hours_end]):
                return False
            return (self.weekend_operating_hours_start <= current_time <= 
                   self.weekend_operating_hours_end)
        
        return (self.operating_hours_start <= current_time <= 
                self.operating_hours_end)

    # Staff Management Methods
    def get_all_staff(self):
        """Get all staff assigned to department"""
        return self.hospital.get_staff_by_department(self.code)

    def get_available_staff(self):
        """Get currently available staff"""
        return self.get_all_staff().filter(
            doctor_profile__available_for_appointments=True,
            doctor_profile__status='active'
        )

    def is_adequately_staffed(self):
        """Check if department has minimum required staff"""
        return self.get_available_staff().count() >= self.minimum_staff_required

    # Resource Management Methods
    def assign_bed(self, is_icu=False):
        """Assign a bed to a patient"""
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
        from .department_emergency import DepartmentEmergency
        
        return DepartmentEmergency.objects.create(
            department=self,
            reason=reason,
            required_staff=self.minimum_staff_required * 2  # Double staff during emergency
        )