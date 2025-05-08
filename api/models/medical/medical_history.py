from django.db import models
from django.utils import timezone
from ..base import TimestampedModel
from .medical_record import MedicalRecord


class FamilyMedicalHistory(TimestampedModel):
    """
    Model for storing family medical history information
    linked to a patient's medical record
    """
    # Relationship
    medical_record = models.ForeignKey(
        MedicalRecord,
        on_delete=models.CASCADE,
        related_name='family_medical_history',
        help_text="Medical record this family history belongs to"
    )
    
    # Relationship to Patient
    RELATION_CHOICES = [
        ('parent', 'Parent'),
        ('sibling', 'Sibling'),
        ('child', 'Child'),
        ('grandparent', 'Grandparent'),
        ('aunt_uncle', 'Aunt/Uncle'),
        ('cousin', 'Cousin'),
        ('other', 'Other')
    ]
    
    relation_type = models.CharField(
        max_length=20,
        choices=RELATION_CHOICES,
        help_text="Relationship to the patient"
    )
    relation_detail = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Additional details about relationship (e.g., 'Maternal Grandmother')"
    )
    
    # Medical Condition
    condition = models.CharField(
        max_length=255,
        help_text="Medical condition or disease"
    )
    condition_code = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="ICD-10 code if available"
    )
    
    # Condition Details
    age_at_onset = models.IntegerField(
        blank=True,
        null=True,
        help_text="Age when condition was diagnosed"
    )
    
    STATUS_CHOICES = [
        ('active', 'Active/Current'),
        ('managed', 'Managed/Controlled'),
        ('resolved', 'Resolved/Cured'),
        ('terminal', 'Terminal'),
        ('deceased', 'Deceased due to condition'),
        ('unknown', 'Unknown')
    ]
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='unknown',
        help_text="Current status of the condition"
    )
    
    severity = models.IntegerField(
        blank=True,
        null=True,
        help_text="Severity scale from 1-5, where 5 is most severe"
    )
    
    # Additional Information
    is_genetic = models.BooleanField(
        default=False,
        help_text="Whether condition has known genetic component"
    )
    is_hereditary = models.BooleanField(
        default=False,
        help_text="Whether condition is considered hereditary"
    )
    risk_factor = models.BooleanField(
        default=True,
        help_text="Whether this is a risk factor for patient"
    )
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Additional notes about family history"
    )
    
    # Metadata
    reported_by = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Who provided this information"
    )
    reported_date = models.DateField(
        default=timezone.now,
        help_text="When this information was reported"
    )
    verified = models.BooleanField(
        default=False,
        help_text="Whether this information has been verified"
    )
    
    class Meta:
        verbose_name = "Family Medical History"
        verbose_name_plural = "Family Medical Histories"
        ordering = ['relation_type', 'condition']
        indexes = [
            models.Index(fields=['medical_record', 'condition']),
            models.Index(fields=['relation_type']),
            models.Index(fields=['is_genetic']),
            models.Index(fields=['risk_factor']),
        ]
    
    def __str__(self):
        return f"{self.condition} - {self.get_relation_type_display()} of {self.medical_record.hpn}"
    
    @property
    def is_first_degree_relative(self):
        """Check if this is a first-degree relative (parent, sibling, child)"""
        return self.relation_type in ['parent', 'sibling', 'child']
    
    @property
    def hereditary_risk_level(self):
        """
        Calculate hereditary risk level based on relation type,
        genetic status, and whether it's a first degree relative
        
        Returns a value from 0-5, where 5 is highest risk
        """
        risk = 0
        
        # Base risk from relation type
        if self.relation_type == 'parent' or self.relation_type == 'sibling':
            risk += 3
        elif self.relation_type == 'child':
            risk += 3
        elif self.relation_type == 'grandparent' or self.relation_type == 'aunt_uncle':
            risk += 2
        else:
            risk += 1
            
        # Adjust for genetic/hereditary status
        if self.is_genetic:
            risk += 1
        if self.is_hereditary:
            risk += 1
            
        # Cap at 5
        return min(5, risk)
        
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        # Update medical record complexity metrics
        self.medical_record.update_complexity_metrics()


