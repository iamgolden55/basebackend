# Payment System Database Schema

## Overview
This document describes the database schema for the PHB Hospital System payment integration, focusing on the PaymentTransaction model and related entities.

---

## PaymentTransaction Model

### Table: `api_paymenttransaction`

The central entity for tracking all payment transactions in the system.

```sql
CREATE TABLE api_paymenttransaction (
    id SERIAL PRIMARY KEY,
    
    -- Identification
    transaction_id VARCHAR(100) UNIQUE NOT NULL,
    
    -- Relationships (nullable for payment-first approach)
    appointment_id INTEGER NULL REFERENCES api_appointment(id),
    patient_id INTEGER NOT NULL REFERENCES api_customuser(id),
    hospital_id INTEGER NULL REFERENCES api_hospital(id),
    
    -- Payment Details
    _encrypted_amount BYTEA NULL,  -- Encrypted sensitive data
    amount_display DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'NGN',
    payment_method VARCHAR(50) NOT NULL,
    payment_status VARCHAR(20) DEFAULT 'pending',
    
    -- Provider Information
    payment_provider VARCHAR(50) NULL,
    provider_reference VARCHAR(100) NULL,
    
    -- Insurance (for future use)
    _encrypted_insurance_data BYTEA NULL,
    insurance_provider VARCHAR(100) NULL,
    insurance_policy_number VARCHAR(100) NULL,
    insurance_coverage_amount DECIMAL(10,2) DEFAULT 0.00,
    
    -- Gateway Data
    _encrypted_gateway_data BYTEA NULL,
    payment_gateway VARCHAR(50) NULL,
    gateway_transaction_id VARCHAR(100) NULL,
    
    -- Audit Trail
    created_by_id INTEGER NOT NULL REFERENCES api_customuser(id),
    last_modified_by_id INTEGER NOT NULL REFERENCES api_customuser(id),
    status_change_history JSONB DEFAULT '[]',
    access_log JSONB DEFAULT '[]',
    
    -- Gift Payment Support
    gift_sender_id INTEGER NULL REFERENCES api_customuser(id),
    
    -- Additional Information
    description TEXT,
    notes TEXT,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
    completed_at TIMESTAMP WITH TIME ZONE NULL
);
```

### Indexes
```sql
-- Performance indexes
CREATE INDEX idx_paymenttransaction_transaction_id ON api_paymenttransaction(transaction_id);
CREATE INDEX idx_paymenttransaction_status ON api_paymenttransaction(payment_status);
CREATE INDEX idx_paymenttransaction_created_at ON api_paymenttransaction(created_at);
CREATE INDEX idx_paymenttransaction_patient ON api_paymenttransaction(patient_id);
CREATE INDEX idx_paymenttransaction_provider_ref ON api_paymenttransaction(provider_reference);
CREATE INDEX idx_paymenttransaction_appointment ON api_paymenttransaction(appointment_id);
CREATE INDEX idx_paymenttransaction_hospital ON api_paymenttransaction(hospital_id);

-- Composite indexes for common queries
CREATE INDEX idx_paymenttransaction_patient_status ON api_paymenttransaction(patient_id, payment_status);
CREATE INDEX idx_paymenttransaction_date_status ON api_paymenttransaction(created_at, payment_status);
```

### Constraints
```sql
-- Check constraints
ALTER TABLE api_paymenttransaction 
ADD CONSTRAINT chk_amount_positive 
CHECK (amount_display >= 0);

ALTER TABLE api_paymenttransaction 
ADD CONSTRAINT chk_insurance_coverage_positive 
CHECK (insurance_coverage_amount >= 0);

-- Unique constraints
ALTER TABLE api_paymenttransaction 
ADD CONSTRAINT unique_transaction_id 
UNIQUE (transaction_id);

-- Foreign key constraints with proper cascading
ALTER TABLE api_paymenttransaction 
ADD CONSTRAINT fk_appointment 
FOREIGN KEY (appointment_id) 
REFERENCES api_appointment(id) 
ON DELETE PROTECT;

ALTER TABLE api_paymenttransaction 
ADD CONSTRAINT fk_patient 
FOREIGN KEY (patient_id) 
REFERENCES api_customuser(id) 
ON DELETE PROTECT;

ALTER TABLE api_paymenttransaction 
ADD CONSTRAINT fk_hospital 
FOREIGN KEY (hospital_id) 
REFERENCES api_hospital(id) 
ON DELETE PROTECT;
```

