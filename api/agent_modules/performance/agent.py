# api/agent_modules/performance/agent.py

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.cache import cache
from ..base import BaseAgent, AgentResponse, AgentUtils
from .services import DatabaseOptimizationService, CachingService, BackgroundTaskService
import logging

logger = logging.getLogger(__name__)


class PerformanceAgent(BaseAgent):
    """
    Agent 4: Performance & Optimization Agent
    
    Handles database optimization, caching strategies, background task management,
    and performance monitoring for the women's health system.
    """
    
    def __init__(self):
        super().__init__("Performance", "1.0.0")
        self.db_optimizer = DatabaseOptimizationService()
        self.cache_service = CachingService()
        self.task_service = BackgroundTaskService()
        self._initialized = False
    
    def initialize(self) -> bool:
        """Initialize the Performance Agent."""
        try:
            # Initialize services
            self.db_optimizer.initialize()
            self.cache_service.initialize()
            self.task_service.initialize()
            
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
        """Validate required dependencies for performance operations."""
        try:
            # Check cache backend
            cache.get("test_key")
            
            # Check database connectivity
            from api.models import MenstrualCycle
            MenstrualCycle.objects.exists()
            
            # Check Celery availability
            from celery import current_app
            current_app.control.inspect()
            
            return True
        except Exception as e:
            self.logger.error(f"Dependency validation failed: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of the Performance Agent."""
        return {
            'name': self.name,
            'version': self.version,
            'initialized': self._initialized,
            'services': {
                'db_optimizer': self.db_optimizer.get_status(),
                'cache_service': self.cache_service.get_status(),
                'task_service': self.task_service.get_status()
            },
            'last_check': timezone.now().isoformat()
        }
    
    # Public API Methods
    
    def optimize_database_queries(self, optimization_type: str = "general") -> AgentResponse:
        """
        Optimize database queries for women's health models.
        
        Args:
            optimization_type: Type of optimization (general, cycles, health_logs)
            
        Returns:
            AgentResponse with optimization results
        """
        try:
            optimization_results = self.db_optimizer.optimize_queries(optimization_type)
            
            self.log_operation("database_optimization", optimization_type=optimization_type)
            
            return AgentResponse(
                success=True,
                data=optimization_results,
                agent_name=self.name,
                operation="optimize_database_queries"
            )
            
        except Exception as e:
            return AgentResponse(**self.handle_error(e, "optimize_database_queries"))
    
    def refresh_cache_layer(self, cache_type: str = "all") -> AgentResponse:
        """
        Refresh caching layers for improved performance.
        
        Args:
            cache_type: Type of cache to refresh (all, user_data, predictions)
            
        Returns:
            AgentResponse with cache refresh results
        """
        try:
            refresh_results = self.cache_service.refresh_cache(cache_type)
            
            self.log_operation("cache_refresh", cache_type=cache_type)
            
            return AgentResponse(
                success=True,
                data=refresh_results,
                agent_name=self.name,
                operation="refresh_cache_layer"
            )
            
        except Exception as e:
            return AgentResponse(**self.handle_error(e, "refresh_cache_layer"))
    
    def schedule_background_task(self, task_name: str, user_id: Optional[int] = None, 
                                params: Optional[Dict[str, Any]] = None) -> AgentResponse:
        """
        Schedule background tasks for data processing.
        
        Args:
            task_name: Name of the task to schedule
            user_id: Optional user ID for user-specific tasks
            params: Optional parameters for the task
            
        Returns:
            AgentResponse with scheduling results
        """
        try:
            if user_id and not AgentUtils.validate_user(user_id):
                return AgentResponse(
                    success=False,
                    error="Invalid user or user not verified",
                    agent_name=self.name,
                    operation="schedule_background_task"
                )
            
            schedule_result = self.task_service.schedule_task(task_name, user_id, params)
            
            self.log_operation("background_task_scheduled", task_name=task_name, user_id=user_id)
            
            return AgentResponse(
                success=True,
                data=schedule_result,
                agent_name=self.name,
                operation="schedule_background_task"
            )
            
        except Exception as e:
            return AgentResponse(**self.handle_error(e, "schedule_background_task"))
    
    def monitor_system_performance(self) -> AgentResponse:
        """
        Monitor overall system performance metrics.
        
        Returns:
            AgentResponse with performance metrics
        """
        try:
            performance_metrics = {
                'database': self.db_optimizer.get_performance_metrics(),
                'cache': self.cache_service.get_cache_metrics(),
                'background_tasks': self.task_service.get_task_metrics(),
                'overall_health': self._calculate_system_health()
            }
            
            self.log_operation("performance_monitoring")
            
            return AgentResponse(
                success=True,
                data=performance_metrics,
                agent_name=self.name,
                operation="monitor_system_performance"
            )
            
        except Exception as e:
            return AgentResponse(**self.handle_error(e, "monitor_system_performance"))
    
    def optimize_user_data_access(self, user_id: int) -> AgentResponse:
        """
        Optimize data access patterns for a specific user.
        
        Args:
            user_id: User ID to optimize for
            
        Returns:
            AgentResponse with optimization results
        """
        try:
            if not AgentUtils.validate_user(user_id):
                return AgentResponse(
                    success=False,
                    error="Invalid user or user not verified",
                    agent_name=self.name,
                    operation="optimize_user_data_access"
                )
            
            optimization_results = self.db_optimizer.optimize_user_queries(user_id)
            cache_results = self.cache_service.preload_user_cache(user_id)
            
            combined_results = {
                'database_optimization': optimization_results,
                'cache_optimization': cache_results,
                'overall_improvement': self._calculate_improvement_score(
                    optimization_results, cache_results
                )
            }
            
            self.log_operation("user_data_optimization", user_id=user_id)
            
            return AgentResponse(
                success=True,
                data=combined_results,
                agent_name=self.name,
                operation="optimize_user_data_access"
            )
            
        except Exception as e:
            return AgentResponse(**self.handle_error(e, "optimize_user_data_access", user_id=user_id))
    
    def cleanup_expired_data(self) -> AgentResponse:
        """
        Clean up expired data and optimize storage.
        
        Returns:
            AgentResponse with cleanup results
        """
        try:
            cleanup_results = self.db_optimizer.cleanup_expired_data()
            cache_cleanup = self.cache_service.cleanup_expired_cache()
            
            combined_results = {
                'database_cleanup': cleanup_results,
                'cache_cleanup': cache_cleanup,
                'total_space_freed': cleanup_results.get('space_freed', 0) + 
                                   cache_cleanup.get('space_freed', 0)
            }
            
            self.log_operation("expired_data_cleanup")
            
            return AgentResponse(
                success=True,
                data=combined_results,
                agent_name=self.name,
                operation="cleanup_expired_data"
            )
            
        except Exception as e:
            return AgentResponse(**self.handle_error(e, "cleanup_expired_data"))
    
    def analyze_query_performance(self, days_back: int = 7) -> AgentResponse:
        """
        Analyze query performance over specified time period.
        
        Args:
            days_back: Number of days to analyze
            
        Returns:
            AgentResponse with performance analysis
        """
        try:
            analysis_results = self.db_optimizer.analyze_query_performance(days_back)
            
            self.log_operation("query_performance_analysis", days_back=days_back)
            
            return AgentResponse(
                success=True,
                data=analysis_results,
                agent_name=self.name,
                operation="analyze_query_performance"
            )
            
        except Exception as e:
            return AgentResponse(**self.handle_error(e, "analyze_query_performance"))
    
    def configure_auto_scaling(self, scaling_config: Dict[str, Any]) -> AgentResponse:
        """
        Configure automatic scaling for background tasks.
        
        Args:
            scaling_config: Configuration for auto-scaling
            
        Returns:
            AgentResponse with configuration results
        """
        try:
            config_results = self.task_service.configure_auto_scaling(scaling_config)
            
            self.log_operation("auto_scaling_configuration")
            
            return AgentResponse(
                success=True,
                data=config_results,
                agent_name=self.name,
                operation="configure_auto_scaling"
            )
            
        except Exception as e:
            return AgentResponse(**self.handle_error(e, "configure_auto_scaling"))
    
    def get_resource_utilization(self) -> AgentResponse:
        """
        Get current resource utilization metrics.
        
        Returns:
            AgentResponse with resource metrics
        """
        try:
            resource_metrics = {
                'database_connections': self.db_optimizer.get_connection_metrics(),
                'memory_usage': self.cache_service.get_memory_metrics(),
                'task_queue_status': self.task_service.get_queue_metrics(),
                'cpu_utilization': self._get_cpu_metrics(),
                'timestamp': timezone.now().isoformat()
            }
            
            self.log_operation("resource_utilization_check")
            
            return AgentResponse(
                success=True,
                data=resource_metrics,
                agent_name=self.name,
                operation="get_resource_utilization"
            )
            
        except Exception as e:
            return AgentResponse(**self.handle_error(e, "get_resource_utilization"))
    
    def optimize_for_peak_load(self) -> AgentResponse:
        """
        Optimize system for expected peak load periods.
        
        Returns:
            AgentResponse with optimization results
        """
        try:
            optimization_results = {
                'database_optimization': self.db_optimizer.prepare_for_peak_load(),
                'cache_preloading': self.cache_service.preload_common_data(),
                'task_queue_scaling': self.task_service.scale_for_peak_load(),
                'readiness_score': 0
            }
            
            # Calculate readiness score
            scores = [
                optimization_results['database_optimization'].get('readiness_score', 0),
                optimization_results['cache_preloading'].get('readiness_score', 0),
                optimization_results['task_queue_scaling'].get('readiness_score', 0)
            ]
            optimization_results['readiness_score'] = sum(scores) / len(scores)
            
            self.log_operation("peak_load_optimization")
            
            return AgentResponse(
                success=True,
                data=optimization_results,
                agent_name=self.name,
                operation="optimize_for_peak_load"
            )
            
        except Exception as e:
            return AgentResponse(**self.handle_error(e, "optimize_for_peak_load"))
    
    # Private helper methods
    
    def _calculate_system_health(self) -> Dict[str, Any]:
        """Calculate overall system health score."""
        try:
            db_health = self.db_optimizer.get_health_score()
            cache_health = self.cache_service.get_health_score()
            task_health = self.task_service.get_health_score()
            
            overall_score = (db_health + cache_health + task_health) / 3
            
            return {
                'overall_score': overall_score,
                'level': 'excellent' if overall_score >= 90 else 
                        'good' if overall_score >= 70 else 
                        'needs_attention' if overall_score >= 50 else 'critical',
                'component_scores': {
                    'database': db_health,
                    'cache': cache_health,
                    'tasks': task_health
                }
            }
        except Exception as e:
            self.logger.error(f"Error calculating system health: {e}")
            return {'overall_score': 0, 'level': 'unknown', 'error': str(e)}
    
    def _calculate_improvement_score(self, db_results: Dict[str, Any], 
                                   cache_results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate improvement score from optimization results."""
        try:
            db_improvement = db_results.get('improvement_percentage', 0)
            cache_improvement = cache_results.get('improvement_percentage', 0)
            
            overall_improvement = (db_improvement + cache_improvement) / 2
            
            return {
                'overall_improvement_percentage': overall_improvement,
                'database_improvement': db_improvement,
                'cache_improvement': cache_improvement,
                'estimated_performance_gain': f"{overall_improvement:.1f}%"
            }
        except Exception as e:
            self.logger.error(f"Error calculating improvement score: {e}")
            return {'overall_improvement_percentage': 0, 'error': str(e)}
    
    def _get_cpu_metrics(self) -> Dict[str, Any]:
        """Get CPU utilization metrics."""
        try:
            import psutil
            cpu_percent = psutil.cpu_percent(interval=1)
            memory_percent = psutil.virtual_memory().percent
            
            return {
                'cpu_usage_percent': cpu_percent,
                'memory_usage_percent': memory_percent,
                'status': 'optimal' if cpu_percent < 70 else 'high' if cpu_percent < 90 else 'critical'
            }
        except ImportError:
            return {
                'cpu_usage_percent': 0,
                'memory_usage_percent': 0,
                'status': 'unavailable',
                'note': 'psutil not available for system metrics'
            }
        except Exception as e:
            self.logger.error(f"Error getting CPU metrics: {e}")
            return {'error': str(e), 'status': 'error'}


# Register the agent
from ..base import AgentRegistry
performance_agent = PerformanceAgent()
AgentRegistry.register_agent(performance_agent)