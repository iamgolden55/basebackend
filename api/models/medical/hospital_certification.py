from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal

class HospitalCertification(models.Model):
    """
    Model representing hospital's quality certifications and accreditations
    """
    CERTIFICATION_STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('suspended', 'Suspended'),
        ('revoked', 'Revoked'),
        ('pending', 'Pending Assessment'),
        ('under_review', 'Under Review'),
        ('provisional', 'Provisional'),
        ('denied', 'Denied')
    ]
    
    CERTIFICATION_LEVEL_CHOICES = [
        ('gold', 'Gold Standard'),
        ('silver', 'Silver Level'),
        ('bronze', 'Bronze Level'),
        ('platinum', 'Platinum Excellence'),
        ('advanced', 'Advanced Certification'),
        ('basic', 'Basic Certification'),
        ('conditional', 'Conditional Approval'),
        ('full', 'Full Accreditation'),
        ('partial', 'Partial Accreditation'),
        ('other', 'Other Level')
    ]
    
    ASSESSMENT_TYPE_CHOICES = [
        ('initial', 'Initial Assessment'),
        ('renewal', 'Renewal Assessment'),
        ('surveillance', 'Surveillance Assessment'),
        ('follow_up', 'Follow-up Assessment'),
        ('complaint_based', 'Complaint-Based Assessment'),
        ('voluntary', 'Voluntary Assessment'),
        ('mandated', 'Mandated Assessment')
    ]
    
    PUBLIC_DISPLAY_CHOICES = [
        ('public', 'Public Display Authorized'),
        ('restricted', 'Restricted Display'),
        ('internal', 'Internal Use Only'),
        ('confidential', 'Confidential')
    ]
    
    # Relationships
    hospital = models.ForeignKey(
        'api.Hospital',
        on_delete=models.CASCADE,
        related_name='certifications'
    )
    certification_body = models.ForeignKey(
        'api.CertificationBody',
        on_delete=models.PROTECT,
        related_name='hospital_certifications'
    )
    
    # Certification Information
    certification_number = models.CharField(
        max_length=100,
        help_text="Official certification number"
    )
    certification_name = models.CharField(
        max_length=200,
        help_text="Name of the certification program"
    )
    certification_standard = models.CharField(
        max_length=100,
        blank=True,
        help_text="Standard or framework used (e.g., ISO 9001, NABH)"
    )
    certification_scope = models.TextField(
        blank=True,
        help_text="Scope of certification (departments, services covered)"
    )
    
    # Status and Level
    certification_status = models.CharField(
        max_length=20,
        choices=CERTIFICATION_STATUS_CHOICES,
        default='active'
    )
    certification_level = models.CharField(
        max_length=20,
        choices=CERTIFICATION_LEVEL_CHOICES,
        blank=True,
        help_text="Level or grade of certification achieved"
    )
    assessment_type = models.CharField(
        max_length=20,
        choices=ASSESSMENT_TYPE_CHOICES,
        default='initial'
    )
    
    # Dates and Validity
    application_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date application was submitted"
    )
    assessment_start_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date assessment began"
    )
    assessment_completion_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date assessment was completed"
    )
    certificate_issue_date = models.DateField(
        help_text="Date certificate was issued"
    )
    certificate_expiry_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date certificate expires"
    )
    
    # Assessment Results
    overall_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Overall assessment score (0-100)"
    )
    compliance_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Compliance percentage achieved"
    )
    assessment_criteria_scores = models.JSONField(
        default=dict,
        help_text="Detailed scores for each assessment criteria"
    )
    strengths_identified = models.TextField(
        blank=True,
        help_text="Key strengths identified during assessment"
    )
    areas_for_improvement = models.TextField(
        blank=True,
        help_text="Areas identified for improvement"
    )
    
    # Conditions and Requirements
    certification_conditions = models.TextField(
        blank=True,
        help_text="Conditions attached to the certification"
    )
    corrective_actions_required = models.TextField(
        blank=True,
        help_text="Corrective actions required to maintain certification"
    )
    corrective_actions_deadline = models.DateField(
        null=True,
        blank=True,
        help_text="Deadline for completing corrective actions"
    )
    corrective_actions_completed = models.BooleanField(
        default=False,
        help_text="Whether corrective actions have been completed"
    )
    
    # Assessment Team and Process
    lead_assessor_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Name of lead assessor"
    )
    assessment_team_size = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Number of assessors in the team"
    )
    assessment_duration_days = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Duration of assessment in days"
    )
    on_site_assessment_days = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Number of days spent on-site"
    )
    
    # Renewal and Surveillance
    next_renewal_due = models.DateField(
        null=True,
        blank=True,
        help_text="Date when next renewal is due"
    )
    surveillance_assessments_required = models.BooleanField(
        default=False,
        help_text="Whether surveillance assessments are required"
    )
    next_surveillance_due = models.DateField(
        null=True,
        blank=True,
        help_text="Date when next surveillance assessment is due"
    )
    surveillance_frequency_months = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Frequency of surveillance assessments in months"
    )
    
    # Financial Information
    assessment_fee_paid = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Assessment fee paid"
    )
    certification_fee_paid = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Certification fee paid"
    )
    annual_maintenance_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Annual maintenance fee"
    )
    currency = models.CharField(
        max_length=3,
        default='USD',
        help_text="Currency for fees"
    )
    
    # Documentation and Evidence
    certificate_document = models.FileField(
        upload_to='certifications/certificates/',
        null=True,
        blank=True,
        help_text="Digital copy of certificate"
    )
    assessment_report = models.FileField(
        upload_to='certifications/reports/',
        null=True,
        blank=True,
        help_text="Assessment report document"
    )
    supporting_documents = models.JSONField(
        default=list,
        help_text="List of supporting documents"
    )
    evidence_provided = models.JSONField(
        default=list,
        help_text="List of evidence provided during assessment"
    )
    
    # Public Display and Marketing
    public_display_permission = models.CharField(
        max_length=20,
        choices=PUBLIC_DISPLAY_CHOICES,
        default='public'
    )
    display_on_website = models.BooleanField(
        default=True,
        help_text="Whether to display on hospital website"
    )
    marketing_materials_approved = models.BooleanField(
        default=False,
        help_text="Whether marketing materials have been approved"
    )
    logo_usage_approved = models.BooleanField(
        default=False,
        help_text="Whether certification body logo usage is approved"
    )
    
    # Verification and Monitoring
    verification_url = models.URLField(
        blank=True,
        help_text="URL to verify certification online"
    )
    public_verification_code = models.CharField(
        max_length=50,
        blank=True,
        help_text="Public verification code"
    )
    last_verified = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last time certification was verified"
    )
    auto_verification_enabled = models.BooleanField(
        default=False,
        help_text="Whether automatic verification is enabled"
    )
    
    # Performance and Impact
    patient_satisfaction_improvement = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Patient satisfaction improvement percentage"
    )
    quality_metrics_improvement = models.JSONField(
        default=dict,
        help_text="Improvement in various quality metrics"
    )
    staff_engagement_improvement = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Staff engagement improvement percentage"
    )
    operational_efficiency_improvement = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Operational efficiency improvement percentage"
    )
    
    # Awards and Recognition
    awards_received = models.JSONField(
        default=list,
        help_text="Awards received related to this certification"
    )
    peer_recognition = models.TextField(
        blank=True,
        help_text="Recognition from peer organizations"
    )
    media_coverage = models.JSONField(
        default=list,
        help_text="Media coverage of certification achievement"
    )
    
    # History and Tracking
    previous_certification_number = models.CharField(
        max_length=100,
        blank=True,
        help_text="Previous certification number (if renewed)"
    )
    certification_history = models.JSONField(
        default=list,
        help_text="History of certification changes"
    )
    assessment_history = models.JSONField(
        default=list,
        help_text="History of assessments conducted"
    )
    
    # Alerts and Notifications
    expiry_alert_sent = models.BooleanField(
        default=False,
        help_text="Whether expiry alert has been sent"
    )
    renewal_alert_sent = models.BooleanField(
        default=False,
        help_text="Whether renewal alert has been sent"
    )
    surveillance_alert_sent = models.BooleanField(
        default=False,
        help_text="Whether surveillance alert has been sent"
    )
    
    # Additional Information
    is_transferable = models.BooleanField(
        default=False,
        help_text="Whether certification can be transferred"
    )
    requires_continuous_compliance = models.BooleanField(
        default=True,
        help_text="Whether continuous compliance monitoring is required"
    )
    patient_impact_documented = models.BooleanField(
        default=False,
        help_text="Whether patient impact has been documented"
    )
    
    # Status Tracking
    is_active = models.BooleanField(
        default=True,
        help_text="Whether certification record is active"
    )
    notes = models.TextField(
        blank=True,
        help_text="Additional notes about the certification"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'api.CustomUser',
        on_delete=models.PROTECT,
        related_name='created_hospital_certifications',
        null=True,
        blank=True
    )
    last_modified_by = models.ForeignKey(
        'api.CustomUser',
        on_delete=models.PROTECT,
        related_name='modified_hospital_certifications',
        null=True,
        blank=True
    )

    class Meta:
        unique_together = [['hospital', 'certification_number', 'certification_body']]
        ordering = ['-certificate_issue_date', 'certification_name']
        indexes = [
            models.Index(fields=['hospital', 'certification_status']),
            models.Index(fields=['certification_number']),
            models.Index(fields=['certification_body']),
            models.Index(fields=['certificate_expiry_date']),
            models.Index(fields=['next_renewal_due']),
            models.Index(fields=['next_surveillance_due']),
            models.Index(fields=['public_display_permission']),
        ]
        permissions = [
            ("can_manage_certifications", "Can manage hospital certifications"),
            ("can_view_certification_details", "Can view certification details"),
            ("can_verify_certifications", "Can verify certification status"),
            ("can_update_assessment_scores", "Can update assessment scores"),
        ]

    def __str__(self):
        return f"{self.hospital.name} - {self.certification_name} ({self.certification_status})"

    def clean(self):
        """Validate hospital certification data"""
        super().clean()
        
        if self.certificate_expiry_date and self.certificate_issue_date > self.certificate_expiry_date:
            raise ValidationError(
                "Certificate issue date must be before expiry date"
            )
        
        if self.assessment_completion_date and self.assessment_start_date:
            if self.assessment_start_date > self.assessment_completion_date:
                raise ValidationError(
                    "Assessment start date must be before completion date"
                )
        
        if self.corrective_actions_deadline and self.certificate_issue_date:
            if self.corrective_actions_deadline < self.certificate_issue_date:
                raise ValidationError(
                    "Corrective actions deadline cannot be before certificate issue date"
                )
        
        # Validate scores are within range
        score_fields = ['overall_score', 'compliance_percentage']
        for field_name in score_fields:
            value = getattr(self, field_name)
            if value is not None and (value < 0 or value > 100):
                raise ValidationError(
                    f"{field_name} must be between 0 and 100"
                )

    def save(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        
        if not self.pk and user:
            self.created_by = user
        if user:
            self.last_modified_by = user
        
        # Add to certification history if this is an update
        if self.pk:
            old_cert = HospitalCertification.objects.get(pk=self.pk)
            if old_cert.certification_status != self.certification_status:
                self.add_to_history('status_change', {
                    'from': old_cert.certification_status,
                    'to': self.certification_status,
                    'date': timezone.now().isoformat()
                })
        
        self.clean()
        super().save(*args, **kwargs)

    @property
    def is_expiring_soon(self):
        """Check if certification is expiring within 90 days"""
        if not self.certificate_expiry_date:
            return False
            
        from datetime import timedelta
        warning_date = timezone.now().date() + timedelta(days=90)
        return self.certificate_expiry_date <= warning_date

    @property
    def is_expired(self):
        """Check if certification is expired"""
        if not self.certificate_expiry_date:
            return False
        return timezone.now().date() > self.certificate_expiry_date

    @property
    def is_renewal_due(self):
        """Check if renewal is due"""
        if not self.next_renewal_due:
            return False
        return timezone.now().date() >= self.next_renewal_due

    @property
    def is_surveillance_due(self):
        """Check if surveillance assessment is due"""
        if not self.next_surveillance_due:
            return False
        return timezone.now().date() >= self.next_surveillance_due

    @property
    def days_until_expiry(self):
        """Calculate days until certification expires"""
        if not self.certificate_expiry_date:
            return None
        
        delta = self.certificate_expiry_date - timezone.now().date()
        return delta.days if delta.days >= 0 else 0

    @property
    def days_until_renewal(self):
        """Calculate days until renewal is due"""
        if not self.next_renewal_due:
            return None
        
        delta = self.next_renewal_due - timezone.now().date()
        return delta.days

    @property
    def certification_age_days(self):
        """Calculate age of certification in days"""
        delta = timezone.now().date() - self.certificate_issue_date
        return delta.days

    def mark_as_renewed(self, new_expiry_date, new_certification_number=None, 
                       new_score=None, user=None):
        """Mark certification as renewed"""
        # Store previous information
        if new_certification_number and new_certification_number != self.certification_number:
            self.previous_certification_number = self.certification_number
            self.certification_number = new_certification_number
        
        if new_expiry_date:
            self.certificate_expiry_date = new_expiry_date
            
            # Calculate next renewal due date (typically 6 months before expiry)
            from dateutil.relativedelta import relativedelta
            self.next_renewal_due = new_expiry_date - relativedelta(months=6)
        
        if new_score:
            self.overall_score = new_score
        
        self.certification_status = 'active'
        self.assessment_type = 'renewal'
        self.renewal_alert_sent = False
        
        self.add_to_history('renewal', {
            'renewal_date': timezone.now().date().isoformat(),
            'new_expiry': new_expiry_date.isoformat() if new_expiry_date else None,
            'new_score': new_score,
            'renewed_by': user.get_full_name() if user else 'System'
        })
        
        self.save()

    def mark_as_expired(self, user=None):
        """Mark certification as expired"""
        self.certification_status = 'expired'
        
        self.add_to_history('expiration', {
            'expired_date': timezone.now().date().isoformat(),
            'marked_by': user.get_full_name() if user else 'System'
        })
        
        self.save()

    def suspend_certification(self, reason, suspended_until=None, user=None):
        """Suspend the certification"""
        self.certification_status = 'suspended'
        
        suspension_info = {
            'suspension_date': timezone.now().date().isoformat(),
            'reason': reason,
            'suspended_by': user.get_full_name() if user else 'System'
        }
        
        if suspended_until:
            suspension_info['suspended_until'] = suspended_until.isoformat()
        
        self.add_to_history('suspension', suspension_info)
        self.save()

    def reinstate_certification(self, user=None):
        """Reinstate a suspended certification"""
        if self.certification_status != 'suspended':
            raise ValidationError("Only suspended certifications can be reinstated")
        
        self.certification_status = 'active'
        
        self.add_to_history('reinstatement', {
            'reinstatement_date': timezone.now().date().isoformat(),
            'reinstated_by': user.get_full_name() if user else 'System'
        })
        
        self.save()

    def record_assessment(self, assessment_date, overall_score=None, 
                         compliance_percentage=None, assessor_name=None, 
                         assessment_notes=None, user=None):
        """Record an assessment"""
        if overall_score:
            self.overall_score = overall_score
        
        if compliance_percentage:
            self.compliance_percentage = compliance_percentage
        
        if assessor_name:
            self.lead_assessor_name = assessor_name
        
        assessment_info = {
            'assessment_date': assessment_date.isoformat(),
            'overall_score': overall_score,
            'compliance_percentage': compliance_percentage,
            'assessor': assessor_name or 'Unknown',
            'assessment_type': self.assessment_type,
            'notes': assessment_notes
        }
        
        self.add_to_assessment_history(assessment_info)
        self.save()

    def complete_corrective_actions(self, completion_notes=None, user=None):
        """Mark corrective actions as completed"""
        self.corrective_actions_completed = True
        
        completion_info = {
            'completion_date': timezone.now().date().isoformat(),
            'completed_by': user.get_full_name() if user else 'System',
            'notes': completion_notes
        }
        
        self.add_to_history('corrective_actions_completed', completion_info)
        self.save()

    def schedule_surveillance(self, surveillance_date, user=None):
        """Schedule next surveillance assessment"""
        self.next_surveillance_due = surveillance_date
        self.surveillance_alert_sent = False
        
        self.add_to_history('surveillance_scheduled', {
            'scheduled_date': surveillance_date.isoformat(),
            'scheduled_by': user.get_full_name() if user else 'System'
        })
        
        self.save()

    def add_to_history(self, event_type, event_data):
        """Add an event to certification history"""
        if not isinstance(self.certification_history, list):
            self.certification_history = []
        
        history_entry = {
            'event_type': event_type,
            'timestamp': timezone.now().isoformat(),
            'data': event_data
        }
        
        self.certification_history.append(history_entry)

    def add_to_assessment_history(self, assessment_data):
        """Add an assessment to assessment history"""
        if not isinstance(self.assessment_history, list):
            self.assessment_history = []
        
        self.assessment_history.append(assessment_data)

    def add_award(self, award_name, award_date, awarding_body, description=None):
        """Add an award related to this certification"""
        if not isinstance(self.awards_received, list):
            self.awards_received = []
        
        award = {
            'name': award_name,
            'date': award_date.isoformat() if hasattr(award_date, 'isoformat') else award_date,
            'awarding_body': awarding_body,
            'description': description,
            'added_on': timezone.now().isoformat()
        }
        
        self.awards_received.append(award)
        self.save()

    def update_quality_metrics(self, patient_satisfaction=None, staff_engagement=None, 
                             operational_efficiency=None, custom_metrics=None):
        """Update quality improvement metrics"""
        if patient_satisfaction:
            self.patient_satisfaction_improvement = patient_satisfaction
        
        if staff_engagement:
            self.staff_engagement_improvement = staff_engagement
        
        if operational_efficiency:
            self.operational_efficiency_improvement = operational_efficiency
        
        if custom_metrics:
            if not isinstance(self.quality_metrics_improvement, dict):
                self.quality_metrics_improvement = {}
            self.quality_metrics_improvement.update(custom_metrics)
        
        self.save()

    def verify_certification_online(self):
        """Attempt to verify certification online if verification URL is available"""
        if not self.verification_url:
            return {'success': False, 'message': 'No verification URL available'}
        
        try:
            import requests
            response = requests.get(
                self.verification_url,
                params={'certification_number': self.certification_number},
                timeout=30
            )
            
            if response.status_code == 200:
                self.last_verified = timezone.now()
                self.save()
                return {'success': True, 'message': 'Certification verified successfully'}
            else:
                return {'success': False, 'message': f'Verification failed: {response.status_code}'}
        
        except Exception as e:
            return {'success': False, 'message': f'Verification error: {str(e)}'}

    def get_certification_summary(self):
        """Get certification summary for display"""
        return {
            'certification_number': self.certification_number,
            'certification_name': self.certification_name,
            'certification_body': self.certification_body.name,
            'status': self.get_certification_status_display(),
            'level': self.get_certification_level_display() if self.certification_level else None,
            'issue_date': self.certificate_issue_date,
            'expiry_date': self.certificate_expiry_date,
            'days_until_expiry': self.days_until_expiry,
            'is_expiring_soon': self.is_expiring_soon,
            'is_expired': self.is_expired,
            'overall_score': self.overall_score,
            'compliance_percentage': self.compliance_percentage,
            'public_display_allowed': self.public_display_permission == 'public',
            'verification_url': self.verification_url
        }

    def get_performance_impact(self):
        """Get performance impact summary"""
        impact = {}
        
        if self.patient_satisfaction_improvement:
            impact['patient_satisfaction'] = f"+{self.patient_satisfaction_improvement}%"
        
        if self.staff_engagement_improvement:
            impact['staff_engagement'] = f"+{self.staff_engagement_improvement}%"
        
        if self.operational_efficiency_improvement:
            impact['operational_efficiency'] = f"+{self.operational_efficiency_improvement}%"
        
        if self.quality_metrics_improvement:
            impact['custom_metrics'] = self.quality_metrics_improvement
        
        return impact

    def get_alerts(self):
        """Get list of alerts for this certification"""
        alerts = []
        
        if self.is_expired:
            alerts.append({
                'type': 'error',
                'message': f'Certification expired on {self.certificate_expiry_date}',
                'priority': 'high'
            })
        elif self.is_expiring_soon:
            alerts.append({
                'type': 'warning',
                'message': f'Certification expires in {self.days_until_expiry} days',
                'priority': 'medium'
            })
        
        if self.is_renewal_due:
            alerts.append({
                'type': 'warning',
                'message': 'Certification renewal is due',
                'priority': 'medium'
            })
        
        if self.is_surveillance_due:
            alerts.append({
                'type': 'info',
                'message': 'Surveillance assessment is due',
                'priority': 'low'
            })
        
        if self.corrective_actions_required and not self.corrective_actions_completed:
            alerts.append({
                'type': 'warning',
                'message': 'Corrective actions required',
                'priority': 'medium'
            })
        
        if self.certification_status == 'suspended':
            alerts.append({
                'type': 'error',
                'message': 'Certification is currently suspended',
                'priority': 'high'
            })
        
        return alerts

    @classmethod
    def get_expiring_certifications(cls, days_ahead=90, hospital=None):
        """Get certifications expiring within specified days"""
        from datetime import timedelta
        cutoff_date = timezone.now().date() + timedelta(days=days_ahead)
        
        queryset = cls.objects.filter(
            certificate_expiry_date__lte=cutoff_date,
            certificate_expiry_date__isnull=False,
            certification_status='active'
        )
        
        if hospital:
            queryset = queryset.filter(hospital=hospital)
        
        return queryset.order_by('certificate_expiry_date')

    @classmethod
    def get_expired_certifications(cls, hospital=None):
        """Get expired certifications"""
        today = timezone.now().date()
        
        queryset = cls.objects.filter(
            certificate_expiry_date__lt=today,
            certificate_expiry_date__isnull=False
        ).exclude(certification_status__in=['expired', 'revoked'])
        
        if hospital:
            queryset = queryset.filter(hospital=hospital)
        
        return queryset.order_by('certificate_expiry_date')

    @classmethod
    def get_public_display_certifications(cls, hospital):
        """Get certifications approved for public display"""
        return cls.objects.filter(
            hospital=hospital,
            certification_status='active',
            public_display_permission='public',
            display_on_website=True
        ).order_by('-overall_score', 'certification_name')

    @classmethod
    def get_certification_summary_by_hospital(cls, hospital=None):
        """Get certification summary statistics"""
        queryset = cls.objects.filter(certification_status='active')
        
        if hospital:
            queryset = queryset.filter(hospital=hospital)
        
        from django.db.models import Avg, Count
        
        return queryset.aggregate(
            total_certifications=Count('id'),
            avg_overall_score=Avg('overall_score'),
            avg_compliance=Avg('compliance_percentage'),
            expiring_soon=Count('id', filter=models.Q(
                certificate_expiry_date__lte=timezone.now().date() + timezone.timedelta(days=90)
            )),
            expired=Count('id', filter=models.Q(
                certificate_expiry_date__lt=timezone.now().date()
            ))
        )