---

## Field Descriptions

### Core Fields

| Field | Type | Description | Nullable |
|-------|------|-------------|----------|
| `id` | SERIAL | Primary key | No |
| `transaction_id` | VARCHAR(100) | Unique transaction identifier (e.g., "TXN-ABC123") | No |
| `appointment_id` | INTEGER | Foreign key to appointment (null for payment-first) | Yes |
| `patient_id` | INTEGER | Foreign key to patient/user | No |
| `hospital_id` | INTEGER | Foreign key to hospital (null for payment-first) | Yes |

### Payment Details

| Field | Type | Description | Nullable |
|-------|------|-------------|----------|
| `_encrypted_amount` | BYTEA | Encrypted actual amount using Django Signer | Yes |
| `amount_display` | DECIMAL(10,2) | Display amount (not encrypted) | No |
| `currency` | VARCHAR(3) | Currency code (NGN, USD, etc.) | No |
| `payment_method` | VARCHAR(50) | Payment method (card, bank_transfer, etc.) | No |
| `payment_status` | VARCHAR(20) | Current payment status | No |
| `payment_provider` | VARCHAR(50) | Provider name (paystack, flutterwave, etc.) | Yes |
| `provider_reference` | VARCHAR(100) | Provider's transaction reference | Yes |

### Encrypted Fields

| Field | Type | Description | Purpose |
|-------|------|-------------|---------|
| `_encrypted_amount` | BYTEA | Actual payment amount | Security |
| `_encrypted_insurance_data` | BYTEA | Insurance details JSON | Privacy |
| `_encrypted_gateway_data` | BYTEA | Gateway response data | Security |

### Audit Fields

| Field | Type | Description | Usage |
|-------|------|-------------|-------|
| `created_by_id` | INTEGER | User who created the transaction | Audit |
| `last_modified_by_id` | INTEGER | User who last modified | Audit |
| `status_change_history` | JSONB | Array of status changes | Tracking |
| `access_log` | JSONB | Array of access events | Security |

---

## Status Values

### Payment Status Enum
```python
PAYMENT_STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('processing', 'Processing'),
    ('completed', 'Completed'),
    ('failed', 'Failed'),
    ('refunded', 'Refunded')
]
```

### Payment Method Enum
```python
PAYMENT_METHOD_CHOICES = [
    ('card', 'Credit/Debit Card'),
    ('bank_transfer', 'Bank Transfer'),
    ('cash', 'Cash'),
    ('insurance', 'Insurance'),
    ('mobile_money', 'Mobile Money'),
    ('wallet', 'E-Wallet'),
]
```

### Currency Enum
```python
CURRENCY_CHOICES = [
    ('USD', 'US Dollar'),
    ('EUR', 'Euro'),
    ('GBP', 'British Pound'),
    ('NGN', 'Nigerian Naira'),
]
```

### Payment Provider Enum
```python
PAYMENT_PROVIDER_CHOICES = [
    ('paystack', 'Paystack'),
    ('moniepoint', 'Moniepoint'),
    ('flutterwave', 'Flutterwave'),
    ('stripe', 'Stripe'),
]
```

---

## JSON Field Structures

### status_change_history
```json
[
  {
    "from_status": "pending",
    "to_status": "completed",
    "changed_by": 4,
    "timestamp": "2025-06-17T09:59:30.123456Z",
    "notes": "Payment confirmed by Paystack webhook"
  }
]
```

### access_log
```json
[
  {
    "user": 4,
    "timestamp": "2025-06-17T09:58:16.055892Z",
    "action": "viewed",
    "ip_address": "192.168.1.100",
    "user_agent": "Mozilla/5.0..."
  }
]
```

