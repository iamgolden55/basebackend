"""
Pharmacy Prescription Views

API endpoints for pharmacies to access patient prescriptions by HPN.
Implements NHS EPS-style patient-choice model with audit logging.

Industry Standards Implemented:
- NHS Electronic Prescription Service (EPS) - Patient-choice model
- PCN (Pharmacists Council of Nigeria) license verification
- Risk-based patient verification (NAFDAC schedules)
- Comprehensive audit trail
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import transaction
from django.utils import timezone
from django.db.models import Value
from django.db.models.functions import Replace, Upper

from api.permissions import IsPharmacist
from api.models.medical.medical_record import MedicalRecord
from api.models.medical.medication import Medication
from api.models.medical.pharmacy import PharmacyAccessLog
from api.models.drug.drug_classification import DrugClassification


def get_client_ip(request):
    """Extract client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsPharmacist])
def get_prescriptions_by_hpn(request):
    """
    Get all prescriptions for a patient by HPN.
    Includes comprehensive drug database information for safe dispensing.

    Industry Standard: NHS EPS Patient-Choice Model
    - Any pharmacy can access if patient is present
    - Mandatory pharmacy license verification (PCN)
    - Risk-based patient verification
    - Complete audit trail

    Query Parameters:
        hpn (required): Patient's Health Patient Number (format: XXX XXX XXX XXXX)
        status (optional): Filter by status (default: 'active')
            - active: Currently active prescriptions
            - all: All prescriptions (active, completed, discontinued)

    Returns:
        200: Success with prescriptions and drug database info
        400: Invalid HPN format or missing parameter
        403: Pharmacy license expired or access denied
        404: Patient not found
        500: Server error

    Audit Trail:
        All accesses are logged to PharmacyAccessLog for compliance
    """
    # Extract parameters
    hpn = request.GET.get('hpn', '').strip()
    status_filter = request.GET.get('status', 'active')

    # Normalize HPN - remove all spaces for flexible search
    # Accepts "ASA 289 843 1620" or "ASA2898431620"
    hpn_normalized = hpn.replace(' ', '').upper()

    # Validate HPN parameter
    if not hpn_normalized:
        return Response(
            {
                'error': 'HPN parameter is required',
                'message': 'Please provide the patient\'s Health Patient Number (HPN)'
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # Get pharmacist profile
    try:
        pharmacist = request.user.pharmacist_profile
    except AttributeError:
        return Response(
            {
                'error': 'Pharmacist profile not found',
                'message': 'Your account is not associated with a pharmacist profile'
            },
            status=status.HTTP_403_FORBIDDEN
        )

    # Verify pharmacy license (PCN standard)
    license_check = pharmacist.can_access_prescriptions()
    if not license_check['allowed']:
        return Response(
            {
                'error': 'Access denied',
                'message': license_check['reason'],
                'requires_action': 'license_renewal'
            },
            status=status.HTTP_403_FORBIDDEN
        )

    # Get pharmacy location - check both hospital affiliation AND practice page
    # Hospital pharmacists: Have hospital affiliation
    # Independent pharmacists: Have professional practice page
    pharmacy_location = None
    location_type = None

    if pharmacist.hospital:
        # Hospital pharmacist
        pharmacy_location = pharmacist.hospital
        location_type = 'hospital'
    elif hasattr(pharmacist.user, 'practice_page'):
        # Independent pharmacist with practice page
        try:
            pharmacy_location = pharmacist.user.practice_page
            location_type = 'practice_page'
        except AttributeError:
            pass

    if not pharmacy_location:
        return Response(
            {
                'error': 'Pharmacy location not found',
                'message': 'Your pharmacist profile is not associated with a pharmacy location. Please link your account to a hospital or create a professional practice page.',
                'suggestions': [
                    'Contact your hospital administrator to link your account',
                    'Create a professional practice page at /professional/practice-pages/create'
                ]
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # Find patient by HPN (flexible search - ignores spaces)
    # Searches for HPN by removing spaces from database values
    # This allows "ASA 289 843 1620" and "ASA2898431620" to both work
    try:
        medical_record = MedicalRecord.objects.annotate(
            hpn_normalized=Upper(Replace(Replace('hpn', Value(' '), Value('')), Value('\t'), Value('')))
        ).select_related('user').get(
            hpn_normalized=hpn_normalized
        )
    except MedicalRecord.DoesNotExist:
        # Log failed access attempt
        PharmacyAccessLog.objects.create(
            pharmacy=None,  # Pharmacy field optional (pharmacist may use practice page)
            pharmacist_user=request.user,
            patient_hpn=hpn,
            patient_user=None,
            access_type='search',
            access_granted=False,
            denial_reason='Patient HPN not found in system',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
        )

        return Response(
            {
                'error': 'Patient not found',
                'message': f'No patient found with HPN: {hpn}',
                'suggestions': [
                    'Verify the HPN number with the patient',
                    'Check for typos in the HPN entry',
                    'Ensure patient is registered in the PHB system'
                ]
            },
            status=status.HTTP_404_NOT_FOUND
        )

    # Get prescriptions with drug database info
    prescriptions_query = Medication.objects.filter(
        medical_record=medical_record
    ).select_related(
        'catalog_entry',  # Drug database
        'prescribed_by',  # Doctor
        'nominated_pharmacy',  # Nominated pharmacy
        'dispensed_by_pharmacy'  # Dispensing pharmacy
    ).prefetch_related(
        'catalog_entry__druginteraction_set'  # Drug interactions
    )

    # Filter by status
    if status_filter == 'active':
        prescriptions_query = prescriptions_query.filter(status='active', is_ongoing=True)
    elif status_filter != 'all':
        prescriptions_query = prescriptions_query.filter(status=status_filter)

    prescriptions = prescriptions_query.order_by('-start_date')

    # Build response with drug database information
    prescriptions_data = []
    prescription_ids = []
    controlled_count = 0

    for med in prescriptions:
        # Get drug database info if available
        drug_info = None
        is_controlled = False

        # Check controlled substance status (3 sources, OR logic):
        # 1. Doctor's manual override (highest priority)
        # 2. Drug database (catalog_entry)
        # 3. Pharmacy instructions keywords (fallback)

        if hasattr(med, 'is_controlled_override') and med.is_controlled_override:
            # Doctor manually marked as controlled
            is_controlled = True

        if med.catalog_entry:
            drug = med.catalog_entry

            # Check if controlled substance (use OR with override)
            if drug.is_controlled_substance:
                is_controlled = True

            drug_info = {
                'generic_name': drug.generic_name,
                'brand_names': drug.brand_names,

                # Regulatory Information
                'nafdac_approved': drug.nafdac_approved,
                'nafdac_schedule': drug.nafdac_schedule,
                'nafdac_schedule_display': drug.get_nafdac_schedule_display(),

                # Risk Flags
                'is_controlled': is_controlled,
                'is_high_risk': drug.is_high_risk,
                'risk_level': drug.get_risk_level(),

                # Prescribing Requirements
                'requires_photo_id': drug.requires_photo_id,
                'requires_special_prescription': drug.requires_special_prescription,
                'maximum_days_supply': drug.maximum_days_supply,

                # Monitoring
                'requires_monitoring': drug.requires_monitoring,
                'monitoring_type': drug.monitoring_type,
                'monitoring_frequency_days': drug.monitoring_frequency_days,

                # Safety Information
                'black_box_warning': drug.black_box_warning,
                'black_box_warning_text': drug.black_box_warning_text if drug.black_box_warning else None,
                'addiction_risk': drug.addiction_risk,
                'abuse_potential': drug.abuse_potential,

                # Age & Pregnancy
                'minimum_age': drug.minimum_age,
                'pregnancy_category': drug.pregnancy_category,
                'breastfeeding_safe': drug.breastfeeding_safe,

                # Interactions
                'major_contraindications': drug.major_contraindications,
                'major_drug_interactions': drug.major_drug_interactions,
                'food_interactions': drug.food_interactions,

                # Alternatives
                'safer_alternatives': drug.safer_alternatives,
                'cheaper_alternatives': drug.cheaper_alternatives,
            }
        else:
            # Fallback: Check pharmacy instructions for controlled substance keywords
            # This handles prescriptions without catalog_entry
            if med.pharmacy_instructions:
                controlled_keywords = [
                    'CONTROLLED SUBSTANCE',
                    'SCHEDULE 2', 'SCHEDULE 3', 'SCHEDULE 4',
                    'CONTROLLED DRUG',
                    'DEA SCHEDULE'
                ]
                pharmacy_text = med.pharmacy_instructions.upper()
                if any(keyword in pharmacy_text for keyword in controlled_keywords):
                    is_controlled = True

        # Count controlled substances (only once per prescription)
        if is_controlled:
            controlled_count += 1

        # Build prescription data
        prescription_data = {
            'id': str(med.id),
            'medication_name': med.medication_name,
            'generic_name': med.generic_name,
            'strength': med.strength,
            'form': med.form,
            'route': med.route,
            'dosage': med.dosage,
            'frequency': med.frequency,

            # Dates
            'start_date': med.start_date.isoformat(),
            'end_date': med.end_date.isoformat() if med.end_date else None,
            'is_ongoing': med.is_ongoing,

            # Instructions
            'patient_instructions': med.patient_instructions,
            'pharmacy_instructions': med.pharmacy_instructions,
            'indication': med.indication,

            # Prescription Management
            'prescription_number': med.prescription_number,
            'refills_authorized': med.refills_authorized,
            'refills_remaining': med.refills_remaining,

            # Status
            'status': med.status,
            'priority': med.priority,

            # Controlled Substance
            'is_controlled_override': getattr(med, 'is_controlled_override', False),

            # Provider
            'prescribed_by': {
                'name': med.prescribed_by.user.get_full_name() if med.prescribed_by else 'Unknown',
                'specialization': med.prescribed_by.specialization if med.prescribed_by and hasattr(med.prescribed_by, 'specialization') else None
            } if med.prescribed_by else None,

            # Nomination
            'nominated_pharmacy': {
                'name': med.nominated_pharmacy.name if med.nominated_pharmacy else None,
                'code': med.nominated_pharmacy.phb_pharmacy_code if med.nominated_pharmacy else None
            } if med.nominated_pharmacy else None,

            # Dispensing
            'dispensed': med.dispensed,
            'dispensed_at': med.dispensed_at.isoformat() if med.dispensed_at else None,
            'dispensed_by_pharmacy': {
                'name': med.dispensed_by_pharmacy.name if med.dispensed_by_pharmacy else None
            } if med.dispensed_by_pharmacy else None,

            # Security
            'nonce': str(med.nonce) if med.nonce else None,
            'signature': med.signature,

            # Drug Database Info (comprehensive)
            'drug_info': drug_info
        }

        prescriptions_data.append(prescription_data)
        prescription_ids.append(str(med.id))

    # Log successful access (audit trail)
    PharmacyAccessLog.objects.create(
        pharmacy=None,  # Pharmacy field optional (pharmacist may use practice page)
        pharmacist_user=request.user,
        patient_hpn=hpn,
        patient_user=medical_record.user,
        access_type='view',
        prescriptions_accessed=prescription_ids,
        prescription_count=len(prescription_ids),
        controlled_substance_count=controlled_count,
        access_granted=True,
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
    )

    # Build response
    response_data = {
        'success': True,
        'patient': {
            'hpn': hpn,
            'name': medical_record.user.get_full_name() if medical_record.user else 'Unknown',
            'blood_type': medical_record.blood_type,
            'allergies': medical_record.allergies,
            'chronic_conditions': medical_record.chronic_conditions,
            'is_high_risk': medical_record.is_high_risk,
        },
        'prescriptions': prescriptions_data,
        'summary': {
            'total_prescriptions': len(prescriptions_data),
            'controlled_substances': controlled_count,
            'requires_enhanced_verification': controlled_count > 0,
        },
        'verification_required': {
            'level_1_basic': True,  # Always required: HPN + Name
            'level_2_government_id': controlled_count > 0,  # Required for controlled substances
            'level_3_prescriber_contact': False  # Reserved for high-risk cases
        },
        'accessed_at': timezone.now().isoformat(),
        'accessed_by': {
            'pharmacist': pharmacist.user.get_full_name(),
            'license_number': pharmacist.pharmacy_license_number,
            'pharmacy': pharmacy_location.practice_name if location_type == 'practice_page' else (pharmacy_location.name if hasattr(pharmacy_location, 'name') else pharmacy_location.__str__())
        }
    }

    return Response(response_data, status=status.HTTP_200_OK)
