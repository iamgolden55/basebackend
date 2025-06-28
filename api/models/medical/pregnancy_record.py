# api/models/medical/pregnancy_record.py

from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from ..base import TimestampedModel
from .womens_health_profile import WomensHealthProfile


class PregnancyRecord(TimestampedModel):
    """
    Model for tracking individual pregnancy records and journey data
    """
    # Relationship
    womens_health_profile = models.ForeignKey(
        WomensHealthProfile,
        on_delete=models.CASCADE,
        related_name='pregnancy_records',
        help_text="Women's health profile this pregnancy belongs to"
    )
    
    # Pregnancy Identification
    pregnancy_number = models.IntegerField(
        help_text="Sequential pregnancy number for this user (1st, 2nd, etc.)"
    )
    
    is_current_pregnancy = models.BooleanField(
        default=False,
        help_text="Whether this is the current ongoing pregnancy"
    )
    
    # Pregnancy Timeline
    last_menstrual_period = models.DateField(
        help_text="Date of last menstrual period (LMP)"
    )
    
    estimated_due_date = models.DateField(
        help_text="Estimated due date (EDD) based on LMP or ultrasound"
    )
    
    conception_date = models.DateField(
        null=True,
        blank=True,
        help_text="Estimated conception date"
    )
    
    pregnancy_start_date = models.DateField(
        help_text="Date pregnancy was confirmed"
    )
    
    # Pregnancy Status and Outcome
    PREGNANCY_STATUS_CHOICES = [
        ('ongoing', 'Ongoing'),
        ('completed_delivery', 'Completed - Live Birth'),
        ('miscarriage', 'Miscarriage'),
        ('stillbirth', 'Stillbirth'),
        ('ectopic', 'Ectopic Pregnancy'),
        ('molar', 'Molar Pregnancy'),
        ('terminated', 'Terminated'),
        ('unknown', 'Unknown Outcome')
    ]
    
    pregnancy_status = models.CharField(
        max_length=20,
        choices=PREGNANCY_STATUS_CHOICES,
        default='ongoing',
        help_text="Current status or outcome of pregnancy"
    )
    
    completion_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date pregnancy ended (delivery, loss, etc.)"
    )
    
    gestational_age_at_completion = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(45)],
        help_text="Gestational age in weeks when pregnancy ended"
    )
    
    # Pregnancy Details
    PREGNANCY_TYPE_CHOICES = [
        ('singleton', 'Singleton'),
        ('twins', 'Twins'),
        ('triplets', 'Triplets'),
        ('higher_order', 'Higher Order Multiple'),
        ('unknown', 'Unknown')
    ]
    
    pregnancy_type = models.CharField(
        max_length=20,
        choices=PREGNANCY_TYPE_CHOICES,
        default='singleton',
        help_text="Type of pregnancy (singleton, multiple, etc.)"
    )
    
    CONCEPTION_METHOD_CHOICES = [
        ('natural', 'Natural Conception'),
        ('ivf', 'In Vitro Fertilization (IVF)'),
        ('iui', 'Intrauterine Insemination (IUI)'),
        ('icsi', 'Intracytoplasmic Sperm Injection (ICSI)'),
        ('donor_egg', 'Donor Egg'),
        ('donor_sperm', 'Donor Sperm'),
        ('fertility_medication', 'Fertility Medication'),
        ('other_art', 'Other Assisted Reproductive Technology'),
        ('unknown', 'Unknown')
    ]
    
    conception_method = models.CharField(
        max_length=25,
        choices=CONCEPTION_METHOD_CHOICES,
        default='natural',
        help_text="Method of conception"
    )
    
    # Risk Factors and Classifications
    RISK_LEVEL_CHOICES = [
        ('low', 'Low Risk'),
        ('moderate', 'Moderate Risk'),
        ('high', 'High Risk'),
        ('very_high', 'Very High Risk')
    ]
    
    risk_level = models.CharField(
        max_length=15,
        choices=RISK_LEVEL_CHOICES,
        default='low',
        help_text="Overall pregnancy risk assessment"
    )
    
    risk_factors = models.JSONField(
        default=list,
        blank=True,
        help_text="List of identified pregnancy risk factors"
    )
    
    # Prenatal Care
    first_prenatal_visit_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date of first prenatal care visit"
    )
    
    first_prenatal_visit_week = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(42)],
        help_text="Gestational week of first prenatal visit"
    )
    
    total_prenatal_visits = models.IntegerField(
        default=0,
        help_text="Total number of prenatal care visits"
    )
    
    adequate_prenatal_care = models.BooleanField(
        null=True,
        blank=True,
        help_text="Whether prenatal care was adequate (Kotelchuck Index)"
    )
    
    # Healthcare Providers
    primary_obstetrician = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Name of primary obstetrician"
    )
    
    hospital_for_delivery = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Planned hospital for delivery"
    )
    
    midwife_care = models.BooleanField(
        default=False,
        help_text="Whether receiving midwife care"
    )
    
    doula_support = models.BooleanField(
        default=False,
        help_text="Whether using doula support"
    )
    
    # Pregnancy Complications
    pregnancy_complications = models.JSONField(
        default=list,
        blank=True,
        help_text="List of pregnancy complications"
    )
    
    gestational_diabetes = models.BooleanField(
        default=False,
        help_text="Diagnosed with gestational diabetes"
    )
    
    preeclampsia = models.BooleanField(
        default=False,
        help_text="Diagnosed with preeclampsia"
    )
    
    placenta_previa = models.BooleanField(
        default=False,
        help_text="Diagnosed with placenta previa"
    )
    
    preterm_labor_risk = models.BooleanField(
        default=False,
        help_text="At risk for preterm labor"
    )
    
    # Delivery Information
    DELIVERY_TYPE_CHOICES = [
        ('vaginal_spontaneous', 'Spontaneous Vaginal'),
        ('vaginal_assisted', 'Assisted Vaginal (Forceps/Vacuum)'),
        ('cesarean_planned', 'Planned Cesarean'),
        ('cesarean_emergency', 'Emergency Cesarean'),
        ('vbac', 'Vaginal Birth After Cesarean (VBAC)'),
        ('unknown', 'Unknown'),
        ('not_applicable', 'Not Applicable')
    ]
    
    delivery_type = models.CharField(
        max_length=20,
        choices=DELIVERY_TYPE_CHOICES,
        null=True,
        blank=True,
        help_text="Type of delivery"
    )
    
    delivery_location = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Location where delivery occurred"
    )
    
    labor_duration_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Duration of labor in hours"
    )
    
    delivery_complications = models.JSONField(
        default=list,
        blank=True,
        help_text="List of delivery complications"
    )
    
    # Postpartum Information
    postpartum_complications = models.JSONField(
        default=list,
        blank=True,
        help_text="List of postpartum complications"
    )
    
    breastfeeding_initiated = models.BooleanField(
        null=True,
        blank=True,
        help_text="Whether breastfeeding was initiated"
    )
    
    breastfeeding_duration_weeks = models.IntegerField(
        null=True,
        blank=True,
        help_text="Duration of breastfeeding in weeks"
    )
    
    postpartum_depression_screening = models.BooleanField(
        null=True,
        blank=True,
        help_text="Whether screened for postpartum depression"
    )
    
    postpartum_depression_result = models.CharField(
        max_length=20,
        choices=[
            ('negative', 'Negative'),
            ('positive', 'Positive'),
            ('borderline', 'Borderline'),
            ('not_screened', 'Not Screened')
        ],
        default='not_screened',
        help_text="Result of postpartum depression screening"
    )
    
    # Birth Outcomes (for completed pregnancies)
    birth_weight_grams = models.IntegerField(
        null=True,
        blank=True,
        help_text="Birth weight in grams"
    )
    
    birth_length_cm = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
        help_text="Birth length in centimeters"
    )
    
    head_circumference_cm = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
        help_text="Head circumference at birth in centimeters"
    )
    
    APGAR_SCORE_CHOICES = [(i, str(i)) for i in range(0, 11)]
    
    apgar_1_minute = models.IntegerField(
        choices=APGAR_SCORE_CHOICES,
        null=True,
        blank=True,
        help_text="APGAR score at 1 minute"
    )
    
    apgar_5_minute = models.IntegerField(
        choices=APGAR_SCORE_CHOICES,
        null=True,
        blank=True,
        help_text="APGAR score at 5 minutes"
    )
    
    # Genetic Testing and Screening
    genetic_screening_completed = models.BooleanField(
        default=False,
        help_text="Whether genetic screening was completed"
    )
    
    genetic_screening_results = models.JSONField(
        default=dict,
        blank=True,
        help_text="Results of genetic screening tests"
    )
    
    amniocentesis_performed = models.BooleanField(
        default=False,
        help_text="Whether amniocentesis was performed"
    )
    
    cvs_performed = models.BooleanField(
        default=False,
        help_text="Whether chorionic villus sampling was performed"
    )
    
    # Lifestyle During Pregnancy
    prenatal_vitamins = models.BooleanField(
        default=False,
        help_text="Taking prenatal vitamins"
    )
    
    folic_acid_supplement = models.BooleanField(
        default=False,
        help_text="Taking folic acid supplements"
    )
    
    smoking_during_pregnancy = models.BooleanField(
        default=False,
        help_text="Smoking during pregnancy"
    )
    
    alcohol_during_pregnancy = models.BooleanField(
        default=False,
        help_text="Alcohol consumption during pregnancy"
    )
    
    exercise_during_pregnancy = models.CharField(
        max_length=20,
        choices=[
            ('none', 'None'),
            ('light', 'Light'),
            ('moderate', 'Moderate'),
            ('vigorous', 'Vigorous')
        ],
        null=True,
        blank=True,
        help_text="Level of exercise during pregnancy"
    )
    
    # Weight and Nutrition
    pre_pregnancy_weight_kg = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Weight before pregnancy in kilograms"
    )
    
    weight_gain_kg = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Total weight gain during pregnancy in kilograms"
    )
    
    adequate_weight_gain = models.BooleanField(
        null=True,
        blank=True,
        help_text="Whether weight gain was adequate for pre-pregnancy BMI"
    )
    
    # Education and Support
    childbirth_classes = models.BooleanField(
        default=False,
        help_text="Attended childbirth preparation classes"
    )
    
    breastfeeding_classes = models.BooleanField(
        default=False,
        help_text="Attended breastfeeding classes"
    )
    
    support_person = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Primary support person during pregnancy"
    )
    
    # Birth Plan Preferences
    birth_plan_created = models.BooleanField(
        default=False,
        help_text="Whether a birth plan was created"
    )
    
    birth_plan_preferences = models.JSONField(
        default=dict,
        blank=True,
        help_text="Birth plan preferences and wishes"
    )
    
    # Notes and Additional Information
    pregnancy_notes = models.TextField(
        blank=True,
        null=True,
        help_text="Additional notes about this pregnancy"
    )
    
    # Metadata
    created_by = models.ForeignKey(
        'api.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_pregnancy_records',
        help_text="User who created this pregnancy record"
    )
    
    last_updated_by = models.ForeignKey(
        'api.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        related_name='updated_pregnancy_records',
        help_text="User who last updated this pregnancy record"
    )
    
    class Meta:
        verbose_name = "Pregnancy Record"
        verbose_name_plural = "Pregnancy Records"
        indexes = [
            models.Index(fields=['womens_health_profile', 'pregnancy_number']),
            models.Index(fields=['is_current_pregnancy']),
            models.Index(fields=['pregnancy_status']),
            models.Index(fields=['estimated_due_date']),
            models.Index(fields=['last_menstrual_period']),
        ]
        ordering = ['-pregnancy_number', '-pregnancy_start_date']
        constraints = [
            models.UniqueConstraint(
                fields=['womens_health_profile'],
                condition=models.Q(is_current_pregnancy=True),
                name='unique_current_pregnancy_per_profile'
            )
        ]
    
    def __str__(self):
        user_name = self.womens_health_profile.user.get_full_name() or self.womens_health_profile.user.username
        return f"Pregnancy #{self.pregnancy_number} - {user_name}"
    
    def save(self, *args, **kwargs):
        # Auto-increment pregnancy number if not set
        if not self.pregnancy_number:
            last_pregnancy = PregnancyRecord.objects.filter(
                womens_health_profile=self.womens_health_profile
            ).order_by('-pregnancy_number').first()
            
            self.pregnancy_number = (last_pregnancy.pregnancy_number + 1) if last_pregnancy else 1
        
        # Ensure only one current pregnancy per profile
        if self.is_current_pregnancy:
            PregnancyRecord.objects.filter(
                womens_health_profile=self.womens_health_profile,
                is_current_pregnancy=True
            ).exclude(id=self.id).update(is_current_pregnancy=False)
        
        # Calculate conception date if not provided
        if not self.conception_date and self.last_menstrual_period:
            self.conception_date = self.last_menstrual_period + timezone.timedelta(days=14)
        
        # Calculate estimated due date if not provided
        if not self.estimated_due_date and self.last_menstrual_period:
            self.estimated_due_date = self.last_menstrual_period + timezone.timedelta(days=280)
        
        super().save(*args, **kwargs)
    
    @property
    def current_gestational_age(self):
        """Calculate current gestational age in weeks and days"""
        if not self.is_current_pregnancy or self.pregnancy_status != 'ongoing':
            return None
        
        today = timezone.now().date()
        if today < self.last_menstrual_period:
            return None
        
        days_pregnant = (today - self.last_menstrual_period).days
        weeks = days_pregnant // 7
        days = days_pregnant % 7
        
        return {
            'weeks': weeks,
            'days': days,
            'total_days': days_pregnant,
            'display': f"{weeks}w {days}d"
        }
    
    @property
    def trimester(self):
        """Determine current trimester"""
        gestational_age = self.current_gestational_age
        if not gestational_age:
            return None
        
        weeks = gestational_age['weeks']
        if weeks <= 12:
            return {'number': 1, 'name': 'First Trimester'}
        elif weeks <= 27:
            return {'number': 2, 'name': 'Second Trimester'}
        else:
            return {'number': 3, 'name': 'Third Trimester'}
    
    @property
    def days_until_due_date(self):
        """Calculate days until due date"""
        if not self.is_current_pregnancy or not self.estimated_due_date:
            return None
        
        today = timezone.now().date()
        if today > self.estimated_due_date:
            return 0  # Past due date
        
        return (self.estimated_due_date - today).days
    
    @property
    def is_high_risk(self):
        """Check if pregnancy is considered high risk"""
        return self.risk_level in ['high', 'very_high'] or len(self.risk_factors) >= 3
    
    def get_birth_weight_category(self):
        """Categorize birth weight"""
        if not self.birth_weight_grams:
            return None
        
        if self.birth_weight_grams < 1500:
            return 'very_low'  # Very Low Birth Weight
        elif self.birth_weight_grams < 2500:
            return 'low'  # Low Birth Weight
        elif self.birth_weight_grams > 4000:
            return 'high'  # Macrosomia
        else:
            return 'normal'  # Normal Birth Weight
    
    def calculate_pregnancy_bmi_category(self):
        """Calculate BMI category at start of pregnancy"""
        if not self.pre_pregnancy_weight_kg:
            return None
        
        # Get height from user profile if available
        height_m = getattr(self.womens_health_profile.user, 'height_m', None)
        if not height_m:
            return None
        
        bmi = self.pre_pregnancy_weight_kg / (height_m ** 2)
        
        if bmi < 18.5:
            return 'underweight'
        elif bmi < 25:
            return 'normal'
        elif bmi < 30:
            return 'overweight'
        else:
            return 'obese'
    
    def get_pregnancy_summary(self):
        """Return pregnancy summary for API responses"""
        summary = {
            'pregnancy_number': self.pregnancy_number,
            'status': self.get_pregnancy_status_display(),
            'is_current': self.is_current_pregnancy,
            'due_date': self.estimated_due_date.isoformat() if self.estimated_due_date else None,
            'risk_level': self.get_risk_level_display(),
            'type': self.get_pregnancy_type_display(),
        }
        
        if self.is_current_pregnancy and self.pregnancy_status == 'ongoing':
            gestational_age = self.current_gestational_age
            if gestational_age:
                summary.update({
                    'gestational_age': gestational_age['display'],
                    'trimester': self.trimester,
                    'days_until_due': self.days_until_due_date
                })
        
        if self.pregnancy_status in ['completed_delivery']:
            summary.update({
                'delivery_type': self.get_delivery_type_display() if self.delivery_type else None,
                'birth_weight': f"{self.birth_weight_grams}g" if self.birth_weight_grams else None,
                'completion_date': self.completion_date.isoformat() if self.completion_date else None
            })
        
        return summary