### _encrypted_insurance_data (decrypted)
```json
{
  "provider": "NHIS",
  "policy_number": "POL123456",
  "coverage_type": "basic",
  "expiry_date": "2025-12-31",
  "member_id": "MEM789012"
}
```

### _encrypted_gateway_data (decrypted)
```json
{
  "paystack_response": {
    "status": "success",
    "reference": "TXN-ABC123",
    "amount": 750000,
    "gateway_response": "Approved by Financial Institution",
    "paid_at": "2025-06-17T09:59:30.000Z",
    "channel": "card",
    "card": {
      "type": "visa",
      "last4": "1234",
      "bank": "Test Bank"
    }
  },
  "security_events": [
    {
      "event": "signature_verified",
      "timestamp": "2025-06-17T09:59:30.000Z",
      "ip_address": "192.168.1.100"
    }
  ]
}
```

---

## Related Tables

### Appointment Relationship
```sql
-- One-to-many: Appointment can have multiple payments (initial + refunds)
SELECT a.appointment_id, p.transaction_id, p.payment_status
FROM api_appointment a
LEFT JOIN api_paymenttransaction p ON a.id = p.appointment_id
WHERE a.patient_id = 4;
```

### Hospital Relationship
```sql
-- Hospital payment analytics
SELECT h.name, 
       COUNT(p.id) as total_payments,
       SUM(p.amount_display) as total_revenue
FROM api_hospital h
LEFT JOIN api_paymenttransaction p ON h.id = p.hospital_id
WHERE p.payment_status = 'completed'
GROUP BY h.id, h.name;
```

### User/Patient Relationship
```sql
-- User payment history
SELECT u.email,
       p.transaction_id,
       p.amount_display,
       p.payment_status,
       p.created_at
FROM api_customuser u
JOIN api_paymenttransaction p ON u.id = p.patient_id
WHERE u.id = 4
ORDER BY p.created_at DESC;
```

---

## Migration Scripts

### Initial Migration (0022)
```python
# api/migrations/0022_alter_paymenttransaction_appointment_and_more.py
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [
        ('api', '0021_previous_migration'),
    ]

    operations = [
        migrations.AlterField(
            model_name='paymenttransaction',
            name='appointment',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='payments', to='api.appointment',
                help_text='Associated appointment (optional for payment-first flow)'
            ),
        ),
        migrations.AlterField(
            model_name='paymenttransaction',
            name='hospital',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='payments', to='api.hospital',
                help_text='Associated hospital (optional for payment-first flow)'
            ),
        ),
    ]
```

### Data Migration Example
```python
# Migrate existing unpaid appointments
from django.db import migrations

def migrate_unpaid_appointments(apps, schema_editor):
    Appointment = apps.get_model('api', 'Appointment')
    PaymentTransaction = apps.get_model('api', 'PaymentTransaction')
    
    # Find appointments without payments
    unpaid_appointments = Appointment.objects.filter(
        payments__isnull=True
    )
    
    for appointment in unpaid_appointments:
        # Create pending payment transaction
        PaymentTransaction.objects.create(
            appointment=appointment,
            patient=appointment.patient,
            hospital=appointment.hospital,
            amount_display=2000.0,  # Default amount
            currency='NGN',
            payment_method='card',
            payment_status='pending',
            payment_provider='paystack',
            created_by=appointment.patient,
            last_modified_by=appointment.patient
        )

class Migration(migrations.Migration):
    dependencies = [
        ('api', '0022_alter_paymenttransaction_appointment_and_more'),
    ]

    operations = [
        migrations.RunPython(migrate_unpaid_appointments),
    ]
```

---

## Query Examples

### Common Queries

#### 1. Get User's Payment History
```sql
SELECT 
    pt.transaction_id,
    pt.amount_display,
    pt.currency,
    pt.payment_status,
    pt.payment_method,
    pt.created_at,
    pt.completed_at,
    a.appointment_id,
    h.name as hospital_name
FROM api_paymenttransaction pt
LEFT JOIN api_appointment a ON pt.appointment_id = a.id
LEFT JOIN api_hospital h ON pt.hospital_id = h.id
WHERE pt.patient_id = 4
ORDER BY pt.created_at DESC
LIMIT 10;
```

