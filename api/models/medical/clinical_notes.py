# api/models/medical/clinical_notes.py

from django.db import models
from django.utils import timezone
from ..base import TimestampedModel
from .medical_record import MedicalRecord


class ClinicalNote(TimestampedModel):
    """
    Model for storing detailed clinical notes and documentation
    with support for different note types and structured data
    """
    # Relationships
    medical_record = models.ForeignKey(
        MedicalRecord,
        on_delete=models.CASCADE,
        related_name='clinical_notes',
        help_text="Medical record this note belongs to"
    )
    
    # Author Information
    author = models.ForeignKey(
        'api.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        related_name='authored_notes',
        help_text="Healthcare provider who authored the note"
    )
    author_role = models.CharField(
        max_length=100,
        help_text="Role of the author (e.g., 'Physician', 'Nurse')"
    )
    
    # Note Metadata
    NOTE_TYPE_CHOICES = [
        # Visit Notes
        ('progress', 'Progress Note'),
        ('admission', 'Admission Note'),
        ('discharge', 'Discharge Summary'),
        ('consultation', 'Consultation Note'),
        ('procedure', 'Procedure Note'),
        ('operative', 'Operative Report'),
        ('emergency', 'Emergency Department Note'),
        
        # Specialized Notes
        ('history_physical', 'History and Physical'),
        ('soap', 'SOAP Note'),
        ('nursing', 'Nursing Note'),
        ('medication', 'Medication Note'),
        ('therapy', 'Therapy Note'),
        ('social_work', 'Social Work Note'),
        ('nutrition', 'Nutrition Note'),
        ('mental_health', 'Mental Health Note'),
        
        # Administrative
        ('phone', 'Phone Communication'),
        ('referral', 'Referral Note'),
        ('transfer', 'Transfer Note'),
        
        # Other
        ('other', 'Other')
    ]
    
    note_type = models.CharField(
        max_length=50,
        choices=NOTE_TYPE_CHOICES,
        help_text="Type of clinical note"
    )
    
    note_date = models.DateTimeField(
        help_text="Date and time of the note"
    )
    
    visit_date = models.DateField(
        blank=True,
        null=True,
        help_text="Date of associated visit or encounter"
    )
    
    # Note Content
    title = models.CharField(
        max_length=255,
        help_text="Title of the note"
    )
    
    content = models.TextField(
        help_text="Full text content of the note"
    )
    
    # Structured Data
    SECTION_CHOICES = [
        ('subjective', 'Subjective'),
        ('objective', 'Objective'),
        ('assessment', 'Assessment'),
        ('plan', 'Plan'),
        ('history', 'History'),
        ('physical_exam', 'Physical Examination'),
        ('lab_results', 'Laboratory Results'),
        ('imaging', 'Imaging Results'),
        ('medications', 'Medications'),
        ('allergies', 'Allergies'),
        ('instructions', 'Instructions'),
        ('follow_up', 'Follow-up'),
        ('review_of_systems', 'Review of Systems'),
        ('family_history', 'Family History'),
        ('social_history', 'Social History'),
        ('chief_complaint', 'Chief Complaint'),
        ('hpi', 'History of Present Illness'),
        ('diagnosis', 'Diagnosis'),
        ('procedure_details', 'Procedure Details'),
        ('vital_signs', 'Vital Signs'),
    ]
    
    structured_content = models.JSONField(
        default=dict,
        blank=True,
        null=True,
        help_text="Structured content organized by sections"
    )
    
    # Clinical Context
    encounter_type = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Type of encounter (e.g., 'Office Visit', 'Telemedicine')"
    )
    
    location = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Location where care was provided"
    )
    
    chief_complaint = models.TextField(
        blank=True,
        null=True,
        help_text="Patient's chief complaint"
    )
    
    # Diagnoses and Problems
    diagnoses = models.JSONField(
        default=list,
        blank=True,
        null=True,
        help_text="List of diagnoses addressed in this note"
    )
    
    # Document Status
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('preliminary', 'Preliminary'),
        ('final', 'Final'),
        ('amended', 'Amended'),
        ('deleted', 'Deleted')
    ]
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        help_text="Status of the clinical note"
    )
    
    # Versioning
    version = models.IntegerField(
        default=1,
        help_text="Version number of the note"
    )
    
    previous_version = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='next_versions',
        help_text="Reference to previous version of this note"
    )
    
    amendment_reason = models.TextField(
        blank=True,
        null=True,
        help_text="Reason for amendment if this is an amended note"
    )
    
    # Accessibility and Sharing
    is_private = models.BooleanField(
        default=False,
        help_text="Whether note contains sensitive information with restricted access"
    )
    
    # NLP and AI
    nlp_processed = models.BooleanField(
        default=False,
        help_text="Whether natural language processing has been applied"
    )
    
    nlp_entities = models.JSONField(
        default=list,
        blank=True,
        null=True,
        help_text="Entities extracted through NLP"
    )
    
    nlp_concepts = models.JSONField(
        default=list,
        blank=True,
        null=True,
        help_text="Medical concepts identified through NLP"
    )
    
    # Signatures and Verification
    signed = models.BooleanField(
        default=False,
        help_text="Whether the note has been signed"
    )
    
    signed_by = models.ForeignKey(
        'api.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='signed_notes',
        help_text="Provider who signed the note"
    )
    
    signed_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Date and time the note was signed"
    )
    
    cosigned_by = models.ForeignKey(
        'api.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cosigned_notes',
        help_text="Provider who cosigned the note"
    )
    
    cosigned_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Date and time the note was cosigned"
    )
    
    class Meta:
        verbose_name = "Clinical Note"
        verbose_name_plural = "Clinical Notes"
        ordering = ['-note_date']
        indexes = [
            models.Index(fields=['medical_record', 'note_date']),
            models.Index(fields=['note_type']),
            models.Index(fields=['author']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.get_note_type_display()} for {self.medical_record.hpn} on {self.note_date.strftime('%Y-%m-%d')}"
    
    def save(self, *args, **kwargs):
        # Set visit date to note date if not provided
        if not self.visit_date and self.note_date:
            self.visit_date = self.note_date.date()
            
        # Check if this is a new note being created
        is_new = self._state.adding
            
        # Save the note
        super().save(*args, **kwargs)
        
        # Send notification if this is a new note and not a draft
        if is_new and self.status != 'draft' and hasattr(self.medical_record, 'user') and self.medical_record.user:
            try:
                from api.models.notifications.notification import Notification
                
                # Create notification for the patient
                Notification.objects.create(
                    notification_type='in_app',
                    title='New Clinical Note Added',
                    message=f'A new clinical note has been added to your medical record by {self.author.get_full_name()}.',
                    user=self.medical_record.user,
                    related_object_type='clinical_note',
                    related_object_id=self.id
                )
            except Exception as e:
                # Log error but don't prevent note creation
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to send clinical note notification: {e}")
                
        # Send notification if note is being shared
        if self.status == 'shared' and hasattr(self.medical_record, 'user') and self.medical_record.user:
            try:
                from api.models.notifications.notification import Notification
                
                # Create notification for the patient
                Notification.objects.create(
                    notification_type='in_app',
                    title='Clinical Note Shared With You',
                    message=f'A clinical note has been shared with you by {self.author.get_full_name()}.',
                    user=self.medical_record.user,
                    related_object_type='clinical_note',
                    related_object_id=self.id
                )
            except Exception as e:
                # Log error but don't prevent note update
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to send clinical note sharing notification: {e}")
                
        # Send notification if note is being finalized
        if self.status == 'finalized' and hasattr(self.medical_record, 'user') and self.medical_record.user:
            try:
                from api.models.notifications.notification import Notification
                
                # Create notification for the patient
                Notification.objects.create(
                    notification_type='in_app',
                    title='Clinical Note Finalized',
                    message=f'A clinical note about your visit has been finalized by {self.author.get_full_name()}.',
                    user=self.medical_record.user,
                    related_object_type='clinical_note',
                    related_object_id=self.id
                )
            except Exception as e:
                # Log error but don't prevent note update
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to send clinical note finalization notification: {e}")
        
        return super().save(*args, **kwargs)
    
    def sign(self, user, cosigner=None):
        """
        Sign the note
        
        Args:
            user: User signing the note
            cosigner: Optional cosigner
            
        Returns:
            True if signing was successful
        """
        if self.signed:
            return False
            
        self.signed = True
        self.signed_by = user
        self.signed_at = timezone.now()
        self.status = 'final'
        
        if cosigner:
            self.cosigned_by = cosigner
            self.cosigned_at = timezone.now()
            
        self.save()
        
        # Send notification to patient when note is signed and finalized
        if hasattr(self.medical_record, 'user') and self.medical_record.user:
            from api.models.notifications.in_app_notification import InAppNotification
            
            note_type_display = self.get_note_type_display()
            
            InAppNotification.create_notification(
                user=self.medical_record.user,
                title=f"{note_type_display} Finalized",
                message=f"Your {note_type_display.lower()} has been finalized and is ready for review.",
                notification_type="medical_record",
                reference_id=f"NOTE-{self.id}"
            )
        
        return True
    
    def amend(self, new_content, reason, user):
        """
        Create an amended version of this note
        
        Args:
            new_content: Updated content text
            reason: Reason for amendment
            user: User making the amendment
            
        Returns:
            New ClinicalNote object
        """
        # Create new version
        new_note = ClinicalNote.objects.create(
            medical_record=self.medical_record,
            author=user,
            author_role=user.role if hasattr(user, 'role') else "Unknown",
            note_type=self.note_type,
            note_date=timezone.now(),
            visit_date=self.visit_date,
            title=self.title,
            content=new_content,
            structured_content=self.structured_content,
            encounter_type=self.encounter_type,
            location=self.location,
            chief_complaint=self.chief_complaint,
            diagnoses=self.diagnoses,
            status='amended',
            version=self.version + 1,
            previous_version=self,
            amendment_reason=reason,
            is_private=self.is_private
        )
        
        # Notify patient about amended note
        if hasattr(self.medical_record, 'user') and self.medical_record.user:
            from api.models.notifications.in_app_notification import InAppNotification
            
            note_type_display = self.get_note_type_display()
            
            InAppNotification.create_notification(
                user=self.medical_record.user,
                title=f"{note_type_display} Updated",
                message=f"Your {note_type_display.lower()} has been updated with new information.",
                notification_type="medical_record",
                reference_id=f"NOTE-{new_note.id}"
            )
        
        return new_note
    
    def get_section(self, section_name):
        """
        Get content from a specific section of the note
        
        Args:
            section_name: Name of the section to retrieve
            
        Returns:
            Content of the requested section or None
        """
        if not self.structured_content:
            return None
            
        return self.structured_content.get(section_name)
    
    @property
    def is_finalized(self):
        """Check if note is in a final state"""
        return self.status in ['final', 'amended']
    
    @property
    def is_editable(self):
        """Check if note can be edited"""
        return self.status in ['draft', 'preliminary']
    
    @property
    def is_amended(self):
        """Check if note has been amended"""
        from django.db.models import Count
        return ClinicalNote.objects.filter(previous_version=self).count() > 0
    
    @property
    def word_count(self):
        """Count words in the note content"""
        if not self.content:
            return 0
        return len(self.content.split())


class HealthcareProviderNote(ClinicalNote):
    """
    Specialized clinical note for physicians and other providers
    with additional fields specific to provider documentation
    """
    # Additional provider-specific fields
    billing_code = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Billing or CPT code associated with this note"
    )
    
    complexity_level = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        choices=[
            ('low', 'Low Complexity'),
            ('moderate', 'Moderate Complexity'),
            ('high', 'High Complexity')
        ],
        help_text="Level of complexity for billing purposes"
    )
    
    time_spent = models.IntegerField(
        blank=True,
        null=True,
        help_text="Time spent with patient in minutes"
    )
    
    # Specialized sections
    assessment_and_plan = models.TextField(
        blank=True,
        null=True,
        help_text="Assessment and plan section"
    )
    
    physical_examination = models.TextField(
        blank=True,
        null=True,
        help_text="Physical examination findings"
    )
    
    medical_decision_making = models.TextField(
        blank=True,
        null=True,
        help_text="Medical decision making documentation"
    )
    
    # Procedure documentation
    procedures_performed = models.JSONField(
        default=list,
        blank=True,
        null=True,
        help_text="Procedures performed during visit"
    )
    
    class Meta:
        verbose_name = "Provider Note"
        verbose_name_plural = "Provider Notes"
        
    def save(self, *args, **kwargs):
        # Ensure note_type is appropriate for provider
        provider_note_types = ['progress', 'consultation', 'admission', 'discharge', 
                              'procedure', 'operative', 'history_physical', 'soap']
        
        if self.note_type not in provider_note_types:
            self.note_type = 'progress'  # Default to progress note
            
        super().save(*args, **kwargs)


class NursingNote(ClinicalNote):
    """
    Specialized clinical note for nursing documentation
    """
    # Nursing-specific fields
    nursing_assessment = models.TextField(
        blank=True,
        null=True,
        help_text="Nursing assessment"
    )
    
    interventions = models.TextField(
        blank=True,
        null=True,
        help_text="Nursing interventions performed"
    )
    
    patient_response = models.TextField(
        blank=True,
        null=True,
        help_text="Patient's response to interventions"
    )
    
    nursing_care_plan = models.TextField(
        blank=True,
        null=True,
        help_text="Nursing care plan"
    )
    
    # Specialized documentation
    intake_output = models.JSONField(
        default=dict,
        blank=True,
        null=True,
        help_text="Intake and output measurements"
    )
    
    adl_status = models.TextField(
        blank=True,
        null=True,
        help_text="Activities of daily living status"
    )
    
    class Meta:
        verbose_name = "Nursing Note"
        verbose_name_plural = "Nursing Notes"
        
    def save(self, *args, **kwargs):
        # Always set note_type to nursing
        self.note_type = 'nursing'
        super().save(*args, **kwargs) 