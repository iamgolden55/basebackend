"""
Drug Database API Views

Provides endpoints for searching and retrieving drug information
from the comprehensive DrugClassification database (505+ drugs).
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from api.models import DrugClassification


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_drugs(request):
    """
    Search for drugs by name (generic, brand, or keyword)

    Query Parameters:
    - q: Search query (required)
    - limit: Maximum results to return (default: 10, max: 50)

    Returns:
    - List of matching drugs with basic information
    """
    search_query = request.GET.get('q', '').strip()
    limit = min(int(request.GET.get('limit', 10)), 50)

    if not search_query:
        return Response(
            {'error': 'Search query parameter "q" is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if len(search_query) < 2:
        return Response(
            {'error': 'Search query must be at least 2 characters'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Search in generic name, brand names, and keywords
    search_term_lower = search_query.lower()

    drugs = DrugClassification.objects.filter(
        Q(generic_name__icontains=search_query) |
        Q(brand_names__icontains=search_query) |
        Q(search_keywords__icontains=search_query),
        is_active=True
    ).values(
        'id',
        'generic_name',
        'brand_names',
        'therapeutic_class',
        'pharmacological_class',
        'nafdac_schedule',
        'is_controlled',
        'requires_physician_only',
        'mechanism_of_action'
    )[:limit]

    results = []
    for drug in drugs:
        # Create a simple description
        description = drug.get('mechanism_of_action', '') or drug.get('pharmacological_class', '') or drug.get('therapeutic_class', '')
        if not description:
            description = 'No description available'

        # Get brand names (limit to first 2)
        brand_names = drug.get('brand_names', [])
        brand_display = ', '.join(brand_names[:2]) if brand_names else ''

        results.append({
            'id': str(drug['id']),
            'name': drug['generic_name'],
            'description': description[:200],  # Limit description length
            'brand_names': brand_display,
            'category': drug.get('therapeutic_class', ''),
            'is_controlled': drug.get('is_controlled', False),
            'requires_physician': drug.get('requires_physician_only', False),
            'nafdac_schedule': drug.get('nafdac_schedule', 'unscheduled')
        })

    return Response({
        'count': len(results),
        'results': results,
        'query': search_query
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_drug_detail(request, drug_id):
    """
    Get detailed information about a specific drug

    Path Parameters:
    - drug_id: UUID of the drug

    Returns:
    - Complete drug information
    """
    try:
        drug = DrugClassification.objects.get(id=drug_id, is_active=True)
    except DrugClassification.DoesNotExist:
        return Response(
            {'error': 'Drug not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    return Response({
        'id': str(drug.id),
        'generic_name': drug.generic_name,
        'brand_names': drug.brand_names,
        'therapeutic_class': drug.therapeutic_class,
        'pharmacological_class': drug.pharmacological_class,
        'mechanism_of_action': drug.mechanism_of_action,

        # Regulatory
        'nafdac_approved': drug.nafdac_approved,
        'nafdac_registration_number': drug.nafdac_registration_number,
        'nafdac_schedule': drug.nafdac_schedule,
        'is_controlled': drug.is_controlled,

        # Prescribing
        'requires_physician_only': drug.requires_physician_only,
        'pharmacist_can_prescribe': drug.pharmacist_can_prescribe,
        'requires_special_prescription': drug.requires_special_prescription,
        'maximum_days_supply': drug.maximum_days_supply,

        # Risk
        'is_high_risk': drug.is_high_risk,
        'requires_monitoring': drug.requires_monitoring,
        'monitoring_type': drug.monitoring_type,
        'addiction_risk': drug.addiction_risk,
        'abuse_potential': drug.abuse_potential,

        # Contraindications
        'major_contraindications': drug.major_contraindications,
        'black_box_warning': drug.black_box_warning,
        'black_box_warning_text': drug.black_box_warning_text,

        # Interactions
        'major_drug_interactions': drug.major_drug_interactions,
        'food_interactions': drug.food_interactions,

        # Age & Pregnancy
        'minimum_age': drug.minimum_age,
        'pregnancy_category': drug.pregnancy_category,
        'breastfeeding_safe': drug.breastfeeding_safe,

        # Alternatives
        'safer_alternatives': drug.safer_alternatives,
        'cheaper_alternatives': drug.cheaper_alternatives,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_drug_statistics(request):
    """
    Get statistics about the drug database

    Returns:
    - Total drug count
    - Breakdown by category
    - Controlled substances count
    """
    from django.db.models import Count

    total_drugs = DrugClassification.objects.filter(is_active=True).count()
    controlled_drugs = DrugClassification.objects.filter(
        is_controlled=True,
        is_active=True
    ).count()
    high_risk_drugs = DrugClassification.objects.filter(
        is_high_risk=True,
        is_active=True
    ).count()

    # Count by NAFDAC schedule
    schedule_counts = DrugClassification.objects.filter(
        is_active=True
    ).values('nafdac_schedule').annotate(
        count=Count('id')
    ).order_by('-count')

    # Count by therapeutic class (top 10)
    therapeutic_counts = DrugClassification.objects.filter(
        is_active=True
    ).exclude(
        therapeutic_class=''
    ).values('therapeutic_class').annotate(
        count=Count('id')
    ).order_by('-count')[:10]

    return Response({
        'total_drugs': total_drugs,
        'controlled_substances': controlled_drugs,
        'high_risk_medications': high_risk_drugs,
        'nafdac_compliant': total_drugs,  # All drugs in DB are NAFDAC compliant
        'by_schedule': list(schedule_counts),
        'top_therapeutic_classes': list(therapeutic_counts)
    })
