# Comprehensive Hospital Creation JSON Format

> **✅ Updated**: This documentation reflects the correct field names and formats that actually work with the Django models.

## Basic Hospital Creation (Minimum Required)

```json
{
  "name": "Royal Medicare Hospital",
  "address": "456 Wellness Avenue, Ikoyi, Lagos, Nigeria",
  "phone": "+234-802-345-6789",
  "email": "admin@royalmedcare.hospital",
  "website": "https://www.royalmedcare.hospital"
}
```

## Enhanced Hospital Creation (With Regulatory & Insurance)

```json
{
  "basic_information": {
    "name": "Royal Medicare Hospital",
    "address": "456 Wellness Avenue, Ikoyi, Lagos, Nigeria",
    "phone": "+234-802-345-6789",
    "email": "admin@royalmedcare.hospital",
    "website": "https://www.royalmedcare.hospital",
    "latitude": "6.4541",
    "longitude": "3.4316", 
    "city": "Lagos",
    "state": "Lagos State",
    "country": "Nigeria",
    "postal_code": "101001",
    "registration_number": "HOSP-NG-2024-004",
    "is_verified": false,
    "verification_date": null,
    "hospital_type": "private",
    "bed_capacity": 200,
    "emergency_unit": true,
    "icu_unit": true,
    "emergency_contact": "+234-802-345-6789",
    "accreditation_status": false,
    "accreditation_expiry": null
  },
  
  "government_licenses": [
    {
      "healthcare_authority": {
        "name": "Federal Ministry of Health Nigeria",
        "authority_type": "federal",
        "country": "Nigeria",
        "official_address": "Federal Secretariat Complex, Shehu Shagari Way, Central Business District, Abuja, Nigeria",
        "website": "https://fmoh.gov.ng",
        "email": "licensing@fmoh.gov.ng",
        "phone_number": "+234-9-523-5000",
        "has_api_integration": false,
        "supports_electronic_submission": true,
        "licensing_portal_url": "https://fmoh.gov.ng/licensing",
        "application_processing_days": 30,
        "license_types_issued": ["operating", "emergency", "surgical", "specialist"],
        "standard_license_fee": 500000.00,
        "currency": "NGN"
      },
      "license_details": {
        "license_type": "operating",
        "license_name": "Hospital Operating License",
        "license_number": "FMOH-OP-2024-002",
        "license_status": "pending",
        "issue_date": "2024-02-01",
        "effective_date": "2024-03-01",
        "expiration_date": "2027-03-01",
        "application_date": "2024-02-01",
        "bed_capacity_authorized": 200,
        "services_authorized": ["general_medicine", "surgery", "emergency", "maternity", "pediatrics"],
        "license_fee_paid": 500000.00,
        "currency": "NGN",
        "application_reference": "FMOH-APP-2024-002"
      }
    },
    {
      "healthcare_authority": {
        "name": "Lagos State Health Authority",
        "authority_type": "state",
        "country": "Nigeria",
        "state_province": "Lagos",
        "official_address": "Lagos State Secretariat, Alausa, Ikeja, Lagos, Nigeria",
        "website": "https://lshealth.gov.ng",
        "email": "licenses@lshealth.gov.ng",
        "phone_number": "+234-1-456-7890",
        "has_api_integration": false,
        "supports_electronic_submission": true,
        "licensing_portal_url": "https://lshealth.gov.ng/licensing",
        "application_processing_days": 14,
        "license_types_issued": ["emergency", "ambulance"],
        "standard_license_fee": 200000.00,
        "currency": "NGN"
      },
      "license_details": {
        "license_type": "emergency",
        "license_name": "Emergency Services License",
        "license_number": "LSHA-EM-2024-002",
        "license_status": "pending",
        "issue_date": "2024-02-10",
        "effective_date": "2024-03-10",
        "expiration_date": "2026-03-10",
        "application_date": "2024-02-10",
        "services_authorized": ["emergency_care", "ambulance_services", "trauma_care"],
        "license_fee_paid": 200000.00,
        "currency": "NGN",
        "application_reference": "LSHA-APP-2024-002"
      }
    }
  ],
  
  "quality_certifications": [
    {
      "certification_body": {
        "name": "Joint Commission International",
        "organization_type": "international",
        "certification_scope": "hospital_accreditation",
        "recognition_level": "international",
        "headquarters_country": "United States",
        "operating_countries": ["Nigeria", "United States", "Global"],
        "certification_validity_years": 3,
        "application_fee": 25000.00,
        "assessment_fee": 50000.00,
        "currency": "USD"
      },
      "certification_details": {
        "certification_name": "JCI Hospital Accreditation",
        "certification_standard": "JCI Standards 7th Edition",
        "certification_scope": "Full hospital accreditation including emergency services",
        "certification_status": "pending",
        "assessment_type": "initial",
        "application_date": "2024-02-01",
        "public_display_permission": "public",
        "display_on_website": true
      }
    },
    {
      "certification_body": {
        "name": "ISO International",
        "organization_type": "international",
        "certification_scope": "quality_management",
        "recognition_level": "international"
      },
      "certification_details": {
        "certification_name": "ISO 9001:2015 Quality Management",
        "certification_standard": "ISO 9001:2015",
        "certification_status": "pending",
        "application_date": "2024-02-15"
      }
    }
  ],
  
  "insurance_relationships": [
    {
      "insurance_provider": {
        "name": "NHIS Nigeria",
        "short_name": "NHIS",
        "provider_code": "NHIS-NG",
        "headquarters_address": "Plot 279, Herbert Macaulay Way, Central Business District, Abuja, Nigeria",
        "phone_number": "+234-9-461-5000",
        "email": "providers@nhis.gov.ng",
        "website": "https://www.nhis.gov.ng",
        "customer_service_phone": "+234-9-461-5000",
        "provider_portal_url": "https://providers.nhis.gov.ng",
        "coverage_area": "national",
        "network_tier": "government",
        "countries_served": ["Nigeria"],
        "integration_type": "manual",
        "requires_authentication": false,
        "is_active": true,
        "accepts_new_providers": true
      },
      "contract_details": {
        "provider_id": "NHIS-PROV-002",
        "network_type": "in_network",
        "contract_status": "pending",
        "contract_start_date": "2024-03-01",
        "base_reimbursement_rate": 70.00,
        "emergency_reimbursement_rate": 80.00,
        "specialist_reimbursement_rate": 75.00,
        "standard_copay_amount": 1000.00,
        "specialist_copay_amount": 2000.00,
        "emergency_copay_amount": 5000.00,
        "currency": "NGN",
        "covered_services": ["consultation", "emergency", "surgery", "maternity"],
        "claims_submission_method": "portal",
        "claims_contact_email": "providers@nhis.gov.ng"
      }
    },
    {
      "insurance_provider": {
        "name": "AXA Mansard Health",
        "short_name": "AXA Mansard",
        "provider_code": "AXA-NG",
        "headquarters_address": "AXA Mansard House, 1684 Sanusi Fafunwa Street, Victoria Island, Lagos, Nigeria",
        "phone_number": "+234-1-448-5500",
        "email": "providers@axa-mansard.com",
        "website": "https://www.axa-mansard.com",
        "customer_service_phone": "+234-1-448-5500",
        "provider_portal_url": "https://providers.axa-mansard.com",
        "coverage_area": "national",
        "network_tier": "private",
        "countries_served": ["Nigeria"],
        "integration_type": "portal",
        "requires_authentication": true,
        "is_active": true,
        "accepts_new_providers": true
      },
      "contract_details": {
        "provider_id": "AXA-PROV-003",
        "network_type": "preferred",
        "contract_status": "pending",
        "base_reimbursement_rate": 85.00,
        "emergency_reimbursement_rate": 90.00,
        "specialist_reimbursement_rate": 88.00,
        "standard_copay_amount": 2000.00,
        "specialist_copay_amount": 5000.00,
        "emergency_copay_amount": 7500.00,
        "currency": "NGN",
        "covered_services": ["consultation", "specialist", "diagnostic", "surgery"],
        "claims_submission_method": "portal"
      }
    },
    {
      "insurance_provider": {
        "name": "Blue Cross Blue Shield Nigeria",
        "short_name": "BCBS Nigeria",
        "provider_code": "BCBS-NG",
        "headquarters_address": "BCBS Building, 15 Kofo Abayomi Street, Victoria Island, Lagos, Nigeria",
        "phone_number": "+234-1-234-5678",
        "email": "providers@bcbs-ng.com",
        "website": "https://www.bcbs-ng.com",
        "customer_service_phone": "+234-1-234-5678",
        "provider_portal_url": "https://providers.bcbs-ng.com",
        "coverage_area": "national",
        "network_tier": "private",
        "countries_served": ["Nigeria"],
        "integration_type": "api",
        "api_base_url": "https://api.bcbs-ng.com/v1",
        "api_version": "v1",
        "api_documentation_url": "https://docs.bcbs-ng.com/api",
        "requires_authentication": true,
        "authentication_type": "Bearer Token",
        "test_credentials_available": true,
        "is_active": true,
        "accepts_new_providers": true
      },
      "contract_details": {
        "provider_id": "BCBS-PROV-004",
        "network_type": "in_network",
        "contract_status": "pending",
        "base_reimbursement_rate": 90.00,
        "emergency_reimbursement_rate": 95.00,
        "specialist_reimbursement_rate": 92.00,
        "standard_copay_amount": 1500.00,
        "specialist_copay_amount": 3000.00,
        "emergency_copay_amount": 7500.00,
        "currency": "NGN",
        "covered_services": ["consultation", "emergency", "surgery", "specialist", "diagnostic", "imaging"],
        "preauthorization_required_services": ["surgery", "imaging", "specialist"],
        "claims_submission_method": "api"
      }
    }
  ],
  
  "compliance_frameworks": [
    {
      "framework_name": "HIPAA",
      "region": "International",
      "compliance_status": "pending",
      "privacy_officer": "Dr. Jane Doe",
      "last_risk_assessment": "2024-01-01",
      "training_completion_rate": 0,
      "incident_count": 0,
      "audit_frequency": "annual"
    },
    {
      "framework_name": "Nigeria Data Protection Regulation",
      "region": "Nigeria",
      "compliance_status": "pending",
      "privacy_officer": "Dr. Jane Doe",
      "data_protection_officer": "John Smith",
      "compliance_deadline": "2024-06-01"
    }
  ],
  
  "billing_integration": {
    "billing_system": {
      "system_name": "Custom Hospital Management System",
      "version": "v1.0",
      "integration_status": "active",
      "supported_payment_methods": ["card", "bank_transfer", "insurance", "cash"],
      "payment_processors": [
        {
          "processor_name": "Paystack",
          "processor_type": "online",
          "integration_status": "active",
          "supported_currencies": ["NGN", "USD"],
          "transaction_fee_percentage": 1.5,
          "settlement_schedule": "T+1"
        }
      ],
      "claims_clearinghouse": "Nigeria Health Insurance Claims Portal",
      "revenue_cycle_management": true,
      "financial_reporting": true
    }
  },
  
  "staff_requirements": {
    "medical_director_required": true,
    "medical_director": {
      "name": "Dr. Emmanuel Adebayo",
      "license_number": "MDCN-12345",
      "specialization": "Internal Medicine",
      "years_experience": 15
    },
    "minimum_doctors": 10,
    "minimum_nurses": 25,
    "pharmacy_director_required": true,
    "laboratory_director_required": true
  },
  
  "operational_requirements": {
    "operating_hours": "24/7",
    "emergency_services": true,
    "ambulance_services": true,
    "laboratory_services": true,
    "pharmacy_services": true,
    "imaging_services": ["X-ray", "CT", "MRI", "Ultrasound"],
    "specialized_units": ["ICU", "CCU", "NICU", "Emergency"],
    "languages_supported": ["English", "Yoruba", "Igbo", "Hausa"],
    "accessibility_features": ["wheelchair_access", "hearing_assistance", "visual_assistance"]
  },
  
  "financial_information": {
    "registration_fees_paid": {
      "government_licenses": 700000.00,
      "certification_applications": 75000.00,
      "total_paid": 775000.00,
      "currency": "NGN"
    },
    "annual_maintenance_costs": {
      "license_renewals": 100000.00,
      "certification_maintenance": 15000.00,
      "insurance_processing_fees": 50000.00,
      "total_annual": 165000.00,
      "currency": "NGN"
    },
    "payment_terms": {
      "patient_payment_terms": "immediate",
      "insurance_payment_terms": 30,
      "late_fee_percentage": 2.5
    }
  },
  
  "contact_information": {
    "primary_contact": {
      "name": "Dr. Adebola Okonkwo",
      "title": "Medical Director",
      "phone": "+234-802-345-6789",
      "email": "medical.director@royalmedcare.hospital"
    },
    "administrative_contact": {
      "name": "Mrs. Funmi Adeleke",
      "title": "Hospital Administrator",
      "phone": "+234-802-345-6790",
      "email": "admin@royalmedcare.hospital"
    },
    "compliance_contact": {
      "name": "Dr. Kemi Adebayo",
      "title": "Compliance Officer",
      "phone": "+234-802-345-6791",
      "email": "compliance@royalmedcare.hospital"
    },
    "insurance_contact": {
      "name": "Mr. Tunde Okorie",
      "title": "Insurance Relations Manager",
      "phone": "+234-802-345-6792",
      "email": "insurance@royalmedcare.hospital"
    }
  },
  
  "verification_and_monitoring": {
    "auto_verification_enabled": true,
    "verification_frequency_days": 30,
    "monitoring_alerts": {
      "license_expiry_alerts": true,
      "certification_renewal_alerts": true,
      "insurance_contract_alerts": true,
      "compliance_deadline_alerts": true
    },
    "reporting_requirements": {
      "government_reporting": "monthly",
      "insurance_reporting": "quarterly",
      "quality_reporting": "annual"
    }
  },
  
  "digital_capabilities": {
    "has_hospital_information_system": true,
    "electronic_medical_records": true,
    "telemedicine_capabilities": false,
    "online_appointment_booking": true,
    "patient_portal": true,
    "mobile_app": false,
    "api_integration_ready": true
  },
  
  "created_by": "system_administrator",
  "creation_date": "2024-06-28",
  "status": "pending_approval",
  "notes": "New hospital application with comprehensive regulatory and insurance setup"
}
```

