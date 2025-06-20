# Payment System API Reference

## Authentication
All payment endpoints require JWT authentication:
```
Authorization: Bearer <jwt_token>
```

## Base URL
```
https://your-domain.com/api/payments/
```

---

## Endpoints

### 1. Initialize Payment

**Endpoint**: `POST /api/payments/initialize/`

**Description**: Creates a PaymentTransaction and initializes payment with provider.

**Request Body**:
```json
{
  "amount": 7500,
  "payment_method": "card",
  "payment_provider": "paystack",
  "appointment_id": null  // Optional - for payment-first approach
}
```

**Response** (Success):
```json
{
  "success": true,
  "payment_id": "TXN-E742A3F30B2E",
  "payment_url": "https://checkout.paystack.com/xyz",
  "provider_reference": "TXN-E742A3F30B2E",
  "amount": 7500.0,
  "currency": "NGN"
}
```

**Response** (Error):
```json
{
  "error": "amount is required"
}
```

**Status Codes**:
- `201`: Payment initialized successfully
- `400`: Invalid request data
- `403`: Rate limited or duplicate payment
- `500`: Server error

---

### 2. Verify Payment

**Endpoint**: `GET /api/payments/verify/{reference}/`

**Description**: Verifies payment status with provider and returns transaction details.

**Path Parameters**:
- `reference`: Payment reference (e.g., "TXN-E742A3F30B2E")

**Response** (Success):
```json
{
  "success": true,
  "payment_id": "TXN-E742A3F30B2E",
  "status": "completed",
  "amount": 7500.0,
  "currency": "NGN",
  "completed_at": "2025-06-17T09:58:16.055892Z",
  "verification_data": {
    "provider": "paystack",
    "gateway_response": "Approved by Financial Institution",
    "reference": "TXN-E742A3F30B2E"
  }
}
```

**Response** (Error):
```json
{
  "error": "Payment not found"
}
```

**Status Codes**:
- `200`: Verification successful
- `404`: Payment not found
- `403`: Unauthorized access
- `500`: Verification failed

---

### 3. Payment History

**Endpoint**: `GET /api/payments/history/`

**Description**: Returns user's payment history with pagination.

**Query Parameters**:
- `page`: Page number (default: 1)
- `limit`: Items per page (default: 10, max: 50)
- `status`: Filter by payment status ('completed', 'pending', 'failed')

**Response**:
```json
{
  "success": true,
  "payments": [
    {
      "transaction_id": "TXN-E742A3F30B2E",
      "amount": 7500.0,
      "currency": "NGN",
      "status": "completed",
      "payment_method": "card",
      "created_at": "2025-06-17T09:58:16.055892Z",
      "completed_at": "2025-06-17T09:59:30.123456Z",
      "appointment": {
        "id": 123,
        "appointment_id": "APT-ABC123",
        "department": "Cardiology",
        "date": "2025-06-20T14:00:00Z"
      }
    }
  ],
  "count": 1,
  "page": 1,
  "total_pages": 1
}
```

---

### 4. Payment Statistics

**Endpoint**: `GET /api/payments/stats/`

**Description**: Returns user's payment statistics and summary.

**Response**:
```json
{
  "success": true,
  "stats": {
    "total_payments": 5,
    "completed_payments": 4,
    "pending_payments": 1,
    "failed_payments": 0,
    "total_amount_paid": 30000.0,
    "recent_payments": [
      {
        "transaction_id": "TXN-E742A3F30B2E",
        "amount": 7500.0,
        "status": "completed",
        "created_at": "2025-06-17T09:58:16.055892Z"
      }
    ]
  }
}
```

---

### 5. Webhook Handler

**Endpoint**: `POST /api/payments/webhook/`

**Description**: Handles payment provider webhooks (e.g., Paystack notifications).

**Headers**:
```
X-Paystack-Signature: <webhook_signature>
Content-Type: application/json
```

**Request Body** (Paystack):
```json
{
  "event": "charge.success",
  "data": {
    "id": 302961,
    "domain": "live",
    "status": "success",
    "reference": "TXN-E742A3F30B2E",
    "amount": 750000,
    "message": null,
    "gateway_response": "Successful",
    "paid_at": "2025-06-17T09:59:30.000Z",
    "created_at": "2025-06-17T09:58:16.000Z",
    "channel": "card",
    "currency": "NGN",
    "ip_address": "41.58.47.26",
    "metadata": {
      "transaction_id": "TXN-E742A3F30B2E",
      "patient_id": 4,
      "payment_type": "pre_appointment"
    },
    "customer": {
      "id": 23070,
      "email": "user@example.com"
    }
  }
}
```

**Response**:
```json
{
  "success": true
}
```

**Status Codes**:
- `200`: Webhook processed successfully
- `400`: Invalid signature or data
- `404`: Payment not found
- `500`: Processing error

---

## Error Handling

