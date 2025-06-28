# api/views/womens_health_views.py

from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction
from datetime import datetime, date
import logging

from api.models import (
    WomensHealthProfile,
    MenstrualCycle,
    PregnancyRecord,
    FertilityTracking,
    HealthGoal,
    DailyHealthLog,
    HealthScreening
)
from api.services.womens_health_verification import (
    WomensHealthVerificationService,
    WomensHealthPermissionMixin
)
from api.serializers import (
    WomensHealthProfileSerializer,
    MenstrualCycleSerializer,
    PregnancyRecordSerializer,
    FertilityTrackingSerializer,
    HealthGoalSerializer,
    DailyHealthLogSerializer,
    HealthScreeningSerializer
)

User = get_user_model()
logger = logging.getLogger(__name__)


class WomensHealthVerificationView(APIView):
    """Handle women's health verification requests"""
    
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get current verification status"""
        try:
            status_data = WomensHealthVerificationService.get_verification_status(request.user)
            return Response({
                'success': True,
                'status': status_data
            })
        except Exception as e:
            logger.error(f"Error getting verification status for user {request.user.id}: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error retrieving verification status'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request):
        """Request verification OTP"""
        try:
            result = WomensHealthVerificationService.request_verification(request.user)
            
            if result['success']:
                return Response(result)
            else:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Error requesting verification for user {request.user.id}: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error processing verification request'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WomensHealthVerifyOTPView(APIView):
    """Verify OTP for women's health access"""
    
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Verify provided OTP"""
        try:
            otp = request.data.get('otp')
            
            if not otp:
                return Response({
                    'success': False,
                    'message': 'OTP is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            result = WomensHealthVerificationService.verify_otp(request.user, otp)
            
            if result['success']:
                return Response(result)
            else:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Error verifying OTP for user {request.user.id}: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error processing OTP verification'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WomensHealthProfileView(APIView, WomensHealthPermissionMixin):
    """Manage women's health profile"""
    
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get user's women's health profile"""
        try:
            self.require_womens_health_verification(request.user)
            
            profile = get_object_or_404(WomensHealthProfile, user=request.user)
            serializer = WomensHealthProfileSerializer(profile)
            
            return Response({
                'success': True,
                'profile': serializer.data
            })
            
        except WomensHealthProfile.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Profile not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error getting profile for user {request.user.id}: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error retrieving profile'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request):
        """Create women's health profile"""
        try:
            self.require_womens_health_verification(request.user)
            
            # Check if profile already exists
            if WomensHealthProfile.objects.filter(user=request.user).exists():
                return Response({
                    'success': False,
                    'message': 'Profile already exists'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            serializer = WomensHealthProfileSerializer(data=request.data)
            if serializer.is_valid():
                profile = serializer.save(user=request.user, last_updated_by=request.user)
                return Response({
                    'success': True,
                    'message': 'Profile created successfully',
                    'profile': WomensHealthProfileSerializer(profile).data
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'success': False,
                    'message': 'Invalid data',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Error creating profile for user {request.user.id}: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error creating profile'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def put(self, request):
        """Update women's health profile"""
        try:
            self.require_womens_health_verification(request.user)
            
            profile = get_object_or_404(WomensHealthProfile, user=request.user)
            serializer = WomensHealthProfileSerializer(profile, data=request.data, partial=True)
            
            if serializer.is_valid():
                profile = serializer.save(last_updated_by=request.user)
                return Response({
                    'success': True,
                    'message': 'Profile updated successfully',
                    'profile': WomensHealthProfileSerializer(profile).data
                })
            else:
                return Response({
                    'success': False,
                    'message': 'Invalid data',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Error updating profile for user {request.user.id}: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error updating profile'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MenstrualCycleView(APIView, WomensHealthPermissionMixin):
    """Manage menstrual cycles"""
    
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get user's menstrual cycles"""
        try:
            self.require_womens_health_verification(request.user)
            
            profile = get_object_or_404(WomensHealthProfile, user=request.user)
            cycles = MenstrualCycle.objects.filter(womens_health_profile=profile).order_by('-cycle_start_date')
            
            # Pagination
            limit = int(request.query_params.get('limit', 10))
            offset = int(request.query_params.get('offset', 0))
            cycles_page = cycles[offset:offset + limit]
            
            serializer = MenstrualCycleSerializer(cycles_page, many=True)
            
            return Response({
                'success': True,
                'cycles': serializer.data,
                'total_count': cycles.count(),
                'has_more': cycles.count() > offset + limit
            })
            
        except Exception as e:
            logger.error(f"Error getting cycles for user {request.user.id}: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error retrieving cycles'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request):
        """Create new menstrual cycle"""
        try:
            self.require_womens_health_verification(request.user)
            
            profile = get_object_or_404(WomensHealthProfile, user=request.user)
            
            serializer = MenstrualCycleSerializer(data=request.data)
            if serializer.is_valid():
                cycle = serializer.save(womens_health_profile=profile)
                return Response({
                    'success': True,
                    'message': 'Cycle created successfully',
                    'cycle': MenstrualCycleSerializer(cycle).data
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'success': False,
                    'message': 'Invalid data',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Error creating cycle for user {request.user.id}: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error creating cycle'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MenstrualCycleDetailView(APIView, WomensHealthPermissionMixin):
    """Manage individual menstrual cycle"""
    
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, cycle_id):
        """Get specific cycle"""
        try:
            self.require_womens_health_verification(request.user)
            
            profile = get_object_or_404(WomensHealthProfile, user=request.user)
            cycle = get_object_or_404(MenstrualCycle, id=cycle_id, womens_health_profile=profile)
            
            serializer = MenstrualCycleSerializer(cycle)
            return Response({
                'success': True,
                'cycle': serializer.data
            })
            
        except Exception as e:
            logger.error(f"Error getting cycle {cycle_id} for user {request.user.id}: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error retrieving cycle'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def put(self, request, cycle_id):
        """Update specific cycle"""
        try:
            self.require_womens_health_verification(request.user)
            
            profile = get_object_or_404(WomensHealthProfile, user=request.user)
            cycle = get_object_or_404(MenstrualCycle, id=cycle_id, womens_health_profile=profile)
            
            serializer = MenstrualCycleSerializer(cycle, data=request.data, partial=True)
            if serializer.is_valid():
                cycle = serializer.save()
                return Response({
                    'success': True,
                    'message': 'Cycle updated successfully',
                    'cycle': MenstrualCycleSerializer(cycle).data
                })
            else:
                return Response({
                    'success': False,
                    'message': 'Invalid data',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Error updating cycle {cycle_id} for user {request.user.id}: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error updating cycle'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request, cycle_id):
        """Delete specific cycle"""
        try:
            self.require_womens_health_verification(request.user)
            
            profile = get_object_or_404(WomensHealthProfile, user=request.user)
            cycle = get_object_or_404(MenstrualCycle, id=cycle_id, womens_health_profile=profile)
            
            cycle.delete()
            return Response({
                'success': True,
                'message': 'Cycle deleted successfully'
            })
            
        except Exception as e:
            logger.error(f"Error deleting cycle {cycle_id} for user {request.user.id}: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error deleting cycle'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PregnancyRecordView(APIView, WomensHealthPermissionMixin):
    """Manage pregnancy records"""
    
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get user's pregnancy records"""
        try:
            self.require_womens_health_verification(request.user)
            
            profile = get_object_or_404(WomensHealthProfile, user=request.user)
            pregnancies = PregnancyRecord.objects.filter(womens_health_profile=profile).order_by('-pregnancy_number')
            
            serializer = PregnancyRecordSerializer(pregnancies, many=True)
            
            return Response({
                'success': True,
                'pregnancies': serializer.data,
                'total_count': pregnancies.count()
            })
            
        except Exception as e:
            logger.error(f"Error getting pregnancies for user {request.user.id}: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error retrieving pregnancy records'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request):
        """Create new pregnancy record"""
        try:
            self.require_womens_health_verification(request.user)
            
            profile = get_object_or_404(WomensHealthProfile, user=request.user)
            
            serializer = PregnancyRecordSerializer(data=request.data)
            if serializer.is_valid():
                pregnancy = serializer.save(womens_health_profile=profile)
                return Response({
                    'success': True,
                    'message': 'Pregnancy record created successfully',
                    'pregnancy': PregnancyRecordSerializer(pregnancy).data
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'success': False,
                    'message': 'Invalid data',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Error creating pregnancy for user {request.user.id}: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error creating pregnancy record'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FertilityTrackingView(APIView, WomensHealthPermissionMixin):
    """Manage fertility tracking data"""
    
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get fertility tracking data"""
        try:
            self.require_womens_health_verification(request.user)
            
            profile = get_object_or_404(WomensHealthProfile, user=request.user)
            
            # Date range filtering
            start_date = request.query_params.get('start_date')
            end_date = request.query_params.get('end_date')
            
            fertility_data = FertilityTracking.objects.filter(womens_health_profile=profile)
            
            if start_date:
                fertility_data = fertility_data.filter(date__gte=start_date)
            if end_date:
                fertility_data = fertility_data.filter(date__lte=end_date)
            
            fertility_data = fertility_data.order_by('-date')
            
            serializer = FertilityTrackingSerializer(fertility_data, many=True)
            
            return Response({
                'success': True,
                'fertility_data': serializer.data,
                'total_count': fertility_data.count()
            })
            
        except Exception as e:
            logger.error(f"Error getting fertility data for user {request.user.id}: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error retrieving fertility data'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request):
        """Add fertility tracking entry"""
        try:
            self.require_womens_health_verification(request.user)
            
            profile = get_object_or_404(WomensHealthProfile, user=request.user)
            
            serializer = FertilityTrackingSerializer(data=request.data)
            if serializer.is_valid():
                tracking = serializer.save(womens_health_profile=profile)
                return Response({
                    'success': True,
                    'message': 'Fertility data added successfully',
                    'tracking': FertilityTrackingSerializer(tracking).data
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'success': False,
                    'message': 'Invalid data',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Error adding fertility data for user {request.user.id}: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error adding fertility data'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HealthGoalView(APIView, WomensHealthPermissionMixin):
    """Manage health goals"""
    
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get user's health goals"""
        try:
            self.require_womens_health_verification(request.user)
            
            profile = get_object_or_404(WomensHealthProfile, user=request.user)
            goals = HealthGoal.objects.filter(womens_health_profile=profile).order_by('-created_at')
            
            # Filter by status if provided
            goal_status = request.query_params.get('status')
            if goal_status:
                goals = goals.filter(status=goal_status)
            
            serializer = HealthGoalSerializer(goals, many=True)
            
            return Response({
                'success': True,
                'goals': serializer.data,
                'total_count': goals.count()
            })
            
        except Exception as e:
            logger.error(f"Error getting goals for user {request.user.id}: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error retrieving health goals'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request):
        """Create new health goal"""
        try:
            self.require_womens_health_verification(request.user)
            
            profile = get_object_or_404(WomensHealthProfile, user=request.user)
            
            serializer = HealthGoalSerializer(data=request.data)
            if serializer.is_valid():
                goal = serializer.save(womens_health_profile=profile)
                return Response({
                    'success': True,
                    'message': 'Health goal created successfully',
                    'goal': HealthGoalSerializer(goal).data
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'success': False,
                    'message': 'Invalid data',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Error creating goal for user {request.user.id}: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error creating health goal'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DailyHealthLogView(APIView, WomensHealthPermissionMixin):
    """Manage daily health logs"""
    
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get daily health logs"""
        try:
            self.require_womens_health_verification(request.user)
            
            profile = get_object_or_404(WomensHealthProfile, user=request.user)
            
            # Date range filtering
            start_date = request.query_params.get('start_date')
            end_date = request.query_params.get('end_date')
            
            logs = DailyHealthLog.objects.filter(womens_health_profile=profile)
            
            if start_date:
                logs = logs.filter(date__gte=start_date)
            if end_date:
                logs = logs.filter(date__lte=end_date)
            
            logs = logs.order_by('-date')
            
            serializer = DailyHealthLogSerializer(logs, many=True)
            
            return Response({
                'success': True,
                'logs': serializer.data,
                'total_count': logs.count()
            })
            
        except Exception as e:
            logger.error(f"Error getting logs for user {request.user.id}: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error retrieving health logs'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request):
        """Create or update daily health log"""
        try:
            self.require_womens_health_verification(request.user)
            
            profile = get_object_or_404(WomensHealthProfile, user=request.user)
            log_date = request.data.get('date')
            
            if not log_date:
                return Response({
                    'success': False,
                    'message': 'Date is required for health log'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Try to get existing log for this date
            try:
                existing_log = DailyHealthLog.objects.get(
                    womens_health_profile=profile,
                    date=log_date
                )
                # Update existing log
                serializer = DailyHealthLogSerializer(existing_log, data=request.data, partial=True)
                if serializer.is_valid():
                    log = serializer.save()
                    logger.info(f"Updated health log for user {request.user.id} on date {log_date}")
                    return Response({
                        'success': True,
                        'message': 'Health log updated successfully',
                        'log': DailyHealthLogSerializer(log).data,
                        'action': 'updated'
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({
                        'success': False,
                        'message': 'Invalid data for update',
                        'errors': serializer.errors
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
            except DailyHealthLog.DoesNotExist:
                # Create new log
                serializer = DailyHealthLogSerializer(data=request.data)
                if serializer.is_valid():
                    log = serializer.save(womens_health_profile=profile)
                    logger.info(f"Created new health log for user {request.user.id} on date {log_date}")
                    return Response({
                        'success': True,
                        'message': 'Health log created successfully',
                        'log': DailyHealthLogSerializer(log).data,
                        'action': 'created'
                    }, status=status.HTTP_201_CREATED)
                else:
                    return Response({
                        'success': False,
                        'message': 'Invalid data for creation',
                        'errors': serializer.errors
                    }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Error processing health log for user {request.user.id}: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error processing health log'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HealthScreeningView(APIView, WomensHealthPermissionMixin):
    """Manage health screenings"""
    
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get health screenings"""
        try:
            self.require_womens_health_verification(request.user)
            
            profile = get_object_or_404(WomensHealthProfile, user=request.user)
            screenings = HealthScreening.objects.filter(womens_health_profile=profile).order_by('-scheduled_date')
            
            # Filter by type if provided
            screening_type = request.query_params.get('type')
            if screening_type:
                screenings = screenings.filter(screening_type=screening_type)
            
            serializer = HealthScreeningSerializer(screenings, many=True)
            
            return Response({
                'success': True,
                'screenings': serializer.data,
                'total_count': screenings.count()
            })
            
        except Exception as e:
            logger.error(f"Error getting screenings for user {request.user.id}: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error retrieving health screenings'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request):
        """Create health screening"""
        try:
            self.require_womens_health_verification(request.user)
            
            profile = get_object_or_404(WomensHealthProfile, user=request.user)
            
            serializer = HealthScreeningSerializer(data=request.data)
            if serializer.is_valid():
                screening = serializer.save(womens_health_profile=profile, created_by=request.user)
                return Response({
                    'success': True,
                    'message': 'Health screening created successfully',
                    'screening': HealthScreeningSerializer(screening).data
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'success': False,
                    'message': 'Invalid data',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Error creating screening for user {request.user.id}: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error creating health screening'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def womens_health_dashboard_data(request):
    """Get comprehensive dashboard data for women's health"""
    try:
        # Check verification
        mixin = WomensHealthPermissionMixin()
        mixin.require_womens_health_verification(request.user)
        
        # Get or create profile for the user
        profile, created = WomensHealthProfile.objects.get_or_create(
            user=request.user,
            defaults={
                'average_cycle_length': 28,
                'average_period_duration': 5,
                'pregnancy_status': 'not_pregnant',
                'total_pregnancies': 0,
                'live_births': 0,
                'miscarriages': 0,
                'abortions': 0,
                'current_contraception': '',
                'fertility_tracking_enabled': False,
                'temperature_tracking': False,
                'cervical_mucus_tracking': False,
                'ovulation_test_tracking': False,
                'pcos': False,
                'endometriosis': False,
                'fibroids': False,
                'thyroid_disorder': False,
                'diabetes': False,
                'gestational_diabetes_history': False,
                'hypertension': False,
                'family_history_breast_cancer': False,
                'family_history_ovarian_cancer': False,
                'family_history_cervical_cancer': False,
                'family_history_diabetes': False,
                'family_history_heart_disease': False,
                'exercise_frequency': '',
                'stress_level': '',
                'sleep_quality': '',
                'health_goals_list': [],
                'notification_preferences': {},
                'privacy_settings': {},
                'profile_completion_percentage': 20,
                'last_updated_by': request.user
            }
        )
        
        # Get current cycle
        current_cycle = MenstrualCycle.objects.filter(
            womens_health_profile=profile,
            is_current_cycle=True
        ).first()
        
        # Get current pregnancy
        current_pregnancy = PregnancyRecord.objects.filter(
            womens_health_profile=profile,
            is_current_pregnancy=True
        ).first()
        
        # Get recent fertility data
        recent_fertility = FertilityTracking.objects.filter(
            womens_health_profile=profile
        ).order_by('-date')[:7]
        
        # Get active goals
        active_goals = HealthGoal.objects.filter(
            womens_health_profile=profile,
            status='active'
        )[:5]
        
        # Get upcoming screenings
        upcoming_screenings = HealthScreening.objects.filter(
            womens_health_profile=profile,
            status='scheduled',
            scheduled_date__gte=timezone.now().date()
        ).order_by('scheduled_date')[:3]
        
        # Get recent health logs
        recent_logs = DailyHealthLog.objects.filter(
            womens_health_profile=profile
        ).order_by('-date')[:7]
        
        dashboard_data = {
            'profile': WomensHealthProfileSerializer(profile).data,
            'current_cycle': MenstrualCycleSerializer(current_cycle).data if current_cycle else None,
            'current_pregnancy': PregnancyRecordSerializer(current_pregnancy).data if current_pregnancy else None,
            'recent_fertility_data': FertilityTrackingSerializer(recent_fertility, many=True).data,
            'active_goals': HealthGoalSerializer(active_goals, many=True).data,
            'upcoming_screenings': HealthScreeningSerializer(upcoming_screenings, many=True).data,
            'recent_health_logs': DailyHealthLogSerializer(recent_logs, many=True).data,
            'summary': {
                'total_cycles': MenstrualCycle.objects.filter(womens_health_profile=profile).count(),
                'total_pregnancies': PregnancyRecord.objects.filter(womens_health_profile=profile).count(),
                'active_goals_count': active_goals.count(),
                'profile_completion': profile.profile_completion_percentage
            }
        }
        
        return Response({
            'success': True,
            'dashboard': dashboard_data
        })
        
    except Exception as e:
        logger.error(f"Error getting dashboard data for user {request.user.id}: {str(e)}")
        return Response({
            'success': False,
            'message': 'Error retrieving dashboard data'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)