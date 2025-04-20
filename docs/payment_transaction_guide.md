# Payment Transaction Guide 🏦

## Overview
The PaymentTransaction model manages all payment-related operations for appointments in the PHB Management system. It handles various payment methods, including insurance coverage, and provides comprehensive tracking of transaction statuses.

## Key Features 🌟

### 1. Payment Methods
- Credit/Debit Card
- Bank Transfer
- Cash
- Insurance
- Mobile Money
- E-Wallet

### 2. Transaction States
```python
PAYMENT_STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('processing', 'Processing'),
    ('completed', 'Completed'),
    ('failed', 'Failed'),
    ('refunded', 'Refunded'),
    ('cancelled', 'Cancelled'),
]
```

### 3. Insurance Integration
- Provider tracking
- Policy number verification
- Coverage amount calculation
- Automatic validation

## Usage Examples 💡

### 1. Creating a Standard Payment

```python
# Create a new payment transaction
transaction = PaymentTransaction.objects.create(
    appointment=appointment,
    patient=patient,
    hospital=hospital,
    amount=5000.00,
    currency='NGN',
    payment_method='card'
)

# After successful payment processing
transaction.mark_as_completed(gateway_response={
    'status': 'success',
    'transaction_ref': 'GAT123456'
})
```

### 2. Insurance Payment

```python
# Create insurance-based payment
insurance_payment = PaymentTransaction.objects.create(
    appointment=appointment,
    patient=patient,
    hospital=hospital,
    amount=10000.00,
    payment_method='insurance',
    insurance_provider='NHIA',
    insurance_policy_number='POL123456',
    insurance_coverage_amount=7000.00  # 70% coverage
)
```

### 3. Processing Refunds

```python
# Process full refund
transaction.process_refund(
    reason="Appointment cancelled by doctor"
)

# Process partial refund
transaction.process_refund(
    amount=2500.00,
    reason="Service partially delivered"
)
```

## Best Practices 🎯

### 1. Transaction Creation
- Always generate unique transaction IDs
- Validate insurance details before processing
- Include detailed description for tracking
- Set appropriate payment method

### 2. Payment Processing
- Handle gateway responses properly
- Store complete gateway response data
- Update status promptly
- Track completion time

### 3. Insurance Handling
- Verify policy before processing
- Validate coverage amounts
- Store provider details
- Track policy numbers

### 4. Refund Management
- Document refund reasons
- Validate refund amounts
- Update status immediately
- Maintain audit trail

## Validation Rules ✅

1. Insurance Payments
   - Provider and policy number required
   - Coverage cannot exceed total amount
   - Valid insurance details required

2. Refunds
   - Only completed payments can be refunded
   - Refund amount cannot exceed payment amount
   - Reason must be provided

3. Status Transitions
   - Proper status flow must be followed
   - Timestamps must be updated
   - Gateway responses must be stored

## Properties and Methods 🛠️

### Properties
- `is_completed`: Check if payment is completed
- `is_refundable`: Check if payment can be refunded
- `payment_duration`: Calculate processing duration

### Methods
- `mark_as_completed()`: Complete payment
- `mark_as_failed()`: Mark payment as failed
- `process_refund()`: Handle refunds
- `get_payment_summary()`: Get transaction summary

## Error Handling 🚨

The model includes built-in validations for:
- Invalid insurance details
- Excessive coverage amounts
- Invalid refund amounts
- Improper status transitions

Example error handling:
```python
try:
    transaction.process_refund(amount=15000.00)  # Amount greater than payment
except ValidationError as e:
    handle_error("Refund amount exceeds payment amount")
```

## Integration Points 🔄

### 1. Appointment System
- Links to appointment records
- Tracks appointment-specific payments
- Handles appointment-related refunds

### 2. Insurance System
- Verifies insurance coverage
- Calculates covered amounts
- Tracks policy details

### 3. Payment Gateways
- Processes card payments
- Handles bank transfers
- Manages mobile money

## Monitoring and Reporting 📊

Key metrics to track:
1. Payment success rates
2. Processing durations
3. Refund frequencies
4. Insurance coverage rates

## Security Considerations 🔒

