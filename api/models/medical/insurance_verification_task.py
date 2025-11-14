from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth import get_user_model
import json

class InsuranceVerificationTask(models.Model):
    """
    Model for managing insurance verification tasks and workflows
    """
    TASK_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('requires_follow_up', 'Requires Follow-up')
    ]
    
    VERIFICATION_METHOD_CHOICES = [
        ('api', 'API Integration'),
        ('portal', 'Insurance Portal'),
        ('phone', 'Phone Call'),
        ('fax', 'Fax Verification'),
        ('email', 'Email Verification'),
        ('manual', 'Manual Process'),
        ('hybrid', 'Multiple Methods')
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ]
    
    VERIFICATION_TYPE_CHOICES = [
        ('eligibility', 'Eligibility Verification'),
        ('benefits', 'Benefits Verification'),
        ('preauth', 'Pre-authorization'),
        ('claims_status', 'Claims Status Check'),
        ('provider_enrollment', 'Provider Enrollment Verification'),
        ('policy_update', 'Policy Information Update')
    ]
    
    # Basic Information
    task_id = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique task identifier"
    )
    patient_policy = models.ForeignKey(
        'api.PatientInsurancePolicy',
        on_delete=models.CASCADE,
        related_name='verification_tasks'
    )
    verification_type = models.CharField(
        max_length=30,
        choices=VERIFICATION_TYPE_CHOICES,
        default='eligibility'
    )
    
    # Task Assignment and Scheduling
    assigned_to = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_verification_tasks',
        help_text="Staff member assigned to this task"
    )
    created_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.PROTECT,
        related_name='created_verification_tasks',
        help_text="User who created this task"
    )
    due_date = models.DateTimeField(
        help_text="When this task should be completed"
    )
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='normal'
    )
    
    # Task Status and Progress
    status = models.CharField(
        max_length=20,
        choices=TASK_STATUS_CHOICES,
        default='pending'
    )
    verification_method = models.CharField(
        max_length=20,
        choices=VERIFICATION_METHOD_CHOICES,
        default='manual'
    )
    attempts_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of verification attempts made"
    )
    max_attempts = models.PositiveIntegerField(
        default=3,
        help_text="Maximum number of attempts before escalation"
    )
    
    # Task Details
    verification_purpose = models.TextField(
        blank=True,
        help_text="Purpose or reason for verification"
    )
    service_details = models.JSONField(
        default=dict,
        help_text="Details about services being verified"
    )
    special_instructions = models.TextField(
        blank=True,
        help_text="Special instructions for verification"
    )
    
    # Contact Information
    insurance_contact_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Name of insurance contact person"
    )
    insurance_contact_phone = models.CharField(
        max_length=20,
        blank=True,
        help_text="Phone number for verification"
    )
    insurance_contact_email = models.EmailField(
        blank=True,
        help_text="Email for verification"
    )
    reference_number = models.CharField(
        max_length=100,
        blank=True,
        help_text="Reference number from insurance company"
    )
    
    # Results and Documentation
    verification_result = models.JSONField(
        default=dict,
        help_text="Structured verification results"
    )
    verification_notes = models.TextField(
        blank=True,
        help_text="Detailed notes from verification process"
    )
    verification_documents = models.JSONField(
        default=list,
        help_text="List of documents uploaded during verification"
    )
    
    # Encrypted Sensitive Data
    _encrypted_verification_response = models.BinaryField(
        null=True,
        blank=True,
        editable=False,
        help_text="Encrypted raw verification response"
    )
    
    # Follow-up and Escalation
    follow_up_required = models.BooleanField(
        default=False,
        help_text="Whether follow-up is required"
    )
    follow_up_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When to follow up"
    )
    escalated_to = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='escalated_verification_tasks',
        help_text="User task was escalated to"
    )
    escalation_reason = models.TextField(
        blank=True,
        help_text="Reason for escalation"
    )
    
    # Performance Tracking
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When verification was started"
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When verification was completed"
    )
    total_time_spent = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Total time spent in minutes"
    )
    
    # Integration and Automation
    api_call_log = models.JSONField(
        default=list,
        help_text="Log of API calls made for this verification"
    )
    automation_attempted = models.BooleanField(
        default=False,
        help_text="Whether automation was attempted first"
    )
    automation_failure_reason = models.TextField(
        blank=True,
        help_text="Why automation failed (if applicable)"
    )
    
    # Quality Assurance
    reviewed_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_verification_tasks',
        help_text="Supervisor who reviewed this task"
    )
    quality_score = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Quality score (1-10) for verification"
    )
    quality_notes = models.TextField(
        blank=True,
        help_text="Quality review notes"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-priority', 'due_date', '-created_at']
        indexes = [
            models.Index(fields=['task_id']),
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['assigned_to', 'status']),
            models.Index(fields=['due_date']),
            models.Index(fields=['verification_type']),
            models.Index(fields=['patient_policy']),
        ]
        permissions = [
            ("can_assign_verification_tasks", "Can assign verification tasks"),
            ("can_view_verification_results", "Can view verification results"),
            ("can_escalate_tasks", "Can escalate verification tasks"),
            ("can_review_quality", "Can review verification quality"),
        ]

    def __str__(self):
        return f"Task {self.task_id} - {self.patient_policy.patient.get_full_name()} ({self.get_status_display()})"

    def clean(self):
        """Validate verification task"""
        super().clean()
        
        if self.follow_up_date and self.follow_up_date <= timezone.now():
            raise ValidationError(
                "Follow-up date must be in the future"
            )
        
        if self.completed_at and self.started_at and self.completed_at < self.started_at:
            raise ValidationError(
                "Completion time cannot be before start time"
            )
        
        if self.attempts_count > self.max_attempts and self.status not in ['completed', 'cancelled', 'failed']:
            raise ValidationError(
                "Maximum attempts exceeded - task should be escalated or failed"
            )

    def save(self, *args, **kwargs):
        # Generate task ID if not provided
        if not self.task_id:
            self.task_id = self.generate_task_id()
        
        # Set started_at when status changes to in_progress
        if self.status == 'in_progress' and not self.started_at:
            self.started_at = timezone.now()
        
        # Set completed_at and calculate time when status changes to completed
        if self.status == 'completed' and not self.completed_at:
            self.completed_at = timezone.now()
            if self.started_at:
                duration = self.completed_at - self.started_at
                self.total_time_spent = int(duration.total_seconds() // 60)
        
        self.clean()
        super().save(*args, **kwargs)

    @property
    def verification_response(self):
        """Decrypt and return verification response"""
        if self._encrypted_verification_response:
            try:
                from django.core.signing import Signer
                signer = Signer(salt='verification_response')
                return json.loads(signer.unsign(self._encrypted_verification_response.decode()))
            except Exception:
                return {}
        return {}

    @verification_response.setter
    def verification_response(self, data):
        """Encrypt and store verification response"""
        if data:
            try:
                from django.core.signing import Signer
                signer = Signer(salt='verification_response')
                self._encrypted_verification_response = signer.sign(json.dumps(data)).encode()
            except Exception:
                pass

    def generate_task_id(self):
        """Generate unique task ID"""
        import uuid
        from datetime import datetime
        
        date_str = datetime.now().strftime("%Y%m%d")
        unique_str = uuid.uuid4().hex[:8].upper()
        return f"VER-{date_str}-{unique_str}"

    @property
    def is_overdue(self):
        """Check if task is overdue"""
        return timezone.now() > self.due_date and self.status not in ['completed', 'cancelled']

    @property
    def time_until_due(self):
        """Calculate time until due date"""
        if self.is_overdue:
            return None
        delta = self.due_date - timezone.now()
        return delta

    @property
    def should_escalate(self):
        """Check if task should be escalated"""
        return (
            self.attempts_count >= self.max_attempts or
            self.is_overdue or
            self.status == 'requires_follow_up'
        )

    def start_verification(self, user=None):
        """Start the verification process"""
        if self.status != 'pending':
            raise ValidationError("Task must be in pending status to start")
        
        self.status = 'in_progress'
        self.started_at = timezone.now()
        if user:
            self.assigned_to = user
        
        self.save()

    def complete_verification(self, result_data, notes=None, user=None):
        """Complete the verification with results"""
        if self.status != 'in_progress':
            raise ValidationError("Task must be in progress to complete")
        
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.verification_result = result_data
        
        if notes:
            self.verification_notes = notes
        
        # Update patient policy with verification results
        if 'eligibility_confirmed' in result_data:
            self.patient_policy.mark_verification_completed(
                verification_response=result_data,
                success=result_data.get('eligibility_confirmed', False)
            )
        
        self.save()

    def fail_verification(self, reason, user=None):
        """Mark verification as failed"""
        self.status = 'failed'
        self.verification_notes = f"Failed: {reason}"
        
        # Update patient policy verification status
        self.patient_policy.mark_verification_completed(
            verification_response={'failed': True, 'reason': reason},
            success=False
        )
        
        self.save()

    def escalate_task(self, escalated_to_user, reason, user=None):
        """Escalate task to another user"""
        self.escalated_to = escalated_to_user
        self.escalation_reason = reason
        self.assigned_to = escalated_to_user
        self.priority = 'high'  # Escalated tasks get high priority
        
        if self.status == 'pending':
            self.status = 'requires_follow_up'
        
        self.save()

    def add_attempt(self, method=None, notes=None, success=False):
        """Record a verification attempt"""
        self.attempts_count += 1
        
        if method:
            self.verification_method = method
        
        if notes:
            current_notes = self.verification_notes or ""
            timestamp = timezone.now().strftime("%Y-%m-%d %H:%M")
            self.verification_notes = f"{current_notes}\n[{timestamp}] Attempt {self.attempts_count}: {notes}"
        
        # Check if maximum attempts reached
        if self.attempts_count >= self.max_attempts and not success:
            self.status = 'requires_follow_up'
            self.follow_up_required = True
        
        self.save()

    def schedule_follow_up(self, follow_up_date, reason=None):
        """Schedule a follow-up for this task"""
        self.follow_up_required = True
        self.follow_up_date = follow_up_date
        self.status = 'requires_follow_up'
        
        if reason:
            self.special_instructions = f"{self.special_instructions}\nFollow-up scheduled: {reason}"
        
        self.save()

    def log_api_call(self, api_endpoint, request_data, response_data, success=True):
        """Log an API call attempt"""
        log_entry = {
            'timestamp': timezone.now().isoformat(),
            'endpoint': api_endpoint,
            'success': success,
            'response_status': response_data.get('status_code') if isinstance(response_data, dict) else None
        }
        
        # Don't log sensitive request/response data, just metadata
        if not success:
            log_entry['error'] = str(response_data)[:200]  # Truncate error messages
        
        self.api_call_log.append(log_entry)
        self.automation_attempted = True
        
        if not success:
            self.automation_failure_reason = str(response_data)[:500]
        
        self.save()

    def set_quality_review(self, score, notes, reviewed_by_user):
        """Set quality review for completed task"""
        if self.status != 'completed':
            raise ValidationError("Can only review completed tasks")
        
        self.quality_score = score
        self.quality_notes = notes
        self.reviewed_by = reviewed_by_user
        self.save()

    def get_task_summary(self):
        """Get task summary for display"""
        return {
            'task_id': self.task_id,
            'patient': self.patient_policy.patient.get_full_name(),
            'insurance_provider': self.patient_policy.insurance_provider.name,
            'verification_type': self.get_verification_type_display(),
            'status': self.get_status_display(),
            'priority': self.get_priority_display(),
            'assigned_to': self.assigned_to.get_full_name() if self.assigned_to else None,
            'due_date': self.due_date,
            'is_overdue': self.is_overdue,
            'attempts_count': self.attempts_count,
            'should_escalate': self.should_escalate,
            'time_spent': self.total_time_spent
        }

    @classmethod
    def create_verification_task(cls, patient_policy, verification_type='eligibility', 
                               assigned_to=None, priority='normal', due_hours=24):
        """Create a new verification task"""
        from datetime import timedelta
        
        due_date = timezone.now() + timedelta(hours=due_hours)
        
        task = cls.objects.create(
            patient_policy=patient_policy,
            verification_type=verification_type,
            assigned_to=assigned_to,
            priority=priority,
            due_date=due_date,
            verification_purpose=f"Verify {verification_type} for {patient_policy.patient.get_full_name()}"
        )
        
        return task

    @classmethod
    def get_pending_tasks(cls, assigned_to_user=None):
        """Get pending verification tasks"""
        queryset = cls.objects.filter(status='pending')
        
        if assigned_to_user:
            queryset = queryset.filter(assigned_to=assigned_to_user)
        
        return queryset.order_by('priority', 'due_date')

    @classmethod
    def get_overdue_tasks(cls):
        """Get overdue verification tasks"""
        return cls.objects.filter(
            due_date__lt=timezone.now(),
            status__in=['pending', 'in_progress', 'requires_follow_up']
        ).order_by('due_date')

    @classmethod
    def get_escalation_candidates(cls):
        """Get tasks that should be escalated"""
        return cls.objects.filter(
            models.Q(attempts_count__gte=models.F('max_attempts')) |
            models.Q(due_date__lt=timezone.now()) |
            models.Q(status='requires_follow_up'),
            status__in=['pending', 'in_progress', 'requires_follow_up']
        ).order_by('-priority', 'due_date')

    @classmethod
    def get_performance_metrics(cls, date_from=None, date_to=None, user=None):
        """Get performance metrics for verification tasks"""
        queryset = cls.objects.filter(status='completed')
        
        if date_from:
            queryset = queryset.filter(completed_at__gte=date_from)
        if date_to:
            queryset = queryset.filter(completed_at__lte=date_to)
        if user:
            queryset = queryset.filter(assigned_to=user)
        
        from django.db.models import Avg, Count
        
        return queryset.aggregate(
            total_completed=Count('id'),
            avg_completion_time=Avg('total_time_spent'),
            avg_attempts=Avg('attempts_count'),
            avg_quality_score=Avg('quality_score')
        )