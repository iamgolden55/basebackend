# api/views/medical/guideline_upload_views.py

import os
import logging
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.db import transaction

from api.models.medical.clinical_guideline import ClinicalGuideline
from api.serializers import ClinicalGuidelineCreateSerializer, ClinicalGuidelineSerializer
from api.permissions import IsHospitalAdmin

logger = logging.getLogger(__name__)


class GuidelineFileUploadView(APIView):
    """
    Secure file upload for clinical guidelines.
    Integrates with the existing medical vault system for secure document storage.
    """
    
    permission_classes = [IsAuthenticated, IsHospitalAdmin]
    parser_classes = [MultiPartParser, FormParser]
    
    def post(self, request, *args, **kwargs):
        """
        Handle clinical guideline file upload with metadata.
        """
        try:
            # Validate user is hospital admin
            if request.user.role != 'hospital_admin':
                return Response({
                    'error': 'Only hospital administrators can upload clinical guidelines.'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Get hospital from admin profile
            try:
                hospital_admin = request.user.hospital_admin_profile
                hospital = hospital_admin.hospital
            except:
                return Response({
                    'error': 'Invalid hospital administrator profile.'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Check if file is provided
            if 'file' not in request.FILES:
                return Response({
                    'error': 'No file provided.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            uploaded_file = request.FILES['file']
            
            # Validate file for clinical guidelines
            validation_result = self._validate_guideline_file(uploaded_file)
            if not validation_result['valid']:
                return Response({
                    'error': validation_result['error']
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Extract guideline metadata from request
            guideline_data = {
                'title': request.data.get('title', ''),
                'description': request.data.get('description', ''),
                'version': request.data.get('version', '1.0'),
                'category': request.data.get('category', ''),
                'specialty': request.data.get('specialty', ''),
                'keywords': self._parse_keywords(request.data.get('keywords', '')),
                'content_type': 'pdf',  # Default for file uploads
                'effective_date': request.data.get('effective_date'),
                'expiry_date': request.data.get('expiry_date', None),
                'target_roles': self._parse_target_roles(request.data.get('target_roles', '')),
                'priority': request.data.get('priority', 'medium')
            }
            
            # Validate guideline metadata
            serializer = ClinicalGuidelineCreateSerializer(
                data=guideline_data, 
                context={'request': request}
            )
            if not serializer.is_valid():
                return Response({
                    'error': 'Invalid guideline data.',
                    'details': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Use transaction to ensure data consistency
            with transaction.atomic():
                # Create the clinical guideline first
                guideline = serializer.save()
                
                # Handle file upload if provided
                if uploaded_file:
                    # Save file to a simple guidelines directory
                    file_path = self._save_guideline_file(uploaded_file, guideline)
                    guideline.file_path = file_path
                    guideline.save(update_fields=['file_path'])
                
                logger.info(f"Clinical guideline uploaded successfully: {guideline.title} by {request.user.email}")
                
                # Return the created guideline
                response_serializer = ClinicalGuidelineSerializer(
                    guideline, 
                    context={'request': request}
                )
                return Response({
                    'message': 'Clinical guideline uploaded successfully.',
                    'guideline': response_serializer.data
                }, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            logger.error(f"Error uploading clinical guideline: {str(e)}")
            return Response({
                'error': 'An unexpected error occurred during upload.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _validate_guideline_file(self, uploaded_file):
        """
        Validate uploaded file for clinical guidelines.
        """
        # Check file extension
        filename = uploaded_file.name.lower()
        allowed_extensions = ['.pdf', '.doc', '.docx', '.txt']
        
        if not any(filename.endswith(ext) for ext in allowed_extensions):
            return {
                'valid': False,
                'error': f'Invalid file type. Allowed types: {", ".join(allowed_extensions)}'
            }
        
        # Check file size (10MB limit for guidelines)
        max_size = 10 * 1024 * 1024  # 10MB
        if uploaded_file.size > max_size:
            return {
                'valid': False,
                'error': f'File too large. Maximum size: {max_size // (1024*1024)}MB'
            }
        
        # Additional validation for clinical guidelines
        if uploaded_file.size < 100:  # Minimum 100 bytes
            return {
                'valid': False,
                'error': 'File appears to be empty or corrupted.'
            }
        
        return {'valid': True}
    
    def _parse_keywords(self, keywords_str):
        """
        Parse keywords from string to list.
        """
        if not keywords_str:
            return []
        
        # Handle both comma-separated and JSON format
        try:
            if keywords_str.startswith('['):
                import json
                return json.loads(keywords_str)
            else:
                return [kw.strip() for kw in keywords_str.split(',') if kw.strip()]
        except:
            return [keywords_str]  # Fallback to single keyword
    
    def _parse_target_roles(self, roles_str):
        """
        Parse target roles from string to list.
        """
        if not roles_str:
            return ['doctor', 'nurse']  # Default roles
        
        try:
            if roles_str.startswith('['):
                import json
                return json.loads(roles_str)
            else:
                return [role.strip() for role in roles_str.split(',') if role.strip()]
        except:
            return ['doctor', 'nurse']  # Fallback to default
    
    def _get_client_ip(self, request):
        """
        Get client IP address from request.
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
        return ip
    
    def _save_guideline_file(self, uploaded_file, guideline):
        """
        Save a clinical guideline file to the media directory.
        """
        import os
        from django.conf import settings
        from django.core.files.storage import default_storage
        
        try:
            # Create guidelines directory
            upload_dir = os.path.join('clinical_guidelines', str(guideline.organization.id))
            
            # Generate a safe filename
            file_extension = os.path.splitext(uploaded_file.name)[1].lower()
            safe_filename = f"{guideline.guideline_id}{file_extension}"
            
            # Full path for storage
            file_path = os.path.join(upload_dir, safe_filename)
            
            # Save file using Django's default storage
            saved_path = default_storage.save(file_path, uploaded_file)
            
            return saved_path
            
        except Exception as e:
            logger.error(f"File save error: {str(e)}")
            raise


class GuidelineFileUpdateView(APIView):
    """
    Update file attachment for existing clinical guideline.
    """
    
    permission_classes = [IsAuthenticated, IsHospitalAdmin]
    parser_classes = [MultiPartParser, FormParser]
    
    def post(self, request, guideline_id, *args, **kwargs):
        """
        Update file for existing guideline.
        """
        try:
            # Get the guideline
            try:
                guideline = ClinicalGuideline.objects.get(guideline_id=guideline_id)
            except ClinicalGuideline.DoesNotExist:
                return Response({
                    'error': 'Guideline not found.'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Check permissions
            if request.user.role != 'hospital_admin':
                return Response({
                    'error': 'Only hospital administrators can update guidelines.'
                }, status=status.HTTP_403_FORBIDDEN)
            
            try:
                hospital_admin = request.user.hospital_admin_profile
                if guideline.organization != hospital_admin.hospital:
                    return Response({
                        'error': 'You can only update guidelines from your organization.'
                    }, status=status.HTTP_403_FORBIDDEN)
            except:
                return Response({
                    'error': 'Invalid hospital administrator profile.'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Check if file is provided
            if 'file' not in request.FILES:
                return Response({
                    'error': 'No file provided.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            uploaded_file = request.FILES['file']
            
            # Validate file
            validation_result = self._validate_guideline_file(uploaded_file)
            if not validation_result['valid']:
                return Response({
                    'error': validation_result['error']
                }, status=status.HTTP_400_BAD_REQUEST)
            
            with transaction.atomic():
                # Remove old file if exists
                if guideline.file_path:
                    # Delete old file using Django's default storage
                    from django.core.files.storage import default_storage
                    try:
                        default_storage.delete(guideline.file_path)
                    except Exception as e:
                        logger.warning(f"Could not delete old file: {str(e)}")
                
                # Save new file
                file_path = self._save_guideline_file(uploaded_file, guideline)
                guideline.file_path = file_path
                guideline.save(update_fields=['file_path'])
                
                logger.info(f"Clinical guideline file updated: {guideline.title} by {request.user.email}")
                
                # Return updated guideline
                serializer = ClinicalGuidelineSerializer(
                    guideline, 
                    context={'request': request}
                )
                return Response({
                    'message': 'Guideline file updated successfully.',
                    'guideline': serializer.data
                }, status=status.HTTP_200_OK)
                
        except Exception as e:
            logger.error(f"Error updating guideline file: {str(e)}")
            return Response({
                'error': 'An unexpected error occurred during file update.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _validate_guideline_file(self, uploaded_file):
        """
        Validate uploaded file for clinical guidelines.
        """
        # Check file extension
        filename = uploaded_file.name.lower()
        allowed_extensions = ['.pdf', '.doc', '.docx', '.txt']
        
        if not any(filename.endswith(ext) for ext in allowed_extensions):
            return {
                'valid': False,
                'error': f'Invalid file type. Allowed types: {", ".join(allowed_extensions)}'
            }
        
        # Check file size (10MB limit for guidelines)
        max_size = 10 * 1024 * 1024  # 10MB
        if uploaded_file.size > max_size:
            return {
                'valid': False,
                'error': f'File too large. Maximum size: {max_size // (1024*1024)}MB'
            }
        
        # Additional validation for clinical guidelines
        if uploaded_file.size < 100:  # Minimum 100 bytes
            return {
                'valid': False,
                'error': 'File appears to be empty or corrupted.'
            }
        
        return {'valid': True}
    
    def _save_guideline_file(self, uploaded_file, guideline):
        """
        Save a clinical guideline file to the media directory.
        """
        import os
        from django.conf import settings
        from django.core.files.storage import default_storage
        
        try:
            # Create guidelines directory
            upload_dir = os.path.join('clinical_guidelines', str(guideline.organization.id))
            
            # Generate a safe filename
            file_extension = os.path.splitext(uploaded_file.name)[1].lower()
            safe_filename = f"{guideline.guideline_id}{file_extension}"
            
            # Full path for storage
            file_path = os.path.join(upload_dir, safe_filename)
            
            # Save file using Django's default storage
            saved_path = default_storage.save(file_path, uploaded_file)
            
            return saved_path
            
        except Exception as e:
            logger.error(f"File save error: {str(e)}")
            raise
    
    def _get_client_ip(self, request):
        """
        Get client IP address from request.
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
        return ip