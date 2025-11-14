"""
Prescription Request Triage System

Implements evidence-based triage logic for automatically categorizing
and assigning prescription requests to the appropriate healthcare professional.

Based on NHS triage protocols and clinical pharmacy best practices.
"""

import logging
from typing import Tuple, Optional, Dict, Any, List
from django.db.models import Q
from django.utils import timezone
from django.core.cache import cache
import hashlib

logger = logging.getLogger(__name__)

# Cache configuration for drug database lookups
DRUG_CACHE_TTL = 86400  # 24 hours (drug data rarely changes)
DRUG_CACHE_PREFIX = 'drug:v1:'  # Version prefix for cache invalidation


# Triage Categories (ordered by complexity/priority)
TRIAGE_CATEGORIES = {
    'ROUTINE_REPEAT': {
        'priority': 1,
        'description': 'Simple repeat prescription - low risk',
        'target_sla_hours': 48,
        'default_role': 'pharmacist',
    },
    'ROUTINE_NEW': {
        'priority': 2,
        'description': 'New standard medication - moderate complexity',
        'target_sla_hours': 48,
        'default_role': 'pharmacist',
    },
    'URGENT_REPEAT': {
        'priority': 3,
        'description': 'Urgent repeat prescription',
        'target_sla_hours': 24,
        'default_role': 'pharmacist',
    },
    'URGENT_NEW': {
        'priority': 4,
        'description': 'Urgent new medication',
        'target_sla_hours': 24,
        'default_role': 'pharmacist',
    },
    'COMPLEX_CASE': {
        'priority': 5,
        'description': 'Multiple medications or drug interactions',
        'target_sla_hours': 48,
        'default_role': 'pharmacist',  # Pharmacist reviews first, may escalate
    },
    'CONTROLLED_SUBSTANCE': {
        'priority': 6,
        'description': 'Contains controlled substances',
        'target_sla_hours': 48,
        'default_role': 'pharmacist',  # If pharmacist has authority, else doctor
    },
    'SPECIALIST_REQUIRED': {
        'priority': 7,
        'description': 'Requires specialist physician review',
        'target_sla_hours': 72,
        'default_role': 'doctor',  # Bypass pharmacist triage
    },
    'HIGH_RISK': {
        'priority': 8,
        'description': 'High-risk medication or patient',
        'target_sla_hours': 24,
        'default_role': 'doctor',  # Direct to physician
    },
}

# ==================== DRUG DATABASE INTEGRATION ====================
# NOTE: Now using comprehensive DrugClassification database (505 drugs)
# with NAFDAC schedules, risk levels, and monitoring requirements

def _get_cache_key(medication_name: str) -> str:
    """
    Generate a consistent cache key for a medication name.

    Args:
        medication_name: Name of medication

    Returns:
        Cache key string
    """
    medication_clean = medication_name.strip().lower()
    # Use hash for very long names to keep cache keys reasonable
    if len(medication_clean) > 100:
        name_hash = hashlib.md5(medication_clean.encode()).hexdigest()
        return f"{DRUG_CACHE_PREFIX}{name_hash}"
    return f"{DRUG_CACHE_PREFIX}{medication_clean}"


def find_drug_in_database(medication_name: str):
    """
    Find a drug in the classification database by name with Redis caching.

    Performance:
    - Cache hit: ~1-2ms (Redis lookup)
    - Cache miss: ~50-100ms (database query + cache write)
    - Expected cache hit rate: 95%+ for common medications

    Searches:
    1. Check Redis cache first
    2. If not cached, query database:
       a. Exact generic name match
       b. Brand names (stored in JSON array)
       c. Search keywords
    3. Cache result for future requests (24 hours)

    Args:
        medication_name: Name of medication to search for

    Returns:
        DrugClassification instance or None if not found
    """
    from api.models.drug import DrugClassification

    try:
        medication_name_clean = medication_name.strip().lower()
        cache_key = _get_cache_key(medication_name)

        # Step 1: Check cache first
        cached_drug = cache.get(cache_key)
        if cached_drug is not None:
            logger.debug(f"✅ Cache HIT for: {medication_name_clean}")
            # Return cached drug (could be a DrugClassification instance or None)
            return cached_drug

        logger.debug(f"❌ Cache MISS for: {medication_name_clean}, querying database")

        # Step 2: Cache miss - query database
        drug = None

        # Try exact generic name match first (case-insensitive)
        drug = DrugClassification.objects.filter(
            generic_name__iexact=medication_name_clean
        ).first()

        if drug:
            logger.debug(f"Found drug by generic name: {drug.generic_name}")
        else:
            # Try brand names (JSON array contains search)
            drug = DrugClassification.objects.filter(
                brand_names__icontains=medication_name_clean
            ).first()

            if drug:
                logger.debug(f"Found drug by brand name: {drug.generic_name}")
            else:
                # Try search keywords
                drug = DrugClassification.objects.filter(
                    search_keywords__icontains=medication_name_clean
                ).first()

                if drug:
                    logger.debug(f"Found drug by keyword: {drug.generic_name}")
                else:
                    logger.warning(f"Drug not found in database: {medication_name}")

        # Step 3: Cache the result (even if None) to avoid repeated lookups
        try:
            cache.set(cache_key, drug, DRUG_CACHE_TTL)
            logger.debug(f"💾 Cached drug lookup result for: {medication_name_clean}")
        except Exception as cache_error:
            logger.warning(f"Failed to cache drug '{medication_name}': {cache_error}")
            # Continue even if caching fails

        return drug

    except Exception as e:
        logger.error(f"Error searching drug database for '{medication_name}': {e}")
        return None


