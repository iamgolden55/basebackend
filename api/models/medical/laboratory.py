from django.db import models
from django.utils import timezone
from ..base import TimestampedModel
from ..user.custom_user import CustomUser
from .medical_record import MedicalRecord


class LaboratoryTestType(TimestampedModel):
    """
    Model for defining different types of laboratory tests
    with reference ranges and other test metadata.
    """
    # Basic Information
    name = models.CharField(
        max_length=255,
        help_text="Name of the laboratory test"
    )
    code = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique code for the test (e.g., 'CBC', 'LIPID', etc.)"
    )
    category = models.CharField(
        max_length=100,
        help_text="Category of the test (e.g., 'Blood', 'Urine', 'Genetic')"
    )
    description = models.TextField(
        help_text="Detailed description of what the test measures"
    )
    
    # Test Metadata
    sample_type = models.CharField(
        max_length=100,
        help_text="Type of sample required (e.g., 'Blood', 'Urine', 'Tissue')"
    )
    processing_time = models.CharField(
        max_length=100,
        help_text="Typical time to process this test"
    )
    fasting_required = models.BooleanField(
        default=False,
        help_text="Whether patient needs to fast before test"
    )
    
    # Reference Ranges
    reference_ranges = models.JSONField(
        default=dict,
        help_text="Reference ranges by age, gender, etc. (JSON format)"
    )
    units = models.CharField(
        max_length=50,
        help_text="Units of measurement for test results"
    )
    
    # Medical Context
    clinical_uses = models.TextField(
        help_text="Common clinical scenarios where this test is ordered"
    )
    result_interpretation = models.TextField(
        help_text="Guidelines for interpreting results"
    )
    associated_conditions = models.TextField(
        blank=True,
        null=True,
        help_text="Medical conditions commonly associated with abnormal results"
    )
    
    # Administrative
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this test is currently available"
    )
    requires_approval = models.BooleanField(
        default=False,
        help_text="Whether test requires special approval"
    )
    
    class Meta:
        ordering = ['category', 'name']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['category']),
            models.Index(fields=['is_active']),
        ]
        
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    def get_reference_range_for_patient(self, age=None, gender=None):
        """
        Return appropriate reference range for a patient based on age and gender
        """
        if not self.reference_ranges:
            return None
            
        # Default range if available
        default_range = self.reference_ranges.get('default')
        
        # Try to get gender-specific range
        if gender and gender in self.reference_ranges:
            gender_range = self.reference_ranges.get(gender)
            
            # If age is provided, try to get age-specific range within gender
            if age and 'age_ranges' in gender_range:
                for age_range in gender_range['age_ranges']:
                    min_age = age_range.get('min_age', 0)
                    max_age = age_range.get('max_age', 200)
                    if min_age <= age <= max_age:
                        return age_range.get('range')
            
            # Return gender-specific default range if no age match
            if 'default' in gender_range:
                return gender_range['default']
                
        # If no gender-specific match, try general age ranges
        if age and 'age_ranges' in self.reference_ranges:
            for age_range in self.reference_ranges['age_ranges']:
                min_age = age_range.get('min_age', 0)
                max_age = age_range.get('max_age', 200)
                if min_age <= age <= max_age:
                    return age_range.get('range')
        
        # Fall back to default range
        return default_range


class LaboratoryResult(TimestampedModel):
    """
    Model for storing laboratory test results linked to a patient's medical record.
    """
    # Relationships
    medical_record = models.ForeignKey(
        MedicalRecord,
        on_delete=models.CASCADE,
        related_name='laboratory_results',
        help_text="Medical record this result belongs to"
    )
    test_type = models.ForeignKey(
        LaboratoryTestType,
        on_delete=models.PROTECT,
        related_name='results',
        help_text="Type of laboratory test"
    )
    ordered_by = models.ForeignKey(
        'api.Doctor',
        on_delete=models.SET_NULL,
        null=True,
        related_name='ordered_lab_tests',
        help_text="Doctor who ordered the test"
    )
    
    # Test Information
    test_date = models.DateTimeField(
        help_text="Date and time the test was performed"
    )
    result_date = models.DateTimeField(
        help_text="Date and time results were available"
    )
    result_value = models.CharField(
        max_length=255,
        help_text="Result value (may be numeric or descriptive)"
    )
    numeric_value = models.FloatField(
        null=True,
        blank=True,
        help_text="Numeric result value for trending (if applicable)"
    )
    units = models.CharField(
        max_length=50,
        help_text="Units of measurement"
    )
    
    # Reference Range
    reference_range_min = models.FloatField(
        null=True,
        blank=True,
        help_text="Lower limit of reference range"
    )
    reference_range_max = models.FloatField(
        null=True,
        blank=True,
        help_text="Upper limit of reference range"
    )
    reference_range_text = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Text description of reference range (for non-numeric results)"
    )
    
    # Result Status
    is_abnormal = models.BooleanField(
        default=False,
        help_text="Whether result is outside normal range"
    )
    abnormal_flags = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Flags for abnormal results (H=High, L=Low, C=Critical, etc.)"
    )
    
    # Processing Information
    specimen_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="ID of the specimen collected"
    )
    lab_facility = models.CharField(
        max_length=255,
        help_text="Name of lab facility that processed test"
    )
    processed_by = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Name of lab technician who processed the test"
    )
    
    # Clinical
    clinical_notes = models.TextField(
        blank=True,
        null=True,
        help_text="Additional clinical notes about the test"
    )
    follow_up_recommended = models.BooleanField(
        default=False,
        help_text="Whether follow-up is recommended"
    )
    follow_up_notes = models.TextField(
        blank=True,
        null=True,
        help_text="Notes about recommended follow-up"
    )
    
    class Meta:
        ordering = ['-test_date']
        indexes = [
            models.Index(fields=['medical_record', 'test_date']),
            models.Index(fields=['test_type']),
            models.Index(fields=['is_abnormal']),
        ]
        
    def __str__(self):
        return f"{self.test_type.name} for {self.medical_record.hpn} on {self.test_date.strftime('%Y-%m-%d')}"
    
    def save(self, *args, **kwargs):
        # Auto-calculate abnormal flag if numeric values are available
        if self.numeric_value is not None and self.reference_range_min is not None and self.reference_range_max is not None:
            if self.numeric_value < self.reference_range_min:
                self.is_abnormal = True
                self.abnormal_flags = 'L'  # Low
            elif self.numeric_value > self.reference_range_max:
                self.is_abnormal = True
                self.abnormal_flags = 'H'  # High
            else:
                self.is_abnormal = False
                self.abnormal_flags = None
        
        super().save(*args, **kwargs)
        
        # Update medical record complexity metrics
        self.medical_record.update_complexity_metrics()
    
    @property
    def result_status(self):
        """Return a descriptive status of the result"""
        if not self.is_abnormal:
            return "Normal"
        
        if self.abnormal_flags == 'L':
            return "Low"
        elif self.abnormal_flags == 'H':
            return "High"
        elif self.abnormal_flags == 'C':
            return "Critical"
        else:
            return "Abnormal"
    
    @property
    def is_critical(self):
        """Check if result is in critical range"""
        return self.abnormal_flags == 'C' 