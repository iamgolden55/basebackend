"""
Security utilities for enhanced security operations
"""
import hashlib
import secrets
import base64
import logging
from typing import Union, Tuple
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)

class SecureTokenManager:
    """Enhanced secure token management"""
    
    @staticmethod
    def generate_token(length: int = 32) -> str:
        """Generate cryptographically secure token"""
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def hash_token(token: str) -> str:
        """Hash token for secure storage using SHA-256"""
        return hashlib.sha256(token.encode()).hexdigest()
    
    @staticmethod
    def verify_token(token: str, hashed_token: str) -> bool:
        """Verify token against hashed version"""
        return hashlib.sha256(token.encode()).hexdigest() == hashed_token
    
    @staticmethod
    def generate_otp(length: int = 6) -> str:
        """Generate numeric OTP"""
        return ''.join([str(secrets.randbelow(10)) for _ in range(length)])

class EnhancedEncryption:
    """Enhanced encryption for medical data"""
    
    @staticmethod
    def derive_key(password: str, salt: bytes = None, iterations: int = 100000) -> Tuple[bytes, bytes]:
        """
        Derive encryption key using PBKDF2 with SHA-256
        Returns (key, salt) tuple
        """
        if salt is None:
            salt = secrets.token_bytes(32)  # 256-bit salt
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,  # 256-bit key
            salt=salt,
            iterations=iterations,
        )
        key = kdf.derive(password.encode())
        return key, salt
    
    @staticmethod
    def encrypt_data(data: str, password: str, salt: bytes = None) -> Tuple[str, str]:
        """
        Encrypt data using Fernet (AES 128 in CBC mode with HMAC SHA-256)
        Returns (encrypted_data_b64, salt_b64) tuple
        """
        try:
            key, salt = EnhancedEncryption.derive_key(password, salt)
            fernet_key = base64.urlsafe_b64encode(key)
            f = Fernet(fernet_key)
            
            encrypted = f.encrypt(data.encode())
            return base64.b64encode(encrypted).decode(), base64.b64encode(salt).decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise
    
    @staticmethod
    def decrypt_data(encrypted_data_b64: str, password: str, salt_b64: str) -> str:
        """
        Decrypt data using provided salt and password
        """
        try:
            salt = base64.b64decode(salt_b64.encode())
            encrypted_data = base64.b64decode(encrypted_data_b64.encode())
            
            key, _ = EnhancedEncryption.derive_key(password, salt)
            fernet_key = base64.urlsafe_b64encode(key)
            f = Fernet(fernet_key)
            
            decrypted = f.decrypt(encrypted_data)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise

class SecurityAuditor:
    """Security event auditing"""
    
    @staticmethod
    def log_security_event(event_type: str, user=None, details: dict = None, 
                          severity: str = 'INFO') -> None:
        """Log security events for audit trail"""
        event = {
            'timestamp': timezone.now().isoformat(),
            'event_type': event_type,
            'user_id': user.id if user else None,
            'user_email': user.email if user else None,
            'severity': severity,
            'details': details or {}
        }
        
        # Log to Django logger
        log_message = f"Security Event: {event_type} - User: {event.get('user_email', 'Anonymous')} - Details: {details}"
        
        if severity == 'CRITICAL':
            logger.critical(log_message)
        elif severity == 'ERROR':
            logger.error(log_message)
        elif severity == 'WARNING':
            logger.warning(log_message)
        else:
            logger.info(log_message)
    
    @staticmethod
    def log_authentication_event(user, event_type: str, success: bool, 
                                request=None, details: dict = None) -> None:
        """Log authentication events"""
        ip_address = None
        user_agent = None
        
        if request:
            ip_address = SecurityAuditor.get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        event_details = {
            'success': success,
            'ip_address': ip_address,
            'user_agent': user_agent,
            **(details or {})
        }
        
        severity = 'INFO' if success else 'WARNING'
        SecurityAuditor.log_security_event(
            event_type=f"auth_{event_type}",
            user=user,
            details=event_details,
            severity=severity
        )
    
    @staticmethod
    def get_client_ip(request) -> str:
        """Extract client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    @staticmethod
    def log_data_access(user, resource_type: str, resource_id: str, 
                       action: str, details: dict = None) -> None:
        """Log medical data access for HIPAA compliance"""
        event_details = {
            'resource_type': resource_type,
            'resource_id': resource_id,
            'action': action,
            **(details or {})
        }
        
        SecurityAuditor.log_security_event(
            event_type="data_access",
            user=user,
            details=event_details,
            severity='INFO'
        )

class SecurityValidator:
    """Security validation utilities"""
    
    @staticmethod
    def validate_password_strength(password: str) -> Tuple[bool, list]:
        """
        Validate password strength
        Returns (is_valid, error_messages)
        """
        errors = []
        
        if len(password) < 12:
            errors.append("Password must be at least 12 characters long")
        
        if not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter")
        
        if not any(c.islower() for c in password):
            errors.append("Password must contain at least one lowercase letter")
        
        if not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one number")
        
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            errors.append("Password must contain at least one special character")
        
        # Check for common passwords (basic check)
        common_passwords = ['password', '123456', 'qwerty', 'admin', 'welcome']
        if password.lower() in common_passwords:
            errors.append("Password is too common")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_file_upload(file, allowed_types: list = None, max_size_mb: int = 10) -> Tuple[bool, str]:
        """
        Validate file upload security
        Returns (is_valid, error_message)
        """
        if not file:
            return False, "No file provided"
        
        # Check file size
        max_size_bytes = max_size_mb * 1024 * 1024
        if file.size > max_size_bytes:
            return False, f"File size exceeds {max_size_mb}MB limit"
        
        # Check file type
        if allowed_types:
            file_extension = file.name.lower().split('.')[-1] if '.' in file.name else ''
            if file_extension not in allowed_types:
                return False, f"File type '{file_extension}' not allowed. Allowed types: {', '.join(allowed_types)}"
        
        # Check for malicious file names
        dangerous_chars = ['..', '/', '\\', '<', '>', ':', '"', '|', '?', '*']
        if any(char in file.name for char in dangerous_chars):
            return False, "Invalid characters in filename"
        
        return True, ""

class RateLimiter:
    """Enhanced rate limiting utilities"""
    
    @staticmethod
    def is_rate_limited(key: str, limit: int, window_seconds: int, 
                       cache_backend=None) -> Tuple[bool, int]:
        """
        Check if request is rate limited
        Returns (is_limited, remaining_attempts)
        """
        from django.core.cache import cache
        
        if cache_backend:
            cache_instance = cache_backend
        else:
            cache_instance = cache
        
        current_count = cache_instance.get(key, 0)
        
        if current_count >= limit:
            return True, 0
        
        # Increment counter
        cache_instance.set(key, current_count + 1, window_seconds)
        
        return False, limit - current_count - 1
    
    @staticmethod
    def reset_rate_limit(key: str, cache_backend=None) -> None:
        """Reset rate limit for a key"""
        from django.core.cache import cache
        
        if cache_backend:
            cache_instance = cache_backend
        else:
            cache_instance = cache
        
        cache_instance.delete(key)

# Utility functions for backward compatibility
def generate_secure_token(length: int = 32) -> str:
    """Generate secure token - backward compatible function"""
    return SecureTokenManager.generate_token(length)

def hash_token(token: str) -> str:
    """Hash token - backward compatible function"""
    return SecureTokenManager.hash_token(token)

def log_security_event(event_type: str, user=None, details: dict = None) -> None:
    """Log security event - backward compatible function"""
    SecurityAuditor.log_security_event(event_type, user, details)