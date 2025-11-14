from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal

class HospitalCompliance(models.Model):
    """
    Model representing hospital's compliance status with various frameworks
    """
    COMPLIANCE_STATUS_CHOICES = [
        ('compliant', 'Fully Compliant'),
        ('partial', 'Partially Compliant'),
        ('non_compliant', 'Non-Compliant'),
        ('in_progress', 'Implementation In Progress'),
        ('assessment_pending', 'Assessment Pending'),
        ('remediation_required', 'Remediation Required'),
        ('under_review', 'Under Review'),
        ('exempted', 'Exempted'),
        ('not_applicable', 'Not Applicable'),
        ('unknown', 'Status Unknown')
    ]
    
    IMPLEMENTATION_STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('planning', 'Planning Phase'),
        ('in_progress', 'Implementation In Progress'),
        ('testing', 'Testing Phase'),
        ('completed', 'Implementation Completed'),
        ('maintenance', 'Maintenance Mode'),
        ('updating', 'Updating Implementation'),
        ('suspended', 'Implementation Suspended'),
        ('failed', 'Implementation Failed')
    ]
    
    RISK_LEVEL_CHOICES = [
        ('critical', 'Critical Risk'),
        ('high', 'High Risk'),
        ('medium', 'Medium Risk'),
        ('low', 'Low Risk'),
        ('minimal', 'Minimal Risk'),
        ('none', 'No Risk')
    ]
    
    ASSESSMENT_TYPE_CHOICES = [
        ('self_assessment', 'Self Assessment'),
        ('internal_audit', 'Internal Audit'),
        ('external_audit', 'External Audit'),
        ('third_party_review', 'Third-Party Review'),
        ('regulatory_inspection', 'Regulatory Inspection'),
        ('certification_audit', 'Certification Audit'),
        ('peer_review', 'Peer Review'),
        ('continuous_monitoring', 'Continuous Monitoring')
    ]
    
    # Relationships
    hospital = models.ForeignKey(
        'api.Hospital',
        on_delete=models.CASCADE,
        related_name='compliance_records'
    )
    compliance_framework = models.ForeignKey(
        'api.ComplianceFramework',
        on_delete=models.PROTECT,
        related_name='hospital_compliance_records'
    )
    
    # Compliance Status
    compliance_status = models.CharField(
        max_length=20,
        choices=COMPLIANCE_STATUS_CHOICES,
        default='unknown'
    )
    implementation_status = models.CharField(
        max_length=20,
        choices=IMPLEMENTATION_STATUS_CHOICES,
        default='not_started'
    )
    risk_level = models.CharField(
        max_length=10,
        choices=RISK_LEVEL_CHOICES,
        default='medium'
    )
    
    # Assessment Information
    last_assessment_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date of last compliance assessment"
    )
    last_assessment_type = models.CharField(
        max_length=25,
        choices=ASSESSMENT_TYPE_CHOICES,
        blank=True
    )
    next_assessment_due = models.DateField(
        null=True,
        blank=True,
        help_text="Date when next assessment is due"
    )
    assessment_frequency_months = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Frequency of assessments in months"
    )
    
    # Compliance Scoring
    overall_compliance_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Overall compliance score (0-100)"
    )
    policy_compliance_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Policy compliance score (0-100)"
    )
    technical_compliance_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Technical compliance score (0-100)"
    )
    training_compliance_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Training compliance score (0-100)"
    )
    
    # Implementation Details
    implementation_start_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date implementation started"
    )
    implementation_target_date = models.DateField(
        null=True,
        blank=True,
        help_text="Target completion date for implementation"
    )
    implementation_completion_date = models.DateField(
        null=True,
        blank=True,
        help_text="Actual completion date"
    )
    implementation_budget = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Budget allocated for implementation"
    )
    implementation_cost_actual = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Actual cost of implementation"
    )
    currency = models.CharField(
        max_length=3,
        default='USD',
        help_text="Currency for costs"
    )
    
    # Requirements Tracking
    required_policies_implemented = models.JSONField(
        default=list,
        help_text="List of required policies that have been implemented"
    )
    required_policies_pending = models.JSONField(
        default=list,
        help_text="List of required policies that are pending"
    )
    training_programs_completed = models.JSONField(
        default=list,
        help_text="List of completed training programs"
    )
    training_programs_pending = models.JSONField(
        default=list,
        help_text="List of pending training programs"
    )
    technical_controls_implemented = models.JSONField(
        default=list,
        help_text="List of implemented technical controls"
    )
    technical_controls_pending = models.JSONField(
        default=list,
        help_text="List of pending technical controls"
    )
    
    # Compliance Issues and Remediation
    identified_gaps = models.JSONField(
        default=list,
        help_text="List of identified compliance gaps"
    )
    remediation_actions = models.JSONField(
        default=list,
        help_text="List of remediation actions required"
    )
    remediation_deadline = models.DateField(
        null=True,
        blank=True,
        help_text="Deadline for completing remediation"
    )
    remediation_completed = models.BooleanField(
        default=False,
        help_text="Whether remediation has been completed"
    )
    remediation_completion_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date remediation was completed"
    )
    
    # Violations and Incidents
    violations_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of compliance violations"
    )
    last_violation_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date of last violation"
    )
    violation_history = models.JSONField(
        default=list,
        help_text="History of compliance violations"
    )
    incident_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of compliance-related incidents"
    )
    incident_history = models.JSONField(
        default=list,
        help_text="History of compliance incidents"
    )
    
    # Documentation and Evidence
    compliance_documentation = models.JSONField(
        default=list,
        help_text="List of compliance documentation"
    )
    evidence_repository = models.JSONField(
        default=list,
        help_text="Repository of compliance evidence"
    )
    audit_trail = models.JSONField(
        default=list,
        help_text="Audit trail of compliance activities"
    )
    supporting_documents = models.FileField(
        upload_to='compliance/documents/',
        null=True,
        blank=True,
        help_text="Supporting compliance documents"
    )
    
    # Personnel and Responsibilities
    compliance_officer = models.ForeignKey(
        'api.CustomUser',
        on_delete=models.PROTECT,
        related_name='compliance_responsibilities',
        null=True,
        blank=True,
        help_text="Designated compliance officer"
    )
    implementation_team = models.JSONField(
        default=list,
        help_text="Team members involved in implementation"
    )
    external_consultants = models.JSONField(
        default=list,
        help_text="External consultants involved"
    )
    
    # Monitoring and Reporting
    monitoring_frequency = models.CharField(
        max_length=20,
        choices=[
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
            ('quarterly', 'Quarterly'),
            ('annually', 'Annually'),
            ('continuous', 'Continuous'),
            ('on_demand', 'On Demand')
        ],
        default='monthly',
        help_text="Frequency of compliance monitoring"
    )
    automated_monitoring_enabled = models.BooleanField(
        default=False,
        help_text="Whether automated monitoring is enabled"
    )
    monitoring_tools = models.JSONField(
        default=list,
        help_text="Tools used for compliance monitoring"
    )
    last_monitoring_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last monitoring check date"
    )
    
    # Reporting and Communication
    reporting_schedule = models.JSONField(
        default=list,
        help_text="Schedule for compliance reporting"
    )
    stakeholder_communications = models.JSONField(
        default=list,
        help_text="Communications to stakeholders about compliance"
    )
    regulatory_submissions = models.JSONField(
        default=list,
        help_text="Submissions to regulatory bodies"
    )
    
    # Performance Metrics
    staff_training_completion_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Percentage of staff who completed training"
    )
    policy_acknowledgment_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Percentage of staff who acknowledged policies"
    )
    incident_response_time_hours = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Average incident response time in hours"
    )
    
    # Improvement and Trends
    compliance_trend = models.CharField(
        max_length=20,
        choices=[
            ('improving', 'Improving'),
            ('stable', 'Stable'),
            ('declining', 'Declining'),
            ('volatile', 'Volatile'),
            ('unknown', 'Unknown')
        ],
        default='unknown',
        help_text="Trend in compliance performance"
    )
    improvement_initiatives = models.JSONField(
        default=list,
        help_text="Active compliance improvement initiatives"
    )
    lessons_learned = models.TextField(
        blank=True,
        help_text="Lessons learned from compliance implementation"
    )
    
    # External Relationships
    regulatory_relationships = models.JSONField(
        default=list,
        help_text="Relationships with regulatory bodies"
    )
    industry_partnerships = models.JSONField(
        default=list,
        help_text="Partnerships for compliance best practices"
    )
    peer_benchmarking = models.JSONField(
        default=list,
        help_text="Benchmarking data with peer organizations"
    )
    
    # Technology Integration
    compliance_software = models.JSONField(
        default=list,
        help_text="Software tools used for compliance management"
    )
    integration_apis = models.JSONField(
        default=list,
        help_text="API integrations for compliance monitoring"
    )
    data_sources = models.JSONField(
        default=list,
        help_text="Data sources for compliance monitoring"
    )
    
    # Alerts and Notifications
    alert_thresholds = models.JSONField(
        default=dict,
        help_text="Thresholds for compliance alerts"
    )
    notification_recipients = models.JSONField(
        default=list,
        help_text="Recipients for compliance notifications"
    )
    escalation_procedures = models.JSONField(
        default=list,
        help_text="Procedures for escalating compliance issues"
    )
    
    # Status Tracking
    is_active = models.BooleanField(
        default=True,
        help_text="Whether compliance record is active"
    )
    requires_immediate_attention = models.BooleanField(
        default=False,
        help_text="Whether this compliance area needs immediate attention"
    )
    executive_visibility = models.BooleanField(
        default=False,
        help_text="Whether this compliance area has executive visibility"
    )
    
    # Additional Information
    special_considerations = models.TextField(
        blank=True,
        help_text="Special considerations for this compliance area"
    )
    external_dependencies = models.TextField(
        blank=True,
        help_text="External dependencies affecting compliance"
    )
    notes = models.TextField(
        blank=True,
        help_text="Additional notes about compliance status"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'api.CustomUser',
        on_delete=models.PROTECT,
        related_name='created_hospital_compliance',
        null=True,
        blank=True
    )
    last_modified_by = models.ForeignKey(
        'api.CustomUser',
        on_delete=models.PROTECT,
        related_name='modified_hospital_compliance',
        null=True,
        blank=True
    )

    class Meta:
        unique_together = [['hospital', 'compliance_framework']]
        ordering = ['-risk_level', 'compliance_framework__priority_level', 'compliance_framework__name']
        indexes = [
            models.Index(fields=['hospital', 'compliance_status']),
            models.Index(fields=['compliance_framework']),
            models.Index(fields=['compliance_status']),
            models.Index(fields=['implementation_status']),
            models.Index(fields=['risk_level']),
            models.Index(fields=['next_assessment_due']),
            models.Index(fields=['remediation_deadline']),
            models.Index(fields=['requires_immediate_attention']),
            models.Index(fields=['executive_visibility']),
        ]
        permissions = [
            ("can_manage_hospital_compliance", "Can manage hospital compliance"),
            ("can_view_compliance_details", "Can view compliance details"),
            ("can_conduct_assessments", "Can conduct compliance assessments"),
            ("can_approve_remediation", "Can approve remediation plans"),
        ]

    def __str__(self):
        return f"{self.hospital.name} - {self.compliance_framework.name} ({self.compliance_status})"

    def clean(self):
        """Validate hospital compliance data"""
        super().clean()
        
        # Validate date relationships
        if self.implementation_start_date and self.implementation_target_date:
            if self.implementation_start_date > self.implementation_target_date:
                raise ValidationError(
                    "Implementation start date must be before target date"
                )
        
        if self.implementation_completion_date and self.implementation_start_date:
            if self.implementation_completion_date < self.implementation_start_date:
                raise ValidationError(
                    "Implementation completion date must be after start date"
                )
        
        if self.remediation_deadline and self.last_assessment_date:
            if self.remediation_deadline < self.last_assessment_date:
                raise ValidationError(
                    "Remediation deadline cannot be before last assessment date"
                )
        
        # Validate scores are within range
        score_fields = [
            'overall_compliance_score',
            'policy_compliance_score',
            'technical_compliance_score',
            'training_compliance_score',
            'staff_training_completion_rate',
            'policy_acknowledgment_rate'
        ]
        
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
        
        # Add to audit trail if this is an update
        if self.pk:
            old_compliance = HospitalCompliance.objects.get(pk=self.pk)
            if old_compliance.compliance_status != self.compliance_status:
                self.add_to_audit_trail('status_change', {
                    'from': old_compliance.compliance_status,
                    'to': self.compliance_status,
                    'date': timezone.now().isoformat(),
                    'changed_by': user.get_full_name() if user else 'System'
                })
        
        self.clean()
        super().save(*args, **kwargs)

    @property
    def is_assessment_overdue(self):
        """Check if assessment is overdue"""
        if not self.next_assessment_due:
            return False
        return timezone.now().date() > self.next_assessment_due

    @property
    def is_remediation_overdue(self):
        """Check if remediation is overdue"""
        if not self.remediation_deadline or self.remediation_completed:
            return False
        return timezone.now().date() > self.remediation_deadline

    @property
    def days_until_assessment(self):
        """Calculate days until next assessment"""
        if not self.next_assessment_due:
            return None
        
        delta = self.next_assessment_due - timezone.now().date()
        return delta.days

    @property
    def days_until_remediation_deadline(self):
        """Calculate days until remediation deadline"""
        if not self.remediation_deadline or self.remediation_completed:
            return None
        
        delta = self.remediation_deadline - timezone.now().date()
        return delta.days

    @property
    def implementation_progress_percentage(self):
        """Calculate implementation progress percentage"""
        if not self.implementation_start_date or not self.implementation_target_date:
            return None
        
        total_days = (self.implementation_target_date - self.implementation_start_date).days
        if total_days <= 0:
            return 100
        
        elapsed_days = (timezone.now().date() - self.implementation_start_date).days
        progress = min(100, max(0, (elapsed_days / total_days) * 100))
        
        return round(progress, 1)

    @property
    def budget_utilization_percentage(self):
        """Calculate budget utilization percentage"""
        if not self.implementation_budget or not self.implementation_cost_actual:
            return None
        
        if self.implementation_budget <= 0:
            return None
        
        utilization = (float(self.implementation_cost_actual) / float(self.implementation_budget)) * 100
        return round(utilization, 1)

    @property
    def compliance_maturity_level(self):
        """Determine compliance maturity level"""
        if not self.overall_compliance_score:
            return "Unknown"
        
        score = float(self.overall_compliance_score)
        
        if score >= 90:
            return "Optimized"
        elif score >= 80:
            return "Advanced"
        elif score >= 70:
            return "Managed"
        elif score >= 60:
            return "Defined"
        elif score >= 50:
            return "Developing"
        else:
            return "Initial"

    def calculate_overall_compliance_score(self):
        """Calculate overall compliance score from component scores"""
        scores = []
        weights = []
        
        if self.policy_compliance_score is not None:
            scores.append(float(self.policy_compliance_score))
            weights.append(0.3)  # 30% weight
        
        if self.technical_compliance_score is not None:
            scores.append(float(self.technical_compliance_score))
            weights.append(0.4)  # 40% weight
        
        if self.training_compliance_score is not None:
            scores.append(float(self.training_compliance_score))
            weights.append(0.3)  # 30% weight
        
        if not scores:
            return None
        
        # Normalize weights
        total_weight = sum(weights)
        if total_weight > 0:
            weights = [w / total_weight for w in weights]
        
        # Calculate weighted average
        weighted_score = sum(score * weight for score, weight in zip(scores, weights))
        return round(weighted_score, 2)

    def update_compliance_score(self, policy_score=None, technical_score=None, 
                              training_score=None, auto_calculate_overall=True):
        """Update compliance scores"""
        if policy_score is not None:
            self.policy_compliance_score = policy_score
        
        if technical_score is not None:
            self.technical_compliance_score = technical_score
        
        if training_score is not None:
            self.training_compliance_score = training_score
        
        if auto_calculate_overall:
            calculated_overall = self.calculate_overall_compliance_score()
            if calculated_overall is not None:
                self.overall_compliance_score = calculated_overall
        
        self.save()

    def record_assessment(self, assessment_date, assessment_type, overall_score=None,
                         policy_score=None, technical_score=None, training_score=None,
                         assessor_name=None, findings=None, user=None):
        """Record a compliance assessment"""
        self.last_assessment_date = assessment_date
        self.last_assessment_type = assessment_type
        
        # Update scores if provided
        if overall_score is not None:
            self.overall_compliance_score = overall_score
        
        if policy_score is not None:
            self.policy_compliance_score = policy_score
        
        if technical_score is not None:
            self.technical_compliance_score = technical_score
        
        if training_score is not None:
            self.training_compliance_score = training_score
        
        # Calculate next assessment due date
        if self.assessment_frequency_months:
            from dateutil.relativedelta import relativedelta
            self.next_assessment_due = assessment_date + relativedelta(months=self.assessment_frequency_months)
        
        # Record in audit trail
        assessment_data = {
            'assessment_date': assessment_date.isoformat(),
            'assessment_type': assessment_type,
            'overall_score': overall_score,
            'policy_score': policy_score,
            'technical_score': technical_score,
            'training_score': training_score,
            'assessor': assessor_name,
            'findings': findings
        }
        
        self.add_to_audit_trail('assessment_completed', assessment_data)
        self.save()

    def add_violation(self, violation_date, violation_type, description, 
                     severity='medium', user=None):
        """Add a compliance violation"""
        self.violations_count += 1
        self.last_violation_date = violation_date
        
        violation_record = {
            'date': violation_date.isoformat(),
            'type': violation_type,
            'description': description,
            'severity': severity,
            'reported_by': user.get_full_name() if user else 'System',
            'recorded_at': timezone.now().isoformat()
        }
        
        if not isinstance(self.violation_history, list):
            self.violation_history = []
        
        self.violation_history.append(violation_record)
        
        # Update risk level based on violations
        self._update_risk_level_based_on_violations()
        
        self.add_to_audit_trail('violation_recorded', violation_record)
        self.save()

    def add_incident(self, incident_date, incident_type, description, 
                    impact_level='medium', user=None):
        """Add a compliance incident"""
        self.incident_count += 1
        
        incident_record = {
            'date': incident_date.isoformat(),
            'type': incident_type,
            'description': description,
            'impact_level': impact_level,
            'reported_by': user.get_full_name() if user else 'System',
            'recorded_at': timezone.now().isoformat()
        }
        
        if not isinstance(self.incident_history, list):
            self.incident_history = []
        
        self.incident_history.append(incident_record)
        
        self.add_to_audit_trail('incident_recorded', incident_record)
        self.save()

    def initiate_remediation(self, remediation_actions, deadline_date, 
                           assigned_to=None, user=None):
        """Initiate remediation process"""
        self.remediation_actions = remediation_actions
        self.remediation_deadline = deadline_date
        self.remediation_completed = False
        
        remediation_data = {
            'actions': remediation_actions,
            'deadline': deadline_date.isoformat(),
            'assigned_to': assigned_to,
            'initiated_by': user.get_full_name() if user else 'System',
            'initiated_at': timezone.now().isoformat()
        }
        
        self.add_to_audit_trail('remediation_initiated', remediation_data)
        self.save()

    def complete_remediation(self, completion_notes=None, user=None):
        """Mark remediation as completed"""
        self.remediation_completed = True
        self.remediation_completion_date = timezone.now().date()
        
        completion_data = {
            'completion_date': self.remediation_completion_date.isoformat(),
            'notes': completion_notes,
            'completed_by': user.get_full_name() if user else 'System'
        }
        
        self.add_to_audit_trail('remediation_completed', completion_data)
        self.save()

    def _update_risk_level_based_on_violations(self):
        """Update risk level based on violation history"""
        if self.violations_count == 0:
            self.risk_level = 'minimal'
        elif self.violations_count <= 2:
            self.risk_level = 'low'
        elif self.violations_count <= 5:
            self.risk_level = 'medium'
        elif self.violations_count <= 10:
            self.risk_level = 'high'
        else:
            self.risk_level = 'critical'

    def add_to_audit_trail(self, event_type, event_data):
        """Add an event to audit trail"""
        if not isinstance(self.audit_trail, list):
            self.audit_trail = []
        
        audit_entry = {
            'event_type': event_type,
            'timestamp': timezone.now().isoformat(),
            'data': event_data
        }
        
        self.audit_trail.append(audit_entry)

    def get_compliance_summary(self):
        """Get compliance summary for dashboard"""
        return {
            'framework_name': self.compliance_framework.name,
            'compliance_status': self.get_compliance_status_display(),
            'implementation_status': self.get_implementation_status_display(),
            'overall_score': self.overall_compliance_score,
            'risk_level': self.get_risk_level_display(),
            'assessment_overdue': self.is_assessment_overdue,
            'remediation_overdue': self.is_remediation_overdue,
            'violations_count': self.violations_count,
            'maturity_level': self.compliance_maturity_level,
            'requires_attention': self.requires_immediate_attention
        }

    def get_implementation_summary(self):
        """Get implementation progress summary"""
        return {
            'status': self.get_implementation_status_display(),
            'progress_percentage': self.implementation_progress_percentage,
            'budget_utilization': self.budget_utilization_percentage,
            'start_date': self.implementation_start_date,
            'target_date': self.implementation_target_date,
            'completion_date': self.implementation_completion_date,
            'team_size': len(self.implementation_team) if self.implementation_team else 0
        }

    def get_alerts(self):
        """Get list of alerts for this compliance area"""
        alerts = []
        
        if self.is_assessment_overdue:
            alerts.append({
                'type': 'error',
                'message': f'Assessment overdue by {abs(self.days_until_assessment)} days',
                'priority': 'high'
            })
        elif self.days_until_assessment and self.days_until_assessment <= 30:
            alerts.append({
                'type': 'warning',
                'message': f'Assessment due in {self.days_until_assessment} days',
                'priority': 'medium'
            })
        
        if self.is_remediation_overdue:
            alerts.append({
                'type': 'error',
                'message': f'Remediation overdue by {abs(self.days_until_remediation_deadline)} days',
                'priority': 'high'
            })
        elif self.days_until_remediation_deadline and self.days_until_remediation_deadline <= 7:
            alerts.append({
                'type': 'warning',
                'message': f'Remediation due in {self.days_until_remediation_deadline} days',
                'priority': 'medium'
            })
        
        if self.risk_level in ['critical', 'high']:
            alerts.append({
                'type': 'error',
                'message': f'{self.get_risk_level_display()} compliance risk',
                'priority': 'high'
            })
        
        if self.compliance_status == 'non_compliant':
            alerts.append({
                'type': 'error',
                'message': 'Non-compliant status requires immediate action',
                'priority': 'critical'
            })
        
        return alerts

    @classmethod
    def get_hospital_compliance_overview(cls, hospital):
        """Get compliance overview for a hospital"""
        from django.db.models import Avg, Count
        
        hospital_compliance = cls.objects.filter(hospital=hospital, is_active=True)
        
        overview = hospital_compliance.aggregate(
            total_frameworks=Count('id'),
            avg_compliance_score=Avg('overall_compliance_score'),
            compliant_count=Count('id', filter=models.Q(compliance_status='compliant')),
            non_compliant_count=Count('id', filter=models.Q(compliance_status='non_compliant')),
            high_risk_count=Count('id', filter=models.Q(risk_level__in=['high', 'critical'])),
            overdue_assessments=Count('id', filter=models.Q(
                next_assessment_due__lt=timezone.now().date()
            )),
            total_violations=models.Sum('violations_count')
        )
        
        overview['compliance_percentage'] = 0
        if overview['total_frameworks'] > 0:
            overview['compliance_percentage'] = round(
                (overview['compliant_count'] / overview['total_frameworks']) * 100, 1
            )
        
        return overview

    @classmethod
    def get_assessment_due_list(cls, hospital=None, days_ahead=30):
        """Get compliance areas with assessments due"""
        from datetime import timedelta
        cutoff_date = timezone.now().date() + timedelta(days=days_ahead)
        
        queryset = cls.objects.filter(
            next_assessment_due__lte=cutoff_date,
            next_assessment_due__isnull=False,
            is_active=True
        )
        
        if hospital:
            queryset = queryset.filter(hospital=hospital)
        
        return queryset.order_by('next_assessment_due')

    @classmethod
    def get_high_risk_compliance_areas(cls, hospital=None):
        """Get high-risk compliance areas"""
        queryset = cls.objects.filter(
            risk_level__in=['high', 'critical'],
            is_active=True
        )
        
        if hospital:
            queryset = queryset.filter(hospital=hospital)
        
        return queryset.order_by('-risk_level', 'compliance_framework__priority_level')

    @classmethod
    def get_compliance_dashboard_data(cls, hospital=None):
        """Get comprehensive compliance dashboard data"""
        queryset = cls.objects.filter(is_active=True)
        
        if hospital:
            queryset = queryset.filter(hospital=hospital)
        
        from django.db.models import Avg, Count
        
        return {
            'overview': queryset.aggregate(
                total_frameworks=Count('id'),
                avg_score=Avg('overall_compliance_score'),
                compliant=Count('id', filter=models.Q(compliance_status='compliant')),
                non_compliant=Count('id', filter=models.Q(compliance_status='non_compliant')),
                high_risk=Count('id', filter=models.Q(risk_level__in=['high', 'critical']))
            ),
            'by_status': queryset.values('compliance_status').annotate(count=Count('id')),
            'by_risk': queryset.values('risk_level').annotate(count=Count('id')),
            'by_framework_type': queryset.values(
                'compliance_framework__framework_type'
            ).annotate(count=Count('id')),
            'assessments_due': queryset.filter(
                next_assessment_due__lte=timezone.now().date() + timezone.timedelta(days=30)
            ).count(),
            'remediation_overdue': queryset.filter(
                remediation_deadline__lt=timezone.now().date(),
                remediation_completed=False
            ).count()
        }