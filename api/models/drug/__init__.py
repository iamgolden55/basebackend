"""
Drug classification and interaction models
"""

from .drug_classification import DrugClassification
from .drug_interaction import DrugInteraction

__all__ = [
    'DrugClassification',
    'DrugInteraction',
]
