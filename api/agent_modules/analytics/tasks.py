# api/agent_modules/analytics/tasks.py

from celery import shared_task
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.cache import cache
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def calculate_health_insights(self, user_id: int) -> Dict[str, Any]:
    """
    Background task to calculate comprehensive health insights for a user.
    
    Args:
        user_id: ID of the user to analyze
        
    Returns:
        Dictionary with calculation results
    """
    try:
        logger.info(f"Calculating health insights for user {user_id}")
        
        from ..analytics.agent import AnalyticsAgent
        from ..analytics.models import HealthInsight
        
        # Initialize analytics agent
        agent = AnalyticsAgent()
        if not agent.initialize():
            raise Exception("Failed to initialize Analytics Agent")
        
        # Generate comprehensive insights
        insights_response = agent.generate_health_insights(user_id)
        
        if not insights_response.success:
            raise Exception(f"Failed to generate insights: {insights_response.error}")
        
        insights_data = insights_response.data
        
        # Store insights in database
        stored_insights = []
        
        # Store cycle analysis insights
        if 'cycle_analysis' in insights_data:
            cycle_data = insights_data['cycle_analysis']
            if 'irregularities' in cycle_data:
                for irregularity in cycle_data['irregularities']:
                    insight = HealthInsight.objects.create(
                        user_id=user_id,
                        insight_type='cycle_irregularity',
                        title=f"Cycle Irregularity: {irregularity['type'].replace('_', ' ').title()}",
                        description=irregularity['description'],
                        confidence_score=0.8,  # Default confidence for detected irregularities
                        data_points={
                            'irregularity_type': irregularity['type'],
                            'severity': irregularity['severity'],
                            'analysis_data': cycle_data
                        },
                        expires_at=timezone.now() + timedelta(days=30)
                    )
                    stored_insights.append(insight.id)
        
        # Store predictions as insights
        if 'predictions' in insights_data:
            predictions = insights_data['predictions']
            
            if 'period_prediction' in predictions and not predictions['period_prediction'].get('insufficient_data'):
                period_pred = predictions['period_prediction']
                insight = HealthInsight.objects.create(
                    user_id=user_id,
                    insight_type='health_prediction',
                    title="Next Period Prediction",
                    description=f"Your next period is predicted for {period_pred['predicted_date'][:10]}",
                    confidence_score=period_pred.get('confidence', 0.7),
                    data_points=period_pred,
                    expires_at=timezone.now() + timedelta(days=35)  # Expire after typical cycle
                )
                stored_insights.append(insight.id)
            
            if 'fertility_prediction' in predictions and not predictions['fertility_prediction'].get('insufficient_data'):
                fertility_pred = predictions['fertility_prediction']
                insight = HealthInsight.objects.create(
                    user_id=user_id,
                    insight_type='health_prediction',
                    title="Fertility Window Prediction",
                    description="Your fertile window has been calculated based on cycle patterns",
                    confidence_score=fertility_pred.get('confidence', 0.7),
                    data_points=fertility_pred,
                    expires_at=timezone.now() + timedelta(days=35)
                )
                stored_insights.append(insight.id)
        
        # Store recommendations as insights
        if 'recommendations' in insights_data:
            recommendations = insights_data['recommendations']
            
            for category, recs in recommendations.items():
                if isinstance(recs, list):
                    for rec in recs:
                        insight = HealthInsight.objects.create(
                            user_id=user_id,
                            insight_type='recommendation',
                            title=rec.get('title', f"{category.title()} Recommendation"),
                            description=rec.get('description', ''),
                            confidence_score=0.6,  # Default confidence for recommendations
                            data_points={
                                'category': category,
                                'recommendation_data': rec
                            },
                            expires_at=timezone.now() + timedelta(days=7)  # Weekly refresh
                        )
                        stored_insights.append(insight.id)
        
        # Cache results for quick access
        cache_key = f"health_insights_{user_id}"
        cache.set(cache_key, insights_data, timeout=3600)  # Cache for 1 hour
        
        logger.info(f"Successfully calculated health insights for user {user_id}. "
                   f"Created {len(stored_insights)} insight records.")
        
        return {
            'success': True,
            'user_id': user_id,
            'insights_created': len(stored_insights),
            'insight_ids': stored_insights,
            'cache_key': cache_key
        }
        
    except Exception as e:
        logger.error(f"Error calculating health insights for user {user_id}: {e}")
        
        # Retry logic
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying health insights calculation for user {user_id} "
                       f"(attempt {self.request.retries + 1})")
            raise self.retry(countdown=60, exc=e)
        
        return {
            'success': False,
            'user_id': user_id,
            'error': str(e),
            'retries_exhausted': True
        }