class SurgicalHistory(TimestampedModel):
    """
    Model for storing patient's surgical history
    """
    # Relationship
    medical_record = models.ForeignKey(
        MedicalRecord,
        on_delete=models.CASCADE,
        related_name='surgical_history',
        help_text="Medical record this surgical history belongs to"
    )
    
    # Procedure Information
    procedure_name = models.CharField(
        max_length=255,
        help_text="Name of surgical procedure"
    )
    procedure_code = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Procedure code (e.g., CPT code)"
    )
    procedure_date = models.DateField(
        help_text="Date of the procedure"
    )
    
    # Facility and Provider
    facility = models.CharField(
        max_length=255,
        blank=True,
        null=True, 
        help_text="Medical facility where procedure was performed"
    )
    surgeon = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Name of surgeon who performed the procedure"
    )
    surgeon_specialty = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Specialty of the surgeon"
    )
    
    # Categorization
    CATEGORY_CHOICES = [
        ('elective', 'Elective'),
        ('urgent', 'Urgent'),
        ('emergency', 'Emergency'),
        ('diagnostic', 'Diagnostic')
    ]
    
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='elective',
        help_text="Category of surgical procedure"
    )
    
    body_area = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Area of the body involved"
    )
    
    # Outcome and Recovery
    OUTCOME_CHOICES = [
        ('successful', 'Successful'),
        ('complications', 'Completed with Complications'),
        ('aborted', 'Aborted'),
        ('converted', 'Converted to Different Procedure'),
        ('unknown', 'Outcome Unknown')
    ]
    
    outcome = models.CharField(
        max_length=20,
        choices=OUTCOME_CHOICES,
        default='successful',
        help_text="Outcome of the procedure"
    )
    
    complications = models.TextField(
        blank=True,
        null=True,
        help_text="Description of any complications"
    )
    
    length_of_stay = models.IntegerField(
        blank=True,
        null=True,
        help_text="Length of hospital stay in days"
    )
    
    recovery_notes = models.TextField(
        blank=True,
        null=True,
        help_text="Notes on recovery process"
    )
    
    # Additional Information
    anesthesia_type = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Type of anesthesia used"
    )
    
    implant_device = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Implant or device information if applicable"
    )
    
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Additional notes about the procedure"
    )
    
    # Follow-up
    follow_up_needed = models.BooleanField(
        default=True,
        help_text="Whether follow-up care is needed"
    )
    
    follow_up_date = models.DateField(
        blank=True,
        null=True,
        help_text="Scheduled follow-up date"
    )
    
    class Meta:
        verbose_name = "Surgical History"
        verbose_name_plural = "Surgical Histories"
        ordering = ['-procedure_date']
        indexes = [
            models.Index(fields=['medical_record', 'procedure_date']),
            models.Index(fields=['procedure_name']),
            models.Index(fields=['category']),
            models.Index(fields=['outcome']),
        ]
    
    def __str__(self):
        return f"{self.procedure_name} for {self.medical_record.hpn} on {self.procedure_date}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        # Update medical record complexity metrics
        self.medical_record.update_complexity_metrics()


class Immunization(TimestampedModel):
    """
    Model for tracking patient immunization records
    """
    # Relationship
    medical_record = models.ForeignKey(
        MedicalRecord,
        on_delete=models.CASCADE,
        related_name='immunizations',
        help_text="Medical record this immunization belongs to"
    )
    
    # Vaccine Information
    vaccine_name = models.CharField(
        max_length=255,
        help_text="Name of vaccine"
    )
    vaccine_code = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Vaccine code (e.g., CVX code)"
    )
    
    # Administration Details
    administration_date = models.DateField(
        help_text="Date vaccine was administered"
    )
    administered_by = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Name of provider who administered vaccine"
    )
    facility = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Facility where vaccine was administered"
    )
    
    # Vaccine Metadata
    dose_number = models.IntegerField(
        default=1,
        help_text="Dose number in series"
    )
    series_complete = models.BooleanField(
        default=False,
        help_text="Whether series is complete"
    )
    route = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Route of administration (e.g., IM, SC, oral)"
    )
    site = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Site of administration (e.g., left arm, right thigh)"
    )
    lot_number = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Vaccine lot number"
    )
    expiration_date = models.DateField(
        blank=True,
        null=True,
        help_text="Vaccine expiration date"
    )
    manufacturer = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Vaccine manufacturer"
    )
    
    # Follow-up
    next_dose_due = models.DateField(
        blank=True,
        null=True,
        help_text="Date next dose is due"
    )
    
    # Outcome
    reaction = models.TextField(
        blank=True,
        null=True,
        help_text="Any reactions to the vaccine"
    )
    
    # Additional Information
    reason_given = models.TextField(
        blank=True,
        null=True,
        help_text="Reason for administering vaccine"
    )
    contraindications_reviewed = models.BooleanField(
        default=True,
        help_text="Whether contraindications were reviewed"
    )
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Additional notes"
    )
    
    class Meta:
        verbose_name = "Immunization"
        verbose_name_plural = "Immunizations"
        ordering = ['-administration_date', 'vaccine_name']
        indexes = [
            models.Index(fields=['medical_record', 'vaccine_name']),
            models.Index(fields=['administration_date']),
            models.Index(fields=['series_complete']),
        ]
    
    def __str__(self):
        return f"{self.vaccine_name} for {self.medical_record.hpn} on {self.administration_date}"
    
    @property
    def is_overdue(self):
        """Check if next dose is overdue"""
        if not self.next_dose_due:
            return False
        
        return self.next_dose_due < timezone.now().date() and not self.series_complete


