"""
Drug Interaction Model

Stores information about drug-drug interactions for the prescription safety system.
Tracks severity, clinical effects, and management strategies for known interactions.
"""

import uuid
from django.db import models
from django.core.exceptions import ValidationError
from .drug_classification import DrugClassification


class DrugInteraction(models.Model):
    """
    Drug-Drug Interaction Information

    Stores documented interactions between medications with severity levels,
    clinical effects, and management recommendations.
    """

    # =================================================================
    # PRIMARY KEY & DRUG REFERENCES
    # =================================================================

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier for the interaction"
    )

    drug_a = models.ForeignKey(
        DrugClassification,
        on_delete=models.CASCADE,
        related_name='interactions_as_drug_a',
        help_text="First drug in the interaction"
    )

    drug_b = models.ForeignKey(
        DrugClassification,
        on_delete=models.CASCADE,
        related_name='interactions_as_drug_b',
        help_text="Second drug in the interaction"
    )

    # =================================================================
    # INTERACTION SEVERITY
    # =================================================================

    SEVERITY_CHOICES = [
        ('mild', 'Mild - Usually no clinical intervention needed'),
        ('moderate', 'Moderate - Monitor patient, may need intervention'),
        ('severe', 'Severe - Requires intervention or close monitoring'),
        ('contraindicated', 'Contraindicated - Do not prescribe together'),
    ]

    interaction_severity = models.CharField(
        max_length=20,
        choices=SEVERITY_CHOICES,
        db_index=True,
        help_text="Severity level of the interaction"
    )

    # =================================================================
    # CLINICAL INFORMATION
    # =================================================================

    clinical_effect = models.TextField(
        help_text="Description of what happens when drugs are taken together"
    )

    mechanism = models.TextField(
        blank=True,
        help_text="Pharmacological mechanism of the interaction"
    )

    onset_timing = models.CharField(
        max_length=50,
        blank=True,
        choices=[
            ('rapid', 'Rapid (within hours)'),
            ('delayed', 'Delayed (days to weeks)'),
            ('variable', 'Variable'),
        ],
        help_text="How quickly the interaction occurs"
    )

    # =================================================================
    # MANAGEMENT & RECOMMENDATIONS
    # =================================================================

    management_strategy = models.TextField(
        help_text="How to manage this interaction clinically"
    )

    alternative_recommendation = models.TextField(
        blank=True,
        help_text="Suggested alternative medications to avoid interaction"
    )

    monitoring_required = models.BooleanField(
        default=False,
        help_text="Whether monitoring is required if drugs must be used together"
    )

    monitoring_parameters = models.TextField(
        blank=True,
        help_text="What to monitor (e.g., INR, blood pressure, renal function)"
    )

    # =================================================================
    # EVIDENCE & DOCUMENTATION
    # =================================================================

    EVIDENCE_LEVEL_CHOICES = [
        ('well_documented', 'Well-Documented (Multiple clinical studies)'),
        ('suspected', 'Suspected (Case reports or theoretical)'),
        ('theoretical', 'Theoretical (Based on pharmacology, not clinical data)'),
    ]

    evidence_level = models.CharField(
        max_length=20,
        choices=EVIDENCE_LEVEL_CHOICES,
        default='suspected',
        help_text="Level of evidence for this interaction"
    )

    references = models.JSONField(
        default=list,
        blank=True,
        help_text="List of references/studies documenting this interaction"
    )

    external_links = models.JSONField(
        default=dict,
        blank=True,
        help_text="Links to external resources (FDA alerts, Drugs.com, etc.)"
    )

    # =================================================================
    # FREQUENCY & PREVALENCE
    # =================================================================

    frequency_of_occurrence = models.CharField(
        max_length=20,
        blank=True,
        choices=[
            ('rare', 'Rare (<1%)'),
            ('uncommon', 'Uncommon (1-10%)'),
            ('common', 'Common (10-50%)'),
            ('very_common', 'Very Common (>50%)'),
        ],
        help_text="How often this interaction occurs clinically"
    )

    # =================================================================
    # ADMINISTRATIVE & METADATA
    # =================================================================

    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Interaction is active in system"
    )

    notes = models.TextField(
        blank=True,
        help_text="Internal notes for pharmacists"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this interaction was added to database"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When this interaction was last updated"
    )

    last_verified_date = models.DateField(
        blank=True,
        null=True,
        help_text="Last date this interaction was verified"
    )

    verified_by = models.CharField(
        max_length=200,
        blank=True,
        help_text="Name/ID of person who verified this interaction"
    )

    # =================================================================
    # META & INDEXES
    # =================================================================

    class Meta:
        db_table = 'drug_interactions'
        verbose_name = 'Drug Interaction'
        verbose_name_plural = 'Drug Interactions'
        ordering = ['-interaction_severity', 'drug_a__generic_name', 'drug_b__generic_name']

        # Ensure each drug pair is unique (prevent duplicates)
        constraints = [
            models.UniqueConstraint(
                fields=['drug_a', 'drug_b'],
                name='unique_drug_pair'
            )
        ]

        indexes = [
            models.Index(fields=['drug_a', 'interaction_severity'], name='idx_interaction_drug_a'),
            models.Index(fields=['drug_b', 'interaction_severity'], name='idx_interaction_drug_b'),
            models.Index(fields=['interaction_severity'], name='idx_interaction_severity'),
            models.Index(fields=['is_active'], name='idx_interaction_active'),
        ]

    # =================================================================
    # METHODS
    # =================================================================

    def __str__(self):
        """String representation"""
        severity_symbol = {
            'mild': '⚠️',
            'moderate': '⚠️⚠️',
            'severe': '🚨',
            'contraindicated': '❌',
        }.get(self.interaction_severity, '')

        return f"{severity_symbol} {self.drug_a.generic_name} + {self.drug_b.generic_name} ({self.interaction_severity})"

    def clean(self):
        """Validate model data"""
        errors = {}

        # Ensure drug_a and drug_b are different
        if self.drug_a_id and self.drug_b_id and self.drug_a_id == self.drug_b_id:
            errors['drug_b'] = 'Drug A and Drug B must be different drugs'

        # If contraindicated, management strategy should recommend avoiding
        if self.interaction_severity == 'contraindicated':
            if not ('avoid' in self.management_strategy.lower() or 'do not' in self.management_strategy.lower()):
                errors['management_strategy'] = 'Contraindicated interactions should include "avoid" in management strategy'

        # If monitoring required, must specify parameters
        if self.monitoring_required and not self.monitoring_parameters:
            errors['monitoring_parameters'] = 'Monitoring parameters required when monitoring_required is True'

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        """Override save to run validation and ensure consistent ordering"""
        # Always store drugs in alphabetical order to prevent duplicate pairs
        if self.drug_a_id and self.drug_b_id:
            if self.drug_a.generic_name > self.drug_b.generic_name:
                self.drug_a, self.drug_b = self.drug_b, self.drug_a

        self.clean()
        super().save(*args, **kwargs)

    # =================================================================
    # QUERY METHODS
    # =================================================================

    @property
    def is_critical(self):
        """Check if this is a critical interaction"""
        return self.interaction_severity in ['severe', 'contraindicated']

    @property
    def severity_color(self):
        """Get color code for severity (for UI display)"""
        color_map = {
            'mild': 'yellow',
            'moderate': 'orange',
            'severe': 'red',
            'contraindicated': 'darkred',
        }
        return color_map.get(self.interaction_severity, 'gray')

    def get_patient_friendly_description(self):
        """
        Get a simplified description suitable for patients

        Returns:
            str: Patient-friendly explanation
        """
        severity_text = {
            'mild': 'These medications may interact slightly.',
            'moderate': 'These medications can interact. Your doctor will monitor you.',
            'severe': 'These medications have a serious interaction. Close monitoring is required.',
            'contraindicated': 'These medications should NOT be taken together.',
        }.get(self.interaction_severity, 'These medications may interact.')

        return f"{severity_text} {self.clinical_effect}"

    @classmethod
    def check_interactions(cls, drug_ids: list):
        """
        Check for interactions between a list of drugs

        Args:
            drug_ids: List of DrugClassification IDs

        Returns:
            QuerySet of DrugInteraction objects
        """
        from django.db.models import Q

        if len(drug_ids) < 2:
            return cls.objects.none()

        # Build query for all pairwise combinations
        query = Q()
        for i, drug_a_id in enumerate(drug_ids):
            for drug_b_id in drug_ids[i+1:]:
                query |= (Q(drug_a_id=drug_a_id) & Q(drug_b_id=drug_b_id)) | \
                         (Q(drug_a_id=drug_b_id) & Q(drug_b_id=drug_a_id))

        return cls.objects.filter(query, is_active=True).select_related(
            'drug_a', 'drug_b'
        ).order_by('-interaction_severity')

    @classmethod
    def get_critical_interactions(cls):
        """Get all severe and contraindicated interactions"""
        return cls.objects.filter(
            interaction_severity__in=['severe', 'contraindicated'],
            is_active=True
        ).select_related('drug_a', 'drug_b')

    @classmethod
    def get_interactions_for_drug(cls, drug_id):
        """
        Get all known interactions for a specific drug

        Args:
            drug_id: DrugClassification ID

        Returns:
            QuerySet of interactions involving this drug
        """
        from django.db.models import Q

        return cls.objects.filter(
            Q(drug_a_id=drug_id) | Q(drug_b_id=drug_id),
            is_active=True
        ).select_related('drug_a', 'drug_b').order_by('-interaction_severity')