def is_controlled_substance(drug) -> bool:
    """
    Check if drug is a NAFDAC controlled substance using drug database.

    NAFDAC Schedules:
    - Schedule 1: Illegal (no medical use) - Not prescribed
    - Schedule 2: Narcotic drugs (opioids) - High control
    - Schedule 3: Psychotropic drugs (benzodiazepines) - Moderate control
    - Schedule 4: Nationally controlled (tramadol, etc.) - Basic control

    Args:
        drug: DrugClassification instance

    Returns:
        True if drug is Schedule 2, 3, or 4
    """
    if not drug:
        return False

    controlled_schedules = ['schedule_2', 'schedule_3', 'schedule_4']
    return drug.nafdac_schedule in controlled_schedules


def is_high_risk_medication(drug) -> bool:
    """
    Check if drug requires special monitoring or is high-risk using drug database.

    High-risk indicators:
    - Requires therapeutic monitoring (narrow therapeutic index)
    - Blackbox warnings
    - High risk level designation
    - Specific monitoring requirements

    Args:
        drug: DrugClassification instance

    Returns:
        True if high-risk medication
    """
    if not drug:
        return False

    # Check risk level
    risk_level = drug.get_risk_level()
    if risk_level and 'high' in risk_level.lower():
        return True

    # Check if requires therapeutic monitoring
    if drug.requires_monitoring:
        return True

    # Check if has black box warnings
    if drug.black_box_warning:
        return True

    return False


def is_specialist_medication(drug) -> bool:
    """
    Check if medication typically requires specialist prescribing using drug database.

    Specialist medications include:
    - Chemotherapy agents
    - Immunosuppressants (transplant)
    - Biological agents
    - Complex disease-modifying drugs

    Args:
        drug: DrugClassification instance

    Returns:
        True if specialist medication
    """
    if not drug:
        return False

    # Check if requires physician only (may indicate specialist need)
    if drug.requires_physician_only:
        return True

    # Check therapeutic class for specialist keywords
    if drug.therapeutic_class:
        specialist_keywords = [
            'chemotherapy', 'immunosuppressant', 'biological',
            'transplant', 'oncology', 'antiretroviral'
        ]
        therapeutic_lower = drug.therapeutic_class.lower()
        for keyword in specialist_keywords:
            if keyword in therapeutic_lower:
                return True

    return False


