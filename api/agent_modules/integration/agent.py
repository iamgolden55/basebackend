# api/agent_modules/integration/agent.py

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from django.contrib.auth import get_user_model
from ..base import BaseAgent, AgentResponse, AgentUtils
from .services import WearableDeviceManager, CalendarIntegrationService, DataAutomationService
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class IntegrationAgent(BaseAgent):
    """
    Integration & Automation Agent
    
    Implements external integrations, automated data collection, 
    and device synchronization capabilities.
    """
    
    def __init__(self):
        super().__init__("Integration", "1.0.0")
        self.device_manager = WearableDeviceManager()
        self.calendar_service = CalendarIntegrationService()
        self.automation_service = DataAutomationService()
        self._initialized = False
    
    def initialize(self) -> bool:
        """Initialize the Integration Agent and its services."""
        try:
            self.logger.info("Initializing Integration Agent...")
            
            # Initialize services
            self.device_manager.initialize()
            self.calendar_service.initialize()
            self.automation_service.initialize()
            
            self._initialized = True
            self.logger.info("Integration Agent initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Integration Agent: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of the Integration Agent."""
        return {
            'name': self.name,
            'version': self.version,
            'initialized': self._initialized,
            'services': {
                'device_manager': self.device_manager.get_status(),
                'calendar_service': self.calendar_service.get_status(),
                'automation_service': self.automation_service.get_status()
            },
            'last_check': datetime.now().isoformat()
        }
    
    def validate_dependencies(self) -> bool:
        """Validate that all required dependencies are available."""
        try:
            # Check required models exist
            from .models import DeviceConnection, IntegrationLog
            
            # Check required services are available
            dependencies = [
                self.device_manager,
                self.calendar_service,
                self.automation_service
            ]
            
            for service in dependencies:
                if not hasattr(service, 'validate_dependencies') or not service.validate_dependencies():
                    return False
            
            return True
            
        except ImportError as e:
            self.logger.error(f"Missing required models: {e}")
            return False
    
    def connect_wearable_device(self, user_id: int, device_type: str, 
                               auth_credentials: Dict[str, Any]) -> AgentResponse:
        """
        Connect a wearable device for a user.
        
        Args:
            user_id: ID of the user
            device_type: Type of device (fitbit, apple_health, etc.)
            auth_credentials: Authentication credentials for the device
            
        Returns:
            AgentResponse with connection result
        """
        try:
            self.log_operation("connect_wearable_device", user_id=user_id, 
                             device_type=device_type)
            
            if not AgentUtils.validate_user(user_id):
                return AgentResponse(
                    success=False,
                    error="Invalid user or user not verified for women's health",
                    agent_name=self.name,
                    operation="connect_wearable_device"
                )
            
            connection_result = self.device_manager.connect_device(
                user_id, device_type, auth_credentials
            )
            
            return AgentResponse(
                success=True,
                data=connection_result,
                agent_name=self.name,
                operation="connect_wearable_device"
            )
            
        except Exception as e:
            return AgentResponse(
                success=False,
                error=str(e),
                agent_name=self.name,
                operation="connect_wearable_device"
            )
    
    def disconnect_device(self, user_id: int, device_id: int) -> AgentResponse:
        """
        Disconnect a wearable device for a user.
        
        Args:
            user_id: ID of the user
            device_id: ID of the device connection to disconnect
            
        Returns:
            AgentResponse with disconnection result
        """
        try:
            self.log_operation("disconnect_device", user_id=user_id, device_id=device_id)
            
            if not AgentUtils.validate_user(user_id):
                return AgentResponse(
                    success=False,
                    error="Invalid user or user not verified for women's health",
                    agent_name=self.name,
                    operation="disconnect_device"
                )
            
            result = self.device_manager.disconnect_device(user_id, device_id)
            
            return AgentResponse(
                success=True,
                data=result,
                agent_name=self.name,
                operation="disconnect_device"
            )
            
        except Exception as e:
            return AgentResponse(
                success=False,
                error=str(e),
                agent_name=self.name,
                operation="disconnect_device"
            )
    
    def sync_device_data(self, user_id: int, device_id: Optional[int] = None,
                        force_sync: bool = False) -> AgentResponse:
        """
        Sync data from connected devices.
        
        Args:
            user_id: ID of the user
            device_id: Specific device to sync (if None, syncs all)
            force_sync: Force sync even if recently synced
            
        Returns:
            AgentResponse with sync results
        """
        try:
            self.log_operation("sync_device_data", user_id=user_id, 
                             device_id=device_id, force_sync=force_sync)
            
            if not AgentUtils.validate_user(user_id):
                return AgentResponse(
                    success=False,
                    error="Invalid user or user not verified for women's health",
                    agent_name=self.name,
                    operation="sync_device_data"
                )
            
            sync_results = self.device_manager.sync_device_data(
                user_id, device_id, force_sync
            )
            
            return AgentResponse(
                success=True,
                data=sync_results,
                agent_name=self.name,
                operation="sync_device_data"
            )
            
        except Exception as e:
            return AgentResponse(
                success=False,
                error=str(e),
                agent_name=self.name,
                operation="sync_device_data"
            )
    
    def get_connected_devices(self, user_id: int) -> AgentResponse:
        """
        Get list of connected devices for a user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            AgentResponse with list of connected devices
        """
        try:
            self.log_operation("get_connected_devices", user_id=user_id)
            
            if not AgentUtils.validate_user(user_id):
                return AgentResponse(
                    success=False,
                    error="Invalid user or user not verified for women's health",
                    agent_name=self.name,
                    operation="get_connected_devices"
                )
            
            devices = self.device_manager.get_user_devices(user_id)
            
            return AgentResponse(
                success=True,
                data=devices,
                agent_name=self.name,
                operation="get_connected_devices"
            )
            
        except Exception as e:
            return AgentResponse(
                success=False,
                error=str(e),
                agent_name=self.name,
                operation="get_connected_devices"
            )
    
    def setup_calendar_integration(self, user_id: int, calendar_type: str,
                                 auth_credentials: Dict[str, Any]) -> AgentResponse:
        """
        Setup calendar integration for a user.
        
        Args:
            user_id: ID of the user
            calendar_type: Type of calendar (google, outlook, etc.)
            auth_credentials: Authentication credentials
            
        Returns:
            AgentResponse with setup result
        """
        try:
            self.log_operation("setup_calendar_integration", user_id=user_id,
                             calendar_type=calendar_type)
            
            if not AgentUtils.validate_user(user_id):
                return AgentResponse(
                    success=False,
                    error="Invalid user or user not verified for women's health",
                    agent_name=self.name,
                    operation="setup_calendar_integration"
                )
            
            setup_result = self.calendar_service.setup_integration(
                user_id, calendar_type, auth_credentials
            )
            
            return AgentResponse(
                success=True,
                data=setup_result,
                agent_name=self.name,
                operation="setup_calendar_integration"
            )
            
        except Exception as e:
            return AgentResponse(
                success=False,
                error=str(e),
                agent_name=self.name,
                operation="setup_calendar_integration"
            )
    
    def sync_appointments(self, user_id: int) -> AgentResponse:
        """
        Sync appointments from calendar.
        
        Args:
            user_id: ID of the user
            
        Returns:
            AgentResponse with sync results
        """
        try:
            self.log_operation("sync_appointments", user_id=user_id)
            
            if not AgentUtils.validate_user(user_id):
                return AgentResponse(
                    success=False,
                    error="Invalid user or user not verified for women's health",
                    agent_name=self.name,
                    operation="sync_appointments"
                )
            
            sync_results = self.calendar_service.sync_appointments(user_id)
            
            return AgentResponse(
                success=True,
                data=sync_results,
                agent_name=self.name,
                operation="sync_appointments"
            )
            
        except Exception as e:
            return AgentResponse(
                success=False,
                error=str(e),
                agent_name=self.name,
                operation="sync_appointments"
            )
    
    def create_health_reminders(self, user_id: int, reminder_type: str,
                              reminder_config: Dict[str, Any]) -> AgentResponse:
        """
        Create health reminders in user's calendar.
        
        Args:
            user_id: ID of the user
            reminder_type: Type of reminder (medication, appointment, etc.)
            reminder_config: Configuration for the reminder
            
        Returns:
            AgentResponse with creation result
        """
        try:
            self.log_operation("create_health_reminders", user_id=user_id,
                             reminder_type=reminder_type)
            
            if not AgentUtils.validate_user(user_id):
                return AgentResponse(
                    success=False,
                    error="Invalid user or user not verified for women's health",
                    agent_name=self.name,
                    operation="create_health_reminders"
                )
            
            reminder_result = self.calendar_service.create_health_reminders(
                user_id, reminder_type, reminder_config
            )
            
            return AgentResponse(
                success=True,
                data=reminder_result,
                agent_name=self.name,
                operation="create_health_reminders"
            )
            
        except Exception as e:
            return AgentResponse(
                success=False,
                error=str(e),
                agent_name=self.name,
                operation="create_health_reminders"
            )
    
    def enable_automated_data_import(self, user_id: int, 
                                   automation_config: Dict[str, Any]) -> AgentResponse:
        """
        Enable automated data import for a user.
        
        Args:
            user_id: ID of the user
            automation_config: Configuration for automation
            
        Returns:
            AgentResponse with setup result
        """
        try:
            self.log_operation("enable_automated_data_import", user_id=user_id)
            
            if not AgentUtils.validate_user(user_id):
                return AgentResponse(
                    success=False,
                    error="Invalid user or user not verified for women's health",
                    agent_name=self.name,
                    operation="enable_automated_data_import"
                )
            
            automation_result = self.automation_service.enable_automation(
                user_id, automation_config
            )
            
            return AgentResponse(
                success=True,
                data=automation_result,
                agent_name=self.name,
                operation="enable_automated_data_import"
            )
            
        except Exception as e:
            return AgentResponse(
                success=False,
                error=str(e),
                agent_name=self.name,
                operation="enable_automated_data_import"
            )
    
    def get_integration_status(self, user_id: int) -> AgentResponse:
        """
        Get comprehensive integration status for a user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            AgentResponse with integration status
        """
        try:
            self.log_operation("get_integration_status", user_id=user_id)
            
            if not AgentUtils.validate_user(user_id):
                return AgentResponse(
                    success=False,
                    error="Invalid user or user not verified for women's health",
                    agent_name=self.name,
                    operation="get_integration_status"
                )
            
            # Get status from all services
            device_status = self.device_manager.get_user_integration_status(user_id)
            calendar_status = self.calendar_service.get_integration_status(user_id)
            automation_status = self.automation_service.get_automation_status(user_id)
            
            integration_status = {
                'devices': device_status,
                'calendar': calendar_status,
                'automation': automation_status,
                'overall_health': self._calculate_integration_health(
                    device_status, calendar_status, automation_status
                ),
                'last_sync_summary': self._get_last_sync_summary(user_id),
                'status_checked_at': datetime.now().isoformat()
            }
            
            return AgentResponse(
                success=True,
                data=integration_status,
                agent_name=self.name,
                operation="get_integration_status"
            )
            
        except Exception as e:
            return AgentResponse(
                success=False,
                error=str(e),
                agent_name=self.name,
                operation="get_integration_status"
            )
    
    def run_data_validation(self, user_id: int, 
                           validation_type: str = "all") -> AgentResponse:
        """
        Run data validation for imported data.
        
        Args:
            user_id: ID of the user
            validation_type: Type of validation to run
            
        Returns:
            AgentResponse with validation results
        """
        try:
            self.log_operation("run_data_validation", user_id=user_id,
                             validation_type=validation_type)
            
            if not AgentUtils.validate_user(user_id):
                return AgentResponse(
                    success=False,
                    error="Invalid user or user not verified for women's health",
                    agent_name=self.name,
                    operation="run_data_validation"
                )
            
            validation_results = self.automation_service.validate_user_data(
                user_id, validation_type
            )
            
            return AgentResponse(
                success=True,
                data=validation_results,
                agent_name=self.name,
                operation="run_data_validation"
            )
            
        except Exception as e:
            return AgentResponse(
                success=False,
                error=str(e),
                agent_name=self.name,
                operation="run_data_validation"
            )
    
    def _calculate_integration_health(self, device_status: Dict[str, Any],
                                    calendar_status: Dict[str, Any],
                                    automation_status: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall integration health score."""
        # TODO: Implement sophisticated health calculation
        connected_devices = len(device_status.get('connected_devices', []))
        calendar_connected = calendar_status.get('connected', False)
        automation_enabled = automation_status.get('enabled', False)
        
        health_score = 0
        if connected_devices > 0:
            health_score += 40
        if calendar_connected:
            health_score += 30
        if automation_enabled:
            health_score += 30
        
        return {
            'score': health_score,
            'level': 'excellent' if health_score >= 80 else 'good' if health_score >= 50 else 'basic',
            'recommendations': self._get_integration_recommendations(
                device_status, calendar_status, automation_status
            )
        }
    
    def _get_last_sync_summary(self, user_id: int) -> Dict[str, Any]:
        """Get summary of last sync operations."""
        from .models import IntegrationLog
        
        recent_logs = IntegrationLog.objects.filter(
            user_id=user_id,
            created_at__gte=datetime.now() - timedelta(days=7)
        ).order_by('-created_at')[:10]
        
        return {
            'total_syncs': recent_logs.count(),
            'successful_syncs': recent_logs.filter(status='success').count(),
            'failed_syncs': recent_logs.filter(status='error').count(),
            'last_sync': recent_logs.first().created_at.isoformat() if recent_logs.exists() else None
        }
    
    def _get_integration_recommendations(self, device_status: Dict[str, Any],
                                       calendar_status: Dict[str, Any],
                                       automation_status: Dict[str, Any]) -> List[str]:
        """Get recommendations for improving integrations."""
        recommendations = []
        
        if not device_status.get('connected_devices'):
            recommendations.append("Connect a wearable device for automatic health data tracking")
        
        if not calendar_status.get('connected'):
            recommendations.append("Connect your calendar to sync health appointments")
        
        if not automation_status.get('enabled'):
            recommendations.append("Enable data automation for seamless health tracking")
        
        return recommendations