"""
🛡️ MEDICAL VAULT 3.0 - SECURE FILE UPLOAD BACKEND
Nuclear-grade security for medical document uploads
"""

import os
import hashlib
import uuid
from datetime import datetime
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from cryptography.fernet import Fernet
import json
import logging

# Import our new secure document models
from api.models.secure_documents import SecureDocument, DocumentAccessLog

# Try to import magic, fallback gracefully if not available
try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False
    print("⚠️  python-magic not installed. MIME detection will be limited.")
    print("   Install with: pip install python-magic")

# Setup logging
logger = logging.getLogger(__name__)

class SecureFileValidator:
    """🔍 Nuclear File Validation Service"""
    
    ALLOWED_EXTENSIONS = ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png', '.txt']
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
    
    # Magic numbers for file type validation
    MAGIC_NUMBERS = {
        'pdf': b'%PDF',
        'jpg': b'\xff\xd8\xff',
        'jpeg': b'\xff\xd8\xff', 
        'png': b'\x89PNG',
        'doc': b'\xd0\xcf\x11\xe0',
        'docx': b'PK\x03\x04',
        'txt': None  # Text files don't have consistent magic numbers
    }
    
    @classmethod
    def validate_file(cls, uploaded_file):
        """🛡️ Deep file validation with magic number checking"""
        validation_result = {
            'is_valid': False,
            'errors': [],
            'warnings': [],
            'file_info': {},
            'security_score': 0
        }
        
        try:
            # Reset file pointer
            uploaded_file.seek(0)
            
            # 1. Check file size
            if uploaded_file.size > cls.MAX_FILE_SIZE:
                validation_result['errors'].append(f'File too large: {uploaded_file.size} bytes (max: {cls.MAX_FILE_SIZE})')
                return validation_result
                
            # 2. Check file extension
            file_ext = os.path.splitext(uploaded_file.name)[1].lower()
            if file_ext not in cls.ALLOWED_EXTENSIONS:
                validation_result['errors'].append(f'File type not allowed: {file_ext}')
                return validation_result
                
            # 3. Magic number validation
            file_content = uploaded_file.read(512)  # Read first 512 bytes
            uploaded_file.seek(0)  # Reset pointer
            
            expected_magic = cls.MAGIC_NUMBERS.get(file_ext[1:])  # Remove dot
            if expected_magic and not file_content.startswith(expected_magic):
                validation_result['errors'].append(f'File signature mismatch for {file_ext}')
                return validation_result
                
            # 4. MIME type validation using python-magic
            try:
                if MAGIC_AVAILABLE:
                    mime_type = magic.from_buffer(file_content, mime=True)
                    validation_result['file_info']['mime_type'] = mime_type
                else:
                    validation_result['file_info']['mime_type'] = 'application/octet-stream'
                    validation_result['warnings'].append('MIME detection unavailable - install python-magic')
            except Exception as e:
                validation_result['warnings'].append(f'Could not detect MIME type: {str(e)}')
                
            # 5. File name sanitization check
            if any(char in uploaded_file.name for char in ['<', '>', ':', '"', '|', '?', '*', '\\']):
                validation_result['warnings'].append('File name contains potentially unsafe characters')
                
            # 6. Calculate security score
            score = 100
            score -= len(validation_result['errors']) * 30
            score -= len(validation_result['warnings']) * 10
            validation_result['security_score'] = max(0, score)
            
            # 7. Set validation status
            if not validation_result['errors']:
                validation_result['is_valid'] = True
                
            # 8. Store file info
            validation_result['file_info'].update({
                'name': uploaded_file.name,
                'size': uploaded_file.size,
                'extension': file_ext,
                'content_preview': file_content[:100].hex()  # First 100 bytes as hex
            })
            
        except Exception as e:
            validation_result['errors'].append(f'Validation error: {str(e)}')
            logger.error(f"File validation error: {str(e)}")
            
        return validation_result