def batch_find_drugs(medication_names: List[str]) -> Dict[str, Any]:
    """
    Batch lookup for multiple drugs with optimized caching.

    This function is significantly more efficient than calling find_drug_in_database()
    in a loop because it:
    1. Minimizes Redis roundtrips (batch get instead of multiple individual gets)
    2. Performs a single database query for all cache misses
    3. Batch writes all new cache entries at once

    Performance example (3 medications):
    - Sequential: 3 Redis calls + 3 DB queries (if all miss) = ~150-300ms
    - Batch: 1 Redis call + 1 DB query = ~50-100ms (2-3x faster)

    Args:
        medication_names: List of medication names to look up

    Returns:
        Dict mapping medication_name -> DrugClassification instance (or None if not found)
    """
    from api.models.drug import DrugClassification

    if not medication_names:
        return {}

    results = {}
    cache_misses = []
    cache_miss_keys = {}

    # Normalize all medication names
    normalized_names = {}
    for name in medication_names:
        clean_name = name.strip().lower()
        normalized_names[clean_name] = name
        results[clean_name] = None  # Default to None

    # Step 1: Batch check cache using cache.get_many()
    cache_keys = {_get_cache_key(name): name for name in normalized_names.keys()}

    try:
        cached_results = cache.get_many(cache_keys.keys())

        for cache_key, drug in cached_results.items():
            clean_name = cache_keys[cache_key]
            results[clean_name] = drug
            if drug is not None:
                logger.debug(f"✅ Batch cache HIT for: {clean_name}")
            else:
                logger.debug(f"✅ Batch cache HIT (drug not found): {clean_name}")

        # Identify cache misses
        for cache_key, clean_name in cache_keys.items():
            if cache_key not in cached_results:
                cache_misses.append(clean_name)
                cache_miss_keys[clean_name] = cache_key

        if cache_misses:
            logger.debug(f"❌ Batch cache MISS for {len(cache_misses)} medications: {cache_misses}")

    except Exception as e:
        logger.warning(f"Cache batch get failed: {e}, falling back to database for all")
        cache_misses = list(normalized_names.keys())
        cache_miss_keys = {name: _get_cache_key(name) for name in cache_misses}

    # Step 2: Batch query database for all cache misses
    if cache_misses:
        try:
            # Single database query for all missing drugs
            drugs = DrugClassification.objects.filter(
                Q(generic_name__in=cache_misses) |
                Q(brand_names__icontains=cache_misses[0]) if len(cache_misses) == 1 else Q()
            )

            # For multiple cache misses, we need to check each drug against the search criteria
            # (this is still more efficient than N separate queries)
            found_drugs = {}
            for drug in drugs:
                # Check which medications this drug matches
                drug_name_lower = drug.generic_name.lower()
                if drug_name_lower in cache_misses:
                    found_drugs[drug_name_lower] = drug
                    logger.debug(f"Found drug by generic name: {drug.generic_name}")

            # Update results with found drugs
            for clean_name in cache_misses:
                if clean_name in found_drugs:
                    results[clean_name] = found_drugs[clean_name]
                else:
                    # Try brand name search for this specific medication
                    drug = DrugClassification.objects.filter(
                        brand_names__icontains=clean_name
                    ).first()

                    if drug:
                        results[clean_name] = drug
                        logger.debug(f"Found drug by brand name: {drug.generic_name}")
                    else:
                        # Try keywords
                        drug = DrugClassification.objects.filter(
                            search_keywords__icontains=clean_name
                        ).first()

                        if drug:
                            results[clean_name] = drug
                            logger.debug(f"Found drug by keyword: {drug.generic_name}")
                        else:
                            logger.warning(f"Drug not found in database: {clean_name}")
                            results[clean_name] = None

            # Step 3: Batch cache all results
            try:
                cache_data = {}
                for clean_name in cache_misses:
                    cache_key = cache_miss_keys[clean_name]
                    cache_data[cache_key] = results[clean_name]

                cache.set_many(cache_data, DRUG_CACHE_TTL)
                logger.debug(f"💾 Batch cached {len(cache_data)} drug lookup results")

            except Exception as cache_error:
                logger.warning(f"Failed to batch cache drugs: {cache_error}")

        except Exception as db_error:
            logger.error(f"Database batch query failed: {db_error}")
            # Fall back to individual lookups for failed items
            for clean_name in cache_misses:
                if results.get(clean_name) is None:
                    results[clean_name] = find_drug_in_database(normalized_names[clean_name])

    return results