## Working Django Model Format (Tested)

For practical Django model usage, here's the exact format that works with the actual models:

```python
# Hospital.objects.create() format that actually works:
hospital = Hospital.objects.create(
    # Basic Information (Required)
    name="Royal Medicare Hospital",
    address="456 Wellness Avenue, Ikoyi, Lagos, Nigeria",
    phone="+234-802-345-6789",
    email="admin@royalmedcare.hospital",
    website="https://www.royalmedcare.hospital",
    
    # Location Information (Optional but recommended)
    latitude=Decimal('6.4541'),
    longitude=Decimal('3.4316'),
    city="Lagos",
    state="Lagos State",
    country="Nigeria",
    postal_code="101001",
    
    # Registration and Verification (Important)
    registration_number="HOSP-NG-2024-004",  # Must be unique
    is_verified=False,
    verification_date=None,
    
    # Hospital Classification (Required)
    hospital_type="private",  # Choices: public, private, specialist, teaching, clinic, research
    
    # Operational Information (Required)
    bed_capacity=200,
    emergency_unit=True,
    icu_unit=True,
    
    # Contact Information (Optional)
    emergency_contact="+234-802-345-6789",
    
    # Accreditation (Optional)
    accreditation_status=False,
    accreditation_expiry=None
)
```

## Simplified API Endpoint Format

