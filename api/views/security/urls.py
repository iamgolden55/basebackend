"""
🛡️ MEDICAL VAULT 3.0 - Security URLs
Complete File Management Endpoints
"""

from django.urls import path
from .secure_upload import SecureFileUploadView
from .secure_file_manager import (
    SecureFileListView,
    SecureFileDetailView, 
    SecureFilePreviewView,
    SecureFileDeleteView,
    vault_statistics
)

urlpatterns = [
    # 🛡️ Secure file upload endpoint
    path('upload/', SecureFileUploadView.as_view(), name='secure-file-upload'),
    
    # 📂 File management endpoints
    path('files/', SecureFileListView.as_view(), name='secure-file-list'),
    path('files/<str:file_id>/', SecureFileDetailView.as_view(), name='secure-file-detail'),
    path('files/<str:file_id>/preview/', SecureFilePreviewView.as_view(), name='secure-file-preview'),
    path('files/<str:file_id>/delete/', SecureFileDeleteView.as_view(), name='secure-file-delete'),
    
    # 📊 Vault statistics
    path('vault/stats/', vault_statistics, name='vault-statistics'),
]