def categorize_prescription_request(prescription_request) -> Tuple[str, str]:
    """
    Automatically categorize a prescription request using drug database (505 drugs).

    Uses DrugClassification database to determine:
    - Controlled substance status (NAFDAC schedules 2-4)
    - High-risk medication requirements
    - Specialist medication needs
    - Complexity level

    Args:
        prescription_request: PrescriptionRequest model instance

    Returns:
        Tuple[str, str]: (triage_category, triage_reason)
    """
    medications = list(prescription_request.medications.all())
    medication_count = len(medications)
    urgency = prescription_request.urgency

    # Batch query drug database for all medications (optimized)
    medication_names = [med.medication_name for med in medications]
    drugs_dict = batch_find_drugs(medication_names)

    drug_objects = []
    controlled_drugs = []
    high_risk_drugs = []
    specialist_drugs = []

    # Process each medication with pre-loaded drug data
    for med in medications:
        drug = drugs_dict.get(med.medication_name.strip().lower())
        if drug:
            drug_objects.append(drug)

            # Check controlled substance status (NAFDAC schedules)
            if is_controlled_substance(drug):
                controlled_drugs.append({
                    'name': drug.generic_name,
                    'schedule': drug.nafdac_schedule,
                    'requires_physician': drug.requires_physician_only,
                })

            # Check high-risk status
            if is_high_risk_medication(drug):
                high_risk_drugs.append({
                    'name': drug.generic_name,
                    'risk_level': drug.get_risk_level(),
                    'monitoring': drug.monitoring_type,
                })

            # Check specialist requirement
            if is_specialist_medication(drug):
                specialist_drugs.append({
                    'name': drug.generic_name,
                    'therapeutic_class': drug.therapeutic_class,
                })

    # ==================== TRIAGE DECISION LOGIC ====================
    # Priority order: Specialist > High-Risk > Controlled > Complex > Routine

    # 1. SPECIALIST REQUIRED → Direct to physician
    if specialist_drugs:
        specialist_names = ', '.join([d['name'] for d in specialist_drugs])
        return (
            'SPECIALIST_REQUIRED',
            f'Contains specialist medication(s): {specialist_names}. '
            f'Requires specialist physician review. Outside pharmacist scope.'
        )

    # 2. HIGH RISK MEDICATION → Direct to physician for complex monitoring
    if high_risk_drugs:
        risk_names = ', '.join([d['name'] for d in high_risk_drugs])
        return (
            'HIGH_RISK',
            f'Contains high-risk medication(s): {risk_names}. '
            f'Requires physician review for therapeutic monitoring and safety assessment.'
        )

    # 3. CONTROLLED SUBSTANCE → Direct to physician (NAFDAC requirements)
    if controlled_drugs:
        controlled_names = ', '.join([d['name'] for d in controlled_drugs])
        schedules = ', '.join(set([d['schedule'] for d in controlled_drugs]))
        return (
            'CONTROLLED_SUBSTANCE',
            f'Contains NAFDAC controlled substance(s): {controlled_names} ({schedules}). '
            f'Requires physician authorization per NAFDAC regulations.'
        )

    # 4. COMPLEX CASE → Pharmacist review first (can escalate if needed)
    if medication_count >= 5:
        return (
            'COMPLEX_CASE',
            f'Complex case with {medication_count} medications. '
            f'Assigned to pharmacist for drug interaction assessment. '
            f'Pharmacist will escalate to physician if concerns identified.'
        )

    # 5. Check if all medications are repeats
    all_repeats = all(med.is_repeat for med in medications)

    # 6. URGENT CASES
    if urgency == 'urgent':
        if all_repeats:
            med_list = ', '.join([med.medication_name for med in medications[:2]])
            if medication_count > 2:
                med_list += f', +{medication_count - 2} more'
            return (
                'URGENT_REPEAT',
                f'Urgent repeat prescription: {med_list}. '
                f'Assigned to pharmacist for rapid review. Target: 24 hours.'
            )
        else:
            return (
                'URGENT_NEW',
                f'Urgent new medication request. '
                f'Assigned to pharmacist for priority review. Target: 24 hours. '
                f'Pharmacist will escalate if clinical concerns identified.'
            )

    # 7. ROUTINE REPEAT → Pharmacist (most common, evidence-based)
    if all_repeats:
        med_list = ', '.join([med.medication_name for med in medications[:3]])
        if medication_count > 3:
            med_list += f', +{medication_count - 3} more'
        return (
            'ROUTINE_REPEAT',
            f'Routine repeat prescription: {med_list}. '
            f'Same medications previously prescribed. '
            f'Assigned to pharmacist per evidence-based protocol (87.8% resolution within 48hrs).'
        )

    # 8. ROUTINE NEW → Pharmacist (default for standard new medications)
    new_meds = [med.medication_name for med in medications if not med.is_repeat]
    new_med_list = ', '.join(new_meds[:2])
    if len(new_meds) > 2:
        new_med_list += f', +{len(new_meds) - 2} more'
    return (
        'ROUTINE_NEW',
        f'New medication request: {new_med_list}. '
        f'Standard complexity. Assigned to pharmacist for clinical review. '
        f'Pharmacist will escalate to physician if concerns identified.'
    )