1. Data Protection
   - Secure storage of payment details
   - Encryption of sensitive data
   - Access control implementation

2. Audit Trail
   - Transaction logging
   - Status change tracking
   - User action recording

3. Enhanced Security Features 🛡️

### Rate Limiting
```python
# Configuration in settings.py
PAYMENT_SECURITY = {
    'rate_limit': {
        'window': 3600,  # 1 hour window
        'max_requests': 100  # Max requests per window
    }
}
```

### Transaction Limits
- Maximum amount per transaction: 1,000,000
- Daily transaction limit: 5,000,000
- Maximum payment attempts: 3
- Lockout duration: 30 minutes

### Geographic Restrictions
- Allowed countries: Nigeria (NG), Ghana (GH), South Africa (ZA)
- IP-based blocking
- Country-based restrictions

### Fraud Prevention
```python
# Example of checking transaction limits
if transaction.amount > settings.PAYMENT_SECURITY['amount_limit']:
    raise ValidationError("Amount exceeds transaction limit")

# Example of checking daily limits
if user_daily_total > settings.PAYMENT_SECURITY['daily_limit']:
    raise ValidationError("Daily transaction limit exceeded")
```

### Security Monitoring
- Real-time suspicious activity detection
- Automated security alerts
- IP-based tracking and blocking
- Transaction pattern analysis

## Payment Provider Integration 💳

### Paystack Integration
```python
# Configuration in settings.py
PAYMENT_PROVIDERS = {
    'paystack': {
        'secret_key': os.environ.get('PAYSTACK_SECRET_KEY'),
        'public_key': os.environ.get('PAYSTACK_PUBLIC_KEY'),
        'webhook_secret': os.environ.get('PAYSTACK_WEBHOOK_SECRET'),
        'callback_url': os.environ.get('PAYSTACK_CALLBACK_URL'),
    }
}

# Usage in code
transaction = PaymentTransaction.objects.create(
    payment_provider='paystack',
    amount=5000.00,
    currency='NGN'
)
payment_url = transaction.initialize_payment()
```

### Available Endpoints
- Initialize Transaction: `/transaction/initialize`
- Verify Transaction: `/transaction/verify`
- Process Refund: `/refund`

## Security Best Practices 🔐

1. Environment Variables
   - Store sensitive keys in `.env` file
   - Never commit secrets to version control
   - Use separate keys for development/production

2. Rate Limiting Implementation
   - Redis-based rate limiting
   - IP-based request tracking
   - Automatic blocking of excessive requests

3. Transaction Monitoring
   - Real-time transaction tracking
   - Suspicious activity alerts
   - Daily limit monitoring
   - Geographic restriction enforcement

4. Error Handling and Logging
```python
try:
    transaction.process_payment()
except SecurityException as e:
    # Log security event
    security_logger.error(f"Security violation: {e}")
    # Alert security team
    notify_security_team(e)
    raise ValidationError("Payment processing failed")
```

## Monitoring and Alerts 📊

1. Security Events
   - Failed payment attempts
   - Suspicious IP activities
   - Geographic restriction violations
   - Rate limit breaches

2. Transaction Monitoring
   - Daily transaction volumes
   - Amount limit violations
   - Payment pattern analysis
   - Provider performance metrics

3. Alert Configuration
```python
# Example security alert
SECURITY_TEAM_EMAIL = os.environ.get('SECURITY_TEAM_EMAIL')
send_mail(
    'Security Alert: Suspicious Activity',
    f'Multiple failed payment attempts from IP: {ip_address}',
    settings.DEFAULT_FROM_EMAIL,
    [settings.SECURITY_TEAM_EMAIL]
)
```

## Cache Configuration ⚡

Redis cache setup for efficient rate limiting:
```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
```

## Deployment Checklist ✅

1. Security Setup
   - Configure Redis for rate limiting
   - Set up security team email
   - Configure payment provider keys
   - Set appropriate transaction limits

2. Environment Configuration
   - Set up all required environment variables
   - Configure allowed countries
   - Set up IP blocking rules
   - Configure rate limiting parameters

3. Monitoring Setup
   - Configure security alerts
   - Set up transaction monitoring
   - Enable audit logging
   - Configure error tracking 