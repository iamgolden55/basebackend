#!/usr/bin/env python
import os
import sys
import django
from datetime import date, datetime
from decimal import Decimal

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from api.models.medical import (
    Hospital, HealthcareAuthority, HospitalLicense, 
    InsuranceProvider, HospitalInsuranceProvider,
    CertificationBody, HospitalCertification,
    ComplianceFramework, HospitalCompliance,
    BillingSystem, HospitalBillingIntegration
)

def create_comprehensive_hospital():
    print("Creating Royal Medicare Hospital with comprehensive regulatory and insurance setup...")
    
    # Check if Royal Medicare Hospital already exists and delete it
    existing_hospitals = Hospital.objects.filter(name="Royal Medicare Hospital")
    if existing_hospitals.exists():
        print(f"Found {existing_hospitals.count()} existing Royal Medicare Hospital(s). Deleting them...")
        existing_hospitals.delete()
        print("✅ Deleted existing Royal Medicare Hospital(s)")
    
    # 1. Create the basic hospital
    hospital = Hospital.objects.create(
        name="Royal Medicare Hospital",
        address="456 Wellness Avenue, Ikoyi, Lagos, Nigeria",
        phone="+234-802-345-6789",
        email="admin@royalmedcare.hospital",
        website="https://www.royalmedcare.hospital",
        latitude=Decimal('6.4541'),
        longitude=Decimal('3.4316'),
        city="Lagos",
        state="Lagos State",
        country="Nigeria",
        postal_code="101001",
        registration_number="HOSP-NG-2024-003",
        is_verified=False,
        hospital_type="private",
        bed_capacity=200,
        emergency_unit=True,
        icu_unit=True,
        emergency_contact="+234-802-345-6789",
        accreditation_status=False
    )
    print(f"✅ Created hospital: {hospital.name}")
    
    # 2. Get or Create Healthcare Authorities
    federal_authority, created = HealthcareAuthority.objects.get_or_create(
        name="Federal Ministry of Health Nigeria",
        defaults={
            'authority_type': "federal",
            'country': "Nigeria",
            'official_address': "Federal Secretariat Complex, Shehu Shagari Way, Central Business District, Abuja, Nigeria",
            'website': "https://fmoh.gov.ng",
            'email': "licensing@fmoh.gov.ng",
            'phone_number': "+234-9-523-5000",
            'has_api_integration': False,
            'supports_electronic_submission': True,
            'licensing_portal_url': "https://fmoh.gov.ng/licensing",
            'application_processing_days': 30,
            'license_types_issued': ["operating", "emergency", "surgical", "specialist"],
            'standard_license_fee': Decimal('500000.00'),
            'currency': "NGN"
        }
    )
    
    state_authority, created = HealthcareAuthority.objects.get_or_create(
        name="Lagos State Health Authority",
        defaults={
            'authority_type': "state",
            'country': "Nigeria",
            'state_province': "Lagos",
            'official_address': "Lagos State Secretariat, Alausa, Ikeja, Lagos, Nigeria",
            'website': "https://lshealth.gov.ng",
            'email': "licenses@lshealth.gov.ng",
            'phone_number': "+234-1-456-7890",
            'has_api_integration': False,
            'supports_electronic_submission': True,
            'licensing_portal_url': "https://lshealth.gov.ng/licensing",
            'application_processing_days': 14,
            'license_types_issued': ["emergency", "ambulance"],
            'standard_license_fee': Decimal('200000.00'),
            'currency': "NGN"
        }
    )
    print(f"✅ Created healthcare authorities: {federal_authority.name}, {state_authority.name}")
    
    # 3. Create Hospital Licenses
    operating_license = HospitalLicense.objects.create(
        hospital=hospital,
        healthcare_authority=federal_authority,
        license_type="operating",
        license_name="Hospital Operating License",
        license_number="FMOH-OP-2024-002",
        license_status="pending",
        issue_date=date(2024, 2, 1),
        effective_date=date(2024, 3, 1),
        expiration_date=date(2027, 3, 1),
        application_date=date(2024, 2, 1),
        bed_capacity_authorized=200,
        services_authorized=["general_medicine", "surgery", "emergency", "maternity", "pediatrics"],
        license_fee_paid=Decimal('500000.00'),
        currency="NGN",
        application_reference="FMOH-APP-2024-002"
    )
    
    emergency_license = HospitalLicense.objects.create(
        hospital=hospital,
        healthcare_authority=state_authority,
        license_type="emergency",
        license_name="Emergency Services License",
        license_number="LSHA-EM-2024-002",
        license_status="pending",
        issue_date=date(2024, 2, 10),
        effective_date=date(2024, 3, 10),
        expiration_date=date(2026, 3, 10),
        application_date=date(2024, 2, 10),
        services_authorized=["emergency_care", "ambulance_services", "trauma_care"],
        license_fee_paid=Decimal('200000.00'),
        currency="NGN",
        application_reference="LSHA-APP-2024-002"
    )
    print(f"✅ Created hospital licenses: {operating_license.license_name}, {emergency_license.license_name}")
    
    # 4. Get or Create Insurance Providers and Relationships
    # NHIS Nigeria
    nhis, created = InsuranceProvider.objects.get_or_create(
        name="NHIS Nigeria",
        defaults={
            'provider_type': "government",
            'coverage_area': "national",
            'countries_served': ["Nigeria"],
            'headquarters_country': "Nigeria",
            'contact_phone': "+234-9-461-5000",
            'contact_email': "providers@nhis.gov.ng",
            'website_url': "https://www.nhis.gov.ng",
            'integration_type': "manual",
            'has_provider_portal': True,
            'provider_portal_url': "https://providers.nhis.gov.ng",
            'verification_method': "manual",
            'network_tier': "government",
            'claim_submission_methods': ["portal", "paper"],
            'average_claim_processing_days': 21,
            'customer_service_rating': Decimal('7.0'),
            'provider_satisfaction_rating': Decimal('6.5'),
            'is_active': True,
            'requires_preauthorization': False
        }
    )
    
    # AXA Mansard
    axa = InsuranceProvider.objects.create(
        name="AXA Mansard Health",
        provider_type="private",
        coverage_area="national",
        countries_served=["Nigeria"],
        headquarters_country="Nigeria",
        contact_phone="+234-1-448-5500",
        contact_email="providers@axa-mansard.com",
        website_url="https://www.axa-mansard.com",
        integration_type="portal",
        has_provider_portal=True,
        provider_portal_url="https://providers.axa-mansard.com",
        verification_method="automated",
        network_tier="private",
        claim_submission_methods=["portal", "api"],
        average_claim_processing_days=14,
        customer_service_rating=Decimal('8.5'),
        provider_satisfaction_rating=Decimal('8.0'),
        is_active=True,
        requires_preauthorization=True
    )
    
    # Blue Cross Blue Shield Nigeria
    bcbs = InsuranceProvider.objects.create(
        name="Blue Cross Blue Shield Nigeria",
        provider_type="private",
        coverage_area="national",
        countries_served=["Nigeria"],
        headquarters_country="Nigeria",
        contact_phone="+234-1-234-5678",
        contact_email="providers@bcbs-ng.com",
        website_url="https://www.bcbs-ng.com",
        integration_type="api",
        has_api_integration=True,
        api_base_url="https://api.bcbs-ng.com/v1",
        has_provider_portal=True,
        provider_portal_url="https://providers.bcbs-ng.com",
        verification_method="real_time",
        network_tier="private",
        claim_submission_methods=["api", "portal"],
        average_claim_processing_days=7,
        customer_service_rating=Decimal('9.0'),
        provider_satisfaction_rating=Decimal('8.8'),
        is_active=True,
        requires_preauthorization=True,
        supports_real_time_verification=True
    )
    print(f"✅ Created insurance providers: {nhis.name}, {axa.name}, {bcbs.name}")
    
    # Create Hospital-Insurance Provider Relationships
    nhis_contract = HospitalInsuranceProvider.objects.create(
        hospital=hospital,
        insurance_provider=nhis,
        provider_id="NHIS-PROV-002",
        network_type="in_network",
        contract_status="pending",
        contract_start_date=date(2024, 3, 1),
        base_reimbursement_rate=Decimal('70.00'),
        emergency_reimbursement_rate=Decimal('80.00'),
        specialist_reimbursement_rate=Decimal('75.00'),
        standard_copay_amount=Decimal('1000.00'),
        specialist_copay_amount=Decimal('2000.00'),
        emergency_copay_amount=Decimal('5000.00'),
        currency="NGN",
        covered_services=["consultation", "emergency", "surgery", "maternity", "pediatrics"],
        claims_submission_method="portal",
        claims_contact_email="providers@nhis.gov.ng",
        payment_terms_days=45,
        auto_adjudication_enabled=False
    )
    
    axa_contract = HospitalInsuranceProvider.objects.create(
        hospital=hospital,
        insurance_provider=axa,
        provider_id="AXA-PROV-003",
        network_type="preferred",
        contract_status="pending",
        contract_start_date=date(2024, 3, 15),
        base_reimbursement_rate=Decimal('85.00'),
        emergency_reimbursement_rate=Decimal('90.00'),
        specialist_reimbursement_rate=Decimal('88.00'),
        standard_copay_amount=Decimal('2000.00'),
        specialist_copay_amount=Decimal('5000.00'),
        emergency_copay_amount=Decimal('7500.00'),
        currency="NGN",
        covered_services=["consultation", "specialist", "diagnostic", "surgery"],
        claims_submission_method="portal",
        payment_terms_days=30,
        auto_adjudication_enabled=True
    )
    
    bcbs_contract = HospitalInsuranceProvider.objects.create(
        hospital=hospital,
        insurance_provider=bcbs,
        provider_id="BCBS-PROV-004",
        network_type="in_network",
        contract_status="pending",
        contract_start_date=date(2024, 4, 1),
        base_reimbursement_rate=Decimal('90.00'),
        emergency_reimbursement_rate=Decimal('95.00'),
        specialist_reimbursement_rate=Decimal('92.00'),
        standard_copay_amount=Decimal('1500.00'),
        specialist_copay_amount=Decimal('3000.00'),
        emergency_copay_amount=Decimal('7500.00'),
        currency="NGN",
        covered_services=["consultation", "emergency", "surgery", "specialist", "diagnostic", "imaging"],
        preauthorization_required_services=["surgery", "imaging", "specialist"],
        claims_submission_method="api",
        payment_terms_days=21,
        auto_adjudication_enabled=True
    )
    print(f"✅ Created insurance contracts: NHIS, AXA Mansard, BCBS")
    
    # 5. Create Certification Bodies and Hospital Certifications
    jci = CertificationBody.objects.create(
        name="Joint Commission International",
        organization_type="international",
        certification_scope="hospital_accreditation",
        recognition_level="international",
        headquarters_country="United States",
        operating_countries=["Nigeria", "United States", "Global"],
        website_url="https://www.jointcommissioninternational.org",
        contact_email="info@jointcommission.org",
        contact_phone="+1-630-792-5000",
        assessment_methodology="on_site_survey",
        certification_validity_years=3,
        application_fee=Decimal('25000.00'),
        assessment_fee=Decimal('50000.00'),
        annual_maintenance_fee=Decimal('5000.00'),
        currency="USD",
        is_active=True,
        reputation_score=Decimal('95.0')
    )
    
    iso_body = CertificationBody.objects.create(
        name="ISO International",
        organization_type="international",
        certification_scope="quality_management",
        recognition_level="international",
        headquarters_country="Switzerland",
        operating_countries=["Global"],
        website_url="https://www.iso.org",
        contact_email="info@iso.org",
        assessment_methodology="document_review_and_audit",
        certification_validity_years=3,
        application_fee=Decimal('5000.00'),
        assessment_fee=Decimal('15000.00'),
        annual_maintenance_fee=Decimal('2000.00'),
        currency="USD",
        is_active=True,
        reputation_score=Decimal('92.0')
    )
    print(f"✅ Created certification bodies: {jci.name}, {iso_body.name}")
    
    # Create Hospital Certifications
    jci_cert = HospitalCertification.objects.create(
        hospital=hospital,
        certification_body=jci,
        certification_name="JCI Hospital Accreditation",
        certification_standard="JCI Standards 7th Edition",
        certification_scope="Full hospital accreditation including emergency services",
        certification_status="pending",
        assessment_type="initial",
        application_date=date(2024, 2, 15),
        public_display_permission="public",
        display_on_website=True,
        marketing_approved=True,
        application_fee_paid=Decimal('25000.00'),
        assessment_fee_paid=Decimal('50000.00'),
        currency="USD"
    )
    
    iso_cert = HospitalCertification.objects.create(
        hospital=hospital,
        certification_body=iso_body,
        certification_name="ISO 9001:2015 Quality Management",
        certification_standard="ISO 9001:2015",
        certification_scope="Quality management system for healthcare services",
        certification_status="pending",
        assessment_type="initial",
        application_date=date(2024, 3, 1),
        public_display_permission="public",
        display_on_website=True,
        marketing_approved=True,
        application_fee_paid=Decimal('5000.00'),
        assessment_fee_paid=Decimal('15000.00'),
        currency="USD"
    )
    print(f"✅ Created hospital certifications: JCI, ISO 9001:2015")
    
    # 6. Create Compliance Frameworks and Hospital Compliance
    hipaa_framework = ComplianceFramework.objects.create(
        name="HIPAA",
        framework_type="privacy",
        region="International",
        regulatory_body="US Department of Health and Human Services",
        framework_version="2013 Final Rule",
        description="Health Insurance Portability and Accountability Act privacy and security rules",
        is_mandatory=False,
        applicability_criteria="Healthcare organizations handling patient data",
        implementation_timeline_months=6,
        assessment_frequency_months=12,
        penalty_range_description="$100 to $1.5 million per violation",
        website_url="https://www.hhs.gov/hipaa",
        is_active=True,
        priority_level="high"
    )
    
    ndpr_framework = ComplianceFramework.objects.create(
        name="Nigeria Data Protection Regulation",
        framework_type="privacy",
        region="Nigeria",
        regulatory_body="National Information Technology Development Agency",
        framework_version="2019",
        description="Nigeria's data protection regulation for personal data processing",
        is_mandatory=True,
        applicability_criteria="Organizations processing personal data in Nigeria",
        implementation_timeline_months=12,
        assessment_frequency_months=12,
        penalty_range_description="Up to 10% of annual turnover or NGN 10 million",
        website_url="https://nitda.gov.ng/ndpr",
        is_active=True,
        priority_level="critical"
    )
    print(f"✅ Created compliance frameworks: {hipaa_framework.name}, {ndpr_framework.name}")
    
    # Create Hospital Compliance Records
    hipaa_compliance = HospitalCompliance.objects.create(
        hospital=hospital,
        compliance_framework=hipaa_framework,
        compliance_status="in_progress",
        implementation_status="planning",
        risk_level="medium",
        last_assessment_date=date(2024, 1, 15),
        last_assessment_type="self_assessment",
        next_assessment_due=date(2024, 7, 15),
        assessment_frequency_months=6,
        overall_compliance_score=None,
        policy_compliance_score=None,
        technical_compliance_score=None,
        training_compliance_score=None,
        implementation_start_date=date(2024, 2, 1),
        implementation_target_date=date(2024, 8, 1),
        implementation_budget=Decimal('150000.00'),
        currency="NGN",
        required_policies_implemented=[],
        required_policies_pending=["Privacy Policy", "Security Policy", "Breach Response Policy"],
        training_programs_completed=[],
        training_programs_pending=["HIPAA Awareness Training", "Security Training"],
        technical_controls_implemented=[],
        technical_controls_pending=["Encryption", "Access Controls", "Audit Logging"],
        monitoring_frequency="monthly",
        automated_monitoring_enabled=False,
        is_active=True
    )
    
    ndpr_compliance = HospitalCompliance.objects.create(
        hospital=hospital,
        compliance_framework=ndpr_framework,
        compliance_status="in_progress",
        implementation_status="planning",
        risk_level="high",
        last_assessment_date=date(2024, 1, 20),
        last_assessment_type="self_assessment",
        next_assessment_due=date(2024, 7, 20),
        assessment_frequency_months=6,
        implementation_start_date=date(2024, 2, 15),
        implementation_target_date=date(2024, 8, 15),
        implementation_budget=Decimal('200000.00'),
        currency="NGN",
        required_policies_implemented=[],
        required_policies_pending=["Data Protection Policy", "Consent Management", "Data Subject Rights"],
        training_programs_completed=[],
        training_programs_pending=["NDPR Compliance Training", "Data Protection Officer Training"],
        technical_controls_implemented=[],
        technical_controls_pending=["Data Minimization", "Consent Management System"],
        monitoring_frequency="monthly",
        automated_monitoring_enabled=False,
        is_active=True,
        requires_immediate_attention=True
    )
    print(f"✅ Created hospital compliance records: HIPAA, NDPR")
    
    # 7. Create Billing System and Integration
    billing_system = BillingSystem.objects.create(
        name="Royal Medicare Hospital Management System",
        vendor_name="Custom Development Team",
        system_code="RMHMS01",
        version="v2.0",
        system_type="comprehensive",
        deployment_type="cloud",
        integration_complexity="moderate",
        vendor_website="https://www.royalmedcare.hospital/billing",
        core_features=[
            "Patient Registration",
            "Appointment Scheduling",
            "Billing and Invoicing",
            "Insurance Claims Processing",
            "Payment Processing",
            "Financial Reporting",
            "Revenue Cycle Management"
        ],
        supported_billing_types=["patient", "insurance", "government"],
        supported_payment_methods=["card", "bank_transfer", "cash", "insurance"],
        insurance_claim_processing=True,
        supported_insurance_types=["private", "government", "international"],
        electronic_claims_submission=True,
        real_time_eligibility_verification=True,
        api_available=True,
        api_version="v1.0",
        webhook_support=True,
        integration_methods=["API", "webhook", "file_transfer"],
        data_formats_supported=["JSON", "XML", "CSV"],
        hipaa_compliant=True,
        pci_dss_compliant=True,
        data_encryption=True,
        pricing_model="custom",
        base_monthly_cost=Decimal('50000.00'),
        currency="NGN",
        implementation_time_weeks=8,
        training_provided=True,
        support_channels=["email", "phone", "chat"],
        support_hours="Business hours + Emergency support",
        is_active=True,
        is_recommended=True
    )
    
    billing_integration = HospitalBillingIntegration.objects.create(
        hospital=hospital,
        billing_system=billing_system,
        integration_name="Royal Medicare Primary Billing",
        integration_type="primary",
        integration_status="active",
        api_endpoint="https://api.royalmedcare.hospital/billing/v1",
        data_sync_method="real_time",
        sync_frequency_minutes=None,
        patient_id_mapping={"external_id": "hospital_patient_id"},
        procedure_code_mapping={"cpt": "hospital_procedure_code"},
        insurance_mapping={"provider_id": "hospital_insurance_id"},
        default_billing_rules={
            "auto_billing": True,
            "payment_terms": 30,
            "late_fees": True
        },
        payment_terms_days=30,
        automatic_billing_enabled=True,
        invoice_generation_enabled=True,
        claims_submission_enabled=True,
        auto_claims_submission=True,
        claims_batch_size=50,
        transaction_fee_percentage=Decimal('0.0000'),
        monthly_subscription_fee=Decimal('50000.00'),
        currency="NGN",
        total_transactions_processed=0,
        successful_transactions=0,
        failed_transactions=0,
        encryption_enabled=True,
        ssl_verification=True,
        rate_limit_enabled=True,
        rate_limit_requests_per_minute=100,
        implementation_date=date(2024, 2, 1),
        go_live_date=date(2024, 3, 1),
        implementation_team=["Hospital IT Team", "Billing System Developers"],
        reporting_enabled=True,
        audit_logging_enabled=True,
        compliance_monitoring=True,
        backup_enabled=True,
        backup_frequency_hours=6,
        backup_retention_days=90,
        test_mode_enabled=False,
        is_active=True,
        health_status="healthy"
    )
    print(f"✅ Created billing system and integration: {billing_system.name}")
    
    print(f"\n🎉 Successfully created Royal Medicare Hospital with comprehensive setup!")
    print(f"Hospital ID: {hospital.id}")
    print(f"Hospital Name: {hospital.name}")
    print(f"Registration Number: {hospital.registration_number}")
    print(f"Address: {hospital.address}")
    print(f"Type: {hospital.get_hospital_type_display()}")
    print(f"Bed Capacity: {hospital.bed_capacity}")
    print(f"\n📋 Summary of created components:")
    print(f"• Hospital Licenses: {HospitalLicense.objects.filter(hospital=hospital).count()}")
    print(f"• Insurance Contracts: {HospitalInsuranceProvider.objects.filter(hospital=hospital).count()}")
    print(f"• Quality Certifications: {HospitalCertification.objects.filter(hospital=hospital).count()}")
    print(f"• Compliance Records: {HospitalCompliance.objects.filter(hospital=hospital).count()}")
    print(f"• Billing Integrations: {HospitalBillingIntegration.objects.filter(hospital=hospital).count()}")
    
    return hospital

if __name__ == "__main__":
    try:
        hospital = create_comprehensive_hospital()
        print("\n✅ Hospital creation completed successfully!")
    except Exception as e:
        print(f"\n❌ Error creating hospital: {str(e)}")
        import traceback
        traceback.print_exc()