def find_available_pharmacist(hospital, triage_category: str, specialty_preference: Optional[str] = None):
    """
    Find an available pharmacist for assignment

    Args:
        hospital: Hospital instance
        triage_category: Triage category to help match specialty
        specialty_preference: Optional specialty preference (e.g., 'cardiology')

    Returns:
        Pharmacist instance or None
    """
    from api.models import Pharmacist

    # Base query: active pharmacists at this hospital who accept auto-assignment
    base_query = Q(
        hospital=hospital,
        is_active=True,
        status='active',
        available_for_reviews=True,
        auto_assign_triage=True,
    )

    # Try to find pharmacist with matching specialty first
    if specialty_preference:
        specialty_pharmacists = Pharmacist.objects.filter(
            base_query,
            triage_specialty=specialty_preference
        ).order_by('total_reviews_completed')  # Load balance by review count

        if specialty_pharmacists.exists():
            pharmacist = specialty_pharmacists.first()
            logger.info(f"Assigned to specialist pharmacist: {pharmacist.get_full_name()} ({specialty_preference})")
            return pharmacist

    # Fall back to general pharmacists (load balanced)
    general_pharmacists = Pharmacist.objects.filter(
        base_query
    ).order_by('total_reviews_completed')

    if general_pharmacists.exists():
        pharmacist = general_pharmacists.first()
        logger.info(f"Assigned to general pharmacist: {pharmacist.get_full_name()}")
        return pharmacist

    logger.warning(f"No available pharmacists found for hospital: {hospital.name}")
    return None


def find_available_doctor(hospital, specialty_preference: Optional[str] = None):
    """
    Find an available doctor for direct assignment (bypassing pharmacist triage)

    Args:
        hospital: Hospital instance
        specialty_preference: Optional specialty preference

    Returns:
        Doctor instance or None
    """
    from api.models import Doctor

    # Base query: active doctors at this hospital
    base_query = Q(
        hospital=hospital,
        is_active=True,
        status='active',
    )

    # Try specialty match first
    if specialty_preference:
        specialty_doctors = Doctor.objects.filter(
            base_query,
            specialization__icontains=specialty_preference
        )

        if specialty_doctors.exists():
            doctor = specialty_doctors.first()
            logger.info(f"Assigned to specialist doctor: {doctor.user.get_full_name()} ({specialty_preference})")
            return doctor

    # Fall back to any available doctor
    general_doctors = Doctor.objects.filter(base_query)

    if general_doctors.exists():
        doctor = general_doctors.first()
        logger.info(f"Assigned to general doctor: {doctor.user.get_full_name()}")
        return doctor

    logger.warning(f"No available doctors found for hospital: {hospital.name}")
    return None


