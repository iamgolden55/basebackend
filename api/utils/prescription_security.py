"""
Prescription Security Utilities

Provides cryptographic signing and verification for prescriptions
to prevent fraud and ensure authenticity.
"""
import hmac
import hashlib
import json
from typing import Dict, Any, Optional
from django.conf import settings
from datetime import datetime, timedelta


def get_secret_key() -> bytes:
    """
    Get the secret key for HMAC signing.
    Uses Django SECRET_KEY for consistency.
    """
    return settings.SECRET_KEY.encode('utf-8')


def generate_prescription_payload(medication) -> Dict[str, Any]:
    """
    Generate the canonical prescription payload for signing.

    Args:
        medication: Medication model instance

    Returns:
        Dictionary containing prescription data to be signed
    """
    patient = medication.medical_record.user

    # Build pharmacy data if available
    pharmacy_data = None
    if medication.nominated_pharmacy:
        pharmacy_data = {
            'name': medication.nominated_pharmacy.name,
            'code': medication.nominated_pharmacy.phb_pharmacy_code,
            'address': medication.nominated_pharmacy.address_line_1,
            'city': medication.nominated_pharmacy.city,
            'postcode': medication.nominated_pharmacy.postcode,
            'phone': medication.nominated_pharmacy.phone
        }

    # Get prescriber name
    prescriber_name = 'Unknown Prescriber'
    if medication.prescribed_by:
        prescriber_name = f"Dr. {medication.prescribed_by.user.get_full_name()}"

    # Calculate expiry (30 days from creation)
    expiry_date = medication.created_at + timedelta(days=30)

    payload = {
        'type': 'PHB_PRESCRIPTION',
        'id': f"PHB-RX-{str(medication.id).zfill(8)}",
        'nonce': str(medication.nonce),
        'hpn': patient.hpn,
        'medication': medication.medication_name,
        'strength': medication.strength,
        'patient': patient.get_full_name(),
        'prescriber': prescriber_name,
        'dosage': medication.dosage,
        'frequency': medication.frequency or 'As directed',
        'pharmacy': pharmacy_data,
        'issued': medication.created_at.isoformat(),
        'expiry': expiry_date.isoformat()
    }

    return payload


def generate_signature(payload: Dict[str, Any]) -> str:
    """
    Generate HMAC-SHA256 signature for prescription data.

    Args:
        payload: Dictionary containing prescription data

    Returns:
        Hex-encoded signature string
    """
    # Sort keys to ensure consistent ordering
    canonical_payload = json.dumps(payload, sort_keys=True)

    # Generate HMAC signature
    signature = hmac.new(
        get_secret_key(),
        canonical_payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    return signature


def verify_signature(payload: Dict[str, Any], provided_signature: str) -> bool:
    """
    Verify HMAC-SHA256 signature for prescription data.

    Args:
        payload: Dictionary containing prescription data
        provided_signature: Signature to verify

    Returns:
        True if signature is valid, False otherwise
    """
    expected_signature = generate_signature(payload)

    # Use constant-time comparison to prevent timing attacks
    return hmac.compare_digest(expected_signature, provided_signature)


def sign_prescription(medication) -> tuple[Dict[str, Any], str]:
    """
    Generate prescription payload and signature.

    Args:
        medication: Medication model instance

    Returns:
        Tuple of (payload, signature)
    """
    payload = generate_prescription_payload(medication)
    signature = generate_signature(payload)

    # Store signature in medication for future verification
    if not medication.signature:
        medication.signature = signature
        medication.save(update_fields=['signature'])

    return payload, signature


def verify_prescription(
    payload: Dict[str, Any],
    signature: str,
    check_expiry: bool = True,
    check_dispensed: bool = True
) -> Dict[str, Any]:
    """
    Comprehensive prescription verification.

    Args:
        payload: Prescription data from QR code
        signature: Provided signature
        check_expiry: Whether to check if prescription is expired
        check_dispensed: Whether to check if already dispensed

    Returns:
        Dictionary with verification results:
        {
            'valid': bool,
            'reason': str,
            'details': dict
        }
    """
    from api.models import Medication

    # Step 1: Verify signature
    if not verify_signature(payload, signature):
        return {
            'valid': False,
            'reason': 'Invalid signature - possible forgery',
            'details': {'step_failed': 'signature_verification'}
        }

    # Step 2: Extract prescription ID and nonce
    try:
        prescription_id_str = payload.get('id', '')
        # Extract numeric ID from "PHB-RX-00000123" format
        prescription_id = int(prescription_id_str.split('-')[-1])
        nonce_str = payload.get('nonce')
    except (ValueError, IndexError):
        return {
            'valid': False,
            'reason': 'Invalid prescription ID format',
            'details': {'step_failed': 'id_parsing'}
        }

    # Step 3: Lookup prescription in database
    try:
        medication = Medication.objects.select_related(
            'medical_record__user',
            'nominated_pharmacy',
            'dispensed_by_pharmacy'
        ).get(id=prescription_id)
    except Medication.DoesNotExist:
        return {
            'valid': False,
            'reason': 'Prescription not found in database',
            'details': {'step_failed': 'database_lookup'}
        }

    # Step 4: Verify nonce matches
    if str(medication.nonce) != nonce_str:
        return {
            'valid': False,
            'reason': 'Nonce mismatch - prescription data tampered',
            'details': {'step_failed': 'nonce_verification'}
        }

    # Step 5: Check expiry (30 days from issue)
    if check_expiry:
        expiry_date = datetime.fromisoformat(payload.get('expiry'))
        if datetime.now() > expiry_date:
            return {
                'valid': False,
                'reason': 'Prescription expired',
                'details': {
                    'step_failed': 'expiry_check',
                    'expiry_date': expiry_date.isoformat()
                }
            }

    # Step 6: Check if already dispensed
    if check_dispensed and medication.dispensed:
        return {
            'valid': False,
            'reason': 'Prescription already dispensed',
            'details': {
                'step_failed': 'dispensing_check',
                'dispensed_at': medication.dispensed_at.isoformat() if medication.dispensed_at else None,
                'dispensed_by': medication.dispensed_by_pharmacy.name if medication.dispensed_by_pharmacy else None
            }
        }

    # All checks passed
    return {
        'valid': True,
        'reason': 'Prescription verified successfully',
        'details': {
            'prescription_id': prescription_id,
            'patient_name': medication.medical_record.user.get_full_name(),
            'medication': medication.medication_name,
            'dosage': medication.dosage,
            'frequency': medication.frequency,
            'patient_hpn': medication.medical_record.user.hpn,
            'dispensed': medication.dispensed,
            'nominated_pharmacy': medication.nominated_pharmacy.name if medication.nominated_pharmacy else None
        }
    }


def log_verification_attempt(
    medication,
    pharmacy_id: Optional[int],
    pharmacy_name: str,
    success: bool,
    reason: str,
    ip_address: Optional[str] = None
) -> None:
    """
    Log a verification attempt for audit trail.

    Args:
        medication: Medication instance
        pharmacy_id: ID of pharmacy attempting verification
        pharmacy_name: Name of pharmacy
        success: Whether verification succeeded
        reason: Reason for success/failure
        ip_address: Optional IP address of request
    """
    attempt = {
        'timestamp': datetime.now().isoformat(),
        'pharmacy_id': pharmacy_id,
        'pharmacy_name': pharmacy_name,
        'success': success,
        'reason': reason,
        'ip_address': ip_address
    }

    # Append to verification log
    if medication.verification_attempts is None:
        medication.verification_attempts = []

    medication.verification_attempts.append(attempt)
    medication.save(update_fields=['verification_attempts'])
