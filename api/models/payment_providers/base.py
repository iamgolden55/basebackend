from abc import ABC, abstractmethod
from django.conf import settings

class BasePaymentProvider(ABC):
    """Base class for payment providers"""
    
    def __init__(self, transaction):
        self.transaction = transaction
        self.config = settings.PAYMENT_PROVIDERS.get(self.provider_id, {})
    
    @property
    @abstractmethod
    def provider_id(self):
        """Unique identifier for the provider"""
        pass
    
    @abstractmethod
    def initialize_payment(self):
        """Initialize a payment and return redirect URL or payment info"""
        pass
    
    @abstractmethod
    def verify_payment(self, reference):
        """Verify payment status"""
        pass
    
    @abstractmethod
    def process_webhook(self, data):
        """Process webhook notifications from provider"""
        pass
    
    @abstractmethod
    def refund_payment(self, amount=None):
        """Process refund"""
        pass 