"""
Prescription Request Models

Models for managing prescription requests from patients to doctors.
Implements NHS-style pooled prescription request system where requests
are sent to all prescribing doctors at a hospital.
"""

from django.db import models
from django.utils import timezone
import uuid


class PrescriptionRequest(models.Model):
    """
    Main prescription request model.

    Represents a patient's request for medication prescriptions.
    Requests are routed to all prescribing doctors at the patient's
    registered hospital (NHS pooled list model).
    """

    STATUS_CHOICES = [
        ('REQUESTED', 'Requested'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('DISPENSED', 'Dispensed'),
        ('CANCELLED', 'Cancelled'),
    ]

    URGENCY_CHOICES = [
        ('routine', 'Routine'),
        ('urgent', 'Urgent'),
    ]

    REQUEST_TYPE_CHOICES = [
        ('repeat', 'Repeat Prescription'),
        ('new', 'New Medication'),
        ('dosage_change', 'Dosage Change'),
    ]

    # Identification
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text='Unique identifier for the prescription request'
    )
    request_reference = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        help_text='Human-readable reference number (e.g., REQ-ABC123)'
    )

    # Patient and Hospital (using string references to avoid circular imports)
    patient = models.ForeignKey(
        'CustomUser',
        on_delete=models.CASCADE,
        related_name='prescription_requests',
        help_text='Patient who submitted the request'
    )
    hospital = models.ForeignKey(
        'Hospital',
        on_delete=models.CASCADE,
        related_name='prescription_requests',
        help_text='Hospital where request is sent'
    )

    # Request Details
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='REQUESTED',
        db_index=True,
        help_text='Current status of the prescription request'
    )
    urgency = models.CharField(
        max_length=10,
        choices=URGENCY_CHOICES,
        default='routine',
        db_index=True,
        help_text='Urgency level (urgent = 1-3 days, routine = 7-10 days)'
    )
    request_type = models.CharField(
        max_length=20,
        choices=REQUEST_TYPE_CHOICES,
        default='repeat',
        help_text='Type of prescription request'
    )

    # Dates
    request_date = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        help_text='When the request was submitted'
    )
    reviewed_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the request was reviewed by a doctor'
    )

    # Review Information
    reviewed_by = models.ForeignKey(
        'Doctor',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_prescription_requests',
        help_text='Doctor who reviewed/approved/rejected the request'
    )
    rejection_reason = models.TextField(
        null=True,
        blank=True,
        help_text='Clinical reason for rejection (if rejected)'
    )
    clinical_notes = models.TextField(
        null=True,
        blank=True,
        help_text='Doctor\'s clinical notes about the approval/rejection'
    )
    requires_followup = models.BooleanField(
        default=False,
        help_text='Whether patient needs follow-up appointment (for rejections)'
    )

    # ==================== PHARMACIST TRIAGE FIELDS ====================
    # Triage Assignment
    triage_category = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        db_index=True,
        help_text='Auto-assigned triage category (e.g., ROUTINE_REPEAT, URGENT_NEW, COMPLEX_CASE)'
    )
    triage_reason = models.TextField(
        null=True,
        blank=True,
        help_text='Explanation of why this triage category was assigned'
    )
    assigned_to_role = models.CharField(
        max_length=20,
        choices=[
            ('pharmacist', 'Pharmacist'),
            ('doctor', 'Doctor'),
            ('admin', 'Admin Staff'),
        ],
        default='pharmacist',
        db_index=True,
        help_text='Role assigned to review this request'
    )
    assigned_to_pharmacist = models.ForeignKey(
        'Pharmacist',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_prescription_requests',
        help_text='Specific pharmacist assigned to review (if assigned_to_role is pharmacist)'
    )
    assigned_to_doctor = models.ForeignKey(
        'Doctor',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_prescription_requests',
        help_text='Specific doctor assigned to review (if assigned_to_role is doctor)'
    )

    # Pharmacist Review
    pharmacist_reviewed_by = models.ForeignKey(
        'Pharmacist',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_prescription_requests',
        help_text='Pharmacist who reviewed this request'
    )
    pharmacist_review_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the pharmacist reviewed the request'
    )
    pharmacist_review_action = models.CharField(
        max_length=20,
        choices=[
            ('approved', 'Approved'),
            ('escalated', 'Escalated to Physician'),
            ('rejected', 'Rejected'),
            ('consultation', 'Patient Consultation Required'),
        ],
        null=True,
        blank=True,
        help_text='Action taken by pharmacist'
    )
    pharmacist_notes = models.TextField(
        null=True,
        blank=True,
        help_text='Pharmacist\'s clinical notes and recommendations'
    )
    escalation_reason = models.TextField(
        null=True,
        blank=True,
        help_text='Reason for escalating to physician (if escalated)'
    )
    clinical_concerns = models.TextField(
        null=True,
        blank=True,
        help_text='Specific clinical concerns identified by pharmacist'
    )
    drug_interactions_checked = models.TextField(
        null=True,
        blank=True,
        help_text='Results of drug interaction check'
    )
    monitoring_requirements = models.TextField(
        null=True,
        blank=True,
        help_text='Required monitoring (e.g., lab tests, blood pressure checks)'
    )
    pharmacist_recommendation = models.TextField(
        null=True,
        blank=True,
        help_text='Pharmacist\'s recommendation to the physician'
    )

    # Pharmacist Performance Tracking
    pharmacist_review_time_minutes = models.FloatField(
        null=True,
        blank=True,
        help_text='Time taken by pharmacist to review (in minutes)'
    )
    had_clinical_intervention = models.BooleanField(
        default=False,
        help_text='Whether pharmacist made a clinical intervention (dosage adjustment, drug interaction warning, etc.)'
    )

    # Additional Information
    additional_notes = models.TextField(
        null=True,
        blank=True,
        help_text='Patient\'s additional notes about the request'
    )
    pharmacy = models.ForeignKey(
        'Pharmacy',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='prescription_requests',
        help_text='Nominated pharmacy for collection'
    )

    # Metadata
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text='When the record was created'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text='When the record was last updated'
    )

    class Meta:
        db_table = 'prescription_requests'
        ordering = ['-urgency', '-request_date']  # Urgent first, then newest
        indexes = [
            models.Index(fields=['-request_date'], name='idx_pr_req_date'),
            models.Index(fields=['status', '-request_date'], name='idx_pr_status_date'),
            models.Index(fields=['urgency', '-request_date'], name='idx_pr_urgency_date'),
            models.Index(fields=['hospital', '-request_date'], name='idx_pr_hospital_date'),
            models.Index(fields=['patient', '-request_date'], name='idx_pr_patient_date'),
            # Triage indexes
            models.Index(fields=['assigned_to_role', 'status', '-request_date'], name='idx_pr_role_status'),
            models.Index(fields=['triage_category', '-request_date'], name='idx_pr_triage_cat'),
            models.Index(fields=['assigned_to_pharmacist', 'status'], name='idx_pr_pharm_status'),
            models.Index(fields=['assigned_to_doctor', 'status'], name='idx_pr_doc_status'),
            models.Index(fields=['pharmacist_review_action', '-pharmacist_review_date'], name='idx_pr_pharm_review'),
        ]
        verbose_name = 'Prescription Request'
        verbose_name_plural = 'Prescription Requests'

    def __str__(self):
        patient_name = self.patient.get_full_name() if hasattr(self.patient, 'get_full_name') else str(self.patient)
        return f"{self.request_reference} - {patient_name} ({self.status})"

    @property
    def is_urgent(self):
        """Check if request is marked as urgent"""
        return self.urgency == 'urgent'

    @property
    def is_pending(self):
        """Check if request is still pending review"""
        return self.status == 'REQUESTED'

    @property
    def medication_count(self):
        """Get count of medications in this request"""
        return self.medications.count()

    @property
    def is_assigned_to_pharmacist(self):
        """Check if request is assigned to a pharmacist"""
        return self.assigned_to_role == 'pharmacist'

    @property
    def is_assigned_to_doctor(self):
        """Check if request is assigned to a doctor"""
        return self.assigned_to_role == 'doctor'

    @property
    def pharmacist_reviewed(self):
        """Check if pharmacist has reviewed this request"""
        return self.pharmacist_reviewed_by is not None

    @property
    def is_escalated(self):
        """Check if request has been escalated to physician"""
        return self.pharmacist_review_action == 'escalated'

    @property
    def is_pharmacist_approved(self):
        """Check if pharmacist approved this request"""
        return self.pharmacist_review_action == 'approved'

    @property
    def awaiting_pharmacist_review(self):
        """Check if request is awaiting pharmacist review"""
        return (
            self.assigned_to_role == 'pharmacist' and
            self.status == 'REQUESTED' and
            self.pharmacist_reviewed_by is None
        )

    @property
    def awaiting_physician_authorization(self):
        """Check if pharmacist approved and awaiting physician authorization"""
        return (
            self.pharmacist_review_action == 'approved' and
            self.status == 'REQUESTED' and
            self.reviewed_by is None
        )

    def assign_to_pharmacist(self, pharmacist, triage_category, triage_reason):
        """
        Assign request to a specific pharmacist for review

        Args:
            pharmacist: Pharmacist instance
            triage_category: Triage category (e.g., ROUTINE_REPEAT)
            triage_reason: Explanation for triage category
        """
        self.assigned_to_role = 'pharmacist'
        self.assigned_to_pharmacist = pharmacist
        self.triage_category = triage_category
        self.triage_reason = triage_reason
        self.save(update_fields=[
            'assigned_to_role', 'assigned_to_pharmacist',
            'triage_category', 'triage_reason', 'updated_at'
        ])

    def assign_to_doctor(self, doctor, triage_category, triage_reason):
        """
        Assign request directly to a doctor (bypassing pharmacist triage)

        Args:
            doctor: Doctor instance
            triage_category: Triage category (e.g., SPECIALIST_REQUIRED)
            triage_reason: Explanation for direct doctor assignment
        """
        self.assigned_to_role = 'doctor'
        self.assigned_to_doctor = doctor
        self.triage_category = triage_category
        self.triage_reason = triage_reason
        self.save(update_fields=[
            'assigned_to_role', 'assigned_to_doctor',
            'triage_category', 'triage_reason', 'updated_at'
        ])