class GeneticInformation(TimestampedModel):
    """
    Model for storing patient genetic information and test results
    """
    # Relationship
    medical_record = models.ForeignKey(
        MedicalRecord,
        on_delete=models.CASCADE,
        related_name='genetic_information',
        help_text="Medical record this genetic information belongs to"
    )
    
    # Test Information
    test_name = models.CharField(
        max_length=255,
        help_text="Name of genetic test"
    )
    test_code = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Test code if applicable"
    )
    test_date = models.DateField(
        help_text="Date test was performed"
    )
    lab_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Laboratory that performed test"
    )
    
    # Results
    TEST_TYPE_CHOICES = [
        ('carrier', 'Carrier Screening'),
        ('diagnostic', 'Diagnostic Testing'),
        ('predictive', 'Predictive Testing'),
        ('pharmacogenomic', 'Pharmacogenomic Testing'),
        ('research', 'Research Testing'),
        ('other', 'Other')
    ]
    
    test_type = models.CharField(
        max_length=20,
        choices=TEST_TYPE_CHOICES,
        help_text="Type of genetic test"
    )
    
    gene_variant = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Specific gene or variant tested"
    )
    
    RESULT_CHOICES = [
        ('positive', 'Positive'),
        ('negative', 'Negative'),
        ('uncertain', 'Variant of Uncertain Significance'),
        ('inconclusive', 'Inconclusive'),
        ('pending', 'Pending')
    ]
    
    result = models.CharField(
        max_length=20,
        choices=RESULT_CHOICES,
        help_text="Test result"
    )
    
    # Clinical Significance
    clinical_significance = models.TextField(
        blank=True,
        null=True,
        help_text="Clinical significance of the result"
    )
    
    health_implications = models.TextField(
        blank=True,
        null=True,
        help_text="Health implications of the result"
    )
    
    risk_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Risk percentage if applicable"
    )
    
    # Counseling
    counseling_provided = models.BooleanField(
        default=False,
        help_text="Whether genetic counseling was provided"
    )
    
    counselor_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Name of genetic counselor"
    )
    
    counseling_date = models.DateField(
        blank=True,
        null=True,
        help_text="Date counseling was provided"
    )
    
    counseling_notes = models.TextField(
        blank=True,
        null=True,
        help_text="Notes from genetic counseling"
    )
    
    # Additional Information
    family_history_relevant = models.BooleanField(
        default=False,
        help_text="Whether family history is relevant to results"
    )
    
    recommendations = models.TextField(
        blank=True,
        null=True,
        help_text="Recommendations based on test results"
    )
    
    follow_up_testing = models.TextField(
        blank=True,
        null=True,
        help_text="Recommended follow-up testing"
    )
    
    documentation = models.FileField(
        upload_to='genetic_tests/',
        blank=True,
        null=True,
        help_text="Related documentation or full test results"
    )
    
    class Meta:
        verbose_name = "Genetic Information"
        verbose_name_plural = "Genetic Information"
        ordering = ['-test_date']
        indexes = [
            models.Index(fields=['medical_record', 'test_type']),
            models.Index(fields=['test_date']),
            models.Index(fields=['result']),
            models.Index(fields=['gene_variant']),
        ]
    
    def __str__(self):
        return f"{self.test_name} for {self.medical_record.hpn} on {self.test_date}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        # Update medical record complexity metrics if positive genetic result
        if self.result == 'positive':
            self.medical_record.update_complexity_metrics() 