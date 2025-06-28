# api/models/medical/health_screening.py

from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from ..base import TimestampedModel
from .womens_health_profile import WomensHealthProfile


class HealthScreening(TimestampedModel):
    """
    Model for tracking women's health screenings and preventive care
    """
    # Relationship
    womens_health_profile = models.ForeignKey(
        WomensHealthProfile,
        on_delete=models.CASCADE,
        related_name='health_screenings',
        help_text="Women's health profile this screening belongs to"
    )
    
    # Screening Type and Information
    SCREENING_TYPE_CHOICES = [
        # Reproductive Health Screenings
        ('pap_smear', 'Pap Smear (Cervical Cancer)'),
        ('hpv_test', 'HPV Test'),
        ('mammogram', 'Mammogram'),
        ('breast_exam_clinical', 'Clinical Breast Exam'),
        ('breast_self_exam', 'Breast Self-Exam'),
        ('pelvic_exam', 'Pelvic Examination'),
        ('std_screening', 'STD/STI Screening'),
        ('pregnancy_test', 'Pregnancy Test'),
        
        # General Health Screenings
        ('blood_pressure', 'Blood Pressure Check'),
        ('cholesterol', 'Cholesterol Test'),
        ('diabetes_screening', 'Diabetes Screening'),
        ('thyroid_test', 'Thyroid Function Test'),
        ('bone_density', 'Bone Density Scan (DEXA)'),
        ('colonoscopy', 'Colonoscopy'),
        ('skin_cancer_screening', 'Skin Cancer Screening'),
        ('eye_exam', 'Eye Examination'),
        ('dental_exam', 'Dental Examination'),
        
        # Mental Health Screenings
        ('depression_screening', 'Depression Screening'),
        ('anxiety_screening', 'Anxiety Screening'),
        ('postpartum_depression', 'Postpartum Depression Screening'),
        
        # Age-Specific Screenings
        ('osteoporosis_screening', 'Osteoporosis Screening'),
        ('cardiac_screening', 'Cardiac Screening'),
        ('lung_cancer_screening', 'Lung Cancer Screening'),
        
        # Custom/Other
        ('custom', 'Custom Screening')
    ]
    
    screening_type = models.CharField(
        max_length=30,
        choices=SCREENING_TYPE_CHOICES,
        help_text="Type of health screening"
    )
    
    custom_screening_name = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Name of custom screening if 'custom' type is selected"
    )
    
    # Scheduling and Timing
    scheduled_date = models.DateField(
        null=True,
        blank=True,
        help_text="Scheduled date for the screening"
    )
    
    completed_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date when screening was completed"
    )
    
    next_due_date = models.DateField(
        null=True,
        blank=True,
        help_text="Next due date for this screening"
    )
    
    # Status
    SCREENING_STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
        ('rescheduled', 'Rescheduled'),
        ('not_applicable', 'Not Applicable'),
        ('pending_results', 'Pending Results')
    ]
    
    status = models.CharField(
        max_length=20,
        choices=SCREENING_STATUS_CHOICES,
        default='scheduled',
        help_text="Current status of the screening"
    )
    
    # Healthcare Provider Information
    provider_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Name of healthcare provider"
    )
    
    clinic_hospital_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Name of clinic or hospital"
    )
    
    provider_type = models.CharField(
        max_length=50,
        choices=[
            ('primary_care', 'Primary Care Physician'),
            ('gynecologist', 'Gynecologist'),
            ('specialist', 'Specialist'),
            ('radiologist', 'Radiologist'),
            ('nurse_practitioner', 'Nurse Practitioner'),
            ('midwife', 'Midwife'),
            ('other', 'Other')
        ],
        null=True,
        blank=True,
        help_text="Type of healthcare provider"
    )
    
    appointment_time = models.TimeField(
        null=True,
        blank=True,
        help_text="Appointment time if scheduled"
    )
    
    # Results and Findings
    RESULT_STATUS_CHOICES = [
        ('normal', 'Normal'),
        ('abnormal', 'Abnormal'),
        ('borderline', 'Borderline'),
        ('inconclusive', 'Inconclusive'),
        ('pending', 'Pending'),
        ('not_available', 'Not Available')
    ]
    
    result_status = models.CharField(
        max_length=20,
        choices=RESULT_STATUS_CHOICES,
        null=True,
        blank=True,
        help_text="Overall result status"
    )
    
    result_details = models.TextField(
        blank=True,
        null=True,
        help_text="Detailed results or findings"
    )
    
    result_values = models.JSONField(
        default=dict,
        blank=True,
        help_text="Numerical or categorical result values"
    )
    
    abnormal_findings = models.TextField(
        blank=True,
        null=True,
        help_text="Description of any abnormal findings"
    )
    
    recommendations = models.TextField(
        blank=True,
        null=True,
        help_text="Healthcare provider recommendations"
    )
    
    # Follow-up Actions
    follow_up_required = models.BooleanField(
        default=False,
        help_text="Whether follow-up is required"
    )
    
    follow_up_type = models.CharField(
        max_length=50,
        choices=[
            ('repeat_screening', 'Repeat Screening'),
            ('specialist_referral', 'Specialist Referral'),
            ('additional_testing', 'Additional Testing'),
            ('treatment', 'Treatment Required'),
            ('lifestyle_changes', 'Lifestyle Changes'),
            ('monitoring', 'Regular Monitoring'),
            ('none', 'No Follow-up Needed')
        ],
        null=True,
        blank=True,
        help_text="Type of follow-up required"
    )
    
    follow_up_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date for follow-up appointment or action"
    )
    
    follow_up_notes = models.TextField(
        blank=True,
        null=True,
        help_text="Notes about follow-up requirements"
    )
    
    # Risk Assessment
    RISK_LEVEL_CHOICES = [
        ('low', 'Low Risk'),
        ('moderate', 'Moderate Risk'),
        ('high', 'High Risk'),
        ('very_high', 'Very High Risk'),
        ('unknown', 'Unknown')
    ]
    
    risk_assessment = models.CharField(
        max_length=15,
        choices=RISK_LEVEL_CHOICES,
        null=True,
        blank=True,
        help_text="Risk assessment based on results"
    )
    
    risk_factors_identified = models.JSONField(
        default=list,
        blank=True,
        help_text="List of identified risk factors"
    )
    
    # Frequency and Recurrence
    recommended_frequency_months = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(120)],
        help_text="Recommended frequency in months"
    )
    
    is_routine = models.BooleanField(
        default=True,
        help_text="Whether this is routine screening or diagnostic"
    )
    
    reason_for_screening = models.CharField(
        max_length=100,
        choices=[
            ('routine', 'Routine Screening'),
            ('symptoms', 'Due to Symptoms'),
            ('family_history', 'Family History'),
            ('follow_up', 'Follow-up'),
            ('high_risk', 'High Risk'),
            ('annual_checkup', 'Annual Checkup'),
            ('other', 'Other')
        ],
        default='routine',
        help_text="Reason for this screening"
    )
    
    # Cost and Insurance
    estimated_cost = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Estimated cost of screening"
    )
    
    insurance_covered = models.BooleanField(
        null=True,
        blank=True,
        help_text="Whether screening is covered by insurance"
    )
    
    copay_amount = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Patient copay amount"
    )
    
    # Preparation and Instructions
    preparation_required = models.BooleanField(
        default=False,
        help_text="Whether special preparation is required"
    )
    
    preparation_instructions = models.TextField(
        blank=True,
        null=True,
        help_text="Instructions for screening preparation"
    )
    
    fasting_required = models.BooleanField(
        default=False,
        help_text="Whether fasting is required"
    )
    
    medications_to_avoid = models.JSONField(
        default=list,
        blank=True,
        help_text="Medications to avoid before screening"
    )
    
    # Experience and Comfort
    comfort_level = models.CharField(
        max_length=20,
        choices=[
            ('very_comfortable', 'Very Comfortable'),
            ('comfortable', 'Comfortable'),
            ('neutral', 'Neutral'),
            ('uncomfortable', 'Uncomfortable'),
            ('very_uncomfortable', 'Very Uncomfortable')
        ],
        null=True,
        blank=True,
        help_text="Patient's comfort level during screening"
    )
    
    pain_level = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        help_text="Pain level during screening (0-10)"
    )
    
    patient_experience_notes = models.TextField(
        blank=True,
        null=True,
        help_text="Patient's notes about the experience"
    )
    
    # Quality and Reliability
    screening_quality = models.CharField(
        max_length=15,
        choices=[
            ('excellent', 'Excellent'),
            ('good', 'Good'),
            ('adequate', 'Adequate'),
            ('poor', 'Poor'),
            ('inadequate', 'Inadequate')
        ],
        null=True,
        blank=True,
        help_text="Quality of the screening procedure"
    )
    
    technical_adequacy = models.BooleanField(
        null=True,
        blank=True,
        help_text="Whether screening was technically adequate"
    )
    
    repeat_needed = models.BooleanField(
        default=False,
        help_text="Whether screening needs to be repeated"
    )
    
    repeat_reason = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Reason for needing to repeat screening"
    )
    
    # Reminders and Notifications
    reminder_enabled = models.BooleanField(
        default=True,
        help_text="Whether reminders are enabled for this screening"
    )
    
    reminder_advance_days = models.IntegerField(
        default=30,
        validators=[MinValueValidator(1), MaxValueValidator(365)],
        help_text="Days in advance to send reminder"
    )
    
    last_reminder_sent = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When last reminder was sent"
    )
    
    # Age-Specific Guidelines
    age_at_screening = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(120)],
        help_text="Patient's age at time of screening"
    )
    
    meets_age_guidelines = models.BooleanField(
        null=True,
        blank=True,
        help_text="Whether screening meets age-based guidelines"
    )
    
    guideline_source = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Source of screening guidelines (e.g., ACS, USPSTF)"
    )
    
    # Notes and Documentation
    screening_notes = models.TextField(
        blank=True,
        null=True,
        help_text="Additional notes about the screening"
    )
    
    provider_notes = models.TextField(
        blank=True,
        null=True,
        help_text="Healthcare provider's notes"
    )
    
    patient_questions = models.TextField(
        blank=True,
        null=True,
        help_text="Patient questions or concerns"
    )
    
    educational_materials_provided = models.JSONField(
        default=list,
        blank=True,
        help_text="Educational materials provided to patient"
    )
    
    # Metadata
    created_by = models.ForeignKey(
        'api.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_health_screenings',
        help_text="User who created this screening record"
    )
    
    last_updated_by = models.ForeignKey(
        'api.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        related_name='updated_health_screenings',
        help_text="User who last updated this screening record"
    )
    
    # External References
    external_system_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="ID from external healthcare system"
    )
    
    report_file_path = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        help_text="Path to screening report file"
    )
    
    class Meta:
        verbose_name = "Health Screening"
        verbose_name_plural = "Health Screenings"
        indexes = [
            models.Index(fields=['womens_health_profile', 'screening_type']),
            models.Index(fields=['status', 'next_due_date']),
            models.Index(fields=['scheduled_date']),
            models.Index(fields=['completed_date']),
            models.Index(fields=['screening_type', 'status']),
        ]
        ordering = ['-scheduled_date', '-completed_date']
    
    def __str__(self):
        user_name = self.womens_health_profile.user.get_full_name() or self.womens_health_profile.user.username
        screening_name = self.custom_screening_name if self.screening_type == 'custom' else self.get_screening_type_display()
        return f"{screening_name} - {user_name}"
    
    def save(self, *args, **kwargs):
        # Auto-calculate next due date if not provided
        if self.completed_date and not self.next_due_date and self.recommended_frequency_months:
            self.next_due_date = self.completed_date + timezone.timedelta(
                days=self.recommended_frequency_months * 30  # Approximate month as 30 days
            )
        
        # Auto-calculate age at screening
        if not self.age_at_screening and self.scheduled_date:
            user_dob = self.womens_health_profile.user.date_of_birth
            if user_dob:
                age_at_screening = (self.scheduled_date - user_dob).days // 365
                self.age_at_screening = age_at_screening
        
        # Update status based on dates
        self.update_status()
        
        super().save(*args, **kwargs)
    
    def update_status(self):
        """Update screening status based on current state"""
        if self.status in ['cancelled', 'not_applicable']:
            return  # Don't change these statuses automatically
        
        today = timezone.now().date()
        
        if self.completed_date:
            if self.result_status == 'pending':
                self.status = 'pending_results'
            else:
                self.status = 'completed'
        elif self.scheduled_date:
            if today > self.scheduled_date:
                self.status = 'overdue'
            else:
                self.status = 'scheduled'
        elif self.next_due_date and today > self.next_due_date:
            self.status = 'overdue'
    
    def is_due_soon(self, days_ahead=30):
        """Check if screening is due within specified days"""
        if not self.next_due_date:
            return False
        
        today = timezone.now().date()
        due_threshold = today + timezone.timedelta(days=days_ahead)
        
        return self.next_due_date <= due_threshold
    
    def days_until_due(self):
        """Calculate days until screening is due"""
        if not self.next_due_date:
            return None
        
        today = timezone.now().date()
        if today >= self.next_due_date:
            return 0  # Overdue
        
        return (self.next_due_date - today).days
    
    def days_since_last(self):
        """Calculate days since last screening of this type"""
        if not self.completed_date:
            return None
        
        today = timezone.now().date()
        return (today - self.completed_date).days
    
    def get_age_appropriate_frequency(self):
        """Get age-appropriate screening frequency recommendations"""
        user_age = self.age_at_screening or self.womens_health_profile.user.age
        if not user_age:
            return None
        
        # Age-based frequency recommendations (simplified)
        frequency_guidelines = {
            'pap_smear': {
                (21, 29): 36,  # Every 3 years
                (30, 65): 36,  # Every 3 years (or 60 months with HPV)
                (65, 120): None  # May stop if adequate screening
            },
            'mammogram': {
                (40, 49): 12,  # Annual (some guidelines)
                (50, 74): 24,  # Every 2 years
                (75, 120): 24  # Continue if life expectancy > 10 years
            },
            'bone_density': {
                (65, 120): 24  # Every 2 years
            },
            'colonoscopy': {
                (50, 75): 120  # Every 10 years
            }
        }
        
        guidelines = frequency_guidelines.get(self.screening_type, {})
        for age_range, frequency in guidelines.items():
            if age_range[0] <= user_age <= age_range[1]:
                return frequency
        
        return self.recommended_frequency_months
    
    def create_follow_up_screening(self):
        """Create a follow-up screening based on recommendations"""
        if not self.follow_up_required or not self.follow_up_date:
            return None
        
        follow_up_screening = HealthScreening.objects.create(
            womens_health_profile=self.womens_health_profile,
            screening_type=self.screening_type,
            custom_screening_name=self.custom_screening_name,
            scheduled_date=self.follow_up_date,
            reason_for_screening='follow_up',
            provider_name=self.provider_name,
            clinic_hospital_name=self.clinic_hospital_name,
            provider_type=self.provider_type,
            recommended_frequency_months=self.recommended_frequency_months,
            created_by=self.last_updated_by
        )
        
        return follow_up_screening
    
    def get_screening_history(self):
        """Get history of similar screenings"""
        return HealthScreening.objects.filter(
            womens_health_profile=self.womens_health_profile,
            screening_type=self.screening_type,
            status='completed'
        ).exclude(id=self.id).order_by('-completed_date')[:5]
    
    def calculate_adherence_score(self):
        """Calculate patient's adherence to screening schedule"""
        history = self.get_screening_history()
        if not history:
            return None
        
        total_screenings = len(history) + 1  # Include current
        on_time_screenings = 0
        
        for screening in history:
            if screening.next_due_date and screening.completed_date:
                # Consider screening on time if completed within 3 months of due date
                grace_period = timezone.timedelta(days=90)
                if screening.completed_date <= (screening.next_due_date + grace_period):
                    on_time_screenings += 1
        
        # Include current screening if completed on time
        if self.completed_date and self.scheduled_date:
            grace_period = timezone.timedelta(days=30)
            if self.completed_date <= (self.scheduled_date + grace_period):
                on_time_screenings += 1
        
        return round((on_time_screenings / total_screenings) * 100, 1)
    
    def get_risk_trend(self):
        """Analyze risk trend over time for this screening type"""
        history = self.get_screening_history()
        if not history:
            return None
        
        risk_scores = {'low': 1, 'moderate': 2, 'high': 3, 'very_high': 4}
        trend_data = []
        
        for screening in reversed(history):  # Chronological order
            if screening.risk_assessment and screening.completed_date:
                trend_data.append({
                    'date': screening.completed_date.isoformat(),
                    'risk_score': risk_scores.get(screening.risk_assessment, 0),
                    'risk_level': screening.risk_assessment
                })
        
        # Include current screening
        if self.risk_assessment and self.completed_date:
            trend_data.append({
                'date': self.completed_date.isoformat(),
                'risk_score': risk_scores.get(self.risk_assessment, 0),
                'risk_level': self.risk_assessment
            })
        
        return trend_data
    
    def get_summary(self):
        """Return screening summary for API responses"""
        return {
            'id': self.id,
            'screening_type': self.get_screening_type_display(),
            'screening_name': self.custom_screening_name if self.screening_type == 'custom' else self.get_screening_type_display(),
            'status': self.get_status_display(),
            'scheduled_date': self.scheduled_date.isoformat() if self.scheduled_date else None,
            'completed_date': self.completed_date.isoformat() if self.completed_date else None,
            'next_due_date': self.next_due_date.isoformat() if self.next_due_date else None,
            'days_until_due': self.days_until_due(),
            'is_due_soon': self.is_due_soon(),
            'result_status': self.get_result_status_display() if self.result_status else None,
            'risk_assessment': self.get_risk_assessment_display() if self.risk_assessment else None,
            'follow_up_required': self.follow_up_required,
            'follow_up_date': self.follow_up_date.isoformat() if self.follow_up_date else None,
            'provider': self.provider_name,
            'clinic': self.clinic_hospital_name,
            'age_at_screening': self.age_at_screening,
            'adherence_score': self.calculate_adherence_score()
        }