# api/agent_modules/analytics/agent.py

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from django.utils import timezone
from ..base import BaseAgent, AgentResponse, AgentUtils
from .services import CycleAnalyticsService, HealthPredictionService, RecommendationService
import logging

logger = logging.getLogger(__name__)


class AnalyticsAgent(BaseAgent):
    """
    Agent 1: Analytics & Intelligence Agent
    
    Handles advanced data analytics, predictive health insights, 
    and AI-driven recommendations for women's health.
    """
    
    def __init__(self):
        super().__init__("Analytics", "1.0.0")
        self.cycle_analytics = CycleAnalyticsService()
        self.health_predictions = HealthPredictionService()
        self.recommendations = RecommendationService()
        self._initialized = False
    
    def initialize(self) -> bool:
        """Initialize the Analytics Agent."""
        try:
            # Initialize services
            self.cycle_analytics.initialize()
            self.health_predictions.initialize()
            self.recommendations.initialize()
            
            # Validate dependencies
            if not self.validate_dependencies():
                return False
            
            self._initialized = True
            self.log_operation("agent_initialized")
            return True
            
        except Exception as e:
            self.handle_error(e, "initialization")
            return False
    
    def validate_dependencies(self) -> bool:
        """Validate required dependencies for analytics operations."""
        try:
            # Check database connectivity
            from api.models import MenstrualCycle, DailyHealthLog
            MenstrualCycle.objects.exists()
            DailyHealthLog.objects.exists()
            
            # Check if required packages are available
            import numpy as np
            import pandas as pd
            from sklearn.linear_model import LinearRegression
            
            return True
        except Exception as e:
            self.logger.error(f"Dependency validation failed: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of the Analytics Agent."""
        return {
            'name': self.name,
            'version': self.version,
            'initialized': self._initialized,
            'services': {
                'cycle_analytics': self.cycle_analytics.get_status(),
                'health_predictions': self.health_predictions.get_status(),
                'recommendations': self.recommendations.get_status()
            },
            'last_check': timezone.now().isoformat()
        }
    
    # Public API Methods
    
    def analyze_cycle_irregularities(self, user_id: int, months_back: int = 6) -> AgentResponse:
        """
        Detect cycle irregularities for a user.
        
        Args:
            user_id: User ID to analyze
            months_back: Number of months to analyze
            
        Returns:
            AgentResponse with irregularity analysis
        """
        try:
            if not AgentUtils.validate_user(user_id):
                return AgentResponse(
                    success=False,
                    error="Invalid user or user not verified",
                    agent_name=self.name,
                    operation="analyze_cycle_irregularities"
                )
            
            analysis = self.cycle_analytics.detect_irregularities(user_id, months_back)
            
            self.log_operation("cycle_irregularity_analysis", user_id=user_id)
            
            return AgentResponse(
                success=True,
                data=analysis,
                agent_name=self.name,
                operation="analyze_cycle_irregularities"
            )
            
        except Exception as e:
            return AgentResponse(**self.handle_error(e, "analyze_cycle_irregularities", user_id=user_id))
    
    def predict_next_period(self, user_id: int) -> AgentResponse:
        """
        Predict user's next menstrual period.
        
        Args:
            user_id: User ID to predict for
            
        Returns:
            AgentResponse with period prediction
        """
        try:
            if not AgentUtils.validate_user(user_id):
                return AgentResponse(
                    success=False,
                    error="Invalid user or user not verified",
                    agent_name=self.name,
                    operation="predict_next_period"
                )
            
            prediction = self.health_predictions.predict_next_period(user_id)
            
            self.log_operation("period_prediction", user_id=user_id)
            
            return AgentResponse(
                success=True,
                data=prediction,
                agent_name=self.name,
                operation="predict_next_period"
            )
            
        except Exception as e:
            return AgentResponse(**self.handle_error(e, "predict_next_period", user_id=user_id))
    
    def predict_fertility_window(self, user_id: int) -> AgentResponse:
        """
        Predict user's fertility window.
        
        Args:
            user_id: User ID to predict for
            
        Returns:
            AgentResponse with fertility window prediction
        """
        try:
            if not AgentUtils.validate_user(user_id):
                return AgentResponse(
                    success=False,
                    error="Invalid user or user not verified",
                    agent_name=self.name,
                    operation="predict_fertility_window"
                )
            
            fertility_data = self.health_predictions.predict_fertility_window(user_id)
            
            self.log_operation("fertility_prediction", user_id=user_id)
            
            return AgentResponse(
                success=True,
                data=fertility_data,
                agent_name=self.name,
                operation="predict_fertility_window"
            )
            
        except Exception as e:
            return AgentResponse(**self.handle_error(e, "predict_fertility_window", user_id=user_id))
    
    def generate_health_insights(self, user_id: int) -> AgentResponse:
        """
        Generate comprehensive health insights for a user.
        
        Args:
            user_id: User ID to analyze
            
        Returns:
            AgentResponse with health insights
        """
        try:
            if not AgentUtils.validate_user(user_id):
                return AgentResponse(
                    success=False,
                    error="Invalid user or user not verified",
                    agent_name=self.name,
                    operation="generate_health_insights"
                )
            
            insights = self.health_predictions.generate_health_insights(user_id)
            
            self.log_operation("health_insights_generation", user_id=user_id)
            
            return AgentResponse(
                success=True,
                data=insights,
                agent_name=self.name,
                operation="generate_health_insights"
            )
            
        except Exception as e:
            return AgentResponse(**self.handle_error(e, "generate_health_insights", user_id=user_id))
    
    def get_personalized_recommendations(self, user_id: int) -> AgentResponse:
        """
        Get personalized health recommendations for a user.
        
        Args:
            user_id: User ID to generate recommendations for
            
        Returns:
            AgentResponse with personalized recommendations
        """
        try:
            if not AgentUtils.validate_user(user_id):
                return AgentResponse(
                    success=False,
                    error="Invalid user or user not verified",
                    agent_name=self.name,
                    operation="get_personalized_recommendations"
                )
            
            recommendations = self.recommendations.generate_personalized_recommendations(user_id)
            
            self.log_operation("personalized_recommendations", user_id=user_id)
            
            return AgentResponse(
                success=True,
                data=recommendations,
                agent_name=self.name,
                operation="get_personalized_recommendations"
            )
            
        except Exception as e:
            return AgentResponse(**self.handle_error(e, "get_personalized_recommendations", user_id=user_id))
    
    def assess_health_risks(self, user_id: int) -> AgentResponse:
        """
        Assess health risks for a user based on their data.
        
        Args:
            user_id: User ID to assess
            
        Returns:
            AgentResponse with risk assessment
        """
        try:
            if not AgentUtils.validate_user(user_id):
                return AgentResponse(
                    success=False,
                    error="Invalid user or user not verified",
                    agent_name=self.name,
                    operation="assess_health_risks"
                )
            
            risk_assessment = self.health_predictions.assess_health_risks(user_id)
            
            self.log_operation("health_risk_assessment", user_id=user_id)
            
            return AgentResponse(
                success=True,
                data=risk_assessment,
                agent_name=self.name,
                operation="assess_health_risks"
            )
            
        except Exception as e:
            return AgentResponse(**self.handle_error(e, "assess_health_risks", user_id=user_id))
    
    def analyze_patterns(self, user_id: int, data_type: str, days_back: int = 90) -> AgentResponse:
        """
        Analyze patterns in user's health data.
        
        Args:
            user_id: User ID to analyze
            data_type: Type of data to analyze (mood, energy, symptoms, etc.)
            days_back: Number of days to look back
            
        Returns:
            AgentResponse with pattern analysis
        """
        try:
            if not AgentUtils.validate_user(user_id):
                return AgentResponse(
                    success=False,
                    error="Invalid user or user not verified",
                    agent_name=self.name,
                    operation="analyze_patterns"
                )
            
            patterns = self.cycle_analytics.analyze_patterns(user_id, data_type, days_back)
            
            self.log_operation("pattern_analysis", user_id=user_id, data_type=data_type)
            
            return AgentResponse(
                success=True,
                data=patterns,
                agent_name=self.name,
                operation="analyze_patterns"
            )
            
        except Exception as e:
            return AgentResponse(**self.handle_error(e, "analyze_patterns", user_id=user_id))


# Register the agent
from ..base import AgentRegistry
analytics_agent = AnalyticsAgent()
AgentRegistry.register_agent(analytics_agent)