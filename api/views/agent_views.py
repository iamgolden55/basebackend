# api/views/agent_views.py

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from django.utils import timezone
import json
import logging

logger = logging.getLogger(__name__)


# Analytics Agent Endpoints
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def analytics_agent_status(request):
    """Get Analytics Agent status."""
    try:
        from api.agent_modules.analytics.agent import AnalyticsAgent
        
        agent = AnalyticsAgent()
        if not agent.initialize():
            return Response({
                'error': 'Failed to initialize Analytics Agent'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        agent_status = agent.get_status()
        return Response(agent_status, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error getting analytics agent status: {e}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def analyze_cycle_irregularities(request):
    """Detect cycle irregularities for a user."""
    try:
        from api.agent_modules.analytics.agent import AnalyticsAgent
        
        data = json.loads(request.body) if request.body else {}
        user_id = data.get('user_id', request.user.id)
        months_back = data.get('months_back', 6)
        
        # Verify user access
        if user_id != request.user.id and not request.user.is_staff:
            return Response({
                'error': 'Unauthorized access to user data'
            }, status=status.HTTP_403_FORBIDDEN)
        
        agent = AnalyticsAgent()
        if not agent.initialize():
            return Response({
                'error': 'Failed to initialize Analytics Agent'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        response = agent.analyze_cycle_irregularities(user_id, months_back)
        
        if response.success:
            return Response(response.to_dict(), status=status.HTTP_200_OK)
        else:
            return Response(response.to_dict(), status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Error analyzing cycle irregularities: {e}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def predict_next_period(request):
    """Predict user's next menstrual period."""
    try:
        from api.agent_modules.analytics.agent import AnalyticsAgent
        
        data = json.loads(request.body) if request.body else {}
        user_id = data.get('user_id', request.user.id)
        
        # Verify user access
        if user_id != request.user.id and not request.user.is_staff:
            return Response({
                'error': 'Unauthorized access to user data'
            }, status=status.HTTP_403_FORBIDDEN)
        
        agent = AnalyticsAgent()
        if not agent.initialize():
            return Response({
                'error': 'Failed to initialize Analytics Agent'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        response = agent.predict_next_period(user_id)
        
        if response.success:
            return Response(response.to_dict(), status=status.HTTP_200_OK)
        else:
            return Response(response.to_dict(), status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Error predicting next period: {e}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def predict_fertility_window(request):
    """Predict user's fertility window."""
    try:
        from api.agent_modules.analytics.agent import AnalyticsAgent
        
        data = json.loads(request.body) if request.body else {}
        user_id = data.get('user_id', request.user.id)
        
        # Verify user access
        if user_id != request.user.id and not request.user.is_staff:
            return Response({
                'error': 'Unauthorized access to user data'
            }, status=status.HTTP_403_FORBIDDEN)
        
        agent = AnalyticsAgent()
        if not agent.initialize():
            return Response({
                'error': 'Failed to initialize Analytics Agent'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        response = agent.predict_fertility_window(user_id)
        
        if response.success:
            return Response(response.to_dict(), status=status.HTTP_200_OK)
        else:
            return Response(response.to_dict(), status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Error predicting fertility window: {e}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_health_insights(request):
    """Generate comprehensive health insights for a user."""
    try:
        from api.agent_modules.analytics.agent import AnalyticsAgent
        
        data = json.loads(request.body) if request.body else {}
        user_id = data.get('user_id', request.user.id)
        
        # Verify user access
        if user_id != request.user.id and not request.user.is_staff:
            return Response({
                'error': 'Unauthorized access to user data'
            }, status=status.HTTP_403_FORBIDDEN)
        
        agent = AnalyticsAgent()
        if not agent.initialize():
            return Response({
                'error': 'Failed to initialize Analytics Agent'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        response = agent.generate_health_insights(user_id)
        
        if response.success:
            return Response(response.to_dict(), status=status.HTTP_200_OK)
        else:
            return Response(response.to_dict(), status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Error generating health insights: {e}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_personalized_recommendations(request):
    """Get personalized health recommendations."""
    try:
        from api.agent_modules.analytics.agent import AnalyticsAgent
        
        data = json.loads(request.body) if request.body else {}
        user_id = data.get('user_id', request.user.id)
        
        # Verify user access
        if user_id != request.user.id and not request.user.is_staff:
            return Response({
                'error': 'Unauthorized access to user data'
            }, status=status.HTTP_403_FORBIDDEN)
        
        agent = AnalyticsAgent()
        if not agent.initialize():
            return Response({
                'error': 'Failed to initialize Analytics Agent'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        response = agent.get_personalized_recommendations(user_id)
        
        if response.success:
            return Response(response.to_dict(), status=status.HTTP_200_OK)
        else:
            return Response(response.to_dict(), status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Error getting personalized recommendations: {e}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def assess_health_risks(request):
    """Assess health risks for a user."""
    try:
        from api.agent_modules.analytics.agent import AnalyticsAgent
        
        data = json.loads(request.body) if request.body else {}
        user_id = data.get('user_id', request.user.id)
        
        # Verify user access
        if user_id != request.user.id and not request.user.is_staff:
            return Response({
                'error': 'Unauthorized access to user data'
            }, status=status.HTTP_403_FORBIDDEN)
        
        agent = AnalyticsAgent()
        if not agent.initialize():
            return Response({
                'error': 'Failed to initialize Analytics Agent'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        response = agent.assess_health_risks(user_id)
        
        if response.success:
            return Response(response.to_dict(), status=status.HTTP_200_OK)
        else:
            return Response(response.to_dict(), status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Error assessing health risks: {e}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def analyze_patterns(request):
    """Analyze patterns in user's health data."""
    try:
        from api.agent_modules.analytics.agent import AnalyticsAgent
        
        data = json.loads(request.body) if request.body else {}
        user_id = data.get('user_id', request.user.id)
        data_type = data.get('data_type', 'mood')
        days_back = data.get('days_back', 90)
        
        # Verify user access
        if user_id != request.user.id and not request.user.is_staff:
            return Response({
                'error': 'Unauthorized access to user data'
            }, status=status.HTTP_403_FORBIDDEN)
        
        agent = AnalyticsAgent()
        if not agent.initialize():
            return Response({
                'error': 'Failed to initialize Analytics Agent'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        response = agent.analyze_patterns(user_id, data_type, days_back)
        
        if response.success:
            return Response(response.to_dict(), status=status.HTTP_200_OK)
        else:
            return Response(response.to_dict(), status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Error analyzing patterns: {e}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Performance Agent Endpoints
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def performance_agent_status(request):
    """Get Performance Agent status."""
    try:
        from api.agent_modules.performance.agent import PerformanceAgent
        
        # Only allow staff users to access performance data
        if not request.user.is_staff:
            return Response({
                'error': 'Unauthorized access'
            }, status=status.HTTP_403_FORBIDDEN)
        
        agent = PerformanceAgent()
        if not agent.initialize():
            return Response({
                'error': 'Failed to initialize Performance Agent'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        agent_status = agent.get_status()
        return Response(agent_status, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error getting performance agent status: {e}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def optimize_database_queries(request):
    """Optimize database queries."""
    try:
        from api.agent_modules.performance.agent import PerformanceAgent
        
        # Only allow staff users to perform optimizations
        if not request.user.is_staff:
            return Response({
                'error': 'Unauthorized access'
            }, status=status.HTTP_403_FORBIDDEN)
        
        data = json.loads(request.body) if request.body else {}
        optimization_type = data.get('optimization_type', 'general')
        
        agent = PerformanceAgent()
        if not agent.initialize():
            return Response({
                'error': 'Failed to initialize Performance Agent'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        response = agent.optimize_database_queries(optimization_type)
        
        if response.success:
            return Response(response.to_dict(), status=status.HTTP_200_OK)
        else:
            return Response(response.to_dict(), status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Error optimizing database queries: {e}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def refresh_cache_layer(request):
    """Refresh caching layers."""
    try:
        from api.agent_modules.performance.agent import PerformanceAgent
        
        # Only allow staff users to refresh cache
        if not request.user.is_staff:
            return Response({
                'error': 'Unauthorized access'
            }, status=status.HTTP_403_FORBIDDEN)
        
        data = json.loads(request.body) if request.body else {}
        cache_type = data.get('cache_type', 'all')
        
        agent = PerformanceAgent()
        if not agent.initialize():
            return Response({
                'error': 'Failed to initialize Performance Agent'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        response = agent.refresh_cache_layer(cache_type)
        
        if response.success:
            return Response(response.to_dict(), status=status.HTTP_200_OK)
        else:
            return Response(response.to_dict(), status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Error refreshing cache layer: {e}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def monitor_system_performance(request):
    """Monitor overall system performance."""
    try:
        from api.agent_modules.performance.agent import PerformanceAgent
        
        # Only allow staff users to monitor performance
        if not request.user.is_staff:
            return Response({
                'error': 'Unauthorized access'
            }, status=status.HTTP_403_FORBIDDEN)
        
        agent = PerformanceAgent()
        if not agent.initialize():
            return Response({
                'error': 'Failed to initialize Performance Agent'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        response = agent.monitor_system_performance()
        
        if response.success:
            return Response(response.to_dict(), status=status.HTTP_200_OK)
        else:
            return Response(response.to_dict(), status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Error monitoring system performance: {e}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Clinical Agent Endpoints
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def clinical_agent_status(request):
    """Get Clinical Agent status."""
    try:
        from api.agent_modules.clinical.agent import ClinicalAgent
        
        agent = ClinicalAgent()
        if not agent.initialize():
            return Response({
                'error': 'Failed to initialize Clinical Agent'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        agent_status = agent.get_status()
        return Response(agent_status, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error getting clinical agent status: {e}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_health_screening_recommendations(request):
    """Get health screening recommendations."""
    try:
        from api.agent_modules.clinical.agent import ClinicalAgent
        
        data = json.loads(request.body) if request.body else {}
        user_id = data.get('user_id', request.user.id)
        
        # Verify user access
        if user_id != request.user.id and not request.user.is_staff:
            return Response({
                'error': 'Unauthorized access to user data'
            }, status=status.HTTP_403_FORBIDDEN)
        
        agent = ClinicalAgent()
        if not agent.initialize():
            return Response({
                'error': 'Failed to initialize Clinical Agent'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        response = agent.get_health_screening_recommendations(user_id)
        
        if response.success:
            return Response(response.to_dict(), status=status.HTTP_200_OK)
        else:
            return Response(response.to_dict(), status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Error getting health screening recommendations: {e}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def schedule_medical_appointment(request):
    """Schedule a medical appointment."""
    try:
        from api.agent_modules.clinical.agent import ClinicalAgent
        
        data = json.loads(request.body) if request.body else {}
        user_id = data.get('user_id', request.user.id)
        appointment_data = data.get('appointment_data', {})
        
        # Verify user access
        if user_id != request.user.id and not request.user.is_staff:
            return Response({
                'error': 'Unauthorized access to user data'
            }, status=status.HTTP_403_FORBIDDEN)
        
        agent = ClinicalAgent()
        if not agent.initialize():
            return Response({
                'error': 'Failed to initialize Clinical Agent'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        response = agent.schedule_medical_appointment(user_id, appointment_data)
        
        if response.success:
            return Response(response.to_dict(), status=status.HTTP_201_CREATED)
        else:
            return Response(response.to_dict(), status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Error scheduling medical appointment: {e}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_medical_history(request):
    """Update user's medical history."""
    try:
        from api.agent_modules.clinical.agent import ClinicalAgent
        
        data = json.loads(request.body) if request.body else {}
        user_id = data.get('user_id', request.user.id)
        medical_data = data.get('medical_data', {})
        
        # Verify user access
        if user_id != request.user.id and not request.user.is_staff:
            return Response({
                'error': 'Unauthorized access to user data'
            }, status=status.HTTP_403_FORBIDDEN)
        
        agent = ClinicalAgent()
        if not agent.initialize():
            return Response({
                'error': 'Failed to initialize Clinical Agent'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        response = agent.update_medical_history(user_id, medical_data)
        
        if response.success:
            return Response(response.to_dict(), status=status.HTTP_200_OK)
        else:
            return Response(response.to_dict(), status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Error updating medical history: {e}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_medical_history_summary(request):
    """Get comprehensive medical history summary."""
    try:
        from api.agent_modules.clinical.agent import ClinicalAgent
        
        user_id = request.GET.get('user_id', request.user.id)
        
        # Verify user access
        if int(user_id) != request.user.id and not request.user.is_staff:
            return Response({
                'error': 'Unauthorized access to user data'
            }, status=status.HTTP_403_FORBIDDEN)
        
        agent = ClinicalAgent()
        if not agent.initialize():
            return Response({
                'error': 'Failed to initialize Clinical Agent'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        response = agent.get_medical_history_summary(int(user_id))
        
        if response.success:
            return Response(response.to_dict(), status=status.HTTP_200_OK)
        else:
            return Response(response.to_dict(), status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Error getting medical history summary: {e}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Health Check Endpoint for Load Balancers
@api_view(['GET'])
def health_check(request):
    """Health check endpoint for load balancers."""
    try:
        # Test database connectivity
        from django.db import connection
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        
        # Test cache connectivity
        from django.core.cache import cache
        cache.set('health_check', 'ok', 10)
        cache_test = cache.get('health_check')
        
        if cache_test != 'ok':
            raise Exception("Cache connectivity failed")
        
        return Response({
            'status': 'healthy',
            'database': 'connected',
            'cache': 'connected',
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return Response({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)