class PrescriptionRequestItem(models.Model):
    """
    Individual medication item within a prescription request.

    Each request can contain multiple medications.
    Stores both the requested details and the approved details
    (which may differ if doctor adjusts dosage/quantity).
    """

    # Link to request
    request = models.ForeignKey(
        PrescriptionRequest,
        on_delete=models.CASCADE,
        related_name='medications',
        help_text='Parent prescription request'
    )

    # Medication details (as requested by patient)
    medication_name = models.CharField(
        max_length=255,
        help_text='Name of the medication'
    )
    strength = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text='Strength/dosage (e.g., 500mg, 10ml)'
    )
    form = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text='Form (tablet, capsule, liquid, inhaler, etc.)'
    )
    quantity = models.IntegerField(
        default=0,
        help_text='Requested quantity'
    )
    dosage = models.TextField(
        null=True,
        blank=True,
        help_text='Requested dosage instructions'
    )
    is_repeat = models.BooleanField(
        default=False,
        help_text='Whether this is a repeat prescription'
    )
    reason = models.TextField(
        null=True,
        blank=True,
        help_text='Reason for request (required for new medications)'
    )

    # Approved details (filled in by doctor when approving)
    approved_quantity = models.IntegerField(
        null=True,
        blank=True,
        help_text='Doctor-approved quantity (may differ from requested)'
    )
    approved_dosage = models.TextField(
        null=True,
        blank=True,
        help_text='Doctor-approved dosage instructions'
    )
    refills_allowed = models.IntegerField(
        default=0,
        help_text='Number of refills allowed (0-11)'
    )

    # Metadata
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text='When the item was created'
    )

    class Meta:
        db_table = 'prescription_request_items'
        ordering = ['id']
        verbose_name = 'Prescription Request Item'
        verbose_name_plural = 'Prescription Request Items'

    def __str__(self):
        return f"{self.medication_name} for {self.request.request_reference}"

    @property
    def is_approved(self):
        """Check if this medication item has been approved"""
        return self.approved_quantity is not None and self.approved_dosage is not None
