# api/models/medical/womens_health_profile.py

from django.db import models
from django.utils import timezone
from ..base import TimestampedModel
from ..user.custom_user import CustomUser


class WomensHealthProfile(TimestampedModel):
    """
    Comprehensive women's health profile including reproductive health,
    pregnancy status, and health preferences
    """
    # Relationship
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='womens_health_profile',
        help_text="User this women's health profile belongs to"
    )
    
    # Basic Reproductive Health Information
    age_at_menarche = models.IntegerField(
        null=True, 
        blank=True,
        help_text="Age at first menstrual period"
    )
    
    average_cycle_length = models.IntegerField(
        default=28,
        help_text="Average menstrual cycle length in days"
    )
    
    average_period_duration = models.IntegerField(
        default=5,
        help_text="Average period duration in days"
    )
    
    # Pregnancy Status
    PREGNANCY_STATUS_CHOICES = [
        ('not_pregnant', 'Not Pregnant'),
        ('trying_to_conceive', 'Trying to Conceive'),
        ('pregnant', 'Pregnant'),
        ('postpartum', 'Postpartum'),
        ('breastfeeding', 'Breastfeeding'),
        ('menopause', 'Menopause'),
        ('unknown', 'Unknown')
    ]
    
    pregnancy_status = models.CharField(
        max_length=20,
        choices=PREGNANCY_STATUS_CHOICES,
        default='not_pregnant',
        help_text="Current pregnancy status"
    )
    
    # Current Pregnancy Information (if applicable)
    current_pregnancy_week = models.IntegerField(
        null=True,
        blank=True,
        help_text="Current week of pregnancy (1-42)"
    )
    
    estimated_due_date = models.DateField(
        null=True,
        blank=True,
        help_text="Estimated due date for current pregnancy"
    )
    
    last_menstrual_period = models.DateField(
        null=True,
        blank=True,
        help_text="Date of last menstrual period"
    )
    
    # Pregnancy History
    total_pregnancies = models.IntegerField(
        default=0,
        help_text="Total number of pregnancies (gravida)"
    )
    
    live_births = models.IntegerField(
        default=0,
        help_text="Number of live births (para)"
    )
    
    miscarriages = models.IntegerField(
        default=0,
        help_text="Number of miscarriages"
    )
    
    abortions = models.IntegerField(
        default=0,
        help_text="Number of abortions"
    )
    
    # Contraception
    CONTRACEPTION_CHOICES = [
        ('none', 'None'),
        ('oral_contraceptive', 'Oral Contraceptive (Birth Control Pill)'),
        ('iud_hormonal', 'IUD - Hormonal'),
        ('iud_copper', 'IUD - Copper'),
        ('implant', 'Contraceptive Implant'),
        ('injection', 'Contraceptive Injection'),
        ('patch', 'Contraceptive Patch'),
        ('ring', 'Vaginal Ring'),
        ('condoms', 'Condoms'),
        ('diaphragm', 'Diaphragm'),
        ('spermicide', 'Spermicide'),
        ('natural_family_planning', 'Natural Family Planning'),
        ('sterilization_tubal', 'Tubal Ligation'),
        ('sterilization_partner', 'Partner Sterilization'),
        ('emergency', 'Emergency Contraception'),
        ('other', 'Other')
    ]
    
    current_contraception = models.CharField(
        max_length=30,
        choices=CONTRACEPTION_CHOICES,
        default='none',
        help_text="Current contraceptive method"
    )
    
    contraception_start_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date current contraception method was started"
    )
    
    # Fertility Tracking Preferences
    fertility_tracking_enabled = models.BooleanField(
        default=False,
        help_text="Whether user wants to track fertility signs"
    )
    
    temperature_tracking = models.BooleanField(
        default=False,
        help_text="Track basal body temperature"
    )
    
    cervical_mucus_tracking = models.BooleanField(
        default=False,
        help_text="Track cervical mucus changes"
    )
    
    ovulation_test_tracking = models.BooleanField(
        default=False,
        help_text="Track ovulation test results"
    )
    
    # Health Conditions
    pcos = models.BooleanField(
        default=False,
        help_text="Polycystic Ovary Syndrome"
    )
    
    endometriosis = models.BooleanField(
        default=False,
        help_text="Endometriosis diagnosis"
    )
    
    fibroids = models.BooleanField(
        default=False,
        help_text="Uterine fibroids"
    )
    
    thyroid_disorder = models.BooleanField(
        default=False,
        help_text="Thyroid disorder"
    )
    
    diabetes = models.BooleanField(
        default=False,
        help_text="Diabetes (Type 1 or 2)"
    )
    
    gestational_diabetes_history = models.BooleanField(
        default=False,
        help_text="History of gestational diabetes"
    )
    
    hypertension = models.BooleanField(
        default=False,
        help_text="High blood pressure"
    )
    
    # Family History
    family_history_breast_cancer = models.BooleanField(
        default=False,
        help_text="Family history of breast cancer"
    )
    
    family_history_ovarian_cancer = models.BooleanField(
        default=False,
        help_text="Family history of ovarian cancer"
    )
    
    family_history_cervical_cancer = models.BooleanField(
        default=False,
        help_text="Family history of cervical cancer"
    )
    
    family_history_diabetes = models.BooleanField(
        default=False,
        help_text="Family history of diabetes"
    )
    
    family_history_heart_disease = models.BooleanField(
        default=False,
        help_text="Family history of heart disease"
    )
    
    # Lifestyle Factors Specific to Women's Health
    exercise_frequency = models.CharField(
        max_length=20,
        choices=[
            ('daily', 'Daily'),
            ('several_times_week', 'Several times per week'),
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
            ('rarely', 'Rarely'),
            ('never', 'Never')
        ],
        default='weekly',
        help_text="Exercise frequency"
    )
    
    stress_level = models.CharField(
        max_length=20,
        choices=[
            ('low', 'Low'),
            ('moderate', 'Moderate'),
            ('high', 'High'),
            ('severe', 'Severe')
        ],
        default='moderate',
        help_text="Self-reported stress level"
    )
    
    sleep_quality = models.CharField(
        max_length=20,
        choices=[
            ('excellent', 'Excellent'),
            ('good', 'Good'),
            ('fair', 'Fair'),
            ('poor', 'Poor'),
            ('very_poor', 'Very Poor')
        ],
        default='good',
        help_text="Sleep quality assessment"
    )
    
    # Preferences and Goals
    health_goals_list = models.JSONField(
        default=list,
        blank=True,
        help_text="List of current health goals"
    )
    
    notification_preferences = models.JSONField(
        default=dict,
        blank=True,
        help_text="Notification preferences for reminders"
    )
    
    privacy_settings = models.JSONField(
        default=dict,
        blank=True,
        help_text="Privacy settings for health data sharing"
    )
    
    # Medical Provider Information
    primary_gynecologist = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Name of primary gynecologist"
    )
    
    last_pap_smear = models.DateField(
        null=True,
        blank=True,
        help_text="Date of last pap smear"
    )
    
    last_mammogram = models.DateField(
        null=True,
        blank=True,
        help_text="Date of last mammogram"
    )
    
    last_gynecological_exam = models.DateField(
        null=True,
        blank=True,
        help_text="Date of last gynecological examination"
    )
    
    # Emergency Contact for Pregnancy
    emergency_contact_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Emergency contact name during pregnancy"
    )
    
    emergency_contact_phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Emergency contact phone number"
    )
    
    emergency_contact_relationship = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Relationship to emergency contact"
    )
    
    # Data Validation and Quality
    profile_completion_percentage = models.IntegerField(
        default=0,
        help_text="Percentage of profile completion (0-100)"
    )
    
    last_updated_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='updated_womens_health_profiles',
        help_text="User who last updated this profile"
    )
    
    class Meta:
        verbose_name = "Women's Health Profile"
        verbose_name_plural = "Women's Health Profiles"
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['pregnancy_status']),
            models.Index(fields=['fertility_tracking_enabled']),
            models.Index(fields=['estimated_due_date']),
        ]
    
    def __str__(self):
        return f"Women's Health Profile for {self.user.get_full_name() or self.user.username}"
    
    def save(self, *args, **kwargs):
        # Calculate profile completion percentage
        self.calculate_completion_percentage()
        super().save(*args, **kwargs)
    
    def calculate_completion_percentage(self):
        """Calculate what percentage of the profile is completed"""
        total_fields = 0
        completed_fields = 0
        
        # Basic fields
        basic_fields = [
            'age_at_menarche', 'average_cycle_length', 'average_period_duration',
            'pregnancy_status', 'current_contraception'
        ]
        
        for field in basic_fields:
            total_fields += 1
            if getattr(self, field):
                completed_fields += 1
        
        # Optional but important fields
        optional_fields = [
            'last_menstrual_period', 'primary_gynecologist', 
            'last_pap_smear', 'exercise_frequency', 'stress_level'
        ]
        
        for field in optional_fields:
            total_fields += 1
            if getattr(self, field):
                completed_fields += 1
        
        self.profile_completion_percentage = int((float(completed_fields) / float(total_fields)) * 100) if total_fields > 0 else 0
    
    @property
    def is_pregnant(self):
        """Check if user is currently pregnant"""
        return self.pregnancy_status == 'pregnant'
    
    @property
    def is_trying_to_conceive(self):
        """Check if user is trying to conceive"""
        return self.pregnancy_status == 'trying_to_conceive'
    
    @property
    def needs_fertility_tracking(self):
        """Check if user might benefit from fertility tracking"""
        return self.pregnancy_status in ['trying_to_conceive', 'not_pregnant'] and self.fertility_tracking_enabled
    
    @property
    def current_cycle_day(self):
        """Calculate current cycle day based on last menstrual period"""
        if not self.last_menstrual_period:
            return None
        
        today = timezone.now().date()
        days_since_lmp = (today - self.last_menstrual_period).days
        
        if days_since_lmp < 0:
            return None
        
        # Calculate cycle day (1-based)
        cycle_day = (days_since_lmp % self.average_cycle_length) + 1
        return cycle_day if cycle_day <= self.average_cycle_length else 1
    
    @property
    def estimated_ovulation_date(self):
        """Estimate next ovulation date based on cycle length"""
        if not self.last_menstrual_period:
            return None
        
        # Typically ovulation occurs 14 days before next period
        ovulation_day = self.average_cycle_length - 14
        if ovulation_day <= 0:
            ovulation_day = self.average_cycle_length // 2
        
        estimated_ovulation = self.last_menstrual_period + timezone.timedelta(days=ovulation_day)
        return estimated_ovulation
    
    @property
    def estimated_next_period(self):
        """Estimate next period date"""
        if not self.last_menstrual_period:
            return None
        
        return self.last_menstrual_period + timezone.timedelta(days=self.average_cycle_length)
    
    def get_fertility_window(self):
        """Calculate fertile window (5 days before + day of ovulation)"""
        ovulation_date = self.estimated_ovulation_date
        if not ovulation_date:
            return None
        
        fertile_start = ovulation_date - timezone.timedelta(days=5)
        fertile_end = ovulation_date
        
        return {
            'start': fertile_start,
            'end': fertile_end,
            'ovulation': ovulation_date
        }
    
    def get_health_summary(self):
        """Return a summary of key health information"""
        return {
            'pregnancy_status': self.get_pregnancy_status_display(),
            'cycle_length': f"{self.average_cycle_length} days",
            'contraception': self.get_current_contraception_display(),
            'fertility_tracking': self.fertility_tracking_enabled,
            'health_conditions': self.get_health_conditions(),
            'profile_completion': f"{self.profile_completion_percentage}%"
        }
    
    def get_health_conditions(self):
        """Return list of current health conditions"""
        conditions = []
        condition_fields = [
            ('pcos', 'PCOS'),
            ('endometriosis', 'Endometriosis'),
            ('fibroids', 'Uterine Fibroids'),
            ('thyroid_disorder', 'Thyroid Disorder'),
            ('diabetes', 'Diabetes'),
            ('hypertension', 'Hypertension')
        ]
        
        for field, display_name in condition_fields:
            if getattr(self, field):
                conditions.append(display_name)
        
        return conditions if conditions else ['None reported']