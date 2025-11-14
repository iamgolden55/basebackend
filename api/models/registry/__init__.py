"""
Registry Models Package

Professional registration and licensing models (PHB National Registry).
Similar to NHS GMC registration system.
"""

from .professional_application import ProfessionalApplication
from .application_document import ApplicationDocument, get_required_documents_for_profession
from .professional_registry import PHBProfessionalRegistry

__all__ = [
    'ProfessionalApplication',
    'ApplicationDocument',
    'get_required_documents_for_profession',
    'PHBProfessionalRegistry',
]
