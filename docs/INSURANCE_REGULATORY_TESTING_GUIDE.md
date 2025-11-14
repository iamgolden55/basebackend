# Insurance & Regulatory System Testing Guide

## Overview
This guide covers testing the newly implemented insurance provider networks and government regulatory compliance system.

## 🏥 Models Implemented

### Insurance Infrastructure
1. **InsuranceProvider** - Insurance companies with flexible integration
2. **HospitalInsuranceProvider** - Hospital-insurance relationships  
3. **PatientInsurancePolicy** - Patient insurance details
4. **InsuranceVerificationTask** - Manual verification workflows

### Government Regulatory
5. **HealthcareAuthority** - Government regulatory bodies
6. **HospitalLicense** - Hospital licenses and registrations

## 🧪 Testing Scenarios

### A. Insurance Provider Setup

#### 1. Create Insurance Providers
```python
# Test insurance providers for different integration types
providers = [
    {
        'name': 'Blue Cross Blue Shield Nigeria',
        'integration_type': 'api',
        'coverage_area': 'national',
        'countries_served': ['Nigeria'],
        'api_base_url': 'https://api.bcbs-ng.com/v1',
        'has_api_integration': True
    },
    {
        'name': 'NHIS Nigeria',
        'integration_type': 'manual',
        'coverage_area': 'national',
        'countries_served': ['Nigeria'],
        'authority_type': 'government'
    },
    {
        'name': 'AXA Mansard Health',
        'integration_type': 'portal',
        'coverage_area': 'national',
        'provider_portal_url': 'https://providers.axa-mansard.com'
    }
]
```

#### 2. Hospital-Insurance Relationships
```python
# Test hospital contracts with insurance providers
hospital_insurance = {
    'hospital': hospital_instance,
    'insurance_provider': bcbs_provider,
    'contract_status': 'active',
    'network_type': 'in_network',
    'base_reimbursement_rate': 80.00,  # 80%
    'standard_copay_amount': 20.00,     # $20 copay
    'specialist_copay_amount': 50.00,   # $50 specialist copay
    'emergency_copay_amount': 100.00    # $100 emergency copay
}
```

### B. Patient Insurance Testing

#### 1. Patient with Active Insurance
```python
patient_policy = {
    'patient': patient_user,
    'insurance_provider': bcbs_provider,
    'policy_number': 'BCBS-12345678',
    'member_id': 'MEM789012',
    'is_primary_insurance': True,
    'annual_deductible': 1000.00,
    'deductible_met_amount': 200.00,  # $200 already met
    'coverage_percentage': 80.00,      # 80% coverage after deductible
    'policy_status': 'active'
}
```

#### 2. Test Coverage Calculations
```python
# Test different service types
test_scenarios = [
    {'service': 'primary_care', 'amount': 150.00},
    {'service': 'specialist', 'amount': 300.00},
    {'service': 'emergency', 'amount': 1500.00}
]

# Expected results for patient with $800 remaining deductible:
# Primary care ($150): Patient pays $150 + $20 copay = $170
# Specialist ($300): Patient pays $300 + $50 copay = $350  
# Emergency ($1500): Patient pays $800 (deductible) + $140 (20% of remaining $700) + $100 copay = $1040
```

### C. Payment Flow Integration Testing

#### 1. Non-Insurance Patient (Current Flow)
```python
# Existing Paystack flow - no changes
payment_transaction = {
    'patient': patient_without_insurance,
    'amount': 150.00,
    'payment_method': 'card',
    'insurance_coverage_amount': 0,
    'payment_provider': 'paystack'
}
# Patient pays full $150 via Paystack
```

#### 2. Insurance Patient (New Enhanced Flow)
```python
# New insurance-integrated flow
payment_transaction = {
    'patient': patient_with_insurance,
    'amount': 50.00,  # Copay amount only
    'payment_method': 'card',
    'insurance_coverage_amount': 100.00,  # What insurance covers
    'insurance_provider': 'BCBS Nigeria',
    'insurance_claim_status': 'submitted',
    'payment_provider': 'paystack'
}
# Patient pays $50 copay via Paystack
# Hospital submits $100 claim to insurance separately
```

### D. Verification Workflow Testing

#### 1. API-Based Verification (Automated)
```python
# Test automatic verification for API-enabled providers
verification_task = InsuranceVerificationTask.create_verification_task(
    patient_policy=patient_policy,
    verification_type='eligibility',
    priority='normal'
)
# Should attempt API call first, fallback to manual if failed
```

#### 2. Manual Verification Workflow
```python
# Test manual verification assignment
task = InsuranceVerificationTask.objects.create(
    patient_policy=nhis_policy,
    verification_type='benefits',
    assigned_to=staff_member,
    verification_method='phone',
    due_date=timezone.now() + timedelta(hours=24)
)

# Test workflow: assign → start → complete/fail → escalate
task.start_verification(user=staff_member)
task.add_attempt(method='phone', notes='Called member services', success=False)
task.escalate_task(escalated_to_user=supervisor, reason='Unable to reach insurance')
```

### E. Government Regulatory Testing

