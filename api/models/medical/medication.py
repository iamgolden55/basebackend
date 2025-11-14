# api/models/medical/medication.py

from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from ..base import TimestampedModel
from .medical_record import MedicalRecord


class MedicationCatalog(TimestampedModel):
    """
    Reference model for medications with detailed information
    that can be linked to patient prescriptions
    """
    # Basic Information
    generic_name = models.CharField(
        max_length=255,
        help_text="Generic name of the medication"
    )
    brand_names = models.JSONField(
        default=list,
        help_text="List of brand names for this medication"
    )
    drug_code = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Standard drug code (e.g., NDC or RxNorm)"
    )
    
    # Classification
    drug_class = models.CharField(
        max_length=100,
        help_text="Therapeutic class of medication"
    )
    atc_code = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        help_text="WHO Anatomical Therapeutic Chemical code"
    )
    
    # Pharmaceutical Information
    available_forms = models.JSONField(
        default=list,
        help_text="List of available forms (tablet, capsule, etc.)"
    )
    available_strengths = models.JSONField(
        default=list,
        help_text="List of available strengths with units"
    )
    standard_routes = models.JSONField(
        default=list,
        help_text="List of standard routes of administration"
    )
    
    # Clinical Information
    indications = models.TextField(
        help_text="Common uses and indications"
    )
    contraindications = models.TextField(
        help_text="Conditions when medication should not be used"
    )
    side_effects = models.TextField(
        help_text="Common side effects"
    )
    serious_side_effects = models.TextField(
        help_text="Serious or life-threatening side effects"
    )
    warnings = models.TextField(
        help_text="Special warnings and precautions"
    )
    
    # Interaction Information
    drug_interactions = models.JSONField(
        default=list,
        help_text="List of interacting drugs and effects"
    )
    food_interactions = models.TextField(
        blank=True,
        null=True,
        help_text="Food-drug interactions"
    )
    
    # Dosing Information
    dosing_information = models.JSONField(
        default=dict,
        help_text="Structured dosing guidelines by condition, age, etc."
    )
    max_daily_dose = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Maximum daily dose"
    )
    
    # Pharmacology
    mechanism_of_action = models.TextField(
        blank=True,
        null=True,
        help_text="How the medication works in the body"
    )
    half_life = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Half-life of medication"
    )
    
    # Special Populations
    pregnancy_category = models.CharField(
        max_length=5,
        blank=True,
        null=True,
        help_text="FDA pregnancy category (A, B, C, D, X)"
    )
    pediatric_use = models.TextField(
        blank=True,
        null=True,
        help_text="Information for pediatric use"
    )
    geriatric_use = models.TextField(
        blank=True,
        null=True,
        help_text="Information for geriatric use"
    )
    
    # Monitoring
    monitoring_required = models.BooleanField(
        default=False,
        help_text="Whether medication requires special monitoring"
    )
    monitoring_parameters = models.TextField(
        blank=True,
        null=True,
        help_text="What to monitor during therapy"
    )
    
    # AI-Specific Fields
    high_alert_medication = models.BooleanField(
        default=False,
        help_text="Whether this is a high-alert medication with risk of harm"
    )
    risk_score = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        default=1,
        help_text="Risk score from 1-10 for AI prioritization"
    )
    
    # Administrative
    is_controlled_substance = models.BooleanField(
        default=False,
        help_text="Whether this is a controlled substance"
    )
    schedule = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        help_text="Schedule for controlled substances"
    )
    requires_prior_auth = models.BooleanField(
        default=False,
        help_text="Whether insurance typically requires prior authorization"
    )
    
    class Meta:
        verbose_name = "Medication Catalog"
        verbose_name_plural = "Medication Catalog"
        indexes = [
            models.Index(fields=['generic_name']),
            models.Index(fields=['drug_class']),
            models.Index(fields=['drug_code']),
            models.Index(fields=['is_controlled_substance']),
            models.Index(fields=['high_alert_medication']),
        ]
    
    def __str__(self):
        return self.generic_name
    
    def get_brand_names_display(self):
        """Return formatted list of brand names"""
        if not self.brand_names:
            return "None"
        return ", ".join(self.brand_names)
    
    def get_interaction_summary(self):
        """Return summary of important drug interactions"""
        if not self.drug_interactions:
            return "No known significant interactions"
        
        severe_interactions = [
            interaction['drug'] 
            for interaction in self.drug_interactions 
            if interaction.get('severity') == 'severe'
        ]
        
        if severe_interactions:
            return f"Severe interactions with: {', '.join(severe_interactions)}"
        
        return f"Has {len(self.drug_interactions)} known interactions"
    
    def get_strength_options(self):
        """Return formatted list of strength options"""
        if not self.available_strengths:
            return "Unknown"
        
        return ", ".join(self.available_strengths)