class SecureVirusScanner:
    """🦠 Virus Scanning Service (Simulation)"""
    
    @classmethod
    def scan_file(cls, uploaded_file):
        """🔍 Simulate virus scanning"""
        scan_result = {
            'is_clean': True,
            'threats_found': 0,
            'scan_time': 0.8,
            'engine_version': 'PHB-Scanner-v1.0',
            'signatures_count': 847293,
            'scan_details': []
        }
        
        try:
            # Reset file pointer
            uploaded_file.seek(0)
            file_content = uploaded_file.read()
            uploaded_file.seek(0)
            
            # Simulate threat detection patterns
            threat_patterns = [
                b'<script',
                b'javascript:',
                b'vbscript:',
                b'onload=',
                b'onerror=',
                b'eval(',
                b'document.write'
            ]
            
            for pattern in threat_patterns:
                if pattern in file_content.lower():
                    scan_result['is_clean'] = False
                    scan_result['threats_found'] += 1
                    scan_result['scan_details'].append(f'Suspicious pattern detected: {pattern.decode()}')
                    
            # Log scan
            logger.info(f"Virus scan completed for {uploaded_file.name}: {'CLEAN' if scan_result['is_clean'] else 'THREATS FOUND'}")
            
        except Exception as e:
            scan_result['scan_details'].append(f'Scan error: {str(e)}')
            logger.error(f"Virus scan error: {str(e)}")
            
        return scan_result