### Standard Error Response Format
```json
{
  "error": "Error message describing what went wrong",
  "error_code": "PAYMENT_FAILED",
  "details": {
    "field": "amount",
    "message": "Amount must be greater than 0"
  }
}
```

### Common Error Codes
- `AMOUNT_REQUIRED`: Amount field is missing or invalid
- `PAYMENT_FAILED`: Payment processing failed
- `INVALID_REFERENCE`: Payment reference not found
- `UNAUTHORIZED`: Invalid or missing authentication
- `RATE_LIMITED`: Too many requests
- `DUPLICATE_PAYMENT`: Duplicate payment attempt detected
- `PROVIDER_ERROR`: Payment provider returned an error

---

## Rate Limiting

The payment API implements rate limiting to prevent abuse:

- **Payment Initialization**: 5 requests per minute per user
- **Payment Verification**: 10 requests per minute per user
- **Payment History**: 20 requests per minute per user

**Rate Limit Headers**:
```
X-RateLimit-Limit: 5
X-RateLimit-Remaining: 4
X-RateLimit-Reset: 1624785600
```

When rate limited:
```json
{
  "error": "Rate limit exceeded. Try again in 60 seconds.",
  "error_code": "RATE_LIMITED"
}
```

---

## Webhook Events

### Paystack Events
- `charge.success`: Payment completed successfully
- `charge.failed`: Payment failed
- `transfer.success`: Refund processed successfully
- `transfer.failed`: Refund failed

### Event Processing
1. Verify webhook signature
2. Find PaymentTransaction by reference
3. Update payment status
4. Log event in audit trail
5. Return success response

---

## Security Considerations

### API Security
- All endpoints require JWT authentication
- Webhook signatures must be verified
- Rate limiting prevents abuse
- Sensitive data is encrypted in database

### Data Protection
- Payment amounts are encrypted using Django Signer
- PII is handled according to GDPR guidelines
- Audit trails track all access and modifications
- Access logs include IP addresses and timestamps

### Best Practices
- Always verify payments server-side
- Never trust client-side payment confirmation alone
- Implement idempotency for critical operations
- Monitor for suspicious payment patterns
- Use HTTPS for all payment-related communications

---

## Testing

### Test Environment
Use Paystack test API keys for development:
```
PAYSTACK_SECRET_KEY=sk_test_xxxxx
PAYSTACK_PUBLIC_KEY=pk_test_xxxxx
```

### Test Data
Paystack provides test card numbers:
- **Success**: 4084084084084081 (Visa)
- **Decline**: 4084084084084002
- **Insufficient Funds**: 4084084084084010

### Webhook Testing
Use tools like ngrok to expose local webhook endpoints:
```bash
ngrok http 8000
# Use the HTTPS URL in Paystack dashboard
```

---

## Integration Examples

### JavaScript/Frontend
```javascript
// Initialize payment
const response = await fetch('/api/payments/initialize/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    amount: 7500,
    payment_method: 'card',
    payment_provider: 'paystack'
  })
});

const data = await response.json();
if (data.success) {
  // Redirect to payment URL or open Paystack modal
  window.location.href = data.payment_url;
}
```

### Python/Backend
```python
import requests

def initialize_payment(user_token, amount):
    response = requests.post(
        'https://your-domain.com/api/payments/initialize/',
        headers={
            'Authorization': f'Bearer {user_token}',
            'Content-Type': 'application/json'
        },
        json={
            'amount': amount,
            'payment_method': 'card',
            'payment_provider': 'paystack'
        }
    )
    return response.json()
```

### cURL Examples
```bash
# Initialize payment
curl -X POST https://your-domain.com/api/payments/initialize/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 7500,
    "payment_method": "card",
    "payment_provider": "paystack"
  }'

# Verify payment
curl -X GET https://your-domain.com/api/payments/verify/TXN-E742A3F30B2E/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Get payment history
curl -X GET https://your-domain.com/api/payments/history/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## Migration Guide

### From Payment-After to Payment-First

If migrating from a system where appointments are created before payment:

1. **Update frontend flow**:
   ```javascript
   // OLD: Create appointment first
   const appointment = await createAppointment(data);
   const payment = await initializePayment({appointmentId: appointment.id});
   
   // NEW: Payment-first approach
   const payment = await initializePayment(data); // No appointmentId
   // Appointment created after payment success
   ```

2. **Handle existing appointments**:
   ```python
   # Migration script for existing unpaid appointments
   unpaid_appointments = Appointment.objects.filter(
       payments__isnull=True
   )
   # Handle or clean up as needed
   ```

3. **Update webhook handling**:
   ```python
   # Handle payments without appointments
   if payment.appointment is None:
       # Payment-first flow - appointment will be created by frontend
       payment.mark_as_completed(gateway_response, user=None)
   ```

---

*API Reference last updated: June 17, 2025*
