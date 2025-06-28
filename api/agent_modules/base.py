# api/agent_modules/base.py

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from django.contrib.auth import get_user_model
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Base class for all agent modules in the women's health backend enhancement project.
    Provides common functionality and enforces standard interfaces.
    """
    
    def __init__(self, name: str, version: str = "1.0.0"):
        self.name = name
        self.version = version
        self.logger = logging.getLogger(f"agent.{name.lower()}")
    
    @abstractmethod
    def initialize(self) -> bool:
        """
        Initialize the agent. Must be implemented by each agent.
        Returns True if initialization successful, False otherwise.
        """
        pass
    
    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """
        Get current status of the agent.
        Returns dictionary with status information.
        """
        pass
    
    @abstractmethod
    def validate_dependencies(self) -> bool:
        """
        Validate that all required dependencies are available.
        Returns True if all dependencies are met, False otherwise.
        """
        pass
    
    def log_operation(self, operation: str, user_id: Optional[int] = None, **kwargs):
        """Log agent operations for monitoring and debugging."""
        log_data = {
            'agent': self.name,
            'operation': operation,
            'user_id': user_id,
            **kwargs
        }
        self.logger.info(f"Agent operation: {log_data}")
    
    def handle_error(self, error: Exception, operation: str, **kwargs):
        """Standardized error handling for all agents."""
        error_data = {
            'agent': self.name,
            'operation': operation,
            'error': str(error),
            'error_type': type(error).__name__,
            **kwargs
        }
        self.logger.error(f"Agent error: {error_data}")
        
        # Could integrate with monitoring service here
        return {
            'success': False,
            'error': str(error),
            'agent': self.name
        }


class AgentRegistry:
    """Registry for managing all agent instances."""
    
    _agents: Dict[str, BaseAgent] = {}
    
    @classmethod
    def register_agent(cls, agent: BaseAgent):
        """Register an agent in the registry."""
        cls._agents[agent.name.lower()] = agent
        logger.info(f"Registered agent: {agent.name}")
    
    @classmethod
    def get_agent(cls, name: str) -> Optional[BaseAgent]:
        """Get an agent by name."""
        return cls._agents.get(name.lower())
    
    @classmethod
    def get_all_agents(cls) -> Dict[str, BaseAgent]:
        """Get all registered agents."""
        return cls._agents.copy()
    
    @classmethod
    def initialize_all_agents(cls) -> Dict[str, bool]:
        """Initialize all registered agents."""
        results = {}
        for name, agent in cls._agents.items():
            try:
                results[name] = agent.initialize()
            except Exception as e:
                logger.error(f"Failed to initialize agent {name}: {e}")
                results[name] = False
        return results
    
    @classmethod
    def get_system_status(cls) -> Dict[str, Any]:
        """Get status of all agents."""
        status = {
            'total_agents': len(cls._agents),
            'agents': {}
        }
        
        for name, agent in cls._agents.items():
            try:
                status['agents'][name] = agent.get_status()
            except Exception as e:
                status['agents'][name] = {
                    'status': 'error',
                    'error': str(e)
                }
        
        return status


# Common data structures and types used across agents
class HealthDataType:
    """Enumeration of health data types."""
    MENSTRUAL_CYCLE = "menstrual_cycle"
    PREGNANCY = "pregnancy"
    FERTILITY = "fertility"
    DAILY_LOG = "daily_log"
    HEALTH_GOAL = "health_goal"
    SCREENING = "screening"


class AgentResponse:
    """Standardized response format for agent operations."""
    
    def __init__(self, success: bool, data: Any = None, error: str = None, 
                 agent_name: str = None, operation: str = None):
        self.success = success
        self.data = data
        self.error = error
        self.agent_name = agent_name
        self.operation = operation
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary."""
        result = {
            'success': self.success,
            'agent': self.agent_name,
            'operation': self.operation
        }
        
        if self.success:
            result['data'] = self.data
        else:
            result['error'] = self.error
            
        return result


# Common utilities for all agents
class AgentUtils:
    """Common utility functions for all agents."""
    
    @staticmethod
    def validate_user(user_id: int) -> bool:
        """Validate that user exists and has women's health verification."""
        try:
            user = User.objects.get(id=user_id)
            return user.womens_health_verified
        except User.DoesNotExist:
            return False
    
    @staticmethod
    def get_user_health_profile(user_id: int):
        """Get user's women's health profile."""
        from api.models import WomensHealthProfile
        try:
            user = User.objects.get(id=user_id)
            return WomensHealthProfile.objects.get(user=user)
        except (User.DoesNotExist, WomensHealthProfile.DoesNotExist):
            return None
    
    @staticmethod
    def format_date_range(start_date, end_date) -> Dict[str, str]:
        """Format date range for consistent API responses."""
        return {
            'start_date': start_date.isoformat() if start_date else None,
            'end_date': end_date.isoformat() if end_date else None
        }