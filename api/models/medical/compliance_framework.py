from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone

class ComplianceFramework(models.Model):
    """
    Model representing compliance frameworks and privacy standards for healthcare
    """
    FRAMEWORK_TYPE_CHOICES = [
        ('privacy', 'Privacy and Data Protection'),
        ('security', 'Information Security'),
        ('quality', 'Quality Management'),
        ('safety', 'Patient Safety'),
        ('operational', 'Operational Standards'),
        ('financial', 'Financial Compliance'),
        ('regulatory', 'Regulatory Requirements'),
        ('environmental', 'Environmental Standards'),
        ('ethics', 'Ethics and Conduct'),
        ('risk', 'Risk Management'),
        ('governance', 'Corporate Governance'),
        ('other', 'Other Framework')
    ]
    
    SCOPE_LEVEL_CHOICES = [
        ('international', 'International Standard'),
        ('regional', 'Regional Requirement'),
        ('national', 'National Law/Regulation'),
        ('state_provincial', 'State/Provincial Regulation'),
        ('local', 'Local Ordinance'),
        ('industry', 'Industry Standard'),
        ('organizational', 'Organizational Policy')
    ]
    
    COMPLIANCE_COMPLEXITY_CHOICES = [
        ('basic', 'Basic Requirements'),
        ('intermediate', 'Intermediate Complexity'),
        ('advanced', 'Advanced Framework'),
        ('expert', 'Expert Level Implementation'),
        ('enterprise', 'Enterprise Grade')
    ]
    
    ENFORCEMENT_LEVEL_CHOICES = [
        ('mandatory', 'Legally Mandatory'),
        ('recommended', 'Industry Recommended'),
        ('voluntary', 'Voluntary Adoption'),
        ('contractual', 'Contractual Requirement'),
        ('best_practice', 'Best Practice Standard')
    ]
    
    # Basic Information
    name = models.CharField(
        max_length=200,
        unique=True,
        help_text="Official name of the compliance framework"
    )
    short_name = models.CharField(
        max_length=50,
        blank=True,
        help_text="Abbreviated name or acronym"
    )
    framework_code = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        help_text="Unique identifier code"
    )
    
    # Framework Classification
    framework_type = models.CharField(
        max_length=20,
        choices=FRAMEWORK_TYPE_CHOICES,
        default='privacy'
    )
    scope_level = models.CharField(
        max_length=20,
        choices=SCOPE_LEVEL_CHOICES,
        default='national'
    )
    compliance_complexity = models.CharField(
        max_length=20,
        choices=COMPLIANCE_COMPLEXITY_CHOICES,
        default='intermediate'
    )
    enforcement_level = models.CharField(
        max_length=20,
        choices=ENFORCEMENT_LEVEL_CHOICES,
        default='mandatory'
    )
    
    # Geographic and Jurisdictional Information
    applicable_countries = models.JSONField(
        default=list,
        help_text="List of countries where this framework applies"
    )
    applicable_regions = models.JSONField(
        default=list,
        help_text="Specific regions, states, or provinces"
    )
    governing_authority = models.CharField(
        max_length=200,
        help_text="Authority or organization that governs this framework"
    )
    regulatory_body = models.CharField(
        max_length=200,
        blank=True,
        help_text="Regulatory body responsible for enforcement"
    )
    
    # Framework Details
    description = models.TextField(
        help_text="Detailed description of the compliance framework"
    )
    purpose = models.TextField(
        blank=True,
        help_text="Primary purpose and objectives of the framework"
    )
    key_principles = models.JSONField(
        default=list,
        help_text="Key principles or pillars of the framework"
    )
    
    # Requirements and Implementation
    core_requirements = models.JSONField(
        default=list,
        help_text="Core compliance requirements"
    )
    implementation_guidelines = models.TextField(
        blank=True,
        help_text="Guidelines for implementing the framework"
    )
    required_policies = models.JSONField(
        default=list,
        help_text="Required policies and procedures"
    )
    mandatory_training_topics = models.JSONField(
        default=list,
        help_text="Mandatory training topics for staff"
    )
    
    # Documentation Requirements
    required_documentation = models.JSONField(
        default=list,
        help_text="Required documentation and records"
    )
    audit_requirements = models.JSONField(
        default=list,
        help_text="Audit and assessment requirements"
    )
    reporting_obligations = models.JSONField(
        default=list,
        help_text="Reporting obligations and frequencies"
    )
    
    # Version and Timeline Information
    version = models.CharField(
        max_length=20,
        blank=True,
        help_text="Current version of the framework"
    )
    effective_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date when framework became effective"
    )
    last_updated = models.DateField(
        null=True,
        blank=True,
        help_text="Last update to the framework"
    )
    next_review_date = models.DateField(
        null=True,
        blank=True,
        help_text="Next scheduled review date"
    )
    
    # Penalties and Consequences
    max_penalty_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Maximum penalty amount for non-compliance"
    )
    penalty_currency = models.CharField(
        max_length=3,
        default='USD',
        help_text="Currency for penalty amounts"
    )
    penalty_structure = models.TextField(
        blank=True,
        help_text="Structure of penalties for violations"
    )
    breach_notification_requirements = models.TextField(
        blank=True,
        help_text="Requirements for breach notification"
    )
    
    # Assessment and Certification
    assessment_frequency_months = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Required frequency of compliance assessments"
    )
    external_audit_required = models.BooleanField(
        default=False,
        help_text="Whether external audits are required"
    )
    certification_available = models.BooleanField(
        default=False,
        help_text="Whether certification programs are available"
    )
    certification_bodies = models.JSONField(
        default=list,
        help_text="List of authorized certification bodies"
    )
    
    # Implementation Timeline
    typical_implementation_months = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Typical time required for full implementation"
    )
    grace_period_months = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Grace period for new organizations"
    )
    phased_implementation = models.BooleanField(
        default=False,
        help_text="Whether implementation can be done in phases"
    )
    implementation_phases = models.JSONField(
        default=list,
        help_text="Description of implementation phases"
    )
    
    # Resources and Support
    official_website = models.URLField(
        blank=True,
        help_text="Official website for the framework"
    )
    guidance_documents_url = models.URLField(
        blank=True,
        help_text="URL for guidance documents"
    )
    training_resources = models.JSONField(
        default=list,
        help_text="Available training resources and materials"
    )
    consultant_directory = models.URLField(
        blank=True,
        help_text="Directory of certified consultants"
    )
    
    # Technology and Tools
    required_technologies = models.JSONField(
        default=list,
        help_text="Required or recommended technologies"
    )
    compatible_software = models.JSONField(
        default=list,
        help_text="Compatible compliance software and tools"
    )
    api_integration_available = models.BooleanField(
        default=False,
        help_text="Whether API integration is available for compliance checking"
    )
    automated_monitoring_tools = models.JSONField(
        default=list,
        help_text="Available automated monitoring tools"
    )
    
    # Healthcare-Specific Information
    applicable_healthcare_sectors = models.JSONField(
        default=list,
        help_text="Healthcare sectors this framework applies to"
    )
    patient_data_requirements = models.TextField(
        blank=True,
        help_text="Specific requirements for patient data handling"
    )
    data_retention_requirements = models.TextField(
        blank=True,
        help_text="Data retention and disposal requirements"
    )
    cross_border_data_rules = models.TextField(
        blank=True,
        help_text="Rules for cross-border data transfers"
    )
    
    # Risk and Impact Assessment
    risk_categories = models.JSONField(
        default=list,
        help_text="Risk categories addressed by this framework"
    )
    impact_assessment_required = models.BooleanField(
        default=False,
        help_text="Whether formal impact assessments are required"
    )
    risk_mitigation_strategies = models.JSONField(
        default=list,
        help_text="Recommended risk mitigation strategies"
    )
    
    # Updates and Changes
    change_notification_process = models.TextField(
        blank=True,
        help_text="Process for notifying changes to the framework"
    )
    stakeholder_consultation = models.BooleanField(
        default=False,
        help_text="Whether stakeholder consultation is part of updates"
    )
    public_comment_period = models.BooleanField(
        default=False,
        help_text="Whether public comment periods are held"
    )
    
    # Integration with Other Frameworks
    related_frameworks = models.JSONField(
        default=list,
        help_text="Related or complementary frameworks"
    )
    conflicting_frameworks = models.JSONField(
        default=list,
        help_text="Frameworks that may conflict with this one"
    )
    harmonization_efforts = models.TextField(
        blank=True,
        help_text="Efforts to harmonize with other frameworks"
    )
    
    # Performance Metrics
    adoption_rate_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Percentage of eligible organizations that have adopted"
    )
    average_implementation_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Average cost of implementation"
    )
    cost_currency = models.CharField(
        max_length=3,
        default='USD',
        help_text="Currency for cost estimates"
    )
    effectiveness_rating = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Effectiveness rating (1-10)"
    )
    
    # Contact and Support Information
    contact_email = models.EmailField(
        blank=True,
        help_text="Contact email for framework inquiries"
    )
    support_phone = models.CharField(
        max_length=20,
        blank=True,
        help_text="Support phone number"
    )
    help_desk_url = models.URLField(
        blank=True,
        help_text="Help desk or support portal URL"
    )
    
    # Status and Tracking
    is_active = models.BooleanField(
        default=True,
        help_text="Whether framework is currently active"
    )
    is_mandatory_for_hospitals = models.BooleanField(
        default=False,
        help_text="Whether this framework is mandatory for hospitals"
    )
    priority_level = models.CharField(
        max_length=10,
        choices=[
            ('critical', 'Critical Priority'),
            ('high', 'High Priority'),
            ('medium', 'Medium Priority'),
            ('low', 'Low Priority')
        ],
        default='medium',
        help_text="Priority level for implementation"
    )
    
    # Additional Information
    industry_best_practices = models.TextField(
        blank=True,
        help_text="Industry best practices related to this framework"
    )
    case_studies = models.JSONField(
        default=list,
        help_text="Links or references to implementation case studies"
    )
    success_metrics = models.JSONField(
        default=list,
        help_text="Metrics to measure successful implementation"
    )
    common_challenges = models.TextField(
        blank=True,
        help_text="Common challenges in implementing this framework"
    )
    notes = models.TextField(
        blank=True,
        help_text="Additional notes about the framework"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'api.CustomUser',
        on_delete=models.PROTECT,
        related_name='created_compliance_frameworks',
        null=True,
        blank=True
    )
    last_modified_by = models.ForeignKey(
        'api.CustomUser',
        on_delete=models.PROTECT,
        related_name='modified_compliance_frameworks',
        null=True,
        blank=True
    )

    class Meta:
        ordering = ['priority_level', 'name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['framework_code']),
            models.Index(fields=['framework_type']),
            models.Index(fields=['scope_level']),
            models.Index(fields=['enforcement_level']),
            models.Index(fields=['is_active']),
            models.Index(fields=['is_mandatory_for_hospitals']),
            models.Index(fields=['priority_level']),
        ]
        permissions = [
            ("can_manage_compliance_frameworks", "Can manage compliance frameworks"),
            ("can_view_framework_details", "Can view framework details"),
            ("can_assess_compliance", "Can assess compliance status"),
        ]

    def __str__(self):
        if self.short_name:
            return f"{self.short_name} ({self.get_scope_level_display()})"
        return f"{self.name} ({self.get_scope_level_display()})"

    def clean(self):
        """Validate compliance framework data"""
        super().clean()
        
        # Generate framework code if not provided
        if not self.framework_code:
            self.framework_code = self.generate_framework_code()
        
        # Validate effective date is not in future for active frameworks
        if self.effective_date and self.effective_date > timezone.now().date() and self.is_active:
            raise ValidationError(
                "Active framework cannot have future effective date"
            )
        
        # Validate last updated is not after next review
        if self.last_updated and self.next_review_date:
            if self.last_updated > self.next_review_date:
                raise ValidationError(
                    "Last updated date cannot be after next review date"
                )
        
        # Validate percentages and ratings
        if self.adoption_rate_percentage is not None:
            if self.adoption_rate_percentage < 0 or self.adoption_rate_percentage > 100:
                raise ValidationError("Adoption rate must be between 0 and 100")
        
        if self.effectiveness_rating is not None:
            if self.effectiveness_rating < 1 or self.effectiveness_rating > 10:
                raise ValidationError("Effectiveness rating must be between 1 and 10")

    def save(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        
        if not self.pk and user:
            self.created_by = user
        if user:
            self.last_modified_by = user
            
        self.clean()
        super().save(*args, **kwargs)

    def generate_framework_code(self):
        """Generate unique framework code"""
        import re
        import random
        
        # Create code from type and name
        type_code = self.framework_type[:3].upper()
        
        # Remove non-alphabetic characters and take first 3 letters of name
        clean_name = re.sub(r'[^A-Za-z]', '', self.name)
        name_code = clean_name[:3].upper()
        
        # Add random number
        suffix = str(random.randint(10, 99))
        code = f"{type_code}{name_code}{suffix}"
        
        # Ensure uniqueness
        counter = 1
        original_code = code
        while ComplianceFramework.objects.filter(framework_code=code).exists():
            code = f"{original_code}{counter}"
            counter += 1
            
        return code

    @property
    def is_review_due(self):
        """Check if framework review is due"""
        if not self.next_review_date:
            return False
        return timezone.now().date() >= self.next_review_date

    @property
    def days_until_review(self):
        """Calculate days until next review"""
        if not self.next_review_date:
            return None
        
        delta = self.next_review_date - timezone.now().date()
        return delta.days

    @property
    def framework_age_years(self):
        """Calculate age of framework in years"""
        if not self.effective_date:
            return None
        
        delta = timezone.now().date() - self.effective_date
        return round(delta.days / 365.25, 1)

    @property
    def estimated_implementation_cost(self):
        """Get estimated implementation cost with currency"""
        if not self.average_implementation_cost:
            return "Cost not specified"
        
        return f"{self.average_implementation_cost} {self.cost_currency}"

    def get_applicable_regions(self):
        """Get formatted list of applicable regions"""
        regions = []
        
        if self.applicable_countries:
            regions.extend(self.applicable_countries)
        
        if self.applicable_regions:
            regions.extend(self.applicable_regions)
        
        return regions if regions else ["Global"]

    def get_core_requirements_summary(self):
        """Get summary of core requirements"""
        if not self.core_requirements:
            return []
        
        # Return first 5 requirements for summary
        return self.core_requirements[:5]

    def get_implementation_timeline(self):
        """Get implementation timeline summary"""
        timeline = {}
        
        if self.typical_implementation_months:
            timeline['typical_duration'] = f"{self.typical_implementation_months} months"
        
        if self.grace_period_months:
            timeline['grace_period'] = f"{self.grace_period_months} months"
        
        if self.phased_implementation and self.implementation_phases:
            timeline['phases'] = len(self.implementation_phases)
        
        return timeline

    def get_penalty_summary(self):
        """Get penalty structure summary"""
        penalty_info = {}
        
        if self.max_penalty_amount:
            penalty_info['max_penalty'] = f"{self.max_penalty_amount} {self.penalty_currency}"
        
        if self.penalty_structure:
            penalty_info['structure'] = self.penalty_structure[:200] + "..." if len(self.penalty_structure) > 200 else self.penalty_structure
        
        return penalty_info

    def get_risk_profile(self):
        """Get risk profile summary"""
        return {
            'categories': self.risk_categories if self.risk_categories else [],
            'impact_assessment_required': self.impact_assessment_required,
            'mitigation_strategies': len(self.risk_mitigation_strategies) if self.risk_mitigation_strategies else 0
        }

    def get_compliance_requirements_checklist(self):
        """Get checklist of compliance requirements"""
        checklist = []
        
        if self.required_policies:
            checklist.extend([f"Policy: {policy}" for policy in self.required_policies])
        
        if self.required_documentation:
            checklist.extend([f"Documentation: {doc}" for doc in self.required_documentation])
        
        if self.mandatory_training_topics:
            checklist.extend([f"Training: {topic}" for topic in self.mandatory_training_topics])
        
        if self.audit_requirements:
            checklist.extend([f"Audit: {req}" for req in self.audit_requirements])
        
        return checklist

    def assess_organization_readiness(self, organization_size="medium", 
                                   current_compliance_level="basic",
                                   available_budget=None):
        """Assess organization's readiness for this framework"""
        readiness_score = 0
        recommendations = []
        
        # Complexity vs capability assessment
        complexity_scores = {
            'basic': 1,
            'intermediate': 2,
            'advanced': 3,
            'expert': 4,
            'enterprise': 5
        }
        
        capability_scores = {
            'basic': 1,
            'intermediate': 2,
            'advanced': 3,
            'expert': 4
        }
        
        framework_complexity = complexity_scores.get(self.compliance_complexity, 3)
        org_capability = capability_scores.get(current_compliance_level, 2)
        
        if org_capability >= framework_complexity:
            readiness_score += 40
            recommendations.append("Organization capability matches framework complexity")
        else:
            gap = framework_complexity - org_capability
            readiness_score += max(0, 40 - (gap * 10))
            recommendations.append(f"Capability gap detected. Recommend training and consultation.")
        
        # Budget assessment
        if available_budget and self.average_implementation_cost:
            if available_budget >= self.average_implementation_cost:
                readiness_score += 30
                recommendations.append("Budget is adequate for implementation")
            else:
                budget_ratio = available_budget / self.average_implementation_cost
                readiness_score += int(30 * budget_ratio)
                recommendations.append("Budget may be insufficient. Consider phased implementation.")
        
        # Timeline assessment
        if self.typical_implementation_months:
            if self.typical_implementation_months <= 6:
                readiness_score += 20
            elif self.typical_implementation_months <= 12:
                readiness_score += 15
            else:
                readiness_score += 10
        
        # Support availability
        if self.training_resources and self.guidance_documents_url:
            readiness_score += 10
            recommendations.append("Good support resources available")
        
        return {
            'readiness_score': min(100, readiness_score),
            'readiness_level': self._get_readiness_level(readiness_score),
            'recommendations': recommendations,
            'estimated_timeline': f"{self.typical_implementation_months} months" if self.typical_implementation_months else "Timeline not specified"
        }

    def _get_readiness_level(self, score):
        """Convert readiness score to level"""
        if score >= 80:
            return "High Readiness"
        elif score >= 60:
            return "Medium Readiness"
        elif score >= 40:
            return "Low Readiness"
        else:
            return "Not Ready"

    def get_related_frameworks_analysis(self):
        """Analyze relationships with other frameworks"""
        analysis = {
            'complementary': self.related_frameworks if self.related_frameworks else [],
            'conflicting': self.conflicting_frameworks if self.conflicting_frameworks else [],
            'harmonization_status': bool(self.harmonization_efforts)
        }
        
        return analysis

    @classmethod
    def get_mandatory_for_hospitals(cls, country=None):
        """Get frameworks mandatory for hospitals"""
        queryset = cls.objects.filter(
            is_mandatory_for_hospitals=True,
            is_active=True
        )
        
        if country:
            queryset = queryset.filter(
                models.Q(applicable_countries__contains=[country]) |
                models.Q(applicable_countries=[]) |
                models.Q(applicable_countries__isnull=True)
            )
        
        return queryset.order_by('priority_level', 'name')

    @classmethod
    def get_by_type(cls, framework_type):
        """Get frameworks by type"""
        return cls.objects.filter(
            framework_type=framework_type,
            is_active=True
        ).order_by('priority_level', 'name')

    @classmethod
    def get_review_due(cls):
        """Get frameworks that need review"""
        today = timezone.now().date()
        
        return cls.objects.filter(
            next_review_date__lte=today,
            is_active=True
        ).order_by('next_review_date')

    @classmethod
    def get_implementation_complexity_summary(cls):
        """Get summary of frameworks by complexity"""
        from django.db.models import Count
        
        return cls.objects.filter(is_active=True).values(
            'compliance_complexity'
        ).annotate(
            count=Count('id')
        ).order_by('compliance_complexity')

    @classmethod
    def get_compliance_dashboard_data(cls, country=None):
        """Get data for compliance dashboard"""
        queryset = cls.objects.filter(is_active=True)
        
        if country:
            queryset = queryset.filter(
                models.Q(applicable_countries__contains=[country]) |
                models.Q(applicable_countries=[])
            )
        
        from django.db.models import Avg, Count
        
        return {
            'total_frameworks': queryset.count(),
            'mandatory_count': queryset.filter(is_mandatory_for_hospitals=True).count(),
            'by_type': queryset.values('framework_type').annotate(count=Count('id')),
            'by_priority': queryset.values('priority_level').annotate(count=Count('id')),
            'avg_implementation_months': queryset.aggregate(
                avg_months=Avg('typical_implementation_months')
            )['avg_months'],
            'review_due_count': queryset.filter(
                next_review_date__lte=timezone.now().date()
            ).count()
        }