# api/views/medical/clinical_guidelines_views.py

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Q, Count, Avg
from django.utils import timezone
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
import logging

from api.models.medical.clinical_guideline import ClinicalGuideline, GuidelineAccess, GuidelineBookmark
from api.serializers import (
    ClinicalGuidelineSerializer, 
    ClinicalGuidelineCreateSerializer,
    GuidelineAccessSerializer,
    GuidelineBookmarkSerializer,
    ClinicalGuidelineStatsSerializer
)
from api.permissions import (
    IsHospitalAdmin, 
    IsHospitalAdminOrReadOnly, 
    CanAccessGuideline, 
    IsGuidelineOwnerOrReadOnly
)

logger = logging.getLogger(__name__)


class ClinicalGuidelineViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing clinical guidelines.
    
    Provides CRUD operations for clinical guidelines with proper permissions:
    - Hospital admins can create, read, update, delete their organization's guidelines
    - Medical staff can read published guidelines from their registered hospitals
    """
    
    queryset = ClinicalGuideline.objects.all()
    lookup_field = 'guideline_id'  # Use guideline_id instead of pk for lookups
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['title', 'description', 'keywords', 'specialty']
    filterset_fields = ['category', 'specialty', 'approval_status', 'priority', 'is_published', 'is_active']
    ordering_fields = ['created_at', 'title', 'effective_date', 'access_count', 'priority']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return ClinicalGuidelineCreateSerializer
        return ClinicalGuidelineSerializer
    
    def get_permissions(self):
        """
        Instantiate and return the list of permissions required for this view.
        """
        if self.action in ['create']:
            permission_classes = [IsHospitalAdmin]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [CanAccessGuideline, IsGuidelineOwnerOrReadOnly]
        else:  # list, retrieve, and custom actions
            permission_classes = [CanAccessGuideline]
        
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """
        Filter queryset based on user role and permissions.
        """
        user = self.request.user
        
        if not user.is_authenticated:
            return ClinicalGuideline.objects.none()
        
        # Hospital admins see all active guidelines from their organization
        if user.role == 'hospital_admin':
            try:
                hospital_admin = user.hospital_admin_profile
                return ClinicalGuideline.objects.filter(
                    organization=hospital_admin.hospital,
                    is_active=True  # Only show active (non-archived) guidelines
                ).select_related('organization', 'created_by', 'approved_by')
            except:
                return ClinicalGuideline.objects.none()
        
        # Medical staff see published guidelines from hospitals they're registered with
        elif user.role in ['doctor', 'nurse', 'pharmacist', 'lab_technician', 
                          'physician_assistant', 'medical_secretary', 'radiologist_tech',
                          'paramedic', 'emt', 'midwife']:
            try:
                # Get hospitals where user is registered/works
                user_hospitals = []
                
                # For doctors, get their primary hospital
                if hasattr(user, 'doctor_profile') and user.doctor_profile.hospital:
                    user_hospitals.append(user.doctor_profile.hospital.id)
                
                # Get other hospital registrations
                hospital_registrations = user.hospital_registrations.filter(
                    status='approved'
                ).values_list('hospital_id', flat=True)
                
                user_hospitals.extend(hospital_registrations)
                
                return ClinicalGuideline.objects.filter(
                    organization_id__in=user_hospitals,
                    is_published=True,
                    is_active=True,
                    approval_status='approved'
                ).select_related('organization', 'created_by', 'approved_by')
                
            except Exception as e:
                logger.error(f"Error filtering guidelines for user {user.id}: {e}")
                return ClinicalGuideline.objects.none()
        
        return ClinicalGuideline.objects.none()
    
    def perform_create(self, serializer):
        """
        Create a new clinical guideline with the current user as creator.
        """
        # The serializer already handles setting organization and created_by
        guideline = serializer.save()
        
        # Log the creation
        logger.info(f"Clinical guideline created: {guideline.title} by {self.request.user.email}")
    
    def perform_update(self, serializer):
        """
        Update a clinical guideline.
        """
        guideline = serializer.save()
        logger.info(f"Clinical guideline updated: {guideline.title} by {self.request.user.email}")
    
    def perform_destroy(self, instance):
        """
        Soft delete by archiving the guideline and cleaning up related bookmarks.
        """
        # Archive the guideline
        instance.archive()
        
        # Deactivate all bookmarks for this guideline
        from api.models.medical.clinical_guideline import GuidelineBookmark
        GuidelineBookmark.objects.filter(
            guideline=instance,
            is_active=True
        ).update(is_active=False)
        
        logger.info(f"Clinical guideline archived: {instance.title} by {self.request.user.email}")
        logger.info(f"Deactivated bookmarks for archived guideline: {instance.title}")
    
    @action(detail=True, methods=['post'])
    def approve(self, request, guideline_id=None):
        """
        Approve a clinical guideline (hospital admin only).
        """
        guideline = self.get_object()
        
        # Check if user can approve (must be hospital admin of the same organization)
        if request.user.role != 'hospital_admin':
            return Response(
                {'error': 'Only hospital administrators can approve guidelines.'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            hospital_admin = request.user.hospital_admin_profile
            if guideline.organization != hospital_admin.hospital:
                return Response(
                    {'error': 'You can only approve guidelines from your organization.'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
        except:
            return Response(
                {'error': 'Invalid hospital administrator.'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Approve the guideline
        guideline.approve(request.user)
        
        # Log the approval
        logger.info(f"Clinical guideline approved: {guideline.title} by {request.user.email}")
        
        serializer = self.get_serializer(guideline)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def publish(self, request, guideline_id=None):
        """
        Publish a clinical guideline (hospital admin only).
        """
        guideline = self.get_object()
        
        if guideline.publish():
            logger.info(f"Clinical guideline published: {guideline.title} by {request.user.email}")
            serializer = self.get_serializer(guideline)
            return Response(serializer.data)
        else:
            return Response(
                {'error': 'Guideline must be approved before publishing.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'])
    def download(self, request, guideline_id=None):
        """
        Download the guideline file with access logging.
        """
        guideline = self.get_object()
        
        # Log the access
        self._log_access(request, guideline, 'download')
        
        # Increment access count
        guideline.increment_access_count()
        
        if not guideline.file_path:
            return Response(
                {'error': 'No file attached to this guideline.'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            # Serve the file using Django's default storage
            from django.core.files.storage import default_storage
            from django.http import FileResponse
            import os
            
            if not default_storage.exists(guideline.file_path):
                return Response(
                    {'error': 'File not found.'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Get the file and create a response
            file_obj = default_storage.open(guideline.file_path, 'rb')
            filename = os.path.basename(guideline.file_path)
            
            response = FileResponse(
                file_obj,
                as_attachment=True,
                filename=f"{guideline.title}.{filename.split('.')[-1]}"
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error serving guideline file {guideline.file_path}: {e}")
            return Response(
                {'error': 'File not found or corrupted.'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post', 'delete'])
    def bookmark(self, request, guideline_id=None):
        """
        Bookmark or unbookmark a guideline.
        """
        guideline = self.get_object()
        
        if request.method == 'POST':
            # Create or update bookmark
            bookmark, created = GuidelineBookmark.objects.get_or_create(
                user=request.user,
                guideline=guideline,
                defaults={'is_active': True}
            )
            
            if not created and not bookmark.is_active:
                bookmark.is_active = True
                bookmark.save()
            
            # Update notes if provided
            notes = request.data.get('notes', '')
            if notes:
                bookmark.notes = notes
                bookmark.save()
            
            # Log the action
            self._log_access(request, guideline, 'bookmarked')
            
            serializer = GuidelineBookmarkSerializer(bookmark, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        elif request.method == 'DELETE':
            # Remove bookmark
            try:
                bookmark = GuidelineBookmark.objects.get(
                    user=request.user,
                    guideline=guideline,
                    is_active=True
                )
                bookmark.is_active = False
                bookmark.save()
                return Response(status=status.HTTP_204_NO_CONTENT)
            except GuidelineBookmark.DoesNotExist:
                return Response(
                    {'error': 'Bookmark not found.'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
    
    @action(detail=False, methods=['get'])
    def my_bookmarks(self, request):
        """
        Get user's bookmarked guidelines (only active, published ones).
        """
        bookmarks = GuidelineBookmark.objects.filter(
            user=request.user,
            is_active=True,
            guideline__is_active=True,  # Only active guidelines
            guideline__is_published=True,  # Only published guidelines
            guideline__approval_status='approved'  # Only approved guidelines
        ).select_related('guideline__organization', 'guideline__created_by')
        
        # Get the guidelines from bookmarks
        guidelines = [bookmark.guideline for bookmark in bookmarks]
        
        serializer = self.get_serializer(guidelines, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def categories(self, request):
        """
        Get available categories with counts.
        """
        queryset = self.get_queryset()
        categories = queryset.values('category').annotate(
            count=Count('id')
        ).order_by('category')
        
        return Response(categories)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Get guidelines statistics for hospital admins.
        """
        if request.user.role != 'hospital_admin':
            return Response(
                {'error': 'Only hospital administrators can view statistics.'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        queryset = self.get_queryset()
        
        stats = {
            'total_guidelines': queryset.count(),
            'published_guidelines': queryset.filter(is_published=True).count(),
            'draft_guidelines': queryset.filter(approval_status='draft').count(),
            'expired_guidelines': queryset.filter(
                expiry_date__lt=timezone.now().date()
            ).count(),
            'most_accessed': {},
            'categories_count': {},
            'recent_activities': []
        }
        
        # Most accessed guideline
        most_accessed = queryset.order_by('-access_count').first()
        if most_accessed:
            stats['most_accessed'] = {
                'title': most_accessed.title,
                'access_count': most_accessed.access_count
            }
        
        # Categories count
        categories = queryset.values('category').annotate(
            count=Count('id')
        ).order_by('-count')
        stats['categories_count'] = {cat['category']: cat['count'] for cat in categories}
        
        # Recent activities (recent access logs)
        recent_access = GuidelineAccess.objects.filter(
            guideline__in=queryset
        ).select_related('user', 'guideline').order_by('-accessed_at')[:10]
        
        stats['recent_activities'] = [
            {
                'user': access.user.get_full_name(),
                'action': access.action,
                'guideline': access.guideline.title,
                'timestamp': access.accessed_at
            }
            for access in recent_access
        ]
        
        serializer = ClinicalGuidelineStatsSerializer(stats)
        return Response(serializer.data)
    
    def _log_access(self, request, guideline, action):
        """
        Log access to a guideline for audit purposes.
        """
        try:
            # Get client IP
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0]
            else:
                ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
            
            # Create access log
            GuidelineAccess.objects.create(
                guideline=guideline,
                user=request.user,
                action=action,
                ip_address=ip,
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                department=getattr(request.user, 'department', '')
            )
        except Exception as e:
            logger.error(f"Error logging guideline access: {e}")


class GuidelineAccessViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing guideline access logs (hospital admin only).
    """
    
    queryset = GuidelineAccess.objects.all()
    serializer_class = GuidelineAccessSerializer
    permission_classes = [IsHospitalAdmin]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['action', 'guideline', 'user']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'guideline__title']
    ordering_fields = ['accessed_at', 'action']
    ordering = ['-accessed_at']
    
    def get_queryset(self):
        """
        Filter access logs to show only those for the admin's organization.
        """
        user = self.request.user
        
        if user.role != 'hospital_admin':
            return GuidelineAccess.objects.none()
        
        try:
            hospital_admin = user.hospital_admin_profile
            return GuidelineAccess.objects.filter(
                guideline__organization=hospital_admin.hospital
            ).select_related('user', 'guideline')
        except:
            return GuidelineAccess.objects.none()


class GuidelineBookmarkViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing guideline bookmarks.
    """
    
    queryset = GuidelineBookmark.objects.all()
    serializer_class = GuidelineBookmarkSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['guideline__category', 'is_active']
    ordering = ['-bookmarked_at']
    
    def get_queryset(self):
        """
        Return only the current user's bookmarks for active, published guidelines.
        """
        return GuidelineBookmark.objects.filter(
            user=self.request.user,
            is_active=True,
            guideline__is_active=True,  # Only active guidelines
            guideline__is_published=True,  # Only published guidelines  
            guideline__approval_status='approved'  # Only approved guidelines
        ).select_related('guideline__organization', 'guideline__created_by')