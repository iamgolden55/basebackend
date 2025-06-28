# api/agent_modules/analytics/models.py

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import json

User = get_user_model()


class HealthInsight(models.Model):
    """
    Model for storing generated health insights and analytics.
    """
    
    INSIGHT_TYPES = [
        ('cycle_irregularity', 'Cycle Irregularity'),
        ('pattern_analysis', 'Pattern Analysis'),
        ('health_prediction', 'Health Prediction'),
        ('risk_assessment', 'Risk Assessment'),
        ('recommendation', 'Recommendation'),
        ('trend_analysis', 'Trend Analysis'),
    ]
    
    CONFIDENCE_LEVELS = [
        ('low', 'Low (0.0-0.4)'),
        ('medium', 'Medium (0.4-0.7)'),
        ('high', 'High (0.7-1.0)'),
    ]
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='health_insights'
    )
    insight_type = models.CharField(
        max_length=50, 
        choices=INSIGHT_TYPES,
        db_index=True
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    confidence_score = models.FloatField(
        help_text="Confidence score between 0.0 and 1.0"
    )
    confidence_level = models.CharField(
        max_length=10,
        choices=CONFIDENCE_LEVELS,
        blank=True
    )
    data_points = models.JSONField(
        default=dict,
        help_text="Additional data and metadata for the insight"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this insight is still relevant"
    )
    expires_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When this insight expires (optional)"
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'insight_type']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['insight_type', 'created_at']),
        ]
    
    def save(self, *args, **kwargs):
        # Set confidence level based on score
        if self.confidence_score >= 0.7:
            self.confidence_level = 'high'
        elif self.confidence_score >= 0.4:
            self.confidence_level = 'medium'
        else:
            self.confidence_level = 'low'
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.user.username} - {self.title} ({self.confidence_level})"
    
    def is_expired(self):
        """Check if the insight has expired."""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False
    
    def to_dict(self):
        """Convert insight to dictionary for API responses."""
        return {
            'id': self.id,
            'insight_type': self.insight_type,
            'title': self.title,
            'description': self.description,
            'confidence_score': self.confidence_score,
            'confidence_level': self.confidence_level,
            'data_points': self.data_points,
            'is_active': self.is_active,
            'is_expired': self.is_expired(),
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }


class CycleInsight(models.Model):
    """
    Model for storing specific cycle-related insights and patterns.
    """
    
    PATTERN_TYPES = [
        ('length_variation', 'Cycle Length Variation'),
        ('flow_pattern', 'Flow Pattern'),
        ('symptom_correlation', 'Symptom Correlation'),
        ('mood_correlation', 'Mood Correlation'),
        ('regularity', 'Cycle Regularity'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='cycle_insights'
    )
    pattern_type = models.CharField(max_length=50, choices=PATTERN_TYPES)
    cycles_analyzed = models.PositiveIntegerField(
        help_text="Number of cycles used in analysis"
    )
    analysis_data = models.JSONField(
        default=dict,
        help_text="Detailed analysis results and statistics"
    )
    regularity_score = models.FloatField(
        blank=True,
        null=True,
        help_text="Regularity score from 0-100"
    )
    insights_generated = models.JSONField(
        default=list,
        help_text="List of specific insights from analysis"
    )
    recommendations = models.JSONField(
        default=list,
        help_text="Recommendations based on analysis"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'pattern_type']),
            models.Index(fields=['user', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.get_pattern_type_display()}"


class PredictionModel(models.Model):
    """
    Model for storing prediction model metadata and performance.
    """
    
    MODEL_TYPES = [
        ('cycle_prediction', 'Cycle Prediction'),
        ('fertility_prediction', 'Fertility Prediction'),
        ('symptom_prediction', 'Symptom Prediction'),
        ('risk_prediction', 'Risk Prediction'),
    ]
    
    name = models.CharField(max_length=100)
    model_type = models.CharField(max_length=50, choices=MODEL_TYPES)
    version = models.CharField(max_length=20)
    description = models.TextField(blank=True)
    algorithm = models.CharField(
        max_length=50,
        help_text="Algorithm used (e.g., linear_regression, random_forest)"
    )
    parameters = models.JSONField(
        default=dict,
        help_text="Model parameters and hyperparameters"
    )
    training_data_size = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Number of samples used for training"
    )
    accuracy_score = models.FloatField(
        blank=True,
        null=True,
        help_text="Model accuracy score"
    )
    performance_metrics = models.JSONField(
        default=dict,
        help_text="Additional performance metrics (precision, recall, etc.)"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['name', 'version']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} v{self.version} ({self.get_model_type_display()})"


class UserPrediction(models.Model):
    """
    Model for storing user-specific predictions.
    """
    
    PREDICTION_STATUSES = [
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('verified', 'Verified'),
        ('incorrect', 'Incorrect'),
        ('expired', 'Expired'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='predictions'
    )
    model = models.ForeignKey(
        PredictionModel,
        on_delete=models.CASCADE,
        related_name='user_predictions'
    )
    prediction_data = models.JSONField(
        help_text="The actual prediction data"
    )
    confidence_score = models.FloatField()
    predicted_date = models.DateField(
        blank=True,
        null=True,
        help_text="Date of predicted event (if applicable)"
    )
    actual_date = models.DateField(
        blank=True,
        null=True,
        help_text="Actual date when event occurred (for verification)"
    )
    status = models.CharField(
        max_length=20,
        choices=PREDICTION_STATUSES,
        default='pending'
    )
    feedback_score = models.IntegerField(
        blank=True,
        null=True,
        help_text="User feedback score (1-5)"
    )
    feedback_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['user', 'predicted_date']),
            models.Index(fields=['model', 'status']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.model.name} prediction"
    
    def calculate_accuracy(self):
        """Calculate prediction accuracy if actual date is available."""
        if self.predicted_date and self.actual_date:
            diff = abs((self.predicted_date - self.actual_date).days)
            # Accuracy decreases as difference increases
            # 0 days diff = 100%, 1 day = 90%, 2 days = 80%, etc.
            accuracy = max(0, 100 - (diff * 10))
            return accuracy
        return None
    
    def mark_verified(self, actual_date, feedback_score=None, notes=""):
        """Mark prediction as verified with actual outcome."""
        self.actual_date = actual_date
        self.status = 'verified'
        if feedback_score:
            self.feedback_score = feedback_score
        if notes:
            self.feedback_notes = notes
        self.save()


class AnalyticsCache(models.Model):
    """
    Model for caching expensive analytics computations.
    """
    
    CACHE_TYPES = [
        ('cycle_analysis', 'Cycle Analysis'),
        ('pattern_analysis', 'Pattern Analysis'),
        ('predictions', 'Predictions'),
        ('insights', 'Insights'),
        ('recommendations', 'Recommendations'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='analytics_cache'
    )
    cache_type = models.CharField(max_length=50, choices=CACHE_TYPES)
    cache_key = models.CharField(
        max_length=200,
        help_text="Unique key for the cached data"
    )
    data = models.JSONField(help_text="Cached computation results")
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'cache_key']
        indexes = [
            models.Index(fields=['user', 'cache_type']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.cache_key}"
    
    def is_expired(self):
        """Check if cache entry has expired."""
        return timezone.now() > self.expires_at
    
    @classmethod
    def cleanup_expired(cls):
        """Remove expired cache entries."""
        expired_count = cls.objects.filter(expires_at__lt=timezone.now()).count()
        cls.objects.filter(expires_at__lt=timezone.now()).delete()
        return expired_count