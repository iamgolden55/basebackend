# api/views/pharmacy_views.py

from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from api.auth import JWTCookieAuthentication
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Q
import logging

from api.models.medical.pharmacy import Pharmacy, NominatedPharmacy
from api.serializers import (
    PharmacySerializer,
    PharmacyListSerializer,
    NominatedPharmacySerializer,
    NominatedPharmacyListSerializer
)

User = get_user_model()
logger = logging.getLogger(__name__)


class PharmacyListView(APIView):
    """
    GET /api/pharmacies/ - List/search pharmacies
    """
    authentication_classes = [JWTCookieAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """
        Get list of pharmacies with optional filters
        Query params:
        - search: Search by name, city, postcode
        - city: Filter by city
        - electronic_prescriptions: Filter by electronic prescription capability
        - latitude: User latitude for distance calculation
        - longitude: User longitude for distance calculation
        - radius: Search radius in km (default: 50)
        """
        try:
            # Start with active pharmacies
            queryset = Pharmacy.objects.filter(is_active=True)

            # Search filter
            search = request.query_params.get('search', '').strip()
            if search:
                queryset = queryset.filter(
                    Q(name__icontains=search) |
                    Q(city__icontains=search) |
                    Q(postcode__icontains=search) |
                    Q(phb_pharmacy_code__icontains=search)
                )

            # City filter
            city = request.query_params.get('city', '').strip()
            if city:
                queryset = queryset.filter(city__iexact=city)

            # Electronic prescriptions filter
            electronic = request.query_params.get('electronic_prescriptions')
            if electronic and electronic.lower() in ['true', '1']:
                queryset = queryset.filter(electronic_prescriptions_enabled=True)

            # Location-based filtering (if lat/lng provided)
            user_lat = request.query_params.get('latitude')
            user_lng = request.query_params.get('longitude')

            # Prepare serializer context for distance calculation
            context = {
                'request': request
            }
            if user_lat and user_lng:
                try:
                    context['user_latitude'] = float(user_lat)
                    context['user_longitude'] = float(user_lng)
                except (ValueError, TypeError):
                    pass

            # Order by name
            queryset = queryset.order_by('name')

            # Serialize
            serializer = PharmacyListSerializer(queryset, many=True, context=context)

            return Response({
                'success': True,
                'count': queryset.count(),
                'pharmacies': serializer.data
            })

        except Exception as e:
            logger.error(f"Error fetching pharmacies: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error fetching pharmacies'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PharmacyDetailView(APIView):
    """
    GET /api/pharmacies/{id}/ - Get pharmacy details
    """
    authentication_classes = [JWTCookieAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        """Get detailed pharmacy information"""
        try:
            pharmacy = get_object_or_404(Pharmacy, pk=pk, is_active=True)

            # Prepare context for distance calculation
            context = {'request': request}
            user_lat = request.query_params.get('latitude')
            user_lng = request.query_params.get('longitude')

            if user_lat and user_lng:
                try:
                    context['user_latitude'] = float(user_lat)
                    context['user_longitude'] = float(user_lng)
                except (ValueError, TypeError):
                    pass

            serializer = PharmacySerializer(pharmacy, context=context)

            return Response({
                'success': True,
                'pharmacy': serializer.data
            })

        except Exception as e:
            logger.error(f"Error fetching pharmacy {pk}: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error fetching pharmacy details'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class NominatedPharmacyView(APIView):
    """
    GET /api/pharmacies/nominated/ - Get current nominated pharmacy
    POST /api/pharmacies/nominated/ - Nominate a pharmacy
    DELETE /api/pharmacies/nominated/ - Remove nomination
    """
    authentication_classes = [JWTCookieAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Get user's current nominated pharmacy"""
        try:
            nomination = NominatedPharmacy.objects.filter(
                user=request.user,
                is_current=True
            ).first()

            if not nomination:
                return Response({
                    'success': True,
                    'has_nomination': False,
                    'message': 'No current pharmacy nomination'
                })

            serializer = NominatedPharmacySerializer(nomination)

            return Response({
                'success': True,
                'has_nomination': True,
                'nomination': serializer.data
            })

        except Exception as e:
            logger.error(f"Error fetching nomination for user {request.user.id}: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error fetching nominated pharmacy'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        """Nominate a pharmacy (admin pharmacy or professional practice page)"""
        try:
            from api.models.professional.professional_practice_page import ProfessionalPracticePage

            pharmacy_id = request.data.get('pharmacy_id')
            practice_page_id = request.data.get('practice_page_id')
            nomination_type = request.data.get('nomination_type', 'repeat')
            notes = request.data.get('notes', '')

            # Must provide either pharmacy_id or practice_page_id
            if not pharmacy_id and not practice_page_id:
                return Response({
                    'success': False,
                    'message': 'Pharmacy ID or Practice Page ID is required'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Cannot provide both
            if pharmacy_id and practice_page_id:
                return Response({
                    'success': False,
                    'message': 'Cannot nominate both a pharmacy and practice page'
                }, status=status.HTTP_400_BAD_REQUEST)

            pharmacy = None
            practice_page = None

            # Validate admin pharmacy
            if pharmacy_id:
                try:
                    pharmacy = Pharmacy.objects.get(id=pharmacy_id, is_active=True, verified=True)
                except Pharmacy.DoesNotExist:
                    return Response({
                        'success': False,
                        'message': 'Pharmacy not found or inactive'
                    }, status=status.HTTP_404_NOT_FOUND)

            # Validate professional practice page
            if practice_page_id:
                try:
                    practice_page = ProfessionalPracticePage.objects.get(
                        id=practice_page_id,
                        is_published=True,
                        verification_status='verified',
                        service_type='in_store',
                        linked_registry_entry__professional_type='pharmacist'
                    )
                except ProfessionalPracticePage.DoesNotExist:
                    return Response({
                        'success': False,
                        'message': 'Practice page not found or not a verified pharmacy'
                    }, status=status.HTTP_404_NOT_FOUND)

            # End any previous current nominations
            NominatedPharmacy.objects.filter(
                user=request.user,
                is_current=True
            ).update(is_current=False, ended_at=timezone.now())

            # Create nomination
            nomination = NominatedPharmacy.objects.create(
                user=request.user,
                pharmacy=pharmacy,
                practice_page=practice_page,
                nomination_type=nomination_type,
                notes=notes,
                is_current=True
            )

            serializer = NominatedPharmacySerializer(nomination)

            return Response({
                'success': True,
                'message': 'Pharmacy nominated successfully',
                'nomination': serializer.data
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Error nominating pharmacy for user {request.user.id}: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error nominating pharmacy'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request):
        """Remove current pharmacy nomination"""
        try:
            nomination = NominatedPharmacy.objects.filter(
                user=request.user,
                is_current=True
            ).first()

            if not nomination:
                return Response({
                    'success': False,
                    'message': 'No current pharmacy nomination found'
                }, status=status.HTTP_404_NOT_FOUND)

            # End the nomination
            nomination.end_nomination()

            return Response({
                'success': True,
                'message': 'Pharmacy nomination removed successfully'
            })

        except Exception as e:
            logger.error(f"Error removing nomination for user {request.user.id}: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error removing pharmacy nomination'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class NominationHistoryView(APIView):
    """
    GET /api/pharmacies/nomination-history/ - Get nomination history
    """
    authentication_classes = [JWTCookieAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Get user's pharmacy nomination history"""
        try:
            nominations = NominatedPharmacy.objects.filter(
                user=request.user
            ).order_by('-nominated_at')

            serializer = NominatedPharmacyListSerializer(nominations, many=True)

            return Response({
                'success': True,
                'count': nominations.count(),
                'nominations': serializer.data
            })

        except Exception as e:
            logger.error(f"Error fetching nomination history for user {request.user.id}: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error fetching nomination history'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class NearbyPharmaciesView(APIView):
    """
    GET /api/pharmacies/nearby/ - Get nearby pharmacies based on user location
    """
    authentication_classes = [JWTCookieAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """
        Get pharmacies near user location
        Query params:
        - latitude: User latitude (required)
        - longitude: User longitude (required)
        - radius: Search radius in km (default: 10)
        - limit: Max number of results (default: 20)
        """
        try:
            user_lat = request.query_params.get('latitude')
            user_lng = request.query_params.get('longitude')

            if not user_lat or not user_lng:
                return Response({
                    'success': False,
                    'message': 'Latitude and longitude are required'
                }, status=status.HTTP_400_BAD_REQUEST)

            try:
                user_lat = float(user_lat)
                user_lng = float(user_lng)
            except (ValueError, TypeError):
                return Response({
                    'success': False,
                    'message': 'Invalid latitude or longitude'
                }, status=status.HTTP_400_BAD_REQUEST)

            radius = float(request.query_params.get('radius', 10))  # default 10km
            limit = int(request.query_params.get('limit', 20))  # default 20 results

            # Get active pharmacies with coordinates
            queryset = Pharmacy.objects.filter(
                is_active=True,
                latitude__isnull=False,
                longitude__isnull=False
            )

            # Prepare context for distance calculation
            context = {
                'request': request,
                'user_latitude': user_lat,
                'user_longitude': user_lng
            }

            # Serialize
            serializer = PharmacyListSerializer(queryset, many=True, context=context)

            # Filter by radius and sort by distance
            pharmacies_with_distance = [
                p for p in serializer.data
                if p.get('distance') is not None and p.get('distance') <= radius
            ]
            pharmacies_with_distance.sort(key=lambda x: x.get('distance', float('inf')))

            # Limit results
            pharmacies_with_distance = pharmacies_with_distance[:limit]

            return Response({
                'success': True,
                'count': len(pharmacies_with_distance),
                'pharmacies': pharmacies_with_distance,
                'radius_km': radius
            })

        except Exception as e:
            logger.error(f"Error fetching nearby pharmacies: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error fetching nearby pharmacies'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================================
# Admin Pharmacy Management (Hospital-affiliated pharmacies)
# ============================================================================

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated, permissions.IsAdminUser])
def create_pharmacy(request):
    """
    Admin-only: Create a new pharmacy (optionally hospital-affiliated)

    POST /api/pharmacies/create/

    Required fields:
    - phb_pharmacy_code: Unique PHB pharmacy code
    - name: Pharmacy name
    - address_line_1: Address line 1
    - city: City
    - postcode: Postal code
    - phone: Phone number

    Optional fields:
    - hospital_id: Hospital ID for affiliation
    - address_line_2: Address line 2
    - state: State
    - country: Country (default: Nigeria)
    - email: Email
    - website: Website
    - latitude: Latitude coordinate
    - longitude: Longitude coordinate
    - electronic_prescriptions_enabled: Boolean (default: False)
    - opening_hours: JSON object with opening hours
    - services_offered: JSON array of services
    - description: Description text
    - verified: Boolean (default: False)
    """
    try:
        from api.models.medical.hospital import Hospital

        # Extract data
        data = request.data

        # Validate hospital_id if provided
        hospital = None
        hospital_id = data.get('hospital_id')
        if hospital_id:
            try:
                hospital = Hospital.objects.get(id=hospital_id)
            except Hospital.DoesNotExist:
                return Response({
                    'success': False,
                    'message': f'Hospital with ID {hospital_id} not found'
                }, status=status.HTTP_404_NOT_FOUND)

        # Check for unique PHB pharmacy code
        phb_pharmacy_code = data.get('phb_pharmacy_code', '').strip()
        if not phb_pharmacy_code:
            return Response({
                'success': False,
                'message': 'PHB pharmacy code is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        if Pharmacy.objects.filter(phb_pharmacy_code=phb_pharmacy_code).exists():
            return Response({
                'success': False,
                'message': f'Pharmacy with code {phb_pharmacy_code} already exists'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Create pharmacy
        pharmacy = Pharmacy.objects.create(
            phb_pharmacy_code=phb_pharmacy_code,
            name=data.get('name', '').strip(),
            address_line_1=data.get('address_line_1', '').strip(),
            address_line_2=data.get('address_line_2', '').strip(),
            city=data.get('city', '').strip(),
            state=data.get('state', '').strip(),
            postcode=data.get('postcode', '').strip(),
            country=data.get('country', 'Nigeria'),
            phone=data.get('phone', '').strip(),
            email=data.get('email', '').strip(),
            website=data.get('website', '').strip(),
            latitude=data.get('latitude'),
            longitude=data.get('longitude'),
            electronic_prescriptions_enabled=data.get('electronic_prescriptions_enabled', False),
            opening_hours=data.get('opening_hours', {}),
            services_offered=data.get('services_offered', []),
            description=data.get('description', '').strip(),
            verified=data.get('verified', False),
            is_active=True,
            hospital=hospital
        )

        logger.info(f"✅ Pharmacy created: {pharmacy.name} ({pharmacy.phb_pharmacy_code})")
        if hospital:
            logger.info(f"   Affiliated with hospital: {hospital.name}")

        # Serialize and return
        serializer = PharmacySerializer(pharmacy)

        return Response({
            'success': True,
            'message': f'Pharmacy "{pharmacy.name}" created successfully',
            'pharmacy': serializer.data
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(f"❌ Error creating pharmacy: {str(e)}")
        return Response({
            'success': False,
            'message': f'Error creating pharmacy: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_hospital_pharmacies(request, hospital_id):
    """
    Get all pharmacies affiliated with a specific hospital

    GET /api/hospitals/{hospital_id}/pharmacies/
    """
    try:
        from api.models.medical.hospital import Hospital

        # Get hospital
        hospital = get_object_or_404(Hospital, id=hospital_id)

        # Get affiliated pharmacies
        pharmacies = Pharmacy.objects.filter(hospital=hospital, is_active=True)

        # Serialize
        serializer = PharmacyListSerializer(pharmacies, many=True)

        return Response({
            'success': True,
            'hospital_id': hospital_id,
            'hospital_name': hospital.name,
            'count': pharmacies.count(),
            'pharmacies': serializer.data
        })

    except Exception as e:
        logger.error(f"❌ Error fetching hospital pharmacies: {str(e)}")
        return Response({
            'success': False,
            'message': 'Error fetching hospital pharmacies'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@permission_classes([permissions.IsAuthenticated, permissions.IsAdminUser])
def update_pharmacy(request, pharmacy_id):
    """
    Admin-only: Update pharmacy details

    PUT /api/pharmacies/{pharmacy_id}/update/
    """
    try:
        from api.models.medical.hospital import Hospital

        # Get pharmacy
        pharmacy = get_object_or_404(Pharmacy, id=pharmacy_id)

        # Update fields
        data = request.data

        # Update hospital affiliation if provided
        hospital_id = data.get('hospital_id')
        if hospital_id is not None:
            if hospital_id == '':
                # Remove hospital affiliation
                pharmacy.hospital = None
            else:
                try:
                    hospital = Hospital.objects.get(id=hospital_id)
                    pharmacy.hospital = hospital
                except Hospital.DoesNotExist:
                    return Response({
                        'success': False,
                        'message': f'Hospital with ID {hospital_id} not found'
                    }, status=status.HTTP_404_NOT_FOUND)

        # Update other fields
        if 'name' in data:
            pharmacy.name = data['name'].strip()
        if 'address_line_1' in data:
            pharmacy.address_line_1 = data['address_line_1'].strip()
        if 'address_line_2' in data:
            pharmacy.address_line_2 = data['address_line_2'].strip()
        if 'city' in data:
            pharmacy.city = data['city'].strip()
        if 'state' in data:
            pharmacy.state = data['state'].strip()
        if 'postcode' in data:
            pharmacy.postcode = data['postcode'].strip()
        if 'country' in data:
            pharmacy.country = data['country']
        if 'phone' in data:
            pharmacy.phone = data['phone'].strip()
        if 'email' in data:
            pharmacy.email = data['email'].strip()
        if 'website' in data:
            pharmacy.website = data['website'].strip()
        if 'latitude' in data:
            pharmacy.latitude = data['latitude']
        if 'longitude' in data:
            pharmacy.longitude = data['longitude']
        if 'electronic_prescriptions_enabled' in data:
            pharmacy.electronic_prescriptions_enabled = data['electronic_prescriptions_enabled']
        if 'opening_hours' in data:
            pharmacy.opening_hours = data['opening_hours']
        if 'services_offered' in data:
            pharmacy.services_offered = data['services_offered']
        if 'description' in data:
            pharmacy.description = data['description'].strip()
        if 'verified' in data:
            pharmacy.verified = data['verified']
        if 'is_active' in data:
            pharmacy.is_active = data['is_active']

        pharmacy.save()

        logger.info(f"✅ Pharmacy updated: {pharmacy.name} ({pharmacy.phb_pharmacy_code})")

        # Serialize and return
        serializer = PharmacySerializer(pharmacy)

        return Response({
            'success': True,
            'message': f'Pharmacy "{pharmacy.name}" updated successfully',
            'pharmacy': serializer.data
        })

    except Exception as e:
        logger.error(f"❌ Error updating pharmacy: {str(e)}")
        return Response({
            'success': False,
            'message': f'Error updating pharmacy: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated, permissions.IsAdminUser])
def delete_pharmacy(request, pharmacy_id):
    """
    Admin-only: Delete (deactivate) a pharmacy

    DELETE /api/pharmacies/{pharmacy_id}/delete/
    """
    try:
        # Get pharmacy
        pharmacy = get_object_or_404(Pharmacy, id=pharmacy_id)

        # Soft delete - just deactivate
        pharmacy.is_active = False
        pharmacy.save()

        logger.info(f"🗑️ Pharmacy deactivated: {pharmacy.name} ({pharmacy.phb_pharmacy_code})")

        return Response({
            'success': True,
            'message': f'Pharmacy "{pharmacy.name}" has been deactivated'
        })

    except Exception as e:
        logger.error(f"❌ Error deleting pharmacy: {str(e)}")
        return Response({
            'success': False,
            'message': f'Error deleting pharmacy: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