@shared_task
def update_cycle_predictions(user_id: int) -> Dict[str, Any]:
    """
    Background task to update cycle predictions when new cycle data is added.
    
    Args:
        user_id: ID of the user
        
    Returns:
        Dictionary with update results
    """
    try:
        logger.info(f"Updating cycle predictions for user {user_id}")
        
        from ..analytics.agent import AnalyticsAgent
        from ..analytics.models import UserPrediction, PredictionModel
        
        # Initialize analytics agent
        agent = AnalyticsAgent()
        if not agent.initialize():
            raise Exception("Failed to initialize Analytics Agent")
        
        # Get new predictions
        period_response = agent.predict_next_period(user_id)
        fertility_response = agent.predict_fertility_window(user_id)
        
        if not period_response.success or not fertility_response.success:
            raise Exception("Failed to generate predictions")
        
        # Get or create prediction models
        period_model, _ = PredictionModel.objects.get_or_create(
            name='basic_period_predictor',
            model_type='cycle_prediction',
            defaults={
                'version': '1.0.0',
                'description': 'Basic period prediction based on cycle history',
                'algorithm': 'average_cycle_length',
                'parameters': {'method': 'simple_average'},
                'is_active': True
            }
        )
        
        fertility_model, _ = PredictionModel.objects.get_or_create(
            name='basic_fertility_predictor',
            model_type='fertility_prediction',
            defaults={
                'version': '1.0.0',
                'description': 'Basic fertility window prediction',
                'algorithm': 'calendar_method',
                'parameters': {'ovulation_offset': 14},
                'is_active': True
            }
        )
        
        # Store new predictions
        predictions_created = []
        
        if not period_response.data.get('insufficient_data'):
            period_data = period_response.data
            prediction = UserPrediction.objects.create(
                user_id=user_id,
                model=period_model,
                prediction_data=period_data,
                confidence_score=period_data.get('confidence', 0.7),
                predicted_date=datetime.fromisoformat(
                    period_data['predicted_date'].replace('Z', '+00:00')
                ).date(),
                status='active'
            )
            predictions_created.append(prediction.id)
        
        if not fertility_response.data.get('insufficient_data'):
            fertility_data = fertility_response.data
            prediction = UserPrediction.objects.create(
                user_id=user_id,
                model=fertility_model,
                prediction_data=fertility_data,
                confidence_score=fertility_data.get('confidence', 0.7),
                predicted_date=datetime.fromisoformat(
                    fertility_data['fertile_window']['peak_day']
                ).date(),
                status='active'
            )
            predictions_created.append(prediction.id)
        
        logger.info(f"Updated cycle predictions for user {user_id}. "
                   f"Created {len(predictions_created)} predictions.")
        
        return {
            'success': True,
            'user_id': user_id,
            'predictions_created': len(predictions_created),
            'prediction_ids': predictions_created
        }
        
    except Exception as e:
        logger.error(f"Error updating cycle predictions for user {user_id}: {e}")
        return {
            'success': False,
            'user_id': user_id,
            'error': str(e)
        }


