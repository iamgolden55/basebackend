# api/models/medical/hospital.py

from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError
from django.db import transaction
from django.contrib.auth import get_user_model
from datetime import date
from .staff_transfer import StaffTransfer
from .department import Department
import uuid

class Hospital(models.Model):
    """
    Hospital model representing medical institutions with staff management capabilities.
    This model serves as the central point for managing medical staff and practices.
    """
    # Basic Information
    name = models.CharField(max_length=200)
    address = models.TextField()
    phone = models.CharField(max_length=20, blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    
    # Registration and Verification
    registration_number = models.CharField(
        max_length=50,
        unique=True,
        null=True,  # Allow null temporarily during migration
        blank=True,
        help_text="Hospital registration number"
    )
    is_verified = models.BooleanField(default=False)
    verification_date = models.DateField(null=True, blank=True)
    
    # Hospital Type and Classification
    HOSPITAL_TYPES = [
        ('public', 'Public Hospital'),
        ('private', 'Private Hospital'),
        ('specialist', 'Specialist Hospital'),
        ('teaching', 'Teaching Hospital'),
        ('clinic', 'Clinic'),
        ('research', 'Research Institution')
    ]
    hospital_type = models.CharField(
        max_length=20,
        choices=HOSPITAL_TYPES,
        default='public'
    )
    
    # Operational Information
    bed_capacity = models.PositiveIntegerField(default=0)
    emergency_unit = models.BooleanField(default=True)
    icu_unit = models.BooleanField(default=False)
    
    # Contact Information
    emergency_contact = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(
        null=True,
        blank=True,
        help_text="Hospital contact email"
    )
    
    # Accreditation and Certification
    accreditation_status = models.BooleanField(default=False)
    accreditation_expiry = models.DateField(null=True, blank=True)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='hospitals',
        null=True,  # Allow null temporarily during migration
        blank=True
    )

    class Meta:
        indexes = [
            models.Index(fields=['registration_number']),
            models.Index(fields=['hospital_type']),
            models.Index(fields=['is_verified']),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_hospital_type_display()})"

    @transaction.atomic
    def add_staff_member(self, user, role, **staff_details):
        """
        Add a new staff member to the hospital.
        This method handles the entire process of converting a user to a staff member.
        """
        if not user.is_verified:
            raise ValidationError("User must be verified before being added as staff")

        # Validate required credentials based on role
        self._validate_staff_credentials(role, staff_details)
        
        # Update user's role and hospital affiliation
        user.role = role
        user.primary_hospital = self
        user.save()

        # Create specific role profile (e.g., Doctor, Nurse, etc.)
        profile = self._create_staff_profile(user, role, **staff_details)
        
        return profile

    def _validate_staff_credentials(self, role, credentials):
        """
        Validate required credentials for different staff roles.
        """
        required_fields = {
            'doctor': ['medical_license_number', 'specialization'],
            'nurse': ['nursing_license_number'],
            'pharmacist': ['pharmacy_license_number'],
            'lab_technician': ['lab_certification_number']
        }

        if role in required_fields:
            missing = [field for field in required_fields[role] 
                      if field not in credentials]
            if missing:
                raise ValidationError(
                    f"Missing required credentials for {role}: {', '.join(missing)}"
                )

    def _create_staff_profile(self, user, role, **details):
        """
        Create the appropriate staff profile based on role.
        """
        from ..medical_staff.doctor import Doctor  # Import here to avoid circular imports
        
        if role == 'doctor':
            return Doctor.objects.create(
                user=user,
                hospital=self,
                **details
            )
        # Add similar blocks for other staff types
        
        return None

    def get_staff_by_role(self, role):
        """
        Get all staff members of a specific role.
        """
        return get_user_model().objects.filter(
            primary_hospital=self,
            role=role
        )

    def get_all_staff(self):
        """
        Get all staff members in the hospital.
        """
        return get_user_model().objects.filter(primary_hospital=self)
    
    def create_department(self, name, code, **department_details):
        """
        Create a new department in the hospital
        """
        return Department.objects.create(
            hospital=self,
            name=name,
            code=code,
            **department_details
        )

    def initiate_staff_transfer(self, staff_member, to_hospital, 
                              from_department, to_department, reason):
        """
        Initiate a staff transfer to another hospital
        """
        if staff_member.primary_hospital != self:
            raise ValueError("Staff member must belong to the initiating hospital")
            
        return StaffTransfer.objects.create(
            staff_member=staff_member,
            from_hospital=self,
            to_hospital=to_hospital,
            from_department=from_department,
            to_department=to_department,
            reason=reason,
            requested_by=self.administrator
        )

    def get_department_staff(self, department_code):
        """
        Get all staff members in a specific department
        """
        department = self.departments.get(code=department_code)
        return get_user_model().objects.filter(
            primary_hospital=self,
            doctor_profile__department=department
        )

    def get_department_stats(self, department_code):
        """
        Get statistics for a specific department
        """
        department = self.departments.get(code=department_code)
        return {
            'total_staff': self.get_department_staff(department_code).count(),
            'bed_capacity': department.bed_capacity,
            'current_patients': department.current_patient_count,
            'utilization_rate': (department.current_patient_count / 
                               department.bed_capacity * 100 
                               if department.bed_capacity > 0 else 0)
        }

    def handle_staff_emergency(self, department_code):
        """
        Handle staff shortages or emergencies in a department
        """
        department = self.departments.get(code=department_code)
        available_staff = self.get_department_staff(department_code).filter(
            doctor_profile__status='active',
            doctor_profile__available_for_appointments=True
        )
        
        if available_staff.count() < department.minimum_staff_required:
            # Find staff from other departments who can help
            qualified_staff = get_user_model().objects.filter(
                primary_hospital=self,
                doctor_profile__department__isnull=False,
                doctor_profile__status='active'
            ).exclude(doctor_profile__department=department)
            
            return qualified_staff

    def verify_staff_credentials(self):
        """
        Verify credentials of all staff members.
        Returns list of staff members with expired or soon-to-expire credentials.
        """
        warnings = []
        
        # Check doctors' licenses
        for doctor in self.doctors.all():
            if doctor.is_license_valid:
                if doctor.days_until_license_expires < 30:
                    warnings.append({
                        'staff': doctor,
                        'warning': f"License expires in {doctor.days_until_license_expires} days"
                    })
            else:
                warnings.append({
                    'staff': doctor,
                    'warning': "License expired"
                })
                
        return warnings

    @property
    def staff_count(self):
        """Get total number of staff members."""
        return self.get_all_staff().count()

    @property
    def is_accreditation_valid(self):
        """Check if hospital's accreditation is current."""
        return self.accreditation_expiry > date.today() if self.accreditation_expiry else False
    
    def save(self, *args, **kwargs):
        if not self.registration_number:
            # Generate a unique registration number if not provided
            self.registration_number = f"H-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

#===================================== GP PRACTICE REGION ===============================================================    

class GPPractice(models.Model):
    name = models.CharField(max_length=200)
    address = models.TextField()
    hospital = models.ForeignKey(
        Hospital,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='gp_practices'
    )

    def __str__(self):
        return self.name