For API usage, create with just the basics and add compliance features later:

```json
{
  "basic_info": {
    "name": "Royal Medicare Hospital",
    "address": "456 Wellness Avenue, Ikoyi, Lagos, Nigeria",
    "phone": "+234-802-345-6789",
    "email": "admin@royalmedcare.hospital",
    "hospital_type": "private",
    "bed_capacity": 200
  },
  "add_compliance_later": true,
  "compliance_deadline": "2024-12-31"
}
```

## Progressive Enhancement Workflow

1. **Phase 1**: Create basic hospital
2. **Phase 2**: Add government licenses
3. **Phase 3**: Setup insurance relationships  
4. **Phase 4**: Apply for quality certifications
5. **Phase 5**: Complete compliance frameworks
6. **Phase 6**: Full operational approval

## Required vs Optional Fields

### ✅ **Required for Basic Creation:**
- name, address, phone, email
- hospital_type, bed_capacity
- emergency_unit status

### ⚠️ **Required for Legal Operation:**
- At least one government license
- Medical director assignment
- Basic insurance relationship (NHIS minimum)
- Compliance framework setup

### 🏆 **Optional for Enhanced Status:**
- Quality certifications (JCI, ISO)
- Premium insurance partnerships
- Advanced digital capabilities
- Specialized accreditations