@shared_task
def analyze_cycle_patterns(user_id: int) -> Dict[str, Any]:
    """
    Background task to analyze cycle patterns and detect irregularities.
    
    Args:
        user_id: ID of the user
        
    Returns:
        Dictionary with analysis results
    """
    try:
        logger.info(f"Analyzing cycle patterns for user {user_id}")
        
        from ..analytics.agent import AnalyticsAgent
        from ..analytics.models import CycleInsight
        
        # Initialize analytics agent
        agent = AnalyticsAgent()
        if not agent.initialize():
            raise Exception("Failed to initialize Analytics Agent")
        
        # Detect irregularities
        irregularities_response = agent.detect_cycle_irregularities(user_id)
        
        if not irregularities_response.success:
            raise Exception(f"Failed to analyze patterns: {irregularities_response.error}")
        
        analysis_data = irregularities_response.data
        
        if analysis_data.get('insufficient_data'):
            return {
                'success': True,
                'user_id': user_id,
                'insufficient_data': True,
                'message': analysis_data.get('message', 'Insufficient data for analysis')
            }
        
        # Store cycle insight
        cycle_insight = CycleInsight.objects.create(
            user_id=user_id,
            pattern_type='regularity',
            cycles_analyzed=analysis_data.get('cycle_count', 0),
            analysis_data=analysis_data,
            regularity_score=analysis_data.get('regularity_score'),
            insights_generated=analysis_data.get('irregularities', []),
            recommendations=[]  # TODO: Generate recommendations based on analysis
        )
        
        # Generate pattern-specific insights
        patterns_response = agent.analyze_health_patterns(user_id)
        
        if patterns_response.success:
            patterns_data = patterns_response.data
            
            for pattern_type, pattern_data in patterns_data.items():
                if pattern_type != 'analysis_date' and not pattern_data.get('no_data'):
                    CycleInsight.objects.create(
                        user_id=user_id,
                        pattern_type=pattern_type.replace('_patterns', ''),
                        cycles_analyzed=pattern_data.get('cycle_count', 0),
                        analysis_data=pattern_data,
                        insights_generated=pattern_data.get('patterns', []),
                        recommendations=pattern_data.get('recommendations', [])
                    )
        
        logger.info(f"Successfully analyzed cycle patterns for user {user_id}")
        
        return {
            'success': True,
            'user_id': user_id,
            'cycles_analyzed': analysis_data.get('cycle_count', 0),
            'regularity_score': analysis_data.get('regularity_score'),
            'irregularities_found': len(analysis_data.get('irregularities', [])),
            'insight_id': cycle_insight.id
        }
        
    except Exception as e:
        logger.error(f"Error analyzing cycle patterns for user {user_id}: {e}")
        return {
            'success': False,
            'user_id': user_id,
            'error': str(e)
        }


@shared_task
def cleanup_expired_insights():
    """
    Periodic task to clean up expired insights and cache entries.
    
    Returns:
        Dictionary with cleanup results
    """
    try:
        logger.info("Starting cleanup of expired insights")
        
        from ..analytics.models import HealthInsight, AnalyticsCache
        
        # Clean up expired insights
        expired_insights = HealthInsight.objects.filter(
            expires_at__lt=timezone.now(),
            is_active=True
        )
        expired_count = expired_insights.count()
        expired_insights.update(is_active=False)
        
        # Clean up expired cache entries
        cache_cleaned = AnalyticsCache.cleanup_expired()
        
        logger.info(f"Cleanup completed: {expired_count} insights deactivated, "
                   f"{cache_cleaned} cache entries removed")
        
        return {
            'success': True,
            'insights_deactivated': expired_count,
            'cache_entries_removed': cache_cleaned
        }
        
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        return {
            'success': False,
            'error': str(e)
        }