#### 2. Hospital Revenue Analytics
```sql
SELECT 
    h.name,
    DATE_TRUNC('month', pt.completed_at) as month,
    COUNT(pt.id) as transaction_count,
    SUM(pt.amount_display) as total_revenue,
    AVG(pt.amount_display) as avg_transaction
FROM api_hospital h
JOIN api_paymenttransaction pt ON h.id = pt.hospital_id
WHERE pt.payment_status = 'completed'
  AND pt.completed_at >= DATE_TRUNC('year', CURRENT_DATE)
GROUP BY h.id, h.name, DATE_TRUNC('month', pt.completed_at)
ORDER BY month DESC, total_revenue DESC;
```

#### 3. Payment Status Summary
```sql
SELECT 
    payment_status,
    COUNT(*) as count,
    SUM(amount_display) as total_amount,
    AVG(amount_display) as avg_amount
FROM api_paymenttransaction
WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY payment_status
ORDER BY count DESC;
```

#### 4. Failed Payment Analysis
```sql
SELECT 
    pt.transaction_id,
    pt.payment_provider,
    pt.amount_display,
    pt.created_at,
    pt._encrypted_gateway_data,
    u.email as patient_email
FROM api_paymenttransaction pt
JOIN api_customuser u ON pt.patient_id = u.id
WHERE pt.payment_status = 'failed'
  AND pt.created_at >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY pt.created_at DESC;
```

#### 5. Pending Payments (Payment-First)
```sql
-- Payments without appointments (payment-first approach)
SELECT 
    pt.transaction_id,
    pt.amount_display,
    pt.created_at,
    u.email as patient_email,
    pt.payment_status
FROM api_paymenttransaction pt
JOIN api_customuser u ON pt.patient_id = u.id
WHERE pt.appointment_id IS NULL
  AND pt.payment_status = 'pending'
  AND pt.created_at >= CURRENT_DATE - INTERVAL '1 hour'
ORDER BY pt.created_at DESC;
```

---

## Performance Considerations

### Indexing Strategy
1. **Primary lookups**: transaction_id, patient_id
2. **Status filtering**: payment_status + created_at
3. **Relationship queries**: appointment_id, hospital_id
4. **Composite indexes**: patient_id + payment_status for user dashboards

### Query Optimization
```sql
-- Use EXPLAIN ANALYZE to check query performance
EXPLAIN ANALYZE
SELECT pt.*, a.appointment_id 
FROM api_paymenttransaction pt
LEFT JOIN api_appointment a ON pt.appointment_id = a.id
WHERE pt.patient_id = 4 
  AND pt.payment_status = 'completed'
ORDER BY pt.created_at DESC
LIMIT 10;
```

### Archiving Strategy
```sql
-- Archive old completed payments (after 2 years)
CREATE TABLE api_paymenttransaction_archive AS
SELECT * FROM api_paymenttransaction
WHERE payment_status = 'completed'
  AND completed_at < CURRENT_DATE - INTERVAL '2 years';

-- Delete archived records from main table
DELETE FROM api_paymenttransaction
WHERE payment_status = 'completed'
  AND completed_at < CURRENT_DATE - INTERVAL '2 years';
```

---

## Backup and Recovery

### Regular Backups
```bash
# Daily backup of payment transactions
pg_dump -h localhost -U postgres -d phb_db \
  -t api_paymenttransaction \
  --data-only \
  > payments_backup_$(date +%Y%m%d).sql
```

### Point-in-Time Recovery
```sql
-- Restore payment transaction to specific timestamp
BEGIN;
DELETE FROM api_paymenttransaction WHERE id = 123;
-- Restore from backup or WAL replay
COMMIT;
```

---

*Database Schema Documentation last updated: June 17, 2025*