#### 1. Healthcare Authority Setup
```python
authorities = [
    {
        'name': 'Federal Ministry of Health Nigeria',
        'authority_type': 'federal',
        'country': 'Nigeria',
        'license_types_issued': ['operating', 'emergency', 'surgical'],
        'application_processing_days': 30,
        'has_api_integration': False
    },
    {
        'name': 'Lagos State Health Authority',
        'authority_type': 'state',
        'country': 'Nigeria',
        'state_province': 'Lagos',
        'supports_electronic_submission': True
    }
]
```

#### 2. Hospital License Tracking
```python
hospital_license = {
    'hospital': hospital_instance,
    'healthcare_authority': fmoh_authority,
    'license_type': 'operating',
    'license_number': 'FMOH-OP-2024-001',
    'issue_date': '2024-01-01',
    'expiration_date': '2025-01-01',
    'license_status': 'active',
    'compliance_score': 95
}

# Test renewal alerts
license.is_expiring_soon  # Should be True if < 60 days to expiry
license.mark_as_renewed(new_expiration_date='2026-01-01')
```

## 📊 Dashboard Testing

### 1. Hospital Compliance Dashboard
Test the following metrics:
- Active licenses count
- Licenses expiring in next 60 days
- Insurance contracts requiring renewal
- Average compliance scores
- Pending verification tasks

### 2. Financial Integration Dashboard  
Test integration with existing payment system:
- Total revenue (Paystack + Insurance claims)
- Insurance reimbursement rates by provider
- Patient copay collections
- Outstanding insurance claims

## 🔄 Integration Testing

### 1. Appointment Booking with Insurance
```python
# Test complete flow: booking → insurance verification → payment → appointment creation
booking_flow = {
    'patient': insured_patient,
    'hospital': hospital,
    'department': cardiology,
    'appointment_date': future_date,
    'insurance_verification': 'required'
}

# Expected flow:
# 1. Check patient insurance status
# 2. Verify coverage for cardiology
# 3. Calculate patient copay ($50)
# 4. Process copay payment via Paystack
# 5. Create appointment
# 6. Submit insurance claim
```

### 2. Emergency Admission Testing
```python
# Test unregistered patient with insurance
emergency_admission = {
    'patient': None,  # Walk-in patient
    'insurance_info': {
        'provider': 'NHIS',
        'policy_number': 'NHIS-987654',
        'member_id': 'MEM456789'
    },
    'service_type': 'emergency'
}

# Expected flow:
# 1. Create temporary patient record
# 2. Initiate insurance verification task
# 3. Provide emergency treatment
# 4. Complete insurance verification post-treatment
# 5. Process billing (emergency copay + insurance claim)
```

## 🚨 Error Handling Testing

### 1. Insurance API Failures
- Test timeout scenarios
- Test invalid credentials
- Test service unavailable
- Verify fallback to manual verification

### 2. Payment Processing Errors
- Test Paystack failures with insurance patients
- Test partial payment scenarios
- Test refund handling for insurance claims

### 3. Compliance Violations
- Test license expiration handling
- Test suspended license workflows
- Test inspection failure scenarios

## 📈 Performance Testing

### 1. Load Testing
- Test insurance verification under high load
- Test concurrent payment processing
- Test database performance with large datasets

### 2. Response Time Testing
- Insurance eligibility checks < 5 seconds
- Payment processing < 10 seconds
- License verification < 2 seconds

## 🔐 Security Testing

### 1. Data Encryption
- Verify insurance data encryption at rest
- Test API credential security
- Test sensitive document handling

### 2. Access Control
- Test role-based permissions
- Test audit trail logging
- Test data privacy compliance

## 📋 Checklist for Go-Live

### Pre-Launch Requirements
- [ ] Insurance providers configured
- [ ] Hospital contracts established
- [ ] Staff trained on verification workflows
- [ ] API integrations tested
- [ ] Payment flows validated
- [ ] Compliance requirements met
- [ ] Security audit completed
- [ ] Performance benchmarks achieved
- [ ] Backup and recovery tested
- [ ] Monitoring systems deployed

### Launch Day Monitoring
- [ ] Payment success rates
- [ ] Insurance verification completion rates
- [ ] API response times
- [ ] Error rates and resolution times
- [ ] Customer support ticket volume
- [ ] Financial reconciliation accuracy

## 🔗 Related Documentation
- `/docs/payments/` - Payment system documentation
- `/docs/appointment_system.md` - Appointment booking flows
- `/docs/hospital_flow.md` - Hospital registration processes
- `PRODUCTION_SECURITY_CHECKLIST.md` - Security requirements

## 🆘 Troubleshooting Common Issues

### Insurance Verification Fails
1. Check provider API credentials
2. Verify network connectivity
3. Check patient policy status
4. Escalate to manual verification

### Payment Integration Issues
1. Verify Paystack configuration
2. Check copay calculation logic
3. Validate insurance coverage amounts
4. Test refund scenarios

### Compliance Alerts Not Triggering
1. Check license expiration dates
2. Verify alert scheduling
3. Test notification delivery
4. Check user permissions

---

*Generated on: 2025-06-28*  
*System Version: Insurance & Regulatory v1.0*  
*Last Updated: Initial Implementation*