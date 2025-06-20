import requests
import hmac
import hashlib
from django.conf import settings
from django.utils import timezone
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
        
        # 🔍 DEBUG: Check what we're getting from config
        print(f"🔧 CONFIG DEBUG: Full config = {self.config}")
        print(f"🔧 CONFIG DEBUG: Secret key = {self.config.get('secret_key', 'NOT_FOUND')}")
        print(f"🔧 CONFIG DEBUG: SETTINGS check = {settings.PAYMENT_PROVIDERS}")
        
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
                "ip_address": self.get_client_ip()
            }
        }
        
        # 🎯 ONLY ADD APPOINTMENT DATA IF APPOINTMENT EXISTS (Payment-First Approach!)
        if self.transaction.appointment:
            data["metadata"]["appointment_id"] = self.transaction.appointment.id
        else:
            # Payment-first approach - no appointment yet
            data["metadata"]["payment_type"] = "pre_appointment"
        
        try:
            # 🔍 Enhanced debugging for payment initialization
            print(f"🚀 PAYSTACK DEBUG: URL = {url}")
            print(f"🚀 PAYSTACK DEBUG: Headers = {headers}")
            print(f"🚀 PAYSTACK DEBUG: Data = {data}")
            
            response = requests.post(
                url, 
                headers=headers, 
                json=data,
                timeout=30  # Add timeout
            )
            
            print(f"🚀 PAYSTACK DEBUG: Response Status = {response.status_code}")
            print(f"🚀 PAYSTACK DEBUG: Response Text = {response.text}")
            
            response.raise_for_status()
            
            result = response.json()
            print(f"✅ PAYSTACK DEBUG: Success Result = {result}")
            
            # Store provider reference
            self.transaction.provider_reference = result['data']['reference']
            self.transaction.save()
            
            return result['data']['authorization_url']
            
        except requests.exceptions.RequestException as e:
            print(f"🚨 PAYSTACK ERROR: Request Exception = {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"🚨 PAYSTACK ERROR: Response Status = {e.response.status_code}")
                print(f"🚨 PAYSTACK ERROR: Response Text = {e.response.text}")
            self.log_error("Payment initialization failed", e)
            raise ValidationError("Payment initialization failed. Please try again.")
    
    def verify_payment(self, reference):
        """Verify Paystack payment status"""
        url = f"{self.api_urls['verify']}/{reference}"
        
        headers = {
            "Authorization": f"Bearer {self.config['secret_key']}"
        }
        
        try:
            print(f"🔍 PAYSTACK VERIFY: Starting verification for reference {reference}")
            print(f"🔍 PAYSTACK VERIFY: Current payment status: {self.transaction.payment_status}")
            
            response = requests.get(
                url, 
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            print(f"🔍 PAYSTACK VERIFY: Response received: {result}")
            
            # Additional verification checks
            if not self.verify_transaction_data(result['data']):
                print(f"❌ PAYSTACK VERIFY: Data verification failed")
                raise ValidationError("Payment verification failed: Data mismatch")
            
            # 🚀 UPDATE PAYMENT STATUS BASED ON PAYSTACK RESPONSE
            paystack_status = result['data']['status']
            print(f"🔍 PAYSTACK VERIFY: Paystack status = {paystack_status}")
            print(f"🔍 PAYSTACK VERIFY: Current payment status = {self.transaction.payment_status}")
            print(f"🔍 PAYSTACK VERIFY: Has appointment = {bool(self.transaction.appointment)}")
            print(f"🔍 PAYSTACK VERIFY: Has description = {bool(self.transaction.description)}")
            
            if paystack_status == 'success':
                # Mark payment as completed if Paystack says it's successful
                if self.transaction.payment_status != 'completed':
                    print(f"🚀 PAYSTACK VERIFY: Triggering mark_as_completed for payment {reference}")
                    try:
                        # Use mark_as_completed to trigger appointment creation for payment-first approach
                        self.transaction.mark_as_completed(gateway_response=result['data'])
                        print(f"✅ PAYSTACK VERIFY: Payment {reference} marked as completed and appointment creation triggered")
                        
                        # Refresh from database to get updated state
                        self.transaction.refresh_from_db()
                        print(f"✅ PAYSTACK VERIFY: After refresh - has appointment: {bool(self.transaction.appointment)}")
                        
                    except Exception as completion_error:
                        print(f"❌ PAYSTACK VERIFY: Error in mark_as_completed for {reference}: {completion_error}")
                        import traceback
                        print(f"❌ PAYSTACK VERIFY: Completion traceback: {traceback.format_exc()}")
                        # Still mark as completed manually to prevent payment loss
                        self.transaction.payment_status = 'completed'
                        self.transaction.completed_at = timezone.now()
                        self.transaction.gateway_data = result['data']
                        self.transaction.save()
                        print(f"⚠️ PAYSTACK VERIFY: Payment {reference} marked as completed manually due to error")
                        
                else:
                    print(f"ℹ️ PAYSTACK VERIFY: Payment {reference} already marked as completed")
                    # Double-check appointment creation for already completed payments
                    if not self.transaction.appointment and self.transaction.description:
                        print(f"🔄 PAYSTACK VERIFY: Re-attempting appointment creation for completed payment {reference}")
                        try:
                            # Re-trigger appointment creation
                            self.transaction.mark_as_completed(gateway_response=result['data'])
                        except Exception as retry_error:
                            print(f"❌ PAYSTACK VERIFY: Retry appointment creation failed: {retry_error}")
                            
            elif paystack_status == 'failed':
                # Mark payment as failed
                if self.transaction.payment_status != 'failed':
                    self.transaction.payment_status = 'failed'
                    self.transaction.gateway_data = result['data']
                    self.transaction.save()
                    print(f"❌ PAYSTACK VERIFY: Payment {reference} marked as failed")
                else:
                    print(f"ℹ️ PAYSTACK VERIFY: Payment {reference} already marked as failed")
            else:
                print(f"⚠️ PAYSTACK VERIFY: Unknown status '{paystack_status}' for payment {reference}")
            
            print(f"🔍 PAYSTACK VERIFY: Final payment status: {self.transaction.payment_status}")
            print(f"🔍 PAYSTACK VERIFY: Final appointment status: {'linked' if self.transaction.appointment else 'none'}")
            
            return result
            
        except requests.exceptions.RequestException as e:
            print(f"🚨 PAYSTACK VERIFY ERROR: {str(e)}")
            self.log_error("Payment verification failed", e)
            raise ValidationError("Payment verification failed. Please contact support.")
    
    def process_webhook(self, data, signature):
        """Process Paystack webhook with enhanced security"""
        if not self.verify_webhook_signature(signature, str(data)):
            self.log_security_event("Invalid webhook signature")
            raise ValidationError("Invalid webhook signature")
            
        try:
            print(f"🔔 WEBHOOK: Processing event '{data['event']}' for transaction {self.transaction.transaction_id}")
            print(f"🔔 WEBHOOK: Current payment status: {self.transaction.payment_status}")
            print(f"🔔 WEBHOOK: Has appointment: {bool(self.transaction.appointment)}")
            print(f"🔔 WEBHOOK: Has description: {bool(self.transaction.description)}")
            
            if data['event'] == 'charge.success':
                # Verify transaction details before marking as complete
                if self.verify_transaction_data(data['data']):
                    print(f"🔔 WEBHOOK: Transaction data verified, triggering mark_as_completed")
                    try:
                        # Use mark_as_completed to trigger appointment creation for payment-first approach
                        self.transaction.mark_as_completed(
                            gateway_response=data,
                            user=None  # System user
                        )
                        print(f"✅ WEBHOOK: Payment {self.transaction.transaction_id} completed and appointment creation triggered")
                        
                        # Refresh and log final state
                        self.transaction.refresh_from_db()
                        print(f"✅ WEBHOOK: Final state - status: {self.transaction.payment_status}, appointment: {'linked' if self.transaction.appointment else 'none'}")
                        
                    except Exception as webhook_completion_error:
                        print(f"❌ WEBHOOK: Error in mark_as_completed: {webhook_completion_error}")
                        import traceback
                        print(f"❌ WEBHOOK: Completion traceback: {traceback.format_exc()}")
                        raise
                        
                else:
                    self.log_security_event("Transaction data mismatch in webhook")
                    raise ValidationError("Transaction data mismatch")
                    
            elif data['event'] == 'charge.failed':
                print(f"❌ WEBHOOK: Processing charge.failed event")
                self.transaction.mark_as_failed(
                    gateway_response=data,
                    user=None  # System user
                )
            else:
                print(f"ℹ️ WEBHOOK: Unhandled event type: {data['event']}")
                
        except Exception as e:
            self.log_error("Webhook processing failed", e)
            raise
    
    def verify_transaction_data(self, data):
        """Verify transaction data matches our records"""
        basic_checks = [
            str(data['amount']) == str(int(self.transaction.amount * 100)),
            data['currency'] == self.transaction.currency,
            data['reference'] == self.transaction.provider_reference,
            data['metadata'].get('transaction_id') == self.transaction.transaction_id
        ]
        
        # 🎯 ONLY CHECK APPOINTMENT_ID IF APPOINTMENT EXISTS (Payment-First Approach!)
        if self.transaction.appointment:
            basic_checks.append(
                data['metadata'].get('appointment_id') == self.transaction.appointment.id
            )
        
        return all(basic_checks)
    
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
        # For now, return a default IP since we don't have access to the request object
        # TODO: Pass request object to provider for accurate IP detection
        return "127.0.0.1"
    
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