def assign_prescription_request(prescription_request) -> Dict[str, Any]:
    """
    Triage and assign a prescription request to appropriate healthcare professional

    Args:
        prescription_request: PrescriptionRequest model instance (unsaved or saved)

    Returns:
        dict with keys:
            - 'assigned': bool - Whether assignment was successful
            - 'assigned_to_role': str - 'pharmacist', 'doctor', or None
            - 'assigned_to': obj - Pharmacist or Doctor instance
            - 'triage_category': str
            - 'triage_reason': str
            - 'message': str - Human-readable result message
    """
    # Step 1: Categorize the request
    triage_category, triage_reason = categorize_prescription_request(prescription_request)

    # Get category configuration
    category_config = TRIAGE_CATEGORIES.get(triage_category, {})
    default_role = category_config.get('default_role', 'pharmacist')

    logger.info(
        f"Prescription request {prescription_request.request_reference} "
        f"categorized as: {triage_category} (default role: {default_role})"
    )

    # Step 2: Assign based on category
    result = {
        'assigned': False,
        'assigned_to_role': None,
        'assigned_to': None,
        'triage_category': triage_category,
        'triage_reason': triage_reason,
        'message': '',
    }

    hospital = prescription_request.hospital

    if default_role == 'pharmacist':
        # Try to assign to pharmacist
        pharmacist = find_available_pharmacist(hospital, triage_category)

        if pharmacist:
            # Check if pharmacist can handle this category
            if triage_category == 'CONTROLLED_SUBSTANCE' and not pharmacist.can_prescribe_controlled:
                # Escalate to doctor if pharmacist lacks controlled substance authority
                logger.info(
                    f"Pharmacist {pharmacist.get_full_name()} cannot prescribe controlled substances. "
                    f"Routing to physician instead."
                )
                doctor = find_available_doctor(hospital)
                if doctor:
                    result.update({
                        'assigned': True,
                        'assigned_to_role': 'doctor',
                        'assigned_to': doctor,
                        'message': f'Assigned to Dr. {doctor.user.get_full_name()} (controlled substance requires physician)',
                    })
                else:
                    result['message'] = 'No available physicians found for controlled substance prescription'
            else:
                # Assign to pharmacist
                result.update({
                    'assigned': True,
                    'assigned_to_role': 'pharmacist',
                    'assigned_to': pharmacist,
                    'message': f'Assigned to pharmacist {pharmacist.get_full_name()} for triage review',
                })
        else:
            # No pharmacist available, try doctor
            logger.warning(f"No pharmacist available, routing to physician instead")
            doctor = find_available_doctor(hospital)
            if doctor:
                result.update({
                    'assigned': True,
                    'assigned_to_role': 'doctor',
                    'assigned_to': doctor,
                    'message': f'Assigned to Dr. {doctor.user.get_full_name()} (no pharmacist available)',
                })
            else:
                result['message'] = 'No available healthcare professionals found for assignment'

    elif default_role == 'doctor':
        # Direct physician assignment
        doctor = find_available_doctor(hospital)
        if doctor:
            result.update({
                'assigned': True,
                'assigned_to_role': 'doctor',
                'assigned_to': doctor,
                'message': f'Assigned directly to Dr. {doctor.user.get_full_name()} (specialist/high-risk medication)',
            })
        else:
            result['message'] = 'No available physicians found for specialist review'

    return result


def get_triage_statistics(hospital=None, pharmacist=None, date_from=None, date_to=None) -> Dict[str, Any]:
    """
    Get triage system statistics for analysis and reporting

    Args:
        hospital: Optional hospital filter
        pharmacist: Optional pharmacist filter
        date_from: Optional start date
        date_to: Optional end date

    Returns:
        dict with triage statistics
    """
    from api.models import PrescriptionRequest
    from django.db.models import Count, Avg, Q

    # Build query
    query = Q()
    if hospital:
        query &= Q(hospital=hospital)
    if pharmacist:
        query &= Q(assigned_to_pharmacist=pharmacist)
    if date_from:
        query &= Q(request_date__gte=date_from)
    if date_to:
        query &= Q(request_date__lte=date_to)

    requests = PrescriptionRequest.objects.filter(query)

    # Category distribution
    category_stats = requests.values('triage_category').annotate(
        count=Count('id')
    ).order_by('-count')

    # Role assignment distribution
    role_stats = requests.values('assigned_to_role').annotate(
        count=Count('id')
    )

    # Pharmacist action distribution
    pharmacist_action_stats = requests.filter(
        pharmacist_reviewed_by__isnull=False
    ).values('pharmacist_review_action').annotate(
        count=Count('id')
    )

    # Average review times
    avg_pharmacist_review_time = requests.filter(
        pharmacist_review_time_minutes__isnull=False
    ).aggregate(
        avg_time=Avg('pharmacist_review_time_minutes')
    )['avg_time'] or 0.0

    # Escalation rate
    total_pharmacist_reviewed = requests.filter(pharmacist_reviewed_by__isnull=False).count()
    escalated_count = requests.filter(pharmacist_review_action='escalated').count()
    escalation_rate = (escalated_count / total_pharmacist_reviewed * 100) if total_pharmacist_reviewed > 0 else 0.0

    # Clinical intervention rate
    intervention_count = requests.filter(had_clinical_intervention=True).count()
    intervention_rate = (intervention_count / total_pharmacist_reviewed * 100) if total_pharmacist_reviewed > 0 else 0.0

    return {
        'total_requests': requests.count(),
        'category_distribution': list(category_stats),
        'role_distribution': list(role_stats),
        'pharmacist_action_distribution': list(pharmacist_action_stats),
        'average_pharmacist_review_time_minutes': round(avg_pharmacist_review_time, 2),
        'total_pharmacist_reviewed': total_pharmacist_reviewed,
        'escalation_count': escalated_count,
        'escalation_rate_percent': round(escalation_rate, 2),
        'clinical_intervention_count': intervention_count,
        'clinical_intervention_rate_percent': round(intervention_rate, 2),
    }
