# api/models/medical/lifestyle.py

from django.db import models
from django.utils import timezone
from ..base import TimestampedModel
from .medical_record import MedicalRecord


class LifestyleInformation(TimestampedModel):
    """
    Model for storing patient lifestyle and socioeconomic information
    relevant to health outcomes and risk assessment
    """
    # Relationship
    medical_record = models.OneToOneField(
        MedicalRecord,
        on_delete=models.CASCADE,
        related_name='lifestyle_information',
        help_text="Medical record this lifestyle information belongs to"
    )
    
    # Diet and Nutrition
    DIET_TYPE_CHOICES = [
        ('regular', 'Regular/No Restrictions'),
        ('vegetarian', 'Vegetarian'),
        ('vegan', 'Vegan'),
        ('pescatarian', 'Pescatarian'),
        ('gluten_free', 'Gluten-Free'),
        ('dairy_free', 'Dairy-Free'),
        ('ketogenic', 'Ketogenic'),
        ('paleo', 'Paleo'),
        ('mediterranean', 'Mediterranean'),
        ('low_carb', 'Low Carbohydrate'),
        ('low_fat', 'Low Fat'),
        ('low_sodium', 'Low Sodium'),
        ('diabetic', 'Diabetic'),
        ('renal', 'Renal/Kidney'),
        ('halal', 'Halal'),
        ('kosher', 'Kosher'),
        ('other', 'Other')
    ]
    
    diet_type = models.CharField(
        max_length=20,
        choices=DIET_TYPE_CHOICES,
        blank=True,
        null=True,
        help_text="Primary diet type"
    )
    
    diet_details = models.TextField(
        blank=True,
        null=True,
        help_text="Additional details about diet"
    )
    
    daily_meals = models.IntegerField(
        blank=True,
        null=True,
        help_text="Typical number of meals per day"
    )
    
    food_allergies = models.TextField(
        blank=True,
        null=True,
        help_text="Food allergies or intolerances"
    )
    
    nutrition_quality = models.CharField(
        max_length=20,
        choices=[
            ('excellent', 'Excellent'),
            ('good', 'Good'),
            ('fair', 'Fair'),
            ('poor', 'Poor'),
            ('unknown', 'Unknown')
        ],
        default='unknown',
        help_text="Overall nutrition quality assessment"
    )
    
    fruit_vegetable_servings = models.IntegerField(
        blank=True,
        null=True,
        help_text="Average daily fruit and vegetable servings"
    )
    
    # Physical Activity
    exercise_frequency = models.CharField(
        max_length=20,
        choices=[
            ('daily', 'Daily'),
            ('several_times_week', 'Several Times per Week'),
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
            ('rarely', 'Rarely'),
            ('never', 'Never')
        ],
        blank=True,
        null=True,
        help_text="Frequency of exercise"
    )
    
    exercise_duration = models.IntegerField(
        blank=True,
        null=True,
        help_text="Average exercise duration in minutes"
    )
    
    exercise_types = models.JSONField(
        default=list,
        blank=True,
        null=True,
        help_text="Types of exercise regularly performed"
    )
    
    activity_level = models.CharField(
        max_length=20,
        choices=[
            ('sedentary', 'Sedentary'),
            ('lightly_active', 'Lightly Active'),
            ('moderately_active', 'Moderately Active'),
            ('very_active', 'Very Active'),
            ('extremely_active', 'Extremely Active')
        ],
        blank=True,
        null=True,
        help_text="Overall physical activity level"
    )
    
    # Sleep Patterns
    average_sleep_hours = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        blank=True,
        null=True,
        help_text="Average hours of sleep per night"
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
        blank=True,
        null=True,
        help_text="Subjective sleep quality"
    )
    
    sleep_disorders = models.TextField(
        blank=True,
        null=True,
        help_text="Known sleep disorders"
    )
    
    # Substance Use
    # Tobacco
    tobacco_use = models.CharField(
        max_length=20,
        choices=[
            ('never', 'Never'),
            ('former', 'Former'),
            ('current', 'Current')
        ],
        blank=True,
        null=True,
        help_text="Tobacco use status"
    )
    
    tobacco_type = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Type of tobacco used (e.g., cigarettes, e-cigarettes, pipe)"
    )
    
    tobacco_frequency = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Frequency of tobacco use"
    )
    
    tobacco_start_age = models.IntegerField(
        blank=True,
        null=True,
        help_text="Age started using tobacco"
    )
    
    tobacco_quit_age = models.IntegerField(
        blank=True,
        null=True,
        help_text="Age quit using tobacco if former user"
    )
    
    tobacco_pack_years = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Pack-years for cigarette smokers"
    )
    
    # Alcohol
    alcohol_use = models.CharField(
        max_length=20,
        choices=[
            ('never', 'Never'),
            ('former', 'Former'),
            ('occasional', 'Occasional'),
            ('moderate', 'Moderate'),
            ('heavy', 'Heavy')
        ],
        blank=True,
        null=True,
        help_text="Alcohol use status"
    )
    
    alcohol_frequency = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Frequency of alcohol consumption"
    )
    
    alcohol_drinks_per_week = models.IntegerField(
        blank=True,
        null=True,
        help_text="Average alcoholic drinks per week"
    )
    
    alcohol_quit_age = models.IntegerField(
        blank=True,
        null=True,
        help_text="Age quit using alcohol if former user"
    )
    
    # Recreational Drugs
    recreational_drug_use = models.CharField(
        max_length=20,
        choices=[
            ('never', 'Never'),
            ('former', 'Former'),
            ('current', 'Current')
        ],
        blank=True,
        null=True,
        help_text="Recreational drug use status"
    )
    
    recreational_drugs = models.JSONField(
        default=list,
        blank=True,
        null=True,
        help_text="Types of recreational drugs used"
    )
    
    # Caffeine
    caffeine_use = models.CharField(
        max_length=20,
        choices=[
            ('none', 'None'),
            ('light', 'Light'),
            ('moderate', 'Moderate'),
            ('heavy', 'Heavy')
        ],
        blank=True,
        null=True,
        help_text="Caffeine consumption level"
    )
    
    caffeine_drinks_per_day = models.IntegerField(
        blank=True,
        null=True,
        help_text="Average caffeinated drinks per day"
    )
    
    # Occupation and Education
    occupation = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Current or most recent occupation"
    )
    
    occupation_category = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Category of occupation"
    )
    
    employment_status = models.CharField(
        max_length=50,
        choices=[
            ('full_time', 'Full-time'),
            ('part_time', 'Part-time'),
            ('self_employed', 'Self-employed'),
            ('unemployed', 'Unemployed'),
            ('retired', 'Retired'),
            ('disabled', 'Unable to work due to disability'),
            ('student', 'Student'),
            ('homemaker', 'Homemaker')
        ],
        blank=True,
        null=True,
        help_text="Current employment status"
    )
    
    education_level = models.CharField(
        max_length=50,
        choices=[
            ('none', 'No formal education'),
            ('primary', 'Primary/Elementary'),
            ('secondary', 'Secondary/High School'),
            ('vocational', 'Vocational/Technical'),
            ('associate', 'Associate Degree'),
            ('bachelor', 'Bachelor\'s Degree'),
            ('master', 'Master\'s Degree'),
            ('doctoral', 'Doctoral Degree'),
            ('professional', 'Professional Degree')
        ],
        blank=True,
        null=True,
        help_text="Highest level of education completed"
    )
    
    occupational_hazards = models.TextField(
        blank=True,
        null=True,
        help_text="Occupational hazards or exposures"
    )
    
    # Living Situation
    housing_type = models.CharField(
        max_length=50,
        choices=[
            ('house', 'House'),
            ('apartment', 'Apartment'),
            ('assisted_living', 'Assisted Living'),
            ('nursing_home', 'Nursing Home'),
            ('homeless', 'Homeless'),
            ('group_home', 'Group Home'),
            ('other', 'Other')
        ],
        blank=True,
        null=True,
        help_text="Type of housing"
    )
    
    household_members = models.IntegerField(
        blank=True,
        null=True,
        help_text="Number of people in household"
    )
    
    living_arrangement = models.CharField(
        max_length=50,
        choices=[
            ('alone', 'Lives Alone'),
            ('family', 'Lives with Family'),
            ('roommates', 'Lives with Roommates'),
            ('spouse', 'Lives with Spouse/Partner'),
            ('caregiver', 'Lives with Caregiver'),
            ('other', 'Other')
        ],
        blank=True,
        null=True,
        help_text="Living arrangement"
    )
    
    dependents = models.IntegerField(
        blank=True,
        null=True,
        help_text="Number of dependents"
    )
    
    # Socioeconomic Factors
    income_range = models.CharField(
        max_length=50,
        choices=[
            ('low', 'Low Income'),
            ('lower_middle', 'Lower Middle Income'),
            ('middle', 'Middle Income'),
            ('upper_middle', 'Upper Middle Income'),
            ('high', 'High Income'),
            ('decline', 'Decline to Answer')
        ],
        blank=True,
        null=True,
        help_text="Income range"
    )
    
    financial_strain = models.CharField(
        max_length=20,
        choices=[
            ('none', 'None'),
            ('low', 'Low'),
            ('moderate', 'Moderate'),
            ('high', 'High'),
            ('severe', 'Severe')
        ],
        blank=True,
        null=True,
        help_text="Level of financial strain"
    )
    
    insurance_status = models.CharField(
        max_length=50,
        choices=[
            ('private', 'Private Insurance'),
            ('public', 'Public Insurance'),
            ('military', 'Military Insurance'),
            ('none', 'No Insurance'),
            ('multiple', 'Multiple')
        ],
        blank=True,
        null=True,
        help_text="Health insurance status"
    )
    
    has_regular_healthcare = models.BooleanField(
        blank=True,
        null=True,
        help_text="Whether patient has regular access to healthcare"
    )
    
    # Transportation and Access
    transportation_access = models.CharField(
        max_length=50,
        choices=[
            ('own_vehicle', 'Own Vehicle'),
            ('public', 'Public Transportation'),
            ('rides_others', 'Rides from Others'),
            ('medical_transport', 'Medical Transportation'),
            ('limited', 'Limited Transportation'),
            ('none', 'No Transportation')
        ],
        blank=True,
        null=True,
        help_text="Primary mode of transportation"
    )
    
    distance_to_healthcare = models.IntegerField(
        blank=True,
        null=True,
        help_text="Distance to nearest healthcare facility in kilometers"
    )
    
    # Environmental Factors
    environmental_exposures = models.JSONField(
        default=list,
        blank=True,
        null=True,
        help_text="Environmental exposures or hazards"
    )
    
    neighborhood_safety = models.CharField(
        max_length=20,
        choices=[
            ('very_safe', 'Very Safe'),
            ('safe', 'Safe'),
            ('neutral', 'Neutral'),
            ('unsafe', 'Unsafe'),
            ('very_unsafe', 'Very Unsafe')
        ],
        blank=True,
        null=True,
        help_text="Perception of neighborhood safety"
    )
    
    access_to_healthy_food = models.CharField(
        max_length=20,
        choices=[
            ('excellent', 'Excellent'),
            ('good', 'Good'),
            ('fair', 'Fair'),
            ('poor', 'Poor'),
            ('very_poor', 'Very Poor')
        ],
        blank=True,
        null=True,
        help_text="Access to healthy food options"
    )
    
    # Psychosocial Factors
    stress_level = models.CharField(
        max_length=20,
        choices=[
            ('low', 'Low'),
            ('moderate', 'Moderate'),
            ('high', 'High'),
            ('severe', 'Severe')
        ],
        blank=True,
        null=True,
        help_text="Self-reported stress level"
    )
    
    social_support = models.CharField(
        max_length=20,
        choices=[
            ('excellent', 'Excellent'),
            ('good', 'Good'),
            ('fair', 'Fair'),
            ('poor', 'Poor'),
            ('none', 'None')
        ],
        blank=True,
        null=True,
        help_text="Level of social support"
    )
    
    spiritual_religious = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Spiritual or religious practices if relevant to health"
    )
    
    # Health Behaviors
    preventive_care = models.CharField(
        max_length=20,
        choices=[
            ('regular', 'Regular'),
            ('occasional', 'Occasional'),
            ('rare', 'Rare'),
            ('never', 'Never')
        ],
        blank=True,
        null=True,
        help_text="Frequency of preventive healthcare visits"
    )
    
    medication_adherence = models.CharField(
        max_length=20,
        choices=[
            ('excellent', 'Excellent'),
            ('good', 'Good'),
            ('fair', 'Fair'),
            ('poor', 'Poor'),
            ('not_applicable', 'Not Applicable')
        ],
        blank=True,
        null=True,
        help_text="Level of medication adherence"
    )
    
    health_literacy = models.CharField(
        max_length=20,
        choices=[
            ('high', 'High'),
            ('adequate', 'Adequate'),
            ('limited', 'Limited'),
            ('low', 'Low'),
            ('unknown', 'Unknown')
        ],
        blank=True,
        null=True,
        help_text="Assessment of health literacy"
    )
    
    # Digital Health
    internet_access = models.CharField(
        max_length=20,
        choices=[
            ('reliable', 'Reliable'),
            ('limited', 'Limited'),
            ('none', 'None')
        ],
        blank=True,
        null=True,
        help_text="Level of internet access"
    )
    
    uses_health_apps = models.BooleanField(
        blank=True,
        null=True,
        help_text="Whether patient uses health apps"
    )
    
    telehealth_capable = models.BooleanField(
        blank=True,
        null=True,
        help_text="Whether patient has capability for telehealth visits"
    )
    
    wearable_devices = models.JSONField(
        default=list,
        blank=True,
        null=True,
        help_text="Health wearables used (e.g., fitness tracker, CGM)"
    )
    
    # Risk Assessment
    lifestyle_risk_assessment = models.JSONField(
        default=dict,
        blank=True,
        null=True,
        help_text="Computed risk assessment based on lifestyle factors"
    )
    
    # Additional Information
    additional_info = models.TextField(
        blank=True,
        null=True,
        help_text="Additional lifestyle information not captured elsewhere"
    )
    
    # Metadata
    last_updated_by = models.ForeignKey(
        'api.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        related_name='updated_lifestyle_information',
        help_text="User who last updated this information"
    )
    
    class Meta:
        verbose_name = "Lifestyle Information"
        verbose_name_plural = "Lifestyle Information"
        indexes = [
            models.Index(fields=['medical_record']),
            models.Index(fields=['tobacco_use']),
            models.Index(fields=['alcohol_use']),
            models.Index(fields=['employment_status']),
        ]
    
    def __str__(self):
        return f"Lifestyle Information for {self.medical_record.hpn}"
    
    def save(self, *args, **kwargs):
        # Compute risk assessment
        self.calculate_lifestyle_risk()
        super().save(*args, **kwargs)
        
        # Update medical record complexity metrics
        if hasattr(self.medical_record, 'update_complexity_metrics'):
            self.medical_record.update_complexity_metrics()
    
    def calculate_lifestyle_risk(self):
        """Calculate risk factors based on lifestyle information"""
        risk_assessment = {
            'risk_factors': [],
            'protective_factors': [],
            'overall_risk': 'unknown'
        }
        
        # Tobacco risk
        if self.tobacco_use == 'current':
            risk_assessment['risk_factors'].append('Current tobacco use')
        elif self.tobacco_use == 'former':
            risk_assessment['risk_factors'].append('Former tobacco use')
        elif self.tobacco_use == 'never':
            risk_assessment['protective_factors'].append('Never used tobacco')
        
        # Alcohol risk
        if self.alcohol_use == 'heavy':
            risk_assessment['risk_factors'].append('Heavy alcohol use')
        elif self.alcohol_use in ['never', 'occasional']:
            risk_assessment['protective_factors'].append('Low or no alcohol use')
        
        # Physical activity
        if self.activity_level in ['moderately_active', 'very_active', 'extremely_active']:
            risk_assessment['protective_factors'].append('Regular physical activity')
        elif self.activity_level == 'sedentary':
            risk_assessment['risk_factors'].append('Sedentary lifestyle')
        
        # Diet
        if self.nutrition_quality in ['excellent', 'good']:
            risk_assessment['protective_factors'].append('Healthy diet')
        elif self.nutrition_quality == 'poor':
            risk_assessment['risk_factors'].append('Poor nutrition')
        
        # Sleep
        if self.average_sleep_hours and self.average_sleep_hours < 6:
            risk_assessment['risk_factors'].append('Insufficient sleep')
        elif self.average_sleep_hours and 7 <= self.average_sleep_hours <= 9:
            risk_assessment['protective_factors'].append('Healthy sleep duration')
        
        # Stress
        if self.stress_level in ['high', 'severe']:
            risk_assessment['risk_factors'].append('High stress levels')
        
        # Social support
        if self.social_support in ['poor', 'none']:
            risk_assessment['risk_factors'].append('Limited social support')
        elif self.social_support in ['excellent', 'good']:
            risk_assessment['protective_factors'].append('Strong social support')
        
        # Calculate overall risk
        risk_count = len(risk_assessment['risk_factors'])
        protective_count = len(risk_assessment['protective_factors'])
        
        if risk_count == 0 and protective_count >= 3:
            risk_assessment['overall_risk'] = 'low'
        elif risk_count >= 3 and protective_count <= 1:
            risk_assessment['overall_risk'] = 'high'
        elif risk_count > 0 or protective_count > 0:
            risk_assessment['overall_risk'] = 'moderate'
        
        self.lifestyle_risk_assessment = risk_assessment
    
    @property
    def smoking_status(self):
        """Formatted smoking status for clinical use"""
        if self.tobacco_use == 'never':
            return "Never smoker"
        elif self.tobacco_use == 'former':
            return f"Former smoker, quit at age {self.tobacco_quit_age}" if self.tobacco_quit_age else "Former smoker"
        elif self.tobacco_use == 'current':
            pack_years = f", {self.tobacco_pack_years} pack-years" if self.tobacco_pack_years else ""
            return f"Current smoker{pack_years}"
        return "Unknown smoking status"
    
    @property
    def alcohol_status(self):
        """Formatted alcohol status for clinical use"""
        if not self.alcohol_use:
            return "Unknown alcohol use"
            
        drinks = f", {self.alcohol_drinks_per_week} drinks/week" if self.alcohol_drinks_per_week else ""
        return f"{self.get_alcohol_use_display()}{drinks}"
    
    def get_summary(self):
        """Return a summary of key lifestyle factors"""
        return {
            'tobacco': self.smoking_status,
            'alcohol': self.alcohol_status,
            'diet': self.get_diet_type_display() if self.diet_type else "Unknown",
            'activity': self.get_activity_level_display() if self.activity_level else "Unknown",
            'sleep': f"{self.average_sleep_hours} hours/night" if self.average_sleep_hours else "Unknown",
            'occupation': self.occupation or "Unknown",
            'education': self.get_education_level_display() if self.education_level else "Unknown",
            'stress': self.get_stress_level_display() if self.stress_level else "Unknown",
            'housing': self.get_housing_type_display() if self.housing_type else "Unknown",
            'overall_risk': self.lifestyle_risk_assessment.get('overall_risk', 'unknown').upper() if self.lifestyle_risk_assessment else "UNKNOWN"
        } 