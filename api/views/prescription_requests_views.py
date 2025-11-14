"""
Prescription Request API Views

Endpoints for patients to request prescriptions and doctors to approve/reject them.
Implements NHS-style prescription request system with email notifications.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db import transaction
from datetime import timedelta
import logging
import uuid

from api.models import CustomUser, Medication, Pharmacy, Doctor, Hospital, PrescriptionRequest, PrescriptionRequestItem, Pharmacist, MedicalRecord
from api.models.drug.drug_classification import DrugClassification
from api.utils.email import (
    send_prescription_request_confirmation,
    send_prescription_request_to_doctors,
    send_prescription_approved_notification,
    send_prescription_rejected_notification,
    send_prescription_request_to_pharmacist,
    send_prescription_escalation_to_physician,
    send_controlled_substance_alert
)
from api.utils.prescription_triage import assign_prescription_request
from api.utils.prescription_security import sign_prescription

logger = logging.getLogger(__name__)


def generate_request_reference():
    """Generate unique prescription request reference number"""
    # Format: REQ-XXXXXX (6 random characters)
    return f"REQ-{uuid.uuid4().hex[:6].upper()}"


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_prescription_request(request):
    """
    Create a new prescription request from patient.

    Request body:
    {
        "medications": [
            {
                "medication_id": "123",  // Optional: for repeat prescriptions
                "medication_name": "Amoxicillin",
                "strength": "500mg",
                "form": "capsule",
                "quantity": 21,
                "dosage": "Take 1 capsule three times daily",
                "is_repeat": true,
                "reason": "Refill needed"  // Required for new medications
            }
        ],
        "request_type": "repeat",  // "repeat" | "new" | "dosage_change"
        "urgency": "routine",  // "routine" | "urgent"
        "additional_notes": "Running low on medication",
        "nominated_pharmacy_id": 5
    }

    Response:
    {
        "id": "uuid",
        "request_reference": "REQ-ABC123",
        "status": "REQUESTED",
        "request_date": "2025-11-01T10:30:00Z",
        "medications": [...],
        "pharmacy": {...},
        "message": "Prescription request submitted successfully"
    }
    """
    try:
        patient = request.user

        # Debug logging
        logger.info(f"Prescription request received from user: {patient.email}")
        logger.info(f"Request data: {request.data}")

        # Validate patient has hospital (field is called 'hospital', not 'primary_hospital')
        if not hasattr(patient, 'hospital') or not patient.hospital:
            logger.warning(f"User {patient.email} has no hospital set")
            return Response(
                {
                    'error': 'You must be registered with a hospital to request prescriptions',
                    'code': 'NO_HOSPITAL'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        hospital = patient.hospital
        logger.info(f"User hospital: {hospital.name}")

        # Extract request data
        medications_data = request.data.get('medications', [])
        request_type = request.data.get('request_type', 'repeat')
        urgency_level = request.data.get('urgency', 'routine')
        additional_notes = request.data.get('additional_notes', '')
        pharmacy_id = request.data.get('nominated_pharmacy_id')

        logger.info(f"Medications count: {len(medications_data)}")
        logger.info(f"Request type: {request_type}, Urgency: {urgency_level}")

        # Validate medications list
        if not medications_data or len(medications_data) == 0:
            logger.warning("No medications provided in request")
            return Response(
                {'error': 'At least one medication must be requested'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate pharmacy if provided
        pharmacy = None
        if pharmacy_id:
            try:
                pharmacy = Pharmacy.objects.get(id=pharmacy_id)
            except Pharmacy.DoesNotExist:
                return Response(
                    {'error': 'Invalid pharmacy ID'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Generate unique request reference
        request_reference = generate_request_reference()

        # Create PrescriptionRequest model instance
        with transaction.atomic():
            prescription_request = PrescriptionRequest.objects.create(
                patient=patient,
                hospital=hospital,
                request_reference=request_reference,
                request_type=request_type,
                urgency=urgency_level,
                status='REQUESTED',
                additional_notes=additional_notes,
                pharmacy=pharmacy,
                request_date=timezone.now()
            )

            # Create request items for each medication
            for med_data in medications_data:
                PrescriptionRequestItem.objects.create(
                    request=prescription_request,
                    medication_name=med_data['medication_name'],
                    strength=med_data.get('strength', ''),
                    form=med_data.get('form', ''),
                    quantity=med_data.get('quantity', 0),
                    dosage=med_data.get('dosage', ''),
                    is_repeat=med_data.get('is_repeat', False),
                    reason=med_data.get('reason', '')
                )

            # ==================== PHARMACIST TRIAGE LOGIC ====================
            # Automatically categorize and assign prescription request
            logger.info(f"Running triage for prescription request {request_reference}")
            triage_result = assign_prescription_request(prescription_request)

            if triage_result['assigned']:
                # Update prescription request with assignment
                prescription_request.triage_category = triage_result['triage_category']
                prescription_request.triage_reason = triage_result['triage_reason']
                prescription_request.assigned_to_role = triage_result['assigned_to_role']

                if triage_result['assigned_to_role'] == 'pharmacist':
                    prescription_request.assigned_to_pharmacist = triage_result['assigned_to']
                elif triage_result['assigned_to_role'] == 'doctor':
                    prescription_request.assigned_to_doctor = triage_result['assigned_to']

                prescription_request.save()
                logger.info(f"✅ Triage complete: {triage_result['message']}")
            else:
                logger.warning(f"⚠️ Triage assignment failed: {triage_result['message']}")
                # Continue with old flow (notify all doctors) if triage fails

        # Prepare medication list for emails
        medications_for_email = []
        for med in medications_data:
            medications_for_email.append({
                'name': med['medication_name'],
                'strength': med.get('strength', ''),
                'form': med.get('form', ''),
                'is_repeat': med.get('is_repeat', False),
                'reason': med.get('reason', '')
            })

        # Calculate expected processing days
        expected_days = "1-3" if urgency_level == 'urgent' else "7-10"

        # Send confirmation email to patient
        try:
            patient_name = patient.get_full_name() if hasattr(patient, 'get_full_name') else patient.email
            pharmacy_name = pharmacy.name if pharmacy else "Your nominated pharmacy"
            pharmacy_address = f"{pharmacy.address_line_1}, {pharmacy.city}, {pharmacy.postcode}" if pharmacy else ""

            send_prescription_request_confirmation(
                patient_email=patient.email,
                patient_name=patient_name,
                request_reference=request_reference,
                medications=medications_for_email,
                urgency=urgency_level,
                expected_days=expected_days,
                pharmacy_name=pharmacy_name,
                pharmacy_address=pharmacy_address,
                hospital_name=hospital.name,
                request_date=timezone.now()
            )
            logger.info(f"Confirmation email sent to patient {patient.email}")
        except Exception as e:
            logger.error(f"Failed to send patient confirmation email: {str(e)}")
            # Don't fail the request if email fails

        # Send notification based on triage assignment
        try:
            patient_dob = patient.date_of_birth.strftime('%d %B, %Y') if hasattr(patient, 'date_of_birth') and patient.date_of_birth else 'Not available'
            patient_age = calculate_age(patient.date_of_birth) if hasattr(patient, 'date_of_birth') and patient.date_of_birth else 'Unknown'
            allergies = patient.allergies if hasattr(patient, 'allergies') and patient.allergies else None
            patient_hpn = patient.hpn if hasattr(patient, 'hpn') else 'Not available'
            current_medications = patient.current_medications if hasattr(patient, 'current_medications') else None

            # Prepare detailed medication list for professional emails
            professional_medications = []
            for med_item in prescription_request.medications.all():
                professional_medications.append({
                    'name': med_item.medication_name,
                    'strength': med_item.strength or '',
                    'form': med_item.form or '',
                    'quantity': med_item.quantity,
                    'dosage': med_item.dosage or '',
                    'is_repeat': med_item.is_repeat,
                    'reason': med_item.reason or ''
                })

            if triage_result['assigned'] and triage_result['assigned_to_role'] == 'pharmacist':
                # Send notification to assigned pharmacist
                pharmacist = triage_result['assigned_to']
                pharmacist_email = pharmacist.professional_email or pharmacist.user.email

                send_prescription_request_to_pharmacist(
                    pharmacist_email=pharmacist_email,
                    pharmacist_name=pharmacist.get_full_name(),
                    patient_name=patient_name,
                    patient_hpn=patient_hpn,
                    patient_dob=patient_dob,
                    patient_age=patient_age,
                    request_reference=request_reference,
                    request_date=timezone.now().strftime('%d %B, %Y at %H:%M'),
                    urgency=urgency_level,
                    medications=professional_medications,
                    pharmacy_name=pharmacy_name,
                    pharmacy_address=pharmacy_address,
                    triage_category=triage_result['triage_category'],
                    triage_reason=triage_result['triage_reason'],
                    allergies=allergies,
                    current_medications=current_medications,
                    request_notes=additional_notes
                )
                logger.info(f"✅ Pharmacist notification sent to {pharmacist.get_full_name()} ({pharmacist_email})")

            elif triage_result['assigned'] and triage_result['assigned_to_role'] == 'doctor':
                # Send notification to assigned doctor (specialist or high-risk case)
                doctor = triage_result['assigned_to']
                doctor_email = doctor.user.email

                # Use old function for doctor notification (to be replaced with escalation template later)
                email_result = send_prescription_request_to_doctors(
                    hospital_id=hospital.id,
                    request_reference=request_reference,
                    patient_name=patient_name,
                    patient_hpn=patient_hpn,
                    patient_dob=patient_dob,
                    patient_age=patient_age,
                    allergies=allergies,
                    medications=medications_for_email,
                    urgency=urgency_level,
                    request_notes=additional_notes,
                    pharmacy_name=pharmacy_name,
                    pharmacy_address=pharmacy_address,
                    request_date=timezone.now()
                )
                logger.info(f"✅ Direct physician notification sent (specialist/high-risk case)")

            else:
                # Fallback: notify all prescribing doctors (old behavior)
                logger.warning("⚠️ Triage failed, falling back to old notification method")
                email_result = send_prescription_request_to_doctors(
                    hospital_id=hospital.id,
                    request_reference=request_reference,
                    patient_name=patient_name,
                    patient_hpn=patient_hpn,
                    patient_dob=patient_dob,
                    patient_age=patient_age,
                    allergies=allergies,
                    medications=medications_for_email,
                    urgency=urgency_level,
                    request_notes=additional_notes,
                    pharmacy_name=pharmacy_name,
                    pharmacy_address=pharmacy_address,
                    request_date=timezone.now()
                )

                if email_result['success']:
                    logger.info(f"Notified {email_result['doctors_notified']} doctors about prescription request {request_reference}")
                else:
                    logger.warning(f"Failed to notify doctors: {email_result.get('error')}")

        except Exception as e:
            logger.error(f"Failed to send professional notification emails: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            # Don't fail the request if email fails

        # TODO: Create in-app notifications for doctors
        # try:
        #     doctors = Doctor.objects.filter(
        #         hospital=hospital,
        #         can_prescribe=True,
        #         user__is_active=True
        #     )
        #
        #     for doctor in doctors:
        #         Notification.objects.create(
        #             user=doctor.user,
        #             type='PRESCRIPTION_REQUEST',
        #             title='New Prescription Request',
        #             message=f'{patient_name} requested prescription',
        #             priority='URGENT' if urgency_level == 'urgent' else 'NORMAL',
        #             data={'request_reference': request_reference}
        #         )
        # except Exception as e:
        #     logger.error(f"Failed to create in-app notifications: {str(e)}")

        # Build response
        response_data = {
            'id': str(prescription_request.id),
            'request_reference': request_reference,
            'status': 'REQUESTED',
            'request_date': prescription_request.request_date.isoformat(),
            'medications': medications_data,
            'message': 'Prescription request submitted successfully'
        }

        if pharmacy:
            response_data['pharmacy'] = {
                'id': pharmacy.id,
                'phb_pharmacy_code': pharmacy.phb_pharmacy_code,
                'name': pharmacy.name,
                'address_line_1': pharmacy.address_line_1,
                'city': pharmacy.city,
                'postcode': pharmacy.postcode,
                'phone': pharmacy.phone,
                'electronic_prescriptions_enabled': pharmacy.electronic_prescriptions_enabled
            }

        logger.info(f"Prescription request created: {request_reference} for patient {patient.email}")

        return Response(response_data, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(f"Error creating prescription request: {str(e)}", exc_info=True)
        return Response(
            {
                'error': 'Failed to create prescription request',
                'details': str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def calculate_age(birth_date):
    """Calculate age from birth date"""
    if not birth_date:
        return None

    today = timezone.now().date()
    age = today.year - birth_date.year

    # Adjust if birthday hasn't occurred this year
    if today.month < birth_date.month or (today.month == birth_date.month and today.day < birth_date.day):
        age -= 1

    return age


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_prescription_requests(request):
    """
    Get prescription request history for current patient.

    Query params:
    - status: Filter by status (REQUESTED, APPROVED, REJECTED, etc.)
    - limit: Number of results to return

    Response:
    {
        "status": "success",
        "requests": [
            {
                "id": "uuid",
                "request_reference": "REQ-ABC123",
                "status": "REQUESTED",
                "request_date": "2025-11-01T10:30:00Z",
                "medications": [...],
                "urgency": "routine"
            }
        ],
        "total_count": 10
    }
    """
    # TODO: Implement once PrescriptionRequest model is created
    return Response(
        {
            'status': 'success',
            'requests': [],
            'total_count': 0,
            'message': 'Prescription request history endpoint - to be implemented with database model'
        },
        status=status.HTTP_200_OK
    )

# =====================================================================
# PROFESSIONAL ENDPOINTS (For Doctors)
# =====================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_doctor_prescription_requests(request):
    """
    Get prescription requests for doctor's hospital (Professional endpoint).

    Query params:
    - status: Filter by status (REQUESTED, APPROVED, REJECTED, ALL)

    Response:
    {
        "status": "success",
        "requests": [...],
        "pending_count": 5,
        "urgent_count": 2,
        "total_count": 10
    }
    """
    try:
        # Verify user is a doctor
        if not hasattr(request.user, 'doctor_profile'):
            return Response(
                {'error': 'Only doctors can access prescription requests'},
                status=status.HTTP_403_FORBIDDEN
            )

        doctor = request.user.doctor_profile
        status_filter = request.GET.get('status', 'ALL')

        # Query prescription requests for doctor's hospital
        query = PrescriptionRequest.objects.filter(hospital=doctor.hospital)

        if status_filter and status_filter != 'ALL':
            query = query.filter(status=status_filter)

        # Get requests with related data
        requests = query.select_related('patient', 'hospital', 'pharmacy').prefetch_related('medications').order_by('-urgency', '-request_date')

        # Build response list
        request_list = []
        for req in requests:
            request_list.append({
                'id': str(req.id),
                'request_reference': req.request_reference,
                'patient_name': req.patient.get_full_name(),
                'patient_hpn': req.patient.hpn if hasattr(req.patient, 'hpn') else 'N/A',
                'patient_dob': req.patient.date_of_birth.strftime('%Y-%m-%d') if hasattr(req.patient, 'date_of_birth') and req.patient.date_of_birth else None,
                'patient_age': calculate_age(req.patient.date_of_birth) if hasattr(req.patient, 'date_of_birth') and req.patient.date_of_birth else None,
                'allergies': req.patient.allergies if hasattr(req.patient, 'allergies') else None,
                'status': req.status,
                'urgency': req.urgency,
                'request_date': req.request_date.isoformat(),
                'medications': [
                    {
                        'medication_name': med.medication_name,
                        'strength': med.strength,
                        'form': med.form,
                        'quantity': med.quantity,
                        'dosage': med.dosage,
                        'is_repeat': med.is_repeat,
                        'reason': med.reason
                    }
                    for med in req.medications.all()
                ],
                'additional_notes': req.additional_notes,
                'pharmacy': {
                    'name': req.pharmacy.name,
                    'address_line_1': req.pharmacy.address_line_1,
                    'city': req.pharmacy.city,
                    'postcode': req.pharmacy.postcode,
                    'phone': req.pharmacy.phone
                } if req.pharmacy else None
            })

        # Calculate counts
        pending_count = PrescriptionRequest.objects.filter(hospital=doctor.hospital, status='REQUESTED').count()
        urgent_count = PrescriptionRequest.objects.filter(hospital=doctor.hospital, status='REQUESTED', urgency='urgent').count()

        return Response({
            'status': 'success',
            'requests': request_list,
            'pending_count': pending_count,
            'urgent_count': urgent_count,
            'total_count': len(request_list),
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f'Error fetching doctor prescription requests: {str(e)}')
        return Response(
            {'error': 'Failed to fetch prescription requests'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_prescription_request_details(request, request_id):
    """
    Get detailed information about a specific prescription request.

    Response:
    {
        "id": "uuid",
        "request_reference": "REQ-ABC123",
        "patient": {
            "name": "John Smith",
            "hpn": "HPN-123456",
            "dob": "1985-05-15",
            "age": 39,
            "allergies": "Penicillin",
            "current_medications": [...]
        },
        "medications": [...],
        "urgency": "urgent",
        "request_date": "2025-11-01T10:30:00Z",
        "additional_notes": "Running low",
        "pharmacy": {...}
    }
    """
    try:
        # Verify user is a doctor
        if not hasattr(request.user, 'doctor_profile'):
            return Response(
                {'error': 'Only doctors can access prescription request details'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Fetch prescription request from database
        try:
            prescription_request = PrescriptionRequest.objects.select_related(
                'patient', 'hospital', 'pharmacy'
            ).prefetch_related('medications').get(id=request_id)
        except PrescriptionRequest.DoesNotExist:
            return Response(
                {'error': 'Prescription request not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Build response
        response_data = {
            'id': str(prescription_request.id),
            'request_reference': prescription_request.request_reference,
            'patient': {
                'name': prescription_request.patient.get_full_name(),
                'hpn': prescription_request.patient.hpn if hasattr(prescription_request.patient, 'hpn') else 'N/A',
                'dob': prescription_request.patient.date_of_birth.strftime('%d %B, %Y') if hasattr(prescription_request.patient, 'date_of_birth') and prescription_request.patient.date_of_birth else 'N/A',
                'age': calculate_age(prescription_request.patient.date_of_birth) if hasattr(prescription_request.patient, 'date_of_birth') and prescription_request.patient.date_of_birth else None,
                'allergies': prescription_request.patient.allergies if hasattr(prescription_request.patient, 'allergies') else None,
                'current_medications': []  # TODO: Fetch from patient's current prescriptions
            },
            'medications': [
                {
                    'medication_name': med.medication_name,
                    'strength': med.strength,
                    'form': med.form,
                    'quantity': med.quantity,
                    'dosage': med.dosage,
                    'is_repeat': med.is_repeat,
                    'reason': med.reason
                }
                for med in prescription_request.medications.all()
            ],
            'urgency': prescription_request.urgency,
            'request_date': prescription_request.request_date.isoformat(),
            'additional_notes': prescription_request.additional_notes,
            'pharmacy': {
                'name': prescription_request.pharmacy.name,
                'address_line_1': prescription_request.pharmacy.address_line_1,
                'city': prescription_request.pharmacy.city,
                'postcode': prescription_request.pharmacy.postcode,
                'phone': prescription_request.pharmacy.phone
            } if prescription_request.pharmacy else None
        }

        return Response(response_data, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f'Error fetching prescription request details: {str(e)}')
        return Response(
            {'error': 'Failed to fetch prescription request details'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def approve_prescription_request(request, request_id):
    """
    Approve a prescription request with custom dosages.
    Creates Medication objects with signed prescription tokens.

    Request body:
    {
        "medications": [
            {
                "medication_name": "Amoxicillin",
                "strength": "500mg",
                "form": "capsule",
                "quantity": 21,
                "dosage_instructions": "Take 1 capsule three times daily",
                "frequency": "Three times daily",
                "refills_allowed": 2
            }
        ],
        "clinical_notes": "Approved for bacterial infection treatment"
    }
    """
    try:
        # Verify user is a doctor
        if not hasattr(request.user, 'doctor_profile'):
            return Response(
                {'error': 'Only doctors can approve prescriptions'},
                status=status.HTTP_403_FORBIDDEN
            )

        doctor = request.user.doctor_profile

        # Get prescription request from database
        try:
            prescription_request = PrescriptionRequest.objects.select_related('patient', 'pharmacy').prefetch_related('medications').get(id=request_id)
        except PrescriptionRequest.DoesNotExist:
            return Response(
                {'error': 'Prescription request not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get approval data
        medications = request.data.get('medications', [])
        clinical_notes = request.data.get('clinical_notes', '')
        patient = prescription_request.patient

        # Update request status and create Medication objects
        with transaction.atomic():
            prescription_request.status = 'APPROVED'
            prescription_request.reviewed_by = doctor
            prescription_request.reviewed_date = timezone.now()
            prescription_request.clinical_notes = clinical_notes
            prescription_request.save()

            # ✨ NEW: Create Medication objects for each approved medication
            created_medications = []

            # Get or create patient's medical record
            medical_record, _ = MedicalRecord.objects.get_or_create(
                user=patient,
                defaults={'hpn': patient.hpn if hasattr(patient, 'hpn') else ''}
            )

            for approved_med in medications:
                # Create Medication object
                medication = Medication.objects.create(
                    medical_record=medical_record,
                    medication_name=approved_med['medication_name'],
                    strength=approved_med.get('strength', ''),
                    form=approved_med.get('form', 'tablet'),
                    route='oral',  # Default, can be customized
                    dosage=approved_med.get('dosage_instructions', ''),
                    frequency=approved_med.get('frequency', 'As directed'),
                    start_date=timezone.now().date(),
                    is_ongoing=True,
                    duration=None,  # Ongoing unless specified
                    patient_instructions=approved_med.get('dosage_instructions', ''),

                    # Prescription details
                    indication=clinical_notes,
                    prescribed_by=doctor,
                    prescription_date=timezone.now(),

                    # Link to nominated pharmacy
                    nominated_pharmacy=prescription_request.pharmacy,

                    # Status
                    status='active',  # Ready for collection

                    # Refills
                    refills_remaining=approved_med.get('refills_allowed', 0)
                )

                # ✨ Generate signed prescription token
                try:
                    payload, signature = sign_prescription(medication)
                    logger.info(
                        f"Created signed prescription: PHB-RX-{str(medication.id).zfill(8)} "
                        f"for {patient.get_full_name()}"
                    )
                except Exception as e:
                    logger.error(f"Failed to sign prescription {medication.id}: {str(e)}")
                    # Continue - prescription is still created even if signing fails

                created_medications.append(medication)

            # Update PrescriptionRequestItem records (for tracking)
            for approved_med in medications:
                for item in prescription_request.medications.all():
                    if item.medication_name == approved_med['medication_name']:
                        item.approved_quantity = approved_med.get('quantity')
                        item.approved_dosage = approved_med.get('dosage_instructions')
                        item.refills_allowed = approved_med.get('refills_allowed', 0)
                        item.save()
                        break

        # Send approval email to patient
        try:
            pharmacy_name = prescription_request.pharmacy.name if prescription_request.pharmacy else 'Your nominated pharmacy'
            pharmacy_address = f"{prescription_request.pharmacy.address_line_1}, {prescription_request.pharmacy.city}" if prescription_request.pharmacy else ''

            send_prescription_approved_notification(
                patient_email=prescription_request.patient.email,
                patient_name=prescription_request.patient.get_full_name(),
                request_reference=prescription_request.request_reference,
                medications=medications,
                clinical_notes=clinical_notes,
                doctor_name=doctor.user.get_full_name(),
                pharmacy_name=pharmacy_name,
                pharmacy_address=pharmacy_address,
                collection_timeline="2-3 days"
            )
            logger.info(f"Approval email sent for {prescription_request.request_reference}")
        except Exception as e:
            logger.error(f"Failed to send approval email: {str(e)}")

        # ✨ NEW: Send critical alert for controlled substances ONLY
        # (No individual emails for routine prescriptions - prevents email overload)
        if prescription_request.pharmacy:
            for idx, medication in enumerate(created_medications):
                is_controlled = False
                nafdac_schedule = None
                med_name = medication.medication_name

                # Check if controlled substance
                try:
                    # Method 1: Check drug database (505 drugs with NAFDAC schedules)
                    drug = DrugClassification.objects.filter(
                        generic_name__iexact=medication.medication_name
                    ).first()

                    if drug and drug.nafdac_schedule in ['2', '3']:
                        is_controlled = True
                        nafdac_schedule = drug.nafdac_schedule
                        med_name = drug.generic_name
                        logger.info(
                            f"Controlled substance detected from database: {med_name} "
                            f"(Schedule {nafdac_schedule})"
                        )

                    # Method 2: Doctor manually specified (for drugs not in database)
                    # Check if this medication has manual controlled substance flag
                    if idx < len(medications):  # Ensure we have the corresponding approved_med
                        approved_med = medications[idx]
                        manual_controlled = approved_med.get('is_controlled', False)
                        manual_schedule = approved_med.get('nafdac_schedule')

                        if manual_controlled or manual_schedule:
                            is_controlled = True
                            nafdac_schedule = manual_schedule or 'Manual'
                            logger.info(
                                f"Controlled substance manually specified by doctor: {med_name} "
                                f"(Schedule {nafdac_schedule})"
                            )

                    # Send URGENT alert if controlled substance detected
                    if is_controlled:
                        send_controlled_substance_alert(
                            pharmacy_email=prescription_request.pharmacy.email,
                            pharmacy_name=prescription_request.pharmacy.name,
                            patient_name=patient.get_full_name(),
                            medication_name=med_name,
                            nafdac_schedule=nafdac_schedule,
                            prescription_id=f"PHB-RX-{str(medication.id).zfill(8)}"
                        )
                        logger.info(
                            f"Controlled substance alert sent to {prescription_request.pharmacy.name} "
                            f"for {med_name} (Schedule {nafdac_schedule})"
                        )

                except Exception as e:
                    logger.error(f"Failed to process controlled substance check: {str(e)}")

        return Response(
            {
                'success': True,
                'message': 'Prescription approved successfully',
                'request_reference': prescription_request.request_reference,
                'prescriptions_created': len(created_medications),
                'prescription_ids': [
                    f"PHB-RX-{str(med.id).zfill(8)}"
                    for med in created_medications
                ]
            },
            status=status.HTTP_200_OK
        )

    except Exception as e:
        logger.error(f'Error approving prescription: {str(e)}')
        return Response(
            {'error': 'Failed to approve prescription'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reject_prescription_request(request, request_id):
    """
    Reject a prescription request with reason.

    Request body:
    {
        "reason": "Medication interaction with current prescriptions",
        "requires_followup": true
    }
    """
    try:
        # Verify user is a doctor
        if not hasattr(request.user, 'doctor_profile'):
            return Response(
                {'error': 'Only doctors can reject prescriptions'},
                status=status.HTTP_403_FORBIDDEN
            )

        doctor = request.user.doctor_profile
        reason = request.data.get('reason')

        if not reason:
            return Response(
                {'error': 'Rejection reason is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get prescription request from database
        try:
            prescription_request = PrescriptionRequest.objects.select_related('patient', 'hospital').get(id=request_id)
        except PrescriptionRequest.DoesNotExist:
            return Response(
                {'error': 'Prescription request not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Update request status
        prescription_request.status = 'REJECTED'
        prescription_request.rejection_reason = reason
        prescription_request.requires_followup = request.data.get('requires_followup', False)
        prescription_request.reviewed_by = doctor
        prescription_request.reviewed_date = timezone.now()
        prescription_request.save()

        # Send rejection email
        try:
            hospital_phone = prescription_request.hospital.phone if hasattr(prescription_request.hospital, 'phone') else ''

            send_prescription_rejected_notification(
                patient_email=prescription_request.patient.email,
                patient_name=prescription_request.patient.get_full_name(),
                request_reference=prescription_request.request_reference,
                rejection_reason=reason,
                requires_followup=prescription_request.requires_followup,
                doctor_name=doctor.user.get_full_name(),
                hospital_name=prescription_request.hospital.name,
                hospital_phone=hospital_phone
            )
            logger.info(f"Rejection email sent for {prescription_request.request_reference}")
        except Exception as e:
            logger.error(f"Failed to send rejection email: {str(e)}")
            # Don't fail the request if email fails

        return Response(
            {
                'success': True,
                'message': 'Prescription request rejected',
                'request_reference': prescription_request.request_reference
            },
            status=status.HTTP_200_OK
        )

    except Exception as e:
        logger.error(f'Error rejecting prescription: {str(e)}')
        return Response(
            {'error': 'Failed to reject prescription'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# =====================================================================
# PHARMACIST ENDPOINTS
# =====================================================================
# NOTE: Pharmacist review endpoints are implemented in pharmacist_triage_views.py
# This separation keeps the codebase organized:
#   - prescription_requests_views.py: Patient requests + Doctor approvals
#   - pharmacist_triage_views.py: Pharmacist reviews (approve/escalate/reject)
#
# The drug database integration happens automatically at request creation time
# (lines 154-174 above) via assign_prescription_request(), which uses the
# enhanced triage logic with DrugClassification database (505 drugs).
#
# Pharmacist endpoints available at /api/provider/prescriptions/triage/:
#   GET  /api/provider/prescriptions/triage/ - Get assigned requests
#   GET  /api/provider/prescriptions/triage/{id}/ - Get request details
#   POST /api/provider/prescriptions/triage/{id}/approve/ - Approve request
#   POST /api/provider/prescriptions/triage/{id}/escalate/ - Escalate to doctor
#   POST /api/provider/prescriptions/triage/{id}/reject/ - Reject request
#   GET  /api/provider/prescriptions/triage/stats/ - Triage statistics
# =====================================================================
