# api/agent_modules/clinical/agent.py

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model
from ..base import BaseAgent, AgentResponse, AgentUtils
from .services import HealthScreeningService, MedicalHistoryService, ProviderIntegrationService
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class ClinicalAgent(BaseAgent):
    """
    Agent 6: Clinical & Provider Agent
    
    Handles healthcare provider integrations, medical appointment management,
    health screening recommendations, and clinical data processing.
    """
    
    def __init__(self):
        super().__init__("Clinical", "1.0.0")
        self.health_screening = HealthScreeningService()
        self.medical_history = MedicalHistoryService()
        self.provider_integration = ProviderIntegrationService()
        self._initialized = False
    
    def initialize(self) -> bool:
        """Initialize the Clinical Agent."""
        try:
            # Initialize services
            self.health_screening.initialize()
            self.medical_history.initialize()
            self.provider_integration.initialize()
            
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
        """Validate required dependencies for clinical operations."""
        try:
            # Check required models exist
            from api.models import Appointment, HealthScreening, MedicalHistory
            
            # Verify database connectivity
            Appointment.objects.exists()
            
            return True
        except Exception as e:
            self.logger.error(f"Dependency validation failed: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of the Clinical Agent."""
        return {
            'name': self.name,
            'version': self.version,
            'initialized': self._initialized,
            'services': {
                'health_screening': self.health_screening.get_status(),
                'medical_history': self.medical_history.get_status(),
                'provider_integration': self.provider_integration.get_status()
            },
            'last_check': timezone.now().isoformat()
        }
    
    # Public API Methods
    
    def get_health_screening_recommendations(self, user_id: int) -> AgentResponse:
        """
        Get personalized health screening recommendations.
        
        Args:
            user_id: User ID to get recommendations for
            
        Returns:
            AgentResponse with screening recommendations
        """
        try:
            if not AgentUtils.validate_user(user_id):
                return AgentResponse(
                    success=False,
                    error="Invalid user or user not verified",
                    agent_name=self.name,
                    operation="get_health_screening_recommendations"
                )
            
            recommendations = self.health_screening.get_screening_recommendations(user_id)
            
            self.log_operation("health_screening_recommendations", user_id=user_id)
            
            return AgentResponse(
                success=True,
                data=recommendations,
                agent_name=self.name,
                operation="get_health_screening_recommendations"
            )
            
        except Exception as e:
            return AgentResponse(**self.handle_error(e, "get_health_screening_recommendations", user_id=user_id))
    
    def schedule_medical_appointment(self, user_id: int, appointment_data: Dict[str, Any]) -> AgentResponse:
        """
        Schedule a medical appointment for a user.
        
        Args:
            user_id: User ID
            appointment_data: Appointment details
            
        Returns:
            AgentResponse with scheduling results
        """
        try:
            if not AgentUtils.validate_user(user_id):
                return AgentResponse(
                    success=False,
                    error="Invalid user or user not verified",
                    agent_name=self.name,
                    operation="schedule_medical_appointment"
                )
            
            appointment_result = self.provider_integration.schedule_appointment(user_id, appointment_data)
            
            self.log_operation("medical_appointment_scheduled", user_id=user_id)
            
            return AgentResponse(
                success=True,
                data=appointment_result,
                agent_name=self.name,
                operation="schedule_medical_appointment"
            )
            
        except Exception as e:
            return AgentResponse(**self.handle_error(e, "schedule_medical_appointment", user_id=user_id))
    
    def update_medical_history(self, user_id: int, medical_data: Dict[str, Any]) -> AgentResponse:
        """
        Update user's medical history with new information.
        
        Args:
            user_id: User ID
            medical_data: Medical history data to update
            
        Returns:
            AgentResponse with update results
        """
        try:
            if not AgentUtils.validate_user(user_id):
                return AgentResponse(
                    success=False,
                    error="Invalid user or user not verified",
                    agent_name=self.name,
                    operation="update_medical_history"
                )
            
            update_result = self.medical_history.update_medical_history(user_id, medical_data)
            
            self.log_operation("medical_history_updated", user_id=user_id)
            
            return AgentResponse(
                success=True,
                data=update_result,
                agent_name=self.name,
                operation="update_medical_history"
            )
            
        except Exception as e:
            return AgentResponse(**self.handle_error(e, "update_medical_history", user_id=user_id))
    
    def get_medical_history_summary(self, user_id: int) -> AgentResponse:
        """
        Get comprehensive medical history summary.
        
        Args:
            user_id: User ID
            
        Returns:
            AgentResponse with medical history summary
        """
        try:
            if not AgentUtils.validate_user(user_id):
                return AgentResponse(
                    success=False,
                    error="Invalid user or user not verified",
                    agent_name=self.name,
                    operation="get_medical_history_summary"
                )
            
            history_summary = self.medical_history.get_comprehensive_summary(user_id)
            
            self.log_operation("medical_history_retrieved", user_id=user_id)
            
            return AgentResponse(
                success=True,
                data=history_summary,
                agent_name=self.name,
                operation="get_medical_history_summary"
            )
            
        except Exception as e:
            return AgentResponse(**self.handle_error(e, "get_medical_history_summary", user_id=user_id))
    
    def connect_healthcare_provider(self, user_id: int, provider_data: Dict[str, Any]) -> AgentResponse:
        """
        Connect user with a healthcare provider.
        
        Args:
            user_id: User ID
            provider_data: Healthcare provider information
            
        Returns:
            AgentResponse with connection results
        """
        try:
            if not AgentUtils.validate_user(user_id):
                return AgentResponse(
                    success=False,
                    error="Invalid user or user not verified",
                    agent_name=self.name,
                    operation="connect_healthcare_provider"
                )
            
            connection_result = self.provider_integration.connect_provider(user_id, provider_data)
            
            self.log_operation("healthcare_provider_connected", user_id=user_id)
            
            return AgentResponse(
                success=True,
                data=connection_result,
                agent_name=self.name,
                operation="connect_healthcare_provider"
            )
            
        except Exception as e:
            return AgentResponse(**self.handle_error(e, "connect_healthcare_provider", user_id=user_id))
    
    def get_upcoming_appointments(self, user_id: int) -> AgentResponse:
        """
        Get user's upcoming medical appointments.
        
        Args:
            user_id: User ID
            
        Returns:
            AgentResponse with upcoming appointments
        """
        try:
            if not AgentUtils.validate_user(user_id):
                return AgentResponse(
                    success=False,
                    error="Invalid user or user not verified",
                    agent_name=self.name,
                    operation="get_upcoming_appointments"
                )
            
            appointments = self.provider_integration.get_upcoming_appointments(user_id)
            
            self.log_operation("upcoming_appointments_retrieved", user_id=user_id)
            
            return AgentResponse(
                success=True,
                data=appointments,
                agent_name=self.name,
                operation="get_upcoming_appointments"
            )
            
        except Exception as e:
            return AgentResponse(**self.handle_error(e, "get_upcoming_appointments", user_id=user_id))
    
    def analyze_health_risks(self, user_id: int) -> AgentResponse:
        """
        Analyze health risks based on medical history and current data.
        
        Args:
            user_id: User ID
            
        Returns:
            AgentResponse with risk analysis
        """
        try:
            if not AgentUtils.validate_user(user_id):
                return AgentResponse(
                    success=False,
                    error="Invalid user or user not verified",
                    agent_name=self.name,
                    operation="analyze_health_risks"
                )
            
            risk_analysis = self.medical_history.analyze_health_risks(user_id)
            
            self.log_operation("health_risk_analysis", user_id=user_id)
            
            return AgentResponse(
                success=True,
                data=risk_analysis,
                agent_name=self.name,
                operation="analyze_health_risks"
            )
            
        except Exception as e:
            return AgentResponse(**self.handle_error(e, "analyze_health_risks", user_id=user_id))
    
    def generate_health_report(self, user_id: int, report_type: str = "comprehensive") -> AgentResponse:
        """
        Generate comprehensive health report for provider sharing.
        
        Args:
            user_id: User ID
            report_type: Type of report to generate
            
        Returns:
            AgentResponse with generated report
        """
        try:
            if not AgentUtils.validate_user(user_id):
                return AgentResponse(
                    success=False,
                    error="Invalid user or user not verified",
                    agent_name=self.name,
                    operation="generate_health_report"
                )
            
            health_report = self.medical_history.generate_health_report(user_id, report_type)
            
            self.log_operation("health_report_generated", user_id=user_id, report_type=report_type)
            
            return AgentResponse(
                success=True,
                data=health_report,
                agent_name=self.name,
                operation="generate_health_report"
            )
            
        except Exception as e:
            return AgentResponse(**self.handle_error(e, "generate_health_report", user_id=user_id))
    
    def track_medication_compliance(self, user_id: int) -> AgentResponse:
        """
        Track medication compliance and adherence.
        
        Args:
            user_id: User ID
            
        Returns:
            AgentResponse with compliance tracking data
        """
        try:
            if not AgentUtils.validate_user(user_id):
                return AgentResponse(
                    success=False,
                    error="Invalid user or user not verified",
                    agent_name=self.name,
                    operation="track_medication_compliance"
                )
            
            compliance_data = self.medical_history.track_medication_compliance(user_id)
            
            self.log_operation("medication_compliance_tracked", user_id=user_id)
            
            return AgentResponse(
                success=True,
                data=compliance_data,
                agent_name=self.name,
                operation="track_medication_compliance"
            )
            
        except Exception as e:
            return AgentResponse(**self.handle_error(e, "track_medication_compliance", user_id=user_id))
    
    def sync_provider_data(self, user_id: int, provider_id: int) -> AgentResponse:
        """
        Sync data with connected healthcare provider.
        
        Args:
            user_id: User ID
            provider_id: Healthcare provider ID
            
        Returns:
            AgentResponse with sync results
        """
        try:
            if not AgentUtils.validate_user(user_id):
                return AgentResponse(
                    success=False,
                    error="Invalid user or user not verified",
                    agent_name=self.name,
                    operation="sync_provider_data"
                )
            
            sync_results = self.provider_integration.sync_provider_data(user_id, provider_id)
            
            self.log_operation("provider_data_synced", user_id=user_id, provider_id=provider_id)
            
            return AgentResponse(
                success=True,
                data=sync_results,
                agent_name=self.name,
                operation="sync_provider_data"
            )
            
        except Exception as e:
            return AgentResponse(**self.handle_error(e, "sync_provider_data", user_id=user_id))
    
    def get_clinical_insights(self, user_id: int) -> AgentResponse:
        """
        Get clinical insights based on health data patterns.
        
        Args:
            user_id: User ID
            
        Returns:
            AgentResponse with clinical insights
        """
        try:
            if not AgentUtils.validate_user(user_id):
                return AgentResponse(
                    success=False,
                    error="Invalid user or user not verified",
                    agent_name=self.name,
                    operation="get_clinical_insights"
                )
            
            clinical_insights = self.medical_history.generate_clinical_insights(user_id)
            
            self.log_operation("clinical_insights_generated", user_id=user_id)
            
            return AgentResponse(
                success=True,
                data=clinical_insights,
                agent_name=self.name,
                operation="get_clinical_insights"
            )
            
        except Exception as e:
            return AgentResponse(**self.handle_error(e, "get_clinical_insights", user_id=user_id))


# Register the agent
from ..base import AgentRegistry
clinical_agent = ClinicalAgent()
AgentRegistry.register_agent(clinical_agent)