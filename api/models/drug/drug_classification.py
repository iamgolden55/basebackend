"""
Drug Classification Model

Comprehensive drug classification system for the PHB prescription triage system.
Includes Nigerian NAFDAC regulations, international classifications, risk flags,
prescribing requirements, and monitoring protocols.

Based on:
- NAFDAC (Nigerian) drug schedules
- WHO Essential Medicines List
- FDA/DEA (US) classifications
- UK controlled drug classifications
"""

import uuid
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone


class DrugClassification(models.Model):
    """
    Comprehensive drug classification and regulatory information

    Stores detailed information about medications including regulatory status,
    prescribing requirements, risk levels, monitoring needs, and search metadata.
    """

    # =================================================================
    # PRIMARY KEY & BASIC IDENTIFICATION
    # =================================================================

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier for the drug"
    )

    generic_name = models.CharField(
        max_length=200,
        unique=True,
        db_index=True,
        help_text="International non-proprietary name (INN) or generic name"
    )

    brand_names = models.JSONField(
        default=list,
        blank=True,
        help_text="List of brand/trade names (e.g., ['Panadol', 'Tylenol'])"
    )

    active_ingredients = models.JSONField(
        default=list,
        blank=True,
        help_text="List of active ingredients with strengths"
    )

    # =================================================================
    # NIGERIAN REGULATORY STATUS (NAFDAC)
    # =================================================================

    NAFDAC_SCHEDULE_CHOICES = [
        ('unscheduled', 'Unscheduled (Not Controlled)'),
        ('schedule_1', 'Schedule 1 (Illegal - No Medical Use)'),
        ('schedule_2', 'Schedule 2 (High Control - Opioids)'),
        ('schedule_3', 'Schedule 3 (Controlled - Benzodiazepines)'),
        ('schedule_4', 'Schedule 4 (Monitored - Tramadol)'),
    ]

    nafdac_approved = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Whether drug is approved by NAFDAC for use in Nigeria"
    )

    nafdac_registration_number = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="NAFDAC registration number (e.g., A4-1234)"
    )

    nafdac_schedule = models.CharField(
        max_length=20,
        choices=NAFDAC_SCHEDULE_CHOICES,
        default='unscheduled',
        db_index=True,
        help_text="NAFDAC controlled substance schedule"
    )

    nafdac_schedule_date = models.DateField(
        blank=True,
        null=True,
        help_text="Date drug was added to NAFDAC schedule (e.g., Tramadol in 2018)"
    )

    # =================================================================
    # INTERNATIONAL REGULATORY CLASSIFICATIONS
    # =================================================================

    US_DEA_SCHEDULE_CHOICES = [
        ('not_scheduled', 'Not Scheduled'),
        ('schedule_1', 'DEA Schedule I'),
        ('schedule_2', 'DEA Schedule II'),
        ('schedule_3', 'DEA Schedule III'),
        ('schedule_4', 'DEA Schedule IV'),
        ('schedule_5', 'DEA Schedule V'),
    ]

    us_dea_schedule = models.CharField(
        max_length=20,
        choices=US_DEA_SCHEDULE_CHOICES,
        default='not_scheduled',
        blank=True,
        help_text="US DEA controlled substance schedule"
    )

    UK_CONTROLLED_DRUG_CHOICES = [
        ('not_controlled', 'Not Controlled'),
        ('class_a', 'Class A (Most Harmful)'),
        ('class_b', 'Class B (Serious Harm)'),
        ('class_c', 'Class C (Harmful)'),
    ]

    uk_controlled_drug_class = models.CharField(
        max_length=20,
        choices=UK_CONTROLLED_DRUG_CHOICES,
        default='not_controlled',
        blank=True,
        help_text="UK controlled drug classification"
    )

    who_essential_medicine = models.BooleanField(
        default=False,
        help_text="Listed on WHO Model List of Essential Medicines"
    )

    # =================================================================
    # PRESCRIBING REQUIREMENTS
    # =================================================================

    requires_special_prescription = models.BooleanField(
        default=False,
        help_text="Requires special prescription form (e.g., controlled substances)"
    )

    requires_physician_only = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Only physicians can prescribe (pharmacists cannot)"
    )

    pharmacist_can_prescribe = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Clinical pharmacists with authority can prescribe"
    )

    maximum_days_supply = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Maximum number of days that can be prescribed at once"
    )

    requires_photo_id = models.BooleanField(
        default=False,
        help_text="Patient must present photo ID to collect (e.g., controlled substances)"
    )

    # =================================================================
    # CLINICAL CLASSIFICATIONS
    # =================================================================

    therapeutic_class = models.CharField(
        max_length=100,
        blank=True,
        db_index=True,
        help_text="Therapeutic category (e.g., 'Analgesic', 'Antibiotic')"
    )

    pharmacological_class = models.CharField(
        max_length=100,
        blank=True,
        help_text="Pharmacological classification (e.g., 'Opioid', 'Beta-blocker')"
    )

    mechanism_of_action = models.TextField(
        blank=True,
        help_text="How the drug works (for pharmacist reference)"
    )

    # =================================================================
    # RISK FLAGS
    # =================================================================

    is_controlled = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Is this a controlled substance (any schedule)"
    )

    is_high_risk = models.BooleanField(
        default=False,
        db_index=True,
        help_text="High-risk medication requiring careful monitoring (e.g., warfarin, insulin)"
    )

    requires_monitoring = models.BooleanField(
        default=False,
        help_text="Requires routine lab/clinical monitoring"
    )

    monitoring_type = models.CharField(
        max_length=100,
        blank=True,
        help_text="Type of monitoring required (e.g., 'INR', 'kidney_function', 'blood_glucose')"
    )

    monitoring_frequency_days = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="How often monitoring is needed (in days, e.g., 30 for monthly)"
    )

    addiction_risk = models.BooleanField(
        default=False,
        help_text="Drug has significant addiction/dependence potential"
    )

    abuse_potential = models.CharField(
        max_length=20,
        choices=[
            ('none', 'No Abuse Potential'),
            ('low', 'Low'),
            ('moderate', 'Moderate'),
            ('high', 'High'),
            ('severe', 'Severe'),
        ],
        default='none',
        help_text="Potential for substance abuse"
    )

    # =================================================================
    # AGE & PREGNANCY RESTRICTIONS
    # =================================================================

    minimum_age = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Minimum age in years (e.g., 18 for controlled substances)"
    )

    maximum_age = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Maximum age in years (if applicable, e.g., pediatric medications)"
    )

    PREGNANCY_CATEGORY_CHOICES = [
        ('A', 'Category A - Safe in pregnancy'),
        ('B', 'Category B - Probably safe'),
        ('C', 'Category C - Risk cannot be ruled out'),
        ('D', 'Category D - Positive evidence of risk'),
        ('X', 'Category X - Contraindicated in pregnancy'),
        ('N', 'Not Categorized'),
    ]

    pregnancy_category = models.CharField(
        max_length=1,
        choices=PREGNANCY_CATEGORY_CHOICES,
        default='N',
        help_text="FDA pregnancy risk category"
    )

    breastfeeding_safe = models.BooleanField(
        default=True,
        help_text="Safe for breastfeeding mothers"
    )

    # =================================================================
    # CONTRAINDICATIONS & WARNINGS
    # =================================================================

    major_contraindications = models.JSONField(
        default=list,
        blank=True,
        help_text="List of medical conditions where drug is contraindicated"
    )

    allergy_cross_reactions = models.JSONField(
        default=list,
        blank=True,
        help_text="Drugs/substances that may cause cross-allergic reactions"
    )

    black_box_warning = models.BooleanField(
        default=False,
        help_text="FDA black box warning (most serious warning)"
    )

    black_box_warning_text = models.TextField(
        blank=True,
        help_text="Text of black box warning"
    )

    # =================================================================
    # DRUG INTERACTIONS (High-level flags)
    # =================================================================

    major_drug_interactions = models.JSONField(
        default=list,
        blank=True,
        help_text="List of drug names with major interactions (detailed interactions in DrugInteraction model)"
    )

    food_interactions = models.JSONField(
        default=list,
        blank=True,
        help_text="Foods that interact with this drug (e.g., grapefruit juice)"
    )

    # =================================================================
    # SEARCH & MATCHING
    # =================================================================

    search_keywords = models.JSONField(
        default=list,
        blank=True,
        help_text="All possible spellings, abbreviations, and variants for matching"
    )

    generic_variations = models.JSONField(
        default=list,
        blank=True,
        help_text="Alternative generic names or spellings"
    )

    common_misspellings = models.JSONField(
        default=list,
        blank=True,
        help_text="Common misspellings to catch (e.g., 'paracetamol' vs 'paracetomol')"
    )

    # =================================================================
    # ALTERNATIVES & SUBSTITUTIONS
    # =================================================================

    safer_alternatives = models.JSONField(
        default=list,
        blank=True,
        help_text="List of safer alternative drugs (generic names)"
    )

    cheaper_alternatives = models.JSONField(
        default=list,
        blank=True,
        help_text="List of more affordable alternatives"
    )

    # =================================================================
    # ADMINISTRATIVE & METADATA
    # =================================================================

    notes = models.TextField(
        blank=True,
        help_text="Internal notes for pharmacists/administrators"
    )

    external_references = models.JSONField(
        default=dict,
        blank=True,
        help_text="Links to external databases (FDA, WHO, etc.)"
    )

    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Drug is active in system (set False if discontinued)"
    )

    discontinued = models.BooleanField(
        default=False,
        help_text="Drug has been discontinued/withdrawn from market"
    )

    discontinued_date = models.DateField(
        blank=True,
        null=True,
        help_text="Date drug was discontinued"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this record was created"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When this record was last updated"
    )

    last_verified_date = models.DateField(
        blank=True,
        null=True,
        help_text="Last date data was verified by medical professional"
    )

    verified_by = models.CharField(
        max_length=200,
        blank=True,
        help_text="Name/ID of person who verified this data"
    )

    # =================================================================
    # META & INDEXES
    # =================================================================

    class Meta:
        db_table = 'drug_classifications'
        verbose_name = 'Drug Classification'
        verbose_name_plural = 'Drug Classifications'
        ordering = ['generic_name']

        indexes = [
            models.Index(fields=['generic_name'], name='idx_drug_generic'),
            models.Index(fields=['nafdac_schedule'], name='idx_drug_nafdac_schedule'),
            models.Index(fields=['therapeutic_class'], name='idx_drug_therapeutic'),
            models.Index(fields=['is_controlled', 'is_high_risk'], name='idx_drug_risk_flags'),
            models.Index(fields=['pharmacist_can_prescribe'], name='idx_drug_pharm_prescribe'),
            models.Index(fields=['is_active'], name='idx_drug_active'),
        ]

    # =================================================================
    # METHODS
    # =================================================================

    def __str__(self):
        """String representation"""
        brands = ', '.join(self.brand_names[:2]) if self.brand_names else ''
        if brands:
            return f"{self.generic_name} ({brands})"
        return self.generic_name

    def clean(self):
        """Validate model data"""
        errors = {}

        # If controlled, must have a schedule
        if self.is_controlled and self.nafdac_schedule == 'unscheduled':
            errors['nafdac_schedule'] = 'Controlled substances must have a NAFDAC schedule'

        # If requires monitoring, must specify type
        if self.requires_monitoring and not self.monitoring_type:
            errors['monitoring_type'] = 'Monitoring type required when requires_monitoring is True'

        # If high-risk or controlled, should require physician or special prescription
        if (self.is_controlled or self.is_high_risk) and not (self.requires_physician_only or self.requires_special_prescription):
            errors['requires_physician_only'] = 'High-risk or controlled substances should require physician prescription'

        # Validate age restrictions
        if self.minimum_age and self.maximum_age:
            if self.minimum_age >= self.maximum_age:
                errors['maximum_age'] = 'Maximum age must be greater than minimum age'

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        """Override save to run validation"""
        self.clean()
        super().save(*args, **kwargs)

    # =================================================================
    # QUERY METHODS
    # =================================================================

    @property
    def is_controlled_substance(self):
        """Check if this is a controlled substance"""
        return self.nafdac_schedule in ['schedule_1', 'schedule_2', 'schedule_3', 'schedule_4']

    @property
    def controlled_schedule_number(self):
        """Get numeric schedule (1-4) or None"""
        schedule_map = {
            'schedule_1': 1,
            'schedule_2': 2,
            'schedule_3': 3,
            'schedule_4': 4,
        }
        return schedule_map.get(self.nafdac_schedule)

    @property
    def all_drug_names(self):
        """Get all possible names for this drug (generic + brands + keywords)"""
        names = [self.generic_name.lower()]
        names.extend([name.lower() for name in self.brand_names])
        names.extend([keyword.lower() for keyword in self.search_keywords])
        return list(set(names))  # Remove duplicates

    def matches_name(self, search_term: str) -> bool:
        """
        Check if search term matches any name of this drug

        Args:
            search_term: The term to search for (case-insensitive)

        Returns:
            True if matches, False otherwise
        """
        search_lower = search_term.lower().strip()
        return search_lower in self.all_drug_names

    def get_prescribing_authority(self):
        """
        Determine who can prescribe this medication

        Returns:
            str: 'physician_only', 'pharmacist', or 'any'
        """
        if self.requires_physician_only:
            return 'physician_only'
        elif self.pharmacist_can_prescribe:
            return 'pharmacist'
        else:
            return 'any'

    def get_risk_level(self):
        """
        Get overall risk level

        Returns:
            str: 'low', 'moderate', 'high', 'critical'
        """
        if self.nafdac_schedule in ['schedule_1', 'schedule_2'] or self.black_box_warning:
            return 'critical'
        elif self.is_high_risk or self.nafdac_schedule == 'schedule_3':
            return 'high'
        elif self.is_controlled or self.requires_monitoring or self.nafdac_schedule == 'schedule_4':
            return 'moderate'
        else:
            return 'low'

    def requires_special_handling(self):
        """Check if drug needs special handling/storage"""
        return self.is_controlled or self.requires_photo_id or self.requires_special_prescription

    @classmethod
    def search_by_name(cls, search_term: str):
        """
        Search for drugs by name (generic, brand, or keyword)

        Args:
            search_term: The search term

        Returns:
            QuerySet of matching drugs
        """
        from django.db.models import Q
        from django.contrib.postgres.search import TrigramSimilarity

        search_lower = search_term.lower().strip()

        # Try exact match first
        exact_match = cls.objects.filter(
            Q(generic_name__iexact=search_term) |
            Q(brand_names__icontains=search_term) |
            Q(search_keywords__icontains=search_term)
        ).first()

        if exact_match:
            return cls.objects.filter(id=exact_match.id)

        # Fallback to partial match
        return cls.objects.filter(
            Q(generic_name__icontains=search_term) |
            Q(brand_names__icontains=search_term) |
            Q(search_keywords__icontains=search_term)
        ).filter(is_active=True)

    @classmethod
    def get_controlled_substances(cls, schedule=None):
        """
        Get all controlled substances

        Args:
            schedule: Optional specific schedule (1, 2, 3, or 4)

        Returns:
            QuerySet of controlled substances
        """
        queryset = cls.objects.filter(is_controlled=True, is_active=True)

        if schedule:
            schedule_str = f'schedule_{schedule}'
            queryset = queryset.filter(nafdac_schedule=schedule_str)

        return queryset.order_by('nafdac_schedule', 'generic_name')

    @classmethod
    def get_high_risk_medications(cls):
        """Get all high-risk medications"""
        return cls.objects.filter(
            is_high_risk=True,
            is_active=True
        ).order_by('generic_name')
