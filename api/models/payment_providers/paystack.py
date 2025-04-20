import requests
import hmac
import hashlib
from django.conf import settings
from .base import BasePaymentProvider
from django.core.exceptions import ValidationError

class PaystackProvider(BasePaymentProvider):
    """Paystack payment provider implementation"""
    
    @property
    def provider_id(self):
        return 'paystack'
    
    @property
    def api_urls(self):
        """Get API URLs from settings"""
        return settings.PAYMENT_PROVIDERS['paystack']['urls']
    
    def verify_webhook_signature(self, signature, payload):
        """Verify Paystack webhook signature"""
        secret = self.config['webhook_secret'].encode()
        computed = hmac.new(
            secret,
            payload.encode(),
            hashlib.sha512
        ).hexdigest()
        return hmac.compare_digest(computed, signature)
    
    def initialize_payment(self):
        """Initialize Paystack payment"""
        url = self.api_urls['initialize']
        
        headers = {
            "Authorization": f"Bearer {self.config['secret_key']}",
            "Content-Type": "application/json",
            "X-Client-IP": self.get_client_ip()
        }
        
        # Add anti-fraud measures
        data = {
            "email": self.transaction.patient.email,
            "amount": int(self.transaction.amount * 100),  # Convert to kobo
            "currency": self.transaction.currency,
            "reference": self.transaction.transaction_id,
            "callback_url": self.config['callback_url'],
            "metadata": {
                "transaction_id": self.transaction.transaction_id,
                "patient_id": self.transaction.patient.id,
                "appointment_id": self.transaction.appointment.id,
                "device_fingerprint": self.transaction.device_fingerprint,
                "ip_address": self.get_client_ip()
            }
        }
        
        try:
            response = requests.post(
                url, 
                headers=headers, 
                json=data,
                timeout=30  # Add timeout
            )
            response.raise_for_status()
            
            result = response.json()
            
            # Store provider reference
            self.transaction.provider_reference = result['data']['reference']
            self.transaction.save()
            
            return result['data']['authorization_url']
            
        except requests.exceptions.RequestException as e:
            self.log_error("Payment initialization failed", e)
            raise ValidationError("Payment initialization failed. Please try again.")
    
    def verify_payment(self, reference):
        """Verify Paystack payment status"""
        url = f"{self.api_urls['verify']}/{reference}"
        
        headers = {
            "Authorization": f"Bearer {self.config['secret_key']}"
        }
        
        try:
            response = requests.get(
                url, 
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            
            # Additional verification checks
            if not self.verify_transaction_data(result['data']):
                raise ValidationError("Payment verification failed: Data mismatch")
                
            return result
            
        except requests.exceptions.RequestException as e:
            self.log_error("Payment verification failed", e)
            raise ValidationError("Payment verification failed. Please contact support.")
    
    def process_webhook(self, data, signature):
        """Process Paystack webhook with enhanced security"""
        if not self.verify_webhook_signature(signature, str(data)):
            self.log_security_event("Invalid webhook signature")
            raise ValidationError("Invalid webhook signature")
            
        try:
            if data['event'] == 'charge.success':
                # Verify transaction details before marking as complete
                if self.verify_transaction_data(data['data']):
                    self.transaction.mark_as_completed(
                        gateway_response=data,
                        user=None  # System user
                    )
                else:
                    self.log_security_event("Transaction data mismatch in webhook")
                    raise ValidationError("Transaction data mismatch")
                    
            elif data['event'] == 'charge.failed':
                self.transaction.mark_as_failed(
                    gateway_response=data,
                    user=None  # System user
                )
                
        except Exception as e:
            self.log_error("Webhook processing failed", e)
            raise
    
    def verify_transaction_data(self, data):
        """Verify transaction data matches our records"""
        return all([
            str(data['amount']) == str(int(self.transaction.amount * 100)),
            data['currency'] == self.transaction.currency,
            data['reference'] == self.transaction.provider_reference,
            data['metadata'].get('transaction_id') == self.transaction.transaction_id
        ])
    
    def log_error(self, message, exception):
        """Log payment processing errors"""
        from django.utils import timezone
        self.transaction.gateway_data = {
            **self.transaction.gateway_data,
            'errors': self.transaction.gateway_data.get('errors', []) + [{
                'message': message,
                'error': str(exception),
                'timestamp': timezone.now().isoformat()
            }]
        }
        self.transaction.save()
    
    def log_security_event(self, message):
        """Log security-related events"""
        from django.utils import timezone
        self.transaction.gateway_data = {
            **self.transaction.gateway_data,
            'security_events': self.transaction.gateway_data.get('security_events', []) + [{
                'message': message,
                'timestamp': timezone.now().isoformat(),
                'ip_address': self.get_client_ip()
            }]
        }
        self.transaction.save()
    
    def get_client_ip(self):
        """Get client IP from request"""
        from django.http import HttpRequest
        request = HttpRequest()
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')
    
    def refund_payment(self, amount=None):
        """Process refund through Paystack"""
        url = "https://api.paystack.co/refund"
        
        headers = {
            "Authorization": f"Bearer {self.config['secret_key']}",
            "Content-Type": "application/json"
        }
        
        data = {
            "transaction": self.transaction.gateway_transaction_id,
            "amount": int(amount * 100) if amount else None
        }
        
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        
        return response.json() 