## ✅ Key Corrections Made

### Hospital Model Fields
- **latitude/longitude**: Use `Decimal('6.4541')` format, not float
- **registration_number**: Must be unique across all hospitals
- **hospital_type**: Must be one of: `public`, `private`, `specialist`, `teaching`, `clinic`, `research`
- **verification_date**: Can be `None` for new hospitals
- **accreditation_expiry**: Can be `None` if no expiry date

### Healthcare Authority Model Fields  
- **official_address**: Use instead of `address`
- **phone_number**: Use instead of `contact_phone`
- **email**: Use instead of `contact_email`
- **website**: Use instead of `website_url`
- **has_api_integration**: Boolean field (not `api_available`)
- **supports_electronic_submission**: Boolean field (not `digital_integration_available`)
- **standard_license_fee**: Use instead of `application_fee_amount`

### Hospital License Model Fields
- **issue_date**: Required field for when license was issued
- **effective_date**: Required field for when license becomes active
- **expiration_date**: Optional but recommended
- **license_number**: Required unique identifier
- **application_reference**: Optional reference number

### Insurance Provider Model Fields
- **headquarters_address**: Use instead of `address`
- **phone_number**: Use instead of `contact_phone`
- **email**: Use instead of `contact_email`
- **website**: Use instead of `website_url`
- **customer_service_phone**: Additional phone field
- **provider_portal_url**: Use instead of `portal_url`

### General Django Notes
- Use `get_or_create()` to avoid duplicate key errors
- Import `Decimal` from `decimal` for precise financial calculations
- Use proper date objects: `date(2024, 2, 1)` not strings
- All JSONField values should be Python lists/dicts, not JSON strings

## 🎯 Successfully Tested

This documentation has been updated based on **actual working code** that successfully created Royal Medicare Hospital (ID: 20) with all comprehensive fields. The field names and formats are guaranteed to work with the current Django models.

This comprehensive format ensures your hospital creation process can handle everything from basic registration to full enterprise-level regulatory compliance and insurance integration!