class Medication(TimestampedModel):
    """
    Model for tracking detailed medication information
    for patient prescriptions, including administration details
    """
    # Relationships
    medical_record = models.ForeignKey(
        MedicalRecord,
        on_delete=models.CASCADE,
        related_name='medications',
        help_text="Medical record this medication belongs to"
    )
    catalog_entry = models.ForeignKey(
        MedicationCatalog,
        on_delete=models.PROTECT,
        related_name='prescriptions',
        null=True,
        blank=True,
        help_text="Reference to catalog information"
    )
    
    # Basic Prescription Information
    medication_name = models.CharField(
        max_length=255,
        help_text="Name of medication as prescribed"
    )
    generic_name = models.CharField(
        max_length=255,
        blank=True,
        help_text="Generic name of medication"
    )
    ndc_code = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="National Drug Code"
    )
    
    # Prescription Details
    strength = models.CharField(
        max_length=100,
        help_text="Medication strength (e.g., '10 mg')"
    )
    form = models.CharField(
        max_length=100,
        help_text="Medication form (e.g., 'tablet', 'capsule')"
    )
    route = models.CharField(
        max_length=100,
        help_text="Route of administration (e.g., 'oral', 'topical')"
    )
    dosage = models.CharField(
        max_length=255,
        help_text="Dosage instructions (e.g., '1 tablet')"
    )
    frequency = models.CharField(
        max_length=255,
        help_text="Frequency of administration (e.g., 'twice daily')"
    )
    
    # Timing and Duration
    start_date = models.DateField(
        help_text="Date medication was started"
    )
    end_date = models.DateField(
        blank=True,
        null=True,
        help_text="Date medication should end (if not ongoing)"
    )
    is_ongoing = models.BooleanField(
        default=True,
        help_text="Whether medication is currently active"
    )
    duration = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Duration of therapy (e.g., '10 days', 'ongoing')"
    )
    
    # Special Instructions
    patient_instructions = models.TextField(
        blank=True,
        null=True,
        help_text="Special instructions for patient"
    )
    pharmacy_instructions = models.TextField(
        blank=True,
        null=True,
        help_text="Special instructions for pharmacy"
    )
    
    # Purpose and Indication
    indication = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Reason medication was prescribed"
    )
    diagnosis_code = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="ICD-10 code for related diagnosis"
    )
    
    # Prescription Management
    prescription_number = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Pharmacy prescription number"
    )
    refills_authorized = models.IntegerField(
        default=0,
        help_text="Number of refills authorized"
    )
    refills_remaining = models.IntegerField(
        default=0,
        help_text="Number of refills remaining"
    )
    
    # Status
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('discontinued', 'Discontinued'),
        ('on_hold', 'On Hold'),
        ('never_administered', 'Never Administered')
    ]
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        help_text="Current status of medication"
    )
    
    # Provider Information
    prescribed_by = models.ForeignKey(
        'api.Doctor',
        on_delete=models.SET_NULL,
        null=True,
        related_name='prescribed_medications',
        help_text="Provider who prescribed the medication"
    )
    
    # Appointment Information
    appointment = models.ForeignKey(
        'api.Appointment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='medications',
        help_text="Appointment during which this medication was prescribed"
    )

    # Pharmacy Information
    nominated_pharmacy = models.ForeignKey(
        'api.Pharmacy',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='nominated_prescriptions',
        help_text="Patient's nominated pharmacy for this prescription (auto-assigned from user's current nomination)"
    )

    pharmacy_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Dispensing pharmacy name (legacy field - use nominated_pharmacy for structured data)"
    )

    # Security and Verification Fields
    nonce = models.UUIDField(
        unique=True,
        null=True,
        blank=True,
        help_text="One-time verification token for prescription security"
    )
    signature = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        help_text="HMAC-SHA256 signature for prescription verification"
    )

    # Dispensing Tracking
    dispensed = models.BooleanField(
        default=False,
        help_text="Whether prescription has been dispensed/collected"
    )
    dispensed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date and time prescription was dispensed"
    )
    dispensed_by_pharmacy = models.ForeignKey(
        'api.Pharmacy',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='dispensed_prescriptions',
        help_text="Pharmacy that dispensed the prescription"
    )
    dispensing_pharmacist_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Name of pharmacist who dispensed the medication"
    )

    # Controlled Substance Override
    is_controlled_override = models.BooleanField(
        default=False,
        help_text="Doctor manually marked as controlled substance (even if not in drug database)"
    )

    verification_attempts = models.JSONField(
        default=list,
        help_text="Log of all verification attempts for audit trail"
    )

    # Additional Clinical Information
    priority = models.IntegerField(
        default=3,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Priority level (1-5), where 1 is highest priority"
    )
    
    # Patient Experience
    side_effects_experienced = models.TextField(
        blank=True,
        null=True,
        help_text="Side effects reported by patient"
    )
    
    ADHERENCE_CHOICES = [
        ('good', 'Good'),
        ('moderate', 'Moderate'),
        ('poor', 'Poor'),
        ('unknown', 'Unknown')
    ]
    
    adherence = models.CharField(
        max_length=20,
        choices=ADHERENCE_CHOICES,
        default='unknown',
        help_text="Patient adherence to medication"
    )
    
    adherence_notes = models.TextField(
        blank=True,
        null=True,
        help_text="Notes about patient adherence"
    )
    
    # Discontinuation
    discontinued_date = models.DateField(
        blank=True,
        null=True,
        help_text="Date medication was discontinued"
    )
    
    DISCONTINUATION_REASONS = [
        ('completed', 'Course Completed'),
        ('adverse_effect', 'Adverse Effect'),
        ('ineffective', 'Not Effective'),
        ('cost', 'Cost Issues'),
        ('patient_choice', 'Patient Choice'),
        ('alternative', 'Alternative Treatment'),
        ('other', 'Other')
    ]
    
    discontinuation_reason = models.CharField(
        max_length=20,
        choices=DISCONTINUATION_REASONS,
        blank=True,
        null=True,
        help_text="Reason for discontinuation"
    )
    
    discontinuation_notes = models.TextField(
        blank=True,
        null=True,
        help_text="Notes about medication discontinuation"
    )
    
    class Meta:
        verbose_name = "Medication"
        verbose_name_plural = "Medications"
        ordering = ['-start_date']
        indexes = [
            models.Index(fields=['medical_record', 'medication_name']),
            models.Index(fields=['medical_record', 'status']),
            models.Index(fields=['start_date']),
            models.Index(fields=['is_ongoing']),
        ]
    
    def __str__(self):
        return f"{self.medication_name} {self.strength} for {self.medical_record.hpn}"
    
    def save(self, *args, **kwargs):
        # Generate nonce for new prescriptions (for security verification)
        if not self.pk and not self.nonce:
            import uuid
            self.nonce = uuid.uuid4()

        # Set generic name from catalog if available and not set
        if self.catalog_entry and not self.generic_name:
            self.generic_name = self.catalog_entry.generic_name

        # Auto-assign patient's nominated pharmacy if not set (on creation only)
        if not self.pk and not self.nominated_pharmacy:
            try:
                # Import here to avoid circular imports
                from .pharmacy import NominatedPharmacy

                # Get patient from medical record
                patient = self.medical_record.user

                # Get current nomination
                current_nomination = NominatedPharmacy.objects.filter(
                    user=patient,
                    is_current=True
                ).first()

                # Assign nominated pharmacy if found
                if current_nomination:
                    self.nominated_pharmacy = current_nomination.pharmacy
                    # Also update pharmacy_name for backward compatibility
                    if not self.pharmacy_name:
                        self.pharmacy_name = current_nomination.pharmacy.name
            except Exception as e:
                # Log but don't fail prescription creation if nomination lookup fails
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Could not auto-assign nominated pharmacy: {str(e)}")

        # Check if medication is discontinued
        if self.status == 'discontinued' and not self.discontinued_date:
            self.discontinued_date = timezone.now().date()
            self.is_ongoing = False

        # Update ongoing status based on end date
        if self.end_date and self.end_date < timezone.now().date():
            self.is_ongoing = False
            if self.status == 'active':
                self.status = 'completed'

        super().save(*args, **kwargs)

        # Update medical record medication count
        if hasattr(self.medical_record, 'update_complexity_metrics'):
            self.medical_record.update_complexity_metrics()
    
    @property
    def days_supply(self):
        """Calculate days supply based on start/end dates"""
        if not self.end_date:
            return None
        
        delta = self.end_date - self.start_date
        return delta.days
    
    @property
    def is_expired(self):
        """Check if prescription is expired"""
        if self.end_date and timezone.now().date() > self.end_date:
            return True
        
        if self.refills_remaining <= 0 and not self.is_ongoing:
            return True
            
        return False
    
    @property
    def is_controlled(self):
        """Check if medication is a controlled substance"""
        if self.catalog_entry:
            return self.catalog_entry.is_controlled_substance
        return False
    
    @property
    def is_high_alert(self):
        """Check if medication is high alert"""
        if self.catalog_entry:
            return self.catalog_entry.high_alert_medication
        return False
    
    def get_interaction_warnings(self, other_medications):
        """
        Check for interactions with other medications
        
        Args:
            other_medications: QuerySet of other Medication objects
            
        Returns:
            List of interaction warnings
        """
        warnings = []
        
        if not self.catalog_entry or not self.catalog_entry.drug_interactions:
            return warnings
        
        interaction_drugs = [
            interaction['drug'].lower()
            for interaction in self.catalog_entry.drug_interactions
        ]
        
        for med in other_medications:
            if med.id == self.id:
                continue
                
            # Check if this medication interacts with the other one
            check_names = [
                med.medication_name.lower(),
                med.generic_name.lower() if med.generic_name else ''
            ]
            
            for drug_name in check_names:
                if drug_name and any(drug_name in inter for inter in interaction_drugs):
                    # Find the interaction details
                    for interaction in self.catalog_entry.drug_interactions:
                        if drug_name in interaction['drug'].lower():
                            warnings.append({
                                'medication': med.medication_name,
                                'severity': interaction.get('severity', 'unknown'),
                                'effect': interaction.get('effect', 'Unknown interaction effect')
                            })
                            break
        
        return warnings
    
    def get_next_refill_date(self):
        """Calculate when next refill is due based on days supply"""
        if not self.is_ongoing or self.refills_remaining <= 0:
            return None
            
        supply_days = self.days_supply
        if not supply_days:
            return None
            
        last_fill_date = self.start_date
        
        # Calculate days since start
        days_since_start = (timezone.now().date() - self.start_date).days
        
        # Calculate next refill date
        refills_used = days_since_start // supply_days
        next_refill_date = self.start_date + timezone.timedelta(days=(refills_used + 1) * supply_days)
        
        # If next refill date is in the past, adjust to today
        if next_refill_date < timezone.now().date():
            next_refill_date = timezone.now().date()
            
        return next_refill_date
    
    def report_side_effect(self, effect_description, severity, reported_date=None):
        """
        Record a side effect for this medication
        
        Args:
            effect_description: Description of side effect
            severity: Severity (mild, moderate, severe)
            reported_date: Date side effect was reported
            
        Returns:
            MedicationSideEffect object
        """
        if not reported_date:
            reported_date = timezone.now().date()
            
        # Append to text field for now
        if self.side_effects_experienced:
            self.side_effects_experienced += f"\n\n{reported_date}: {severity.upper()} - {effect_description}"
        else:
            self.side_effects_experienced = f"{reported_date}: {severity.upper()} - {effect_description}"
            
        self.save()
        
        # If severe, change status to on_hold
        if severity.lower() == 'severe':
            self.status = 'on_hold'
            self.save()
            
        return True
        
    def update_adherence(self, adherence_status, notes=None):
        """
        Update adherence information
        
        Args:
            adherence_status: One of the ADHERENCE_CHOICES
            notes: Optional notes about adherence
            
        Returns:
            True if updated successfully
        """
        self.adherence = adherence_status
        
        if notes:
            if self.adherence_notes:
                self.adherence_notes += f"\n\n{timezone.now().date()}: {notes}"
            else:
                self.adherence_notes = f"{timezone.now().date()}: {notes}"
                
        self.save()
        return True
        
    def discontinue(self, reason, notes=None):
        """
        Discontinue this medication
        
        Args:
            reason: One of the DISCONTINUATION_REASONS
            notes: Optional notes about discontinuation
            
        Returns:
            True if discontinued successfully
        """
        self.status = 'discontinued'
        self.is_ongoing = False
        self.discontinued_date = timezone.now().date()
        self.discontinuation_reason = reason
        
        if notes:
            self.discontinuation_notes = notes
            
        self.save()
        return True 