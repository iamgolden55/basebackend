"""
Pharmacist Triage API Views

Endpoints for clinical pharmacists to review, approve, escalate, or reject
prescription requests that have been assigned to them via the triage system.
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db import transaction
from django.db.models import Q
from datetime import timedelta
import logging

from api.models import (
    PrescriptionRequest,
    PrescriptionRequestItem,
    Pharmacist,
    Doctor,
    CustomUser
)
from api.utils.email import (
    send_pharmacist_approved_prescription_to_doctor,
    send_prescription_escalation_to_physician,
    send_prescription_rejected_notification
)
from api.utils.prescription_triage import get_triage_statistics

logger = logging.getLogger(__name__)


def get_pharmacist_from_user(user):
    """
    Get pharmacist profile from user or return error response

    Args:
        user: CustomUser instance

    Returns:
        tuple: (pharmacist, error_response)
            - If successful: (Pharmacist instance, None)
            - If failed: (None, Response instance)
    """
    try:
        pharmacist = Pharmacist.objects.get(user=user)
        if not pharmacist.is_active or pharmacist.status != 'active':
            return None, Response(
                {'error': 'Your pharmacist account is not active'},
                status=status.HTTP_403_FORBIDDEN
            )
        return pharmacist, None
    except Pharmacist.DoesNotExist:
        return None, Response(
            {'error': 'You are not registered as a pharmacist'},
            status=status.HTTP_403_FORBIDDEN
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_assigned_prescription_requests(request):
    """
    Get prescription requests assigned to the logged-in pharmacist

    Query parameters:
    - status: Filter by status (REQUESTED, APPROVED, REJECTED)
    - urgency: Filter by urgency (urgent, routine)
    - triage_category: Filter by triage category
    - reviewed: Filter by review status (true/false)
    - page: Page number (default: 1)
    - per_page: Results per page (default: 20)

    Response:
    {
        "requests": [
            {
                "id": "uuid",
                "request_reference": "REQ-ABC123",
                "patient_name": "John Doe",
                "patient_hpn": "HPN123456",
                "status": "REQUESTED",
                "urgency": "routine",
                "triage_category": "ROUTINE_REPEAT",
                "triage_reason": "...",
                "medication_count": 3,
                "request_date": "2025-11-01T10:30:00Z",
                "pharmacist_reviewed": false,
                "awaiting_review": true
            }
        ],
        "pagination": {
            "page": 1,
            "per_page": 20,
            "total": 45,
            "pages": 3
        },
        "stats": {
            "awaiting_review": 12,
            "reviewed_today": 8,
            "urgent_pending": 3
        }
    }
    """
    pharmacist, error = get_pharmacist_from_user(request.user)
    if error:
        return error

    # Build query
    query = Q(assigned_to_pharmacist=pharmacist)

    # Apply filters
    status_filter = request.GET.get('status')
    if status_filter:
        query &= Q(status=status_filter.upper())

    urgency_filter = request.GET.get('urgency')
    if urgency_filter:
        query &= Q(urgency=urgency_filter.lower())

    triage_category_filter = request.GET.get('triage_category')
    if triage_category_filter:
        query &= Q(triage_category=triage_category_filter.upper())

    reviewed_filter = request.GET.get('reviewed')
    if reviewed_filter == 'true':
        query &= Q(pharmacist_reviewed_by__isnull=False)
    elif reviewed_filter == 'false':
        query &= Q(pharmacist_reviewed_by__isnull=True)

    # Get prescription requests
    prescription_requests = PrescriptionRequest.objects.filter(query).select_related(
        'patient', 'hospital', 'pharmacy'
    ).prefetch_related('medications').order_by('-urgency', '-request_date')

    # Pagination
    page = int(request.GET.get('page', 1))
    per_page = int(request.GET.get('per_page', 20))
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    total = prescription_requests.count()
    pages = (total + per_page - 1) // per_page

    paginated_requests = prescription_requests[start_idx:end_idx]

    # Build response
    requests_data = []
    for pr in paginated_requests:
        patient_name = pr.patient.get_full_name() if hasattr(pr.patient, 'get_full_name') else pr.patient.email
        patient_hpn = pr.patient.hpn if hasattr(pr.patient, 'hpn') else 'N/A'

        requests_data.append({
            'id': str(pr.id),
            'request_reference': pr.request_reference,
            'patient_name': patient_name,
            'patient_hpn': patient_hpn,
            'status': pr.status,
            'urgency': pr.urgency,
            'triage_category': pr.triage_category,
            'triage_reason': pr.triage_reason,
            'medication_count': pr.medication_count,
            'request_date': pr.request_date.isoformat(),
            'pharmacist_reviewed': pr.pharmacist_reviewed,
            'pharmacist_review_action': pr.pharmacist_review_action,
            'awaiting_review': pr.awaiting_pharmacist_review,
        })

    # Calculate stats
    all_assigned = PrescriptionRequest.objects.filter(assigned_to_pharmacist=pharmacist)
    awaiting_review = all_assigned.filter(
        status='REQUESTED',
        pharmacist_reviewed_by__isnull=True
    ).count()
    reviewed_today = all_assigned.filter(
        pharmacist_review_date__gte=timezone.now().date()
    ).count()
    urgent_pending = all_assigned.filter(
        status='REQUESTED',
        urgency='urgent',
        pharmacist_reviewed_by__isnull=True
    ).count()

    return Response({
        'requests': requests_data,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'pages': pages
        },
        'stats': {
            'awaiting_review': awaiting_review,
            'reviewed_today': reviewed_today,
            'urgent_pending': urgent_pending
        }
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_prescription_request_detail(request, request_id):
    """
    Get detailed information for a specific prescription request

    Response includes:
    - Full patient information
    - Medication list with dosages
    - Patient allergies and current medications
    - Triage information
    - Pharmacy details
    """
    pharmacist, error = get_pharmacist_from_user(request.user)
    if error:
        return error

    try:
        pr = PrescriptionRequest.objects.select_related(
            'patient', 'hospital', 'pharmacy', 'assigned_to_pharmacist'
        ).prefetch_related('medications').get(id=request_id)

        # Verify pharmacist has access
        if pr.assigned_to_pharmacist != pharmacist:
            return Response(
                {'error': 'This prescription request is not assigned to you'},
                status=status.HTTP_403_FORBIDDEN
            )

        patient = pr.patient
        patient_name = patient.get_full_name() if hasattr(patient, 'get_full_name') else patient.email
        patient_dob = patient.date_of_birth.strftime('%Y-%m-%d') if hasattr(patient, 'date_of_birth') and patient.date_of_birth else None
        patient_age = None
        if patient_dob:
            from datetime import datetime
            dob = datetime.strptime(patient_dob, '%Y-%m-%d')
            today = datetime.today()
            patient_age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

        # Get medications
        medications = []
        for med in pr.medications.all():
            medications.append({
                'id': med.id,
                'medication_name': med.medication_name,
                'strength': med.strength,
                'form': med.form,
                'quantity': med.quantity,
                'dosage': med.dosage,
                'is_repeat': med.is_repeat,
                'reason': med.reason,
                'approved_quantity': med.approved_quantity,
                'approved_dosage': med.approved_dosage,
                'refills_allowed': med.refills_allowed
            })

        # Build response
        response_data = {
            'id': str(pr.id),
            'request_reference': pr.request_reference,
            'status': pr.status,
            'urgency': pr.urgency,
            'request_type': pr.request_type,
            'request_date': pr.request_date.isoformat(),
            'patient': {
                'name': patient_name,
                'hpn': patient.hpn if hasattr(patient, 'hpn') else 'N/A',
                'email': patient.email,
                'phone': patient.phone if hasattr(patient, 'phone') else None,
                'date_of_birth': patient_dob,
                'age': patient_age,
                'allergies': patient.allergies if hasattr(patient, 'allergies') else None,
                'current_medications': patient.current_medications if hasattr(patient, 'current_medications') else None,
            },
            'hospital': {
                'id': pr.hospital.id,
                'name': pr.hospital.name
            },
            'pharmacy': None,
            'triage': {
                'category': pr.triage_category,
                'reason': pr.triage_reason,
                'assigned_date': pr.created_at.isoformat()
            },
            'medications': medications,
            'additional_notes': pr.additional_notes,
            'pharmacist_review': {
                'reviewed': pr.pharmacist_reviewed,
                'review_date': pr.pharmacist_review_date.isoformat() if pr.pharmacist_review_date else None,
                'review_action': pr.pharmacist_review_action,
                'pharmacist_notes': pr.pharmacist_notes,
                'escalation_reason': pr.escalation_reason,
                'clinical_concerns': pr.clinical_concerns,
                'drug_interactions_checked': pr.drug_interactions_checked,
                'monitoring_requirements': pr.monitoring_requirements,
                'pharmacist_recommendation': pr.pharmacist_recommendation
            }
        }

        if pr.pharmacy:
            response_data['pharmacy'] = {
                'id': pr.pharmacy.id,
                'name': pr.pharmacy.name,
                'address': f"{pr.pharmacy.address_line_1}, {pr.pharmacy.city}, {pr.pharmacy.postcode}",
                'phone': pr.pharmacy.phone if hasattr(pr.pharmacy, 'phone') else None
            }

        return Response(response_data)

    except PrescriptionRequest.DoesNotExist:
        return Response(
            {'error': 'Prescription request not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def approve_prescription_request(request, request_id):
    """
    Pharmacist approves prescription request and forwards to physician for final authorization

    Request body:
    {
        "pharmacist_notes": "Clinical review completed. No drug interactions found.",
        "drug_interactions_checked": "Checked against current medications - no interactions",
        "monitoring_requirements": "Monitor blood pressure weekly for 2 weeks",
        "approved_medications": [
            {
                "medication_id": 123,
                "approved_quantity": 30,
                "approved_dosage": "Take 1 tablet daily with food",
                "refills_allowed": 3
            }
        ],
        "had_clinical_intervention": false
    }
    """
    pharmacist, error = get_pharmacist_from_user(request.user)
    if error:
        return error

    try:
        with transaction.atomic():
            pr = PrescriptionRequest.objects.select_for_update().get(id=request_id)

            # Verify pharmacist has access
            if pr.assigned_to_pharmacist != pharmacist:
                return Response(
                    {'error': 'This prescription request is not assigned to you'},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Verify request is still pending
            if pr.status != 'REQUESTED':
                return Response(
                    {'error': f'Cannot approve - request status is {pr.status}'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Verify not already reviewed
            if pr.pharmacist_reviewed_by:
                return Response(
                    {'error': 'This request has already been reviewed'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Extract request data
            pharmacist_notes = request.data.get('pharmacist_notes', '')
            drug_interactions = request.data.get('drug_interactions_checked', '')
            monitoring_requirements = request.data.get('monitoring_requirements', '')
            approved_medications = request.data.get('approved_medications', [])
            had_intervention = request.data.get('had_clinical_intervention', False)

            # Calculate review time
            review_time = (timezone.now() - pr.request_date).total_seconds() / 60.0

            # Update prescription request
            pr.pharmacist_reviewed_by = pharmacist
            pr.pharmacist_review_date = timezone.now()
            pr.pharmacist_review_action = 'approved'
            pr.pharmacist_notes = pharmacist_notes
            pr.drug_interactions_checked = drug_interactions
            pr.monitoring_requirements = monitoring_requirements
            pr.pharmacist_review_time_minutes = review_time
            pr.had_clinical_intervention = had_intervention
            pr.save()

            # Update approved medication details
            for approved_med in approved_medications:
                try:
                    med_item = PrescriptionRequestItem.objects.get(
                        id=approved_med['medication_id'],
                        request=pr
                    )
                    med_item.approved_quantity = approved_med.get('approved_quantity', med_item.quantity)
                    med_item.approved_dosage = approved_med.get('approved_dosage', med_item.dosage)
                    med_item.refills_allowed = approved_med.get('refills_allowed', 0)
                    med_item.save()
                except PrescriptionRequestItem.DoesNotExist:
                    logger.warning(f"Medication item {approved_med['medication_id']} not found")

            # Update pharmacist performance stats
            pharmacist.increment_review_stats(
                action='approved',
                review_time_minutes=review_time,
                had_intervention=had_intervention
            )

            # Send email to physician for final authorization
            try:
                # Find a doctor at the hospital for authorization
                doctor = Doctor.objects.filter(
                    hospital=pr.hospital,
                    is_active=True,
                    status='active'
                ).first()

                if doctor:
                    patient = pr.patient
                    patient_name = patient.get_full_name() if hasattr(patient, 'get_full_name') else patient.email
                    patient_dob = patient.date_of_birth.strftime('%d %B, %Y') if hasattr(patient, 'date_of_birth') and patient.date_of_birth else 'Not available'
                    patient_age = None
                    if hasattr(patient, 'date_of_birth') and patient.date_of_birth:
                        from datetime import datetime
                        dob = patient.date_of_birth
                        today = datetime.today()
                        patient_age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

                    # Prepare medication list
                    medications = []
                    for med_item in pr.medications.all():
                        medications.append({
                            'name': med_item.medication_name,
                            'strength': med_item.strength or '',
                            'form': med_item.form or '',
                            'approved_quantity': med_item.approved_quantity or med_item.quantity,
                            'approved_dosage': med_item.approved_dosage or med_item.dosage,
                            'refills_allowed': med_item.refills_allowed
                        })

                    pharmacy_name = pr.pharmacy.name if pr.pharmacy else 'Nominated pharmacy'
                    pharmacy_address = f"{pr.pharmacy.address_line_1}, {pr.pharmacy.city}, {pr.pharmacy.postcode}" if pr.pharmacy else ''

                    send_pharmacist_approved_prescription_to_doctor(
                        doctor_email=doctor.user.email,
                        doctor_name=doctor.user.get_full_name(),
                        pharmacist_name=pharmacist.get_full_name(),
                        patient_name=patient_name,
                        patient_hpn=patient.hpn if hasattr(patient, 'hpn') else 'N/A',
                        patient_dob=patient_dob,
                        patient_age=patient_age or 'Unknown',
                        request_reference=pr.request_reference,
                        request_id=str(pr.id),
                        request_date=pr.request_date.strftime('%d %B, %Y'),
                        review_date=timezone.now().strftime('%d %B, %Y'),
                        medications=medications,
                        pharmacy_name=pharmacy_name,
                        pharmacy_address=pharmacy_address,
                        pharmacist_notes=pharmacist_notes,
                        drug_interactions=drug_interactions,
                        monitoring_required=monitoring_requirements,
                        allergies=patient.allergies if hasattr(patient, 'allergies') else None
                    )
                    logger.info(f"✅ Pharmacist approval email sent to Dr. {doctor.user.get_full_name()}")

            except Exception as e:
                logger.error(f"Failed to send pharmacist approval email: {str(e)}")
                # Don't fail the approval if email fails

            return Response({
                'message': 'Prescription request approved successfully',
                'request_reference': pr.request_reference,
                'pharmacist_action': 'approved',
                'next_step': 'Awaiting physician final authorization',
                'review_time_minutes': round(review_time, 2)
            })

    except PrescriptionRequest.DoesNotExist:
        return Response(
            {'error': 'Prescription request not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def escalate_prescription_request(request, request_id):
    """
    Pharmacist escalates prescription request to physician for direct review

    Request body:
    {
        "escalation_reason": "Complex drug interaction with patient's current medications",
        "clinical_concerns": "Patient is taking warfarin - potential interaction with requested NSAID",
        "pharmacist_recommendation": "Suggest alternative pain management or dose adjustment",
        "pharmacist_notes": "Reviewed medication history - significant interaction risk",
        "had_clinical_intervention": true
    }
    """
    pharmacist, error = get_pharmacist_from_user(request.user)
    if error:
        return error

    try:
        with transaction.atomic():
            pr = PrescriptionRequest.objects.select_for_update().get(id=request_id)

            # Verify pharmacist has access
            if pr.assigned_to_pharmacist != pharmacist:
                return Response(
                    {'error': 'This prescription request is not assigned to you'},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Verify request is still pending
            if pr.status != 'REQUESTED':
                return Response(
                    {'error': f'Cannot escalate - request status is {pr.status}'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Verify not already reviewed
            if pr.pharmacist_reviewed_by:
                return Response(
                    {'error': 'This request has already been reviewed'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Extract request data
            escalation_reason = request.data.get('escalation_reason', '')
            clinical_concerns = request.data.get('clinical_concerns', '')
            pharmacist_recommendation = request.data.get('pharmacist_recommendation', '')
            pharmacist_notes = request.data.get('pharmacist_notes', '')
            had_intervention = request.data.get('had_clinical_intervention', True)  # Default true for escalations

            if not escalation_reason:
                return Response(
                    {'error': 'escalation_reason is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Calculate review time
            review_time = (timezone.now() - pr.request_date).total_seconds() / 60.0

            # Update prescription request
            pr.pharmacist_reviewed_by = pharmacist
            pr.pharmacist_review_date = timezone.now()
            pr.pharmacist_review_action = 'escalated'
            pr.pharmacist_notes = pharmacist_notes
            pr.escalation_reason = escalation_reason
            pr.clinical_concerns = clinical_concerns
            pr.pharmacist_recommendation = pharmacist_recommendation
            pr.pharmacist_review_time_minutes = review_time
            pr.had_clinical_intervention = had_intervention
            pr.assigned_to_role = 'doctor'  # Re-assign to physician
            pr.save()

            # Update pharmacist performance stats
            pharmacist.increment_review_stats(
                action='escalated',
                review_time_minutes=review_time,
                had_intervention=had_intervention
            )

            # Send escalation email to physician
            try:
                # Find a doctor at the hospital
                doctor = Doctor.objects.filter(
                    hospital=pr.hospital,
                    is_active=True,
                    status='active'
                ).first()

                if doctor:
                    pr.assigned_to_doctor = doctor
                    pr.save(update_fields=['assigned_to_doctor'])

                    patient = pr.patient
                    patient_name = patient.get_full_name() if hasattr(patient, 'get_full_name') else patient.email
                    patient_dob = patient.date_of_birth.strftime('%d %B, %Y') if hasattr(patient, 'date_of_birth') and patient.date_of_birth else 'Not available'
                    patient_age = None
                    if hasattr(patient, 'date_of_birth') and patient.date_of_birth:
                        from datetime import datetime
                        dob = patient.date_of_birth
                        today = datetime.today()
                        patient_age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

                    # Prepare medication list
                    medications = []
                    for med_item in pr.medications.all():
                        medications.append({
                            'name': med_item.medication_name,
                            'strength': med_item.strength or '',
                            'form': med_item.form or '',
                            'quantity': med_item.quantity,
                            'dosage': med_item.dosage or '',
                            'is_repeat': med_item.is_repeat,
                            'controlled': False,  # TODO: Add controlled substance check
                            'flagged': True,  # Escalated meds are flagged
                            'flag_reason': clinical_concerns or escalation_reason
                        })

                    pharmacy_name = pr.pharmacy.name if pr.pharmacy else 'Nominated pharmacy'
                    pharmacy_address = f"{pr.pharmacy.address_line_1}, {pr.pharmacy.city}, {pr.pharmacy.postcode}" if pr.pharmacy else ''

                    send_prescription_escalation_to_physician(
                        doctor_email=doctor.user.email,
                        doctor_name=doctor.user.get_full_name(),
                        pharmacist_name=pharmacist.get_full_name(),
                        patient_name=patient_name,
                        patient_hpn=patient.hpn if hasattr(patient, 'hpn') else 'N/A',
                        patient_dob=patient_dob,
                        patient_age=patient_age or 'Unknown',
                        request_reference=pr.request_reference,
                        request_id=str(pr.id),
                        request_date=pr.request_date.strftime('%d %B, %Y'),
                        review_date=timezone.now().strftime('%d %B, %Y'),
                        urgency=pr.urgency,
                        escalation_category=pr.triage_category,
                        escalation_reason=escalation_reason,
                        medications=medications,
                        pharmacy_name=pharmacy_name,
                        pharmacy_address=pharmacy_address,
                        clinical_concerns=clinical_concerns,
                        pharmacist_recommendation=pharmacist_recommendation,
                        allergies=patient.allergies if hasattr(patient, 'allergies') else None,
                        current_medications=patient.current_medications if hasattr(patient, 'current_medications') else None,
                        medical_conditions=patient.medical_conditions if hasattr(patient, 'medical_conditions') else None,
                        request_notes=pr.additional_notes
                    )
                    logger.info(f"✅ Escalation email sent to Dr. {doctor.user.get_full_name()}")

            except Exception as e:
                logger.error(f"Failed to send escalation email: {str(e)}")
                # Don't fail the escalation if email fails

            return Response({
                'message': 'Prescription request escalated to physician successfully',
                'request_reference': pr.request_reference,
                'pharmacist_action': 'escalated',
                'escalation_reason': escalation_reason,
                'next_step': 'Awaiting physician review',
                'review_time_minutes': round(review_time, 2)
            })

    except PrescriptionRequest.DoesNotExist:
        return Response(
            {'error': 'Prescription request not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reject_prescription_request(request, request_id):
    """
    Pharmacist rejects prescription request

    Request body:
    {
        "rejection_reason": "Contraindication with patient's allergy to penicillin",
        "pharmacist_notes": "Patient has documented allergy - cannot safely prescribe",
        "requires_appointment": true,
        "had_clinical_intervention": true
    }
    """
    pharmacist, error = get_pharmacist_from_user(request.user)
    if error:
        return error

    try:
        with transaction.atomic():
            pr = PrescriptionRequest.objects.select_for_update().get(id=request_id)

            # Verify pharmacist has access
            if pr.assigned_to_pharmacist != pharmacist:
                return Response(
                    {'error': 'This prescription request is not assigned to you'},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Verify request is still pending
            if pr.status != 'REQUESTED':
                return Response(
                    {'error': f'Cannot reject - request status is {pr.status}'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Verify not already reviewed
            if pr.pharmacist_reviewed_by:
                return Response(
                    {'error': 'This request has already been reviewed'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Extract request data
            rejection_reason = request.data.get('rejection_reason', '')
            pharmacist_notes = request.data.get('pharmacist_notes', '')
            requires_appointment = request.data.get('requires_appointment', False)
            had_intervention = request.data.get('had_clinical_intervention', True)

            if not rejection_reason:
                return Response(
                    {'error': 'rejection_reason is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Calculate review time
            review_time = (timezone.now() - pr.request_date).total_seconds() / 60.0

            # Update prescription request
            pr.status = 'REJECTED'
            pr.pharmacist_reviewed_by = pharmacist
            pr.pharmacist_review_date = timezone.now()
            pr.pharmacist_review_action = 'rejected'
            pr.pharmacist_notes = pharmacist_notes
            pr.rejection_reason = rejection_reason
            pr.requires_followup = requires_appointment
            pr.pharmacist_review_time_minutes = review_time
            pr.had_clinical_intervention = had_intervention
            pr.save()

            # Update pharmacist performance stats
            pharmacist.increment_review_stats(
                action='rejected',
                review_time_minutes=review_time,
                had_intervention=had_intervention
            )

            # Send rejection email to patient
            try:
                patient = pr.patient
                patient_name = patient.get_full_name() if hasattr(patient, 'get_full_name') else patient.email

                send_prescription_rejected_notification(
                    patient_email=patient.email,
                    patient_name=patient_name,
                    request_reference=pr.request_reference,
                    rejection_reason=rejection_reason,
                    requires_followup_appointment=requires_appointment,
                    hospital_name=pr.hospital.name
                )
                logger.info(f"✅ Rejection email sent to patient {patient.email}")

            except Exception as e:
                logger.error(f"Failed to send rejection email: {str(e)}")
                # Don't fail the rejection if email fails

            return Response({
                'message': 'Prescription request rejected successfully',
                'request_reference': pr.request_reference,
                'pharmacist_action': 'rejected',
                'rejection_reason': rejection_reason,
                'requires_appointment': requires_appointment,
                'review_time_minutes': round(review_time, 2)
            })

    except PrescriptionRequest.DoesNotExist:
        return Response(
            {'error': 'Prescription request not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_pharmacist_triage_statistics(request):
    """
    Get triage statistics for the logged-in pharmacist

    Response:
    {
        "total_reviews_completed": 125,
        "approval_rate": 68.5,
        "escalation_rate": 22.3,
        "rejection_rate": 9.2,
        "intervention_rate": 36.1,
        "average_review_time_minutes": 18.5,
        "reviews_this_week": 28,
        "reviews_this_month": 125,
        "urgent_pending": 3,
        "routine_pending": 12
    }
    """
    pharmacist, error = get_pharmacist_from_user(request.user)
    if error:
        return error

    # Get overall stats from pharmacist model
    total_reviews = pharmacist.total_reviews_completed
    approval_rate = pharmacist.get_approval_rate()
    escalation_rate = pharmacist.get_escalation_rate()
    intervention_rate = pharmacist.get_intervention_rate()

    rejection_count = pharmacist.total_rejected
    rejection_rate = (rejection_count / total_reviews * 100) if total_reviews > 0 else 0.0

    # Get time-based stats
    one_week_ago = timezone.now() - timedelta(days=7)
    one_month_ago = timezone.now() - timedelta(days=30)

    reviews_this_week = PrescriptionRequest.objects.filter(
        pharmacist_reviewed_by=pharmacist,
        pharmacist_review_date__gte=one_week_ago
    ).count()

    reviews_this_month = PrescriptionRequest.objects.filter(
        pharmacist_reviewed_by=pharmacist,
        pharmacist_review_date__gte=one_month_ago
    ).count()

    # Get pending stats
    urgent_pending = PrescriptionRequest.objects.filter(
        assigned_to_pharmacist=pharmacist,
        status='REQUESTED',
        urgency='urgent',
        pharmacist_reviewed_by__isnull=True
    ).count()

    routine_pending = PrescriptionRequest.objects.filter(
        assigned_to_pharmacist=pharmacist,
        status='REQUESTED',
        urgency='routine',
        pharmacist_reviewed_by__isnull=True
    ).count()

    return Response({
        'total_reviews_completed': total_reviews,
        'total_approved': pharmacist.total_approved,
        'total_escalated': pharmacist.total_escalated,
        'total_rejected': pharmacist.total_rejected,
        'approval_rate': round(approval_rate, 2),
        'escalation_rate': round(escalation_rate, 2),
        'rejection_rate': round(rejection_rate, 2),
        'intervention_rate': round(intervention_rate, 2),
        'average_review_time_minutes': round(pharmacist.average_review_time_minutes, 2),
        'clinical_interventions_count': pharmacist.clinical_interventions_count,
        'reviews_this_week': reviews_this_week,
        'reviews_this_month': reviews_this_month,
        'urgent_pending': urgent_pending,
        'routine_pending': routine_pending,
        'total_pending': urgent_pending + routine_pending
    })