@shared_task
def generate_weekly_insights_report(user_id: int) -> Dict[str, Any]:
    """
    Generate weekly insights report for a user.
    
    Args:
        user_id: ID of the user
        
    Returns:
        Dictionary with report generation results
    """
    try:
        logger.info(f"Generating weekly insights report for user {user_id}")
        
        from ..analytics.models import HealthInsight, CycleInsight
        from django.db.models import Q
        
        # Get insights from the last week
        week_ago = timezone.now() - timedelta(days=7)
        
        recent_insights = HealthInsight.objects.filter(
            user_id=user_id,
            created_at__gte=week_ago,
            is_active=True
        ).order_by('-created_at')
        
        recent_cycle_insights = CycleInsight.objects.filter(
            user_id=user_id,
            created_at__gte=week_ago
        ).order_by('-created_at')
        
        # Compile report data
        report_data = {
            'user_id': user_id,
            'report_period': {
                'start': week_ago.isoformat(),
                'end': timezone.now().isoformat()
            },
            'insights_summary': {
                'total_insights': recent_insights.count(),
                'high_confidence': recent_insights.filter(confidence_level='high').count(),
                'medium_confidence': recent_insights.filter(confidence_level='medium').count(),
                'low_confidence': recent_insights.filter(confidence_level='low').count(),
            },
            'insight_types': {},
            'cycle_analysis_summary': {
                'total_analyses': recent_cycle_insights.count(),
                'pattern_types': list(recent_cycle_insights.values_list('pattern_type', flat=True).distinct())
            },
            'key_insights': [insight.to_dict() for insight in recent_insights[:5]],  # Top 5 insights
            'recommendations_count': recent_insights.filter(insight_type='recommendation').count()
        }
        
        # Count insights by type
        for insight_type, _ in HealthInsight.INSIGHT_TYPES:
            count = recent_insights.filter(insight_type=insight_type).count()
            if count > 0:
                report_data['insight_types'][insight_type] = count
        
        # Cache the report
        cache_key = f"weekly_report_{user_id}_{timezone.now().strftime('%Y_%W')}"
        cache.set(cache_key, report_data, timeout=86400 * 7)  # Cache for a week
        
        logger.info(f"Generated weekly insights report for user {user_id}: "
                   f"{recent_insights.count()} insights, {recent_cycle_insights.count()} analyses")
        
        return {
            'success': True,
            'user_id': user_id,
            'report_data': report_data,
            'cache_key': cache_key
        }
        
    except Exception as e:
        logger.error(f"Error generating weekly report for user {user_id}: {e}")
        return {
            'success': False,
            'user_id': user_id,
            'error': str(e)
        }


@shared_task
def batch_update_predictions(user_ids: list = None) -> Dict[str, Any]:
    """
    Batch update predictions for multiple users.
    
    Args:
        user_ids: List of user IDs to update (if None, updates all users)
        
    Returns:
        Dictionary with batch update results
    """
    try:
        logger.info(f"Starting batch prediction update for {len(user_ids) if user_ids else 'all'} users")
        
        if user_ids is None:
            # Get all users with women's health verification
            users = User.objects.filter(womens_health_verified=True)
            user_ids = list(users.values_list('id', flat=True))
        
        results = {
            'total_users': len(user_ids),
            'successful_updates': 0,
            'failed_updates': 0,
            'errors': []
        }
        
        for user_id in user_ids:
            try:
                # Schedule individual prediction update
                update_cycle_predictions.delay(user_id)
                results['successful_updates'] += 1
                
            except Exception as e:
                results['failed_updates'] += 1
                results['errors'].append({
                    'user_id': user_id,
                    'error': str(e)
                })
                logger.error(f"Failed to schedule prediction update for user {user_id}: {e}")
        
        logger.info(f"Batch prediction update completed: {results['successful_updates']} successful, "
                   f"{results['failed_updates']} failed")
        
        return {
            'success': True,
            'results': results
        }
        
    except Exception as e:
        logger.error(f"Error in batch prediction update: {e}")
        return {
            'success': False,
            'error': str(e)
        }