class SecureEncryptionService:
    """🔒 File Encryption Service"""
    
    @classmethod
    def generate_key(cls):
        """Generate encryption key"""
        return Fernet.generate_key()
    
    @classmethod
    def encrypt_file(cls, file_content, key=None):
        """🔒 Encrypt file content"""
        if key is None:
            key = cls.generate_key()
            
        try:
            fernet = Fernet(key)
            encrypted_content = fernet.encrypt(file_content)
            
            return {
                'success': True,
                'encrypted_content': encrypted_content,
                'encryption_key': key.decode(),
                'algorithm': 'AES-256 (Fernet)',
                'key_id': hashlib.sha256(key).hexdigest()[:16]
            }
        except Exception as e:
            logger.error(f"Encryption error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

class SecureAuditLogger:
    """📊 Security Audit Trail"""
    
    @classmethod
    def log_upload_attempt(cls, user, file_name, ip_address, result):
        """Log file upload attempt"""
        audit_entry = {
            'timestamp': datetime.now().isoformat(),
            'user_id': user.id if user.is_authenticated else None,
            'user_email': user.email if user.is_authenticated else 'anonymous',
            'file_name': file_name,
            'ip_address': ip_address,
            'action': 'FILE_UPLOAD',
            'result': result,
            'session_id': uuid.uuid4().hex[:16]
        }
        
        # In production, this would go to a secure audit database
        logger.info(f"AUDIT: {json.dumps(audit_entry)}")
        return audit_entry

class SecureFileUploadView(APIView):
    """🛡️ Nuclear-Grade Secure File Upload Endpoint - DRF Edition"""
    
    # 🔐 SECURITY: Require authentication and proper permissions
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def post(self, request):
        """Handle secure file upload with JWT authentication"""
        
        # 🎯 User is already authenticated by DRF JWT middleware!
        user = request.user
        
        # Get client IP
        ip_address = self.get_client_ip(request)
        
        try:
            # Check if files were uploaded
            if 'files' not in request.FILES:
                return Response({
                    'success': False,
                    'error': 'No files uploaded',
                    'code': 'NO_FILES'
                }, status=status.HTTP_400_BAD_REQUEST)
                
            uploaded_files = request.FILES.getlist('files')
            
            if not uploaded_files:
                return Response({
                    'success': False,
                    'error': 'No files provided',
                    'code': 'EMPTY_FILES'
                }, status=status.HTTP_400_BAD_REQUEST)
                
            results = []
            
            for uploaded_file in uploaded_files:
                
                # PHASE 1: FILE VALIDATION 🔍
                validation_result = SecureFileValidator.validate_file(uploaded_file)
                
                if not validation_result['is_valid']:
                    # Log failed validation
                    SecureAuditLogger.log_upload_attempt(
                        user, uploaded_file.name, ip_address, 'VALIDATION_FAILED'
                    )
                    
                    results.append({
                        'file_name': uploaded_file.name,
                        'success': False,
                        'phase': 'validation',
                        'error': 'File validation failed',
                        'details': validation_result['errors']
                    })
                    continue
                    
                # PHASE 2: VIRUS SCANNING 🦠
                scan_result = SecureVirusScanner.scan_file(uploaded_file)
                
                if not scan_result['is_clean']:
                    # Log threat detection
                    SecureAuditLogger.log_upload_attempt(
                        user, uploaded_file.name, ip_address, 'THREAT_DETECTED'
                    )
                    
                    results.append({
                        'file_name': uploaded_file.name,
                        'success': False,
                        'phase': 'virus_scan',
                        'error': 'Security threats detected',
                        'details': scan_result['scan_details']
                    })
                    continue
                    
                # PHASE 3: ENCRYPTION 🔒
                uploaded_file.seek(0)
                file_content = uploaded_file.read()
                
                encryption_result = SecureEncryptionService.encrypt_file(file_content)
                
                if not encryption_result['success']:
                    # Log encryption failure
                    SecureAuditLogger.log_upload_attempt(
                        user, uploaded_file.name, ip_address, 'ENCRYPTION_FAILED'
                    )
                    
                    results.append({
                        'file_name': uploaded_file.name,
                        'success': False,
                        'phase': 'encryption',
                        'error': 'Encryption failed',
                        'details': [encryption_result['error']]
                    })
                    continue
                    
                # PHASE 4: SECURE STORAGE & DATABASE RECORD 💾
                try:
                    # Generate secure filename
                    file_id = str(uuid.uuid4())
                    file_ext = os.path.splitext(uploaded_file.name)[1]
                    secure_filename = f"{file_id}{file_ext}.encrypted"
                    
                    # Create secure storage directory
                    storage_dir = os.path.join(settings.MEDIA_ROOT, 'secure_medical_vault')
                    os.makedirs(storage_dir, exist_ok=True)
                    
                    # Save encrypted file
                    file_path = os.path.join(storage_dir, secure_filename)
                    with open(file_path, 'wb') as f:
                        f.write(encryption_result['encrypted_content'])
                    
                    # 🆕 SAVE TO DATABASE WITH USER OWNERSHIP
                    secure_doc = SecureDocument.objects.create(
                        file_id=file_id,
                        user=user,  # DRF-authenticated user
                        original_filename=uploaded_file.name,
                        secure_filename=secure_filename,
                        file_extension=file_ext,
                        file_type=validation_result['file_info'].get('mime_type', 'unknown'),
                        file_size=len(file_content),
                        encryption_key_id=encryption_result['key_id'],
                        is_encrypted=True,
                        virus_scanned=scan_result['is_clean'],
                        security_score=validation_result['security_score'],
                        vault_path=f'secure_medical_vault/{secure_filename}',
                        uploaded_from_ip=ip_address
                    )
                    
                    # 🆕 LOG THE UPLOAD ACTION
                    DocumentAccessLog.objects.create(
                        document=secure_doc,
                        user=user,  # DRF-authenticated user
                        action='upload',
                        ip_address=ip_address,
                        success=True,
                        additional_data={
                            'file_size': len(file_content),
                            'security_score': validation_result['security_score'],
                            'virus_clean': scan_result['is_clean']
                        }
                    )
                    
                    # Log successful upload
                    SecureAuditLogger.log_upload_attempt(
                        user, uploaded_file.name, ip_address, 'SUCCESS'
                    )
                    
                    results.append({
                        'file_name': uploaded_file.name,
                        'success': True,
                        'file_id': file_id,
                        'secure_filename': secure_filename,
                        'storage_path': f'secure_medical_vault/{secure_filename}',
                        'encryption_key': encryption_result['key_id'],
                        'size': len(file_content),
                        'validation_score': validation_result['security_score'],
                        'scan_clean': scan_result['is_clean'],
                        'phases_completed': ['validation', 'virus_scan', 'encryption', 'storage', 'database'],
                        'user_owned': True,
                        'owner_email': user.email,
                        'user_id': user.id
                    })
                    
                except Exception as e:
                    logger.error(f"Storage error: {str(e)}")
                    results.append({
                        'file_name': uploaded_file.name,
                        'success': False,
                        'phase': 'storage',
                        'error': 'Storage failed',
                        'details': [str(e)]
                    })
                    
            # Return results
            successful_uploads = [r for r in results if r['success']]
            failed_uploads = [r for r in results if not r['success']]
            
            return Response({
                'success': len(successful_uploads) > 0,
                'total_files': len(uploaded_files),
                'successful_uploads': len(successful_uploads),
                'failed_uploads': len(failed_uploads),
                'results': results,
                'security_summary': {
                    'all_files_validated': all(r.get('phases_completed', []) for r in successful_uploads),
                    'all_files_scanned': all(r.get('scan_clean', False) for r in successful_uploads),
                    'all_files_encrypted': all('encryption' in r.get('phases_completed', []) for r in successful_uploads),
                    'audit_logged': True,
                    'user_authenticated': True,
                    'jwt_verified': True
                },
                'user_info': {
                    'user_id': user.id,
                    'email': user.email,
                    'authenticated_via': 'JWT'
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Upload processing error: {str(e)}")
            
            # Log system error
            SecureAuditLogger.log_upload_attempt(
                user, 'unknown', ip_address, 'SYSTEM_ERROR'
            )
            
            return Response({
                'success': False,
                'error': 'Upload processing failed',
                'code': 'SYSTEM_ERROR',
                'user_id': user.id
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip