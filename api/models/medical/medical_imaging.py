# api/models/medical/medical_imaging.py

from django.db import models
from django.utils import timezone
from django.core.validators import FileExtensionValidator
from ..base import TimestampedModel
from .medical_record import MedicalRecord


class ImagingType(TimestampedModel):
    """
    Reference model defining different types of medical imaging
    """
    # Basic Information
    name = models.CharField(
        max_length=255,
        help_text="Name of imaging type (e.g., 'X-Ray', 'MRI')"
    )
    code = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique code for imaging type"
    )
    
    # Description
    description = models.TextField(
        help_text="Description of this imaging type"
    )
    preparation_instructions = models.TextField(
        blank=True,
        null=True,
        help_text="Patient preparation instructions"
    )
    
    # Technical Details
    uses_radiation = models.BooleanField(
        default=False,
        help_text="Whether this imaging type uses ionizing radiation"
    )
    uses_contrast = models.BooleanField(
        default=False,
        help_text="Whether this imaging type typically uses contrast"
    )
    typical_duration = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Typical duration of procedure"
    )
    
    # Additional Information
    contraindications = models.TextField(
        blank=True,
        null=True,
        help_text="Contraindications for this imaging type"
    )
    risks = models.TextField(
        blank=True,
        null=True,
        help_text="Risks associated with this imaging type"
    )
    
    class Meta:
        verbose_name = "Imaging Type"
        verbose_name_plural = "Imaging Types"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class MedicalImage(TimestampedModel):
    """
    Model for storing medical imaging records and associated metadata
    """
    # Relationships
    medical_record = models.ForeignKey(
        MedicalRecord,
        on_delete=models.CASCADE,
        related_name='medical_images',
        help_text="Medical record this image belongs to"
    )
    imaging_type = models.ForeignKey(
        ImagingType,
        on_delete=models.PROTECT,
        related_name='images',
        help_text="Type of medical image"
    )
    ordered_by = models.ForeignKey(
        'api.Doctor',
        on_delete=models.SET_NULL,
        null=True,
        related_name='ordered_images',
        help_text="Doctor who ordered the imaging"
    )
    
    # Study Information
    study_date = models.DateTimeField(
        help_text="Date and time when imaging was performed"
    )
    accession_number = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Medical facility's accession number"
    )
    study_uid = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="DICOM Study Instance UID if available"
    )
    
    # Body Information
    BODY_REGION_CHOICES = [
        ('head', 'Head'),
        ('neck', 'Neck'),
        ('chest', 'Chest/Thorax'),
        ('abdomen', 'Abdomen'),
        ('pelvis', 'Pelvis'),
        ('spine', 'Spine'),
        ('upper_extremity', 'Upper Extremity'),
        ('lower_extremity', 'Lower Extremity'),
        ('whole_body', 'Whole Body'),
        ('other', 'Other')
    ]
    
    body_region = models.CharField(
        max_length=20,
        choices=BODY_REGION_CHOICES,
        help_text="Body region imaged"
    )
    body_part_detail = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Specific body part detail (e.g., 'Left Knee')"
    )
    laterality = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        choices=[
            ('left', 'Left'),
            ('right', 'Right'),
            ('bilateral', 'Bilateral'),
            ('not_applicable', 'Not Applicable')
        ],
        help_text="Laterality of body part if applicable"
    )
    
    # Facility Information
    facility = models.CharField(
        max_length=255,
        help_text="Facility where imaging was performed"
    )
    
    # Procedure Details
    with_contrast = models.BooleanField(
        default=False,
        help_text="Whether contrast was used"
    )
    contrast_type = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Type of contrast used if applicable"
    )
    procedure_notes = models.TextField(
        blank=True,
        null=True,
        help_text="Notes about the procedure"
    )
    
    # Clinical Information
    clinical_indication = models.TextField(
        help_text="Clinical reason for the imaging"
    )
    findings = models.TextField(
        blank=True,
        null=True,
        help_text="Findings from the imaging"
    )
    impression = models.TextField(
        blank=True,
        null=True,
        help_text="Radiologist's impression"
    )
    
    # Results
    RESULT_CHOICES = [
        ('normal', 'Normal'),
        ('abnormal', 'Abnormal'),
        ('critical', 'Critical Abnormality'),
        ('inconclusive', 'Inconclusive'),
        ('pending', 'Pending Interpretation')
    ]
    
    result = models.CharField(
        max_length=20,
        choices=RESULT_CHOICES,
        default='pending',
        help_text="Overall result of imaging"
    )
    
    structured_findings = models.JSONField(
        default=dict,
        blank=True,
        null=True,
        help_text="Structured findings in JSON format"
    )
    
    # Interpretation
    interpreted_by = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Name of radiologist who interpreted the image"
    )
    interpretation_date = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Date and time of interpretation"
    )
    
    # Image Storage
    image_file = models.FileField(
        upload_to='medical_images/%Y/%m/%d/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'dcm', 'dicom'])],
        help_text="Actual image file if stored directly"
    )
    pacs_link = models.URLField(
        blank=True,
        null=True,
        help_text="Link to image in PACS system"
    )
    series_count = models.IntegerField(
        default=1,
        help_text="Number of series in this study"
    )
    image_count = models.IntegerField(
        default=1,
        help_text="Total number of images in this study"
    )
    
    # Follow-up
    requires_followup = models.BooleanField(
        default=False,
        help_text="Whether follow-up imaging is recommended"
    )
    followup_notes = models.TextField(
        blank=True,
        null=True,
        help_text="Notes about recommended follow-up"
    )
    followup_date = models.DateField(
        blank=True,
        null=True,
        help_text="Recommended date for follow-up imaging"
    )
    
    # AI Analysis
    ai_analyzed = models.BooleanField(
        default=False,
        help_text="Whether image has been analyzed by AI"
    )
    ai_findings = models.JSONField(
        default=dict,
        blank=True,
        null=True,
        help_text="AI analysis results in JSON format"
    )
    ai_confidence = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="AI confidence score (0-1)"
    )
    
    class Meta:
        verbose_name = "Medical Image"
        verbose_name_plural = "Medical Images"
        ordering = ['-study_date']
        indexes = [
            models.Index(fields=['medical_record', 'study_date']),
            models.Index(fields=['imaging_type']),
            models.Index(fields=['body_region']),
            models.Index(fields=['result']),
        ]
    
    def __str__(self):
        return f"{self.imaging_type.name} of {self.get_body_region_display()} for {self.medical_record.hpn} on {self.study_date.strftime('%Y-%m-%d')}"
    
    def save(self, *args, **kwargs):
        # If interpretation date is set but result is still pending, update result
        if self.interpretation_date and self.result == 'pending':
            self.result = 'abnormal'  # Default to abnormal if interpreted but not explicitly set
            
        super().save(*args, **kwargs)
        
        # Update medical record complexity metrics
        if hasattr(self.medical_record, 'update_complexity_metrics') and self.result in ['abnormal', 'critical']:
            self.medical_record.update_complexity_metrics()
    
    @property
    def is_critical(self):
        """Check if image has critical findings"""
        return self.result == 'critical'
    
    @property
    def is_interpreted(self):
        """Check if image has been interpreted"""
        return self.interpretation_date is not None
    
    @property
    def age_of_study(self):
        """Calculate age of imaging study"""
        if not self.study_date:
            return None
            
        now = timezone.now()
        delta = now - self.study_date
        return delta.days
        
    @property
    def is_recent(self):
        """Check if study is recent (less than 30 days old)"""
        age = self.age_of_study
        if age is None:
            return False
        return age < 30
    
    def get_summary(self):
        """Return a summary of the imaging study"""
        return {
            'type': self.imaging_type.name,
            'date': self.study_date,
            'body_region': self.get_body_region_display(),
            'result': self.get_result_display(),
            'findings': self.findings[:150] + '...' if self.findings and len(self.findings) > 150 else self.findings,
            'facility': self.facility,
            'requires_followup': self.requires_followup
        }
        
    def mark_as_interpreted(self, interpreter_name, result, findings, impression=None):
        """
        Mark image as interpreted
        
        Args:
            interpreter_name: Name of interpreting radiologist
            result: One of RESULT_CHOICES
            findings: Text findings
            impression: Optional impressions
            
        Returns:
            True if successful
        """
        self.interpreted_by = interpreter_name
        self.interpretation_date = timezone.now()
        self.result = result
        self.findings = findings
        
        if impression:
            self.impression = impression
            
        self.save()
        return True 