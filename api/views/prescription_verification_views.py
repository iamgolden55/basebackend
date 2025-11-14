"""
Prescription Verification API Views

Endpoints for pharmacies to verify and dispense prescriptions securely.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from django.utils import timezone
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import JsonResponse
import json

from api.models import Medication, Pharmacy
from api.utils.prescription_security import (
    verify_prescription,
    log_verification_attempt,
    sign_prescription
)


def get_client_ip(request):
    """Extract client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@csrf_exempt
def verify_prescription_qr(request):
    """
    Public endpoint for pharmacy QR code verification.
    No authentication required.

    This is a pure Django view (not DRF) to completely bypass authentication middleware.

    This endpoint is called when a pharmacy scans a prescription QR code.
    It performs comprehensive verification including signature check,
    expiry check, and dispensing status check.

    Request body:
    {
        "payload": {...},  // QR code data
        "signature": "...",  // HMAC signature
        "pharmacy_code": "PHB-PH-001234",  // Optional: pharmacy identifier
        "pharmacy_name": "City Pharmacy"   // Optional: pharmacy name
    }

    Response:
    {
        "valid": true/false,
        "reason": "...",
        "details": {...}
    }
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.info("=== VERIFY PRESCRIPTION ENDPOINT CALLED (Pure Django View) ===")

    # Only allow POST requests
    if request.method != 'POST':
        return JsonResponse(
            {'valid': False, 'reason': 'Method not allowed'},
            status=405
        )

    try:
        # Parse JSON body
        data = json.loads(request.body)
        payload = data.get('payload')
        signature = data.get('signature')
        pharmacy_code = data.get('pharmacy_code')
        pharmacy_name = data.get('pharmacy_name', 'Unknown Pharmacy')

        logger.info(f"Verification request - Pharmacy: {pharmacy_name}, Code: {pharmacy_code}")

        # Validate request
        if not payload or not signature:
            return JsonResponse(
                {
                    'valid': False,
                    'reason': 'Missing required fields: payload and signature'
                },
                status=400
            )

        # Perform verification
        result = verify_prescription(
            payload=payload,
            signature=signature,
            check_expiry=True,
            check_dispensed=True
        )

        logger.info(f"Verification result: {result['valid']} - {result['reason']}")

        # Log verification attempt
        if result.get('details', {}).get('prescription_id'):
            try:
                medication = Medication.objects.get(
                    id=result['details']['prescription_id']
                )

                # Get pharmacy ID if code provided
                pharmacy_id = None
                if pharmacy_code:
                    try:
                        pharmacy = Pharmacy.objects.get(phb_pharmacy_code=pharmacy_code)
                        pharmacy_id = pharmacy.id
                        pharmacy_name = pharmacy.name
                    except Pharmacy.DoesNotExist:
                        logger.warning(f"Pharmacy not found: {pharmacy_code}")

                log_verification_attempt(
                    medication=medication,
                    pharmacy_id=pharmacy_id,
                    pharmacy_name=pharmacy_name,
                    success=result['valid'],
                    reason=result['reason'],
                    ip_address=get_client_ip(request)
                )
            except Medication.DoesNotExist:
                logger.error(f"Medication not found: {result['details'].get('prescription_id')}")

        return JsonResponse(result, status=200)

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in request body: {str(e)}")
        return JsonResponse(
            {'valid': False, 'reason': 'Invalid JSON in request body'},
            status=400
        )
    except Exception as e:
        logger.error(f"Verification error: {str(e)}", exc_info=True)
        return JsonResponse(
            {'valid': False, 'reason': f'Server error: {str(e)}'},
            status=500
        )


@csrf_exempt
def dispense_prescription(request):
    """
    Mark a prescription as dispensed.

    Pure Django view (not DRF) to bypass authentication middleware.

    This endpoint is called after a pharmacy has verified a prescription
    and is ready to dispense it to the patient.

    Request body:
    {
        "prescription_id": "PHB-RX-00000123",
        "nonce": "uuid-string",
        "pharmacy_code": "PHB-PH-001234",
        "pharmacist_name": "John Smith",
        "verification_notes": "Patient ID verified"
    }

    Response:
    {
        "success": true/false,
        "message": "...",
        "details": {...}
    }
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.info("=== DISPENSE PRESCRIPTION ENDPOINT CALLED ===")

    # Only allow POST requests
    if request.method != 'POST':
        return JsonResponse(
            {'success': False, 'message': 'Method not allowed'},
            status=405
        )

    try:
        # Parse JSON body
        data = json.loads(request.body)
        prescription_id_str = data.get('prescription_id')
        nonce_str = data.get('nonce')
        pharmacy_code = data.get('pharmacy_code')
        pharmacist_name = data.get('pharmacist_name')
        verification_notes = data.get('verification_notes', '')

        logger.info(f"Dispense request - Prescription: {prescription_id_str}, Pharmacy: {pharmacy_code}")

        # Validate required fields (pharmacy_code is optional for practice page pharmacists)
        if not all([prescription_id_str, nonce_str, pharmacist_name]):
            return JsonResponse(
                {
                    'success': False,
                    'message': 'Missing required fields: prescription_id, nonce, and pharmacist_name are required'
                },
                status=400
            )

        try:
            # Extract numeric ID
            prescription_id = int(prescription_id_str.split('-')[-1])
        except (ValueError, IndexError):
            return JsonResponse(
                {
                    'success': False,
                    'message': 'Invalid prescription ID format'
                },
                status=400
            )

        # Lookup pharmacy (optional - may be None for practice page pharmacists)
        pharmacy = None
        pharmacy_name = pharmacist_name  # Default to pharmacist name

        if pharmacy_code:
            try:
                pharmacy = Pharmacy.objects.get(phb_pharmacy_code=pharmacy_code)
                pharmacy_name = pharmacy.name
            except Pharmacy.DoesNotExist:
                # Pharmacy code provided but not found - this is OK for practice pages
                logger.warning(f"Pharmacy code provided but not found: {pharmacy_code}")
                pharmacy_name = pharmacy_code

        # Lookup prescription
        try:
            medication = Medication.objects.select_related(
                'medical_record__user',
                'nominated_pharmacy'
            ).get(id=prescription_id)
        except Medication.DoesNotExist:
            return JsonResponse(
                {
                    'success': False,
                    'message': 'Prescription not found'
                },
                status=404
            )

        # Verify nonce
        if str(medication.nonce) != nonce_str:
            log_verification_attempt(
                medication=medication,
                pharmacy_id=pharmacy.id if pharmacy else None,
                pharmacy_name=pharmacy_name,
                success=False,
                reason='Nonce mismatch during dispensing',
                ip_address=get_client_ip(request)
            )

            logger.warning(f"Nonce mismatch for prescription {prescription_id}")
            return JsonResponse(
                {
                    'success': False,
                    'message': 'Invalid verification token - prescription data may be tampered'
                },
                status=400
            )

        # Check if already dispensed
        if medication.dispensed:
            return JsonResponse(
                {
                    'success': False,
                    'message': 'Prescription already dispensed',
                    'details': {
                        'dispensed_at': medication.dispensed_at.isoformat() if medication.dispensed_at else None,
                        'dispensed_by': medication.dispensed_by_pharmacy.name if medication.dispensed_by_pharmacy else None,
                        'pharmacist': medication.dispensing_pharmacist_name
                    }
                },
                status=400
            )

        # Check expiry (30 days from creation)
        expiry_date = medication.created_at + timezone.timedelta(days=30)
        if timezone.now() > expiry_date:
            return JsonResponse(
                {
                    'success': False,
                    'message': 'Prescription expired',
                    'details': {
                        'expiry_date': expiry_date.isoformat()
                    }
                },
                status=400
            )

        # Mark as dispensed
        with transaction.atomic():
            medication.dispensed = True
            medication.dispensed_at = timezone.now()
            medication.dispensed_by_pharmacy = pharmacy
            medication.dispensing_pharmacist_name = pharmacist_name

            # Update status to completed
            if medication.status == 'active':
                medication.status = 'completed'

            medication.save()

            # Log successful dispensing
            log_verification_attempt(
                medication=medication,
                pharmacy_id=pharmacy.id if pharmacy else None,
                pharmacy_name=pharmacy_name,
                success=True,
                reason=f'Prescription dispensed successfully. {verification_notes}',
                ip_address=get_client_ip(request)
            )

        logger.info(f"Successfully dispensed prescription {prescription_id}")

        return JsonResponse(
            {
                'success': True,
                'message': 'Prescription dispensed successfully',
                'details': {
                    'prescription_id': prescription_id_str,
                    'patient_name': medication.medical_record.user.get_full_name(),
                    'medication': medication.medication_name,
                    'dispensed_at': medication.dispensed_at.isoformat(),
                    'dispensed_by': pharmacy_name,
                    'pharmacist': pharmacist_name
                }
            },
            status=200
        )

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in request body: {str(e)}")
        return JsonResponse(
            {'success': False, 'message': 'Invalid JSON in request body'},
            status=400
        )
    except Exception as e:
        logger.error(f"Dispense error: {str(e)}", exc_info=True)
        return JsonResponse(
            {'success': False, 'message': f'Server error: {str(e)}'},
            status=500
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def regenerate_prescription_signature(request, prescription_id):
    """
    Regenerate signature for an existing prescription.

    This is useful for prescriptions created before the security system
    was implemented, or if the signature needs to be refreshed.

    Only the prescription owner or staff can regenerate signatures.
    """
    try:
        medication = Medication.objects.select_related(
            'medical_record__user'
        ).get(id=prescription_id)
    except Medication.DoesNotExist:
        return Response(
            {'error': 'Prescription not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Check permissions
    if not (
        request.user == medication.medical_record.user or
        request.user.is_staff
    ):
        return Response(
            {'error': 'Permission denied'},
            status=status.HTTP_403_FORBIDDEN
        )

    # Generate new signature
    payload, signature = sign_prescription(medication)

    return Response(
        {
            'message': 'Signature regenerated successfully',
            'prescription_id': f"PHB-RX-{str(medication.id).zfill(8)}",
            'nonce': str(medication.nonce),
            'signature': signature
        },
        status=status.HTTP_200_OK
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_prescription_verification_log(request, prescription_id):
    """
    Get verification log for a prescription.

    Only accessible by prescription owner or staff.
    Returns all verification attempts for audit purposes.
    """
    try:
        medication = Medication.objects.select_related(
            'medical_record__user'
        ).get(id=prescription_id)
    except Medication.DoesNotExist:
        return Response(
            {'error': 'Prescription not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Check permissions
    if not (
        request.user == medication.medical_record.user or
        request.user.is_staff
    ):
        return Response(
            {'error': 'Permission denied'},
            status=status.HTTP_403_FORBIDDEN
        )

    return Response(
        {
            'prescription_id': f"PHB-RX-{str(medication.id).zfill(8)}",
            'patient_name': medication.medical_record.user.get_full_name(),
            'medication': medication.medication_name,
            'dispensed': medication.dispensed,
            'dispensed_at': medication.dispensed_at.isoformat() if medication.dispensed_at else None,
            'dispensed_by': medication.dispensed_by_pharmacy.name if medication.dispensed_by_pharmacy else None,
            'verification_attempts': medication.verification_attempts or []
        },
        status=status.HTTP_200_OK
    )
