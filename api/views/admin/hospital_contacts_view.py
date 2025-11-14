from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.views import APIView
from django.utils import timezone
from datetime import timedelta

class HospitalAdminContactsView(APIView):
    """
    Hospital Administrator Communication Hub
    For the platform owner to communicate with actual hospital admin users (like admin.stnicholas65@example.com)
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get(self, request):
        try:
            from api.models.medical.hospital_auth import HospitalAdmin
            
            # Get all hospital admin users
            hospital_admins = HospitalAdmin.objects.select_related('user', 'hospital').all()
            
            # Recently created admins (by user date_joined)
            recently_active = hospital_admins.filter(
                user__date_joined__gte=timezone.now() - timedelta(days=30)
            ).order_by('-user__date_joined')[:10]
            
            # Organize contacts by categories
            contacts_data = {
                'recently_active': [],
                'by_hospital_type': {
                    'public': [],
                    'private': [],
                    'specialist': [],
                    'teaching': [],
                    'clinic': [],
                    'research': []
                },
                'by_region': {},
                'all_admins': [],
                'active_admins': []
            }
            
            # Process recently active admins
            for admin in recently_active:
                admin_data = {
                    'id': admin.id,
                    'user_id': admin.user.id,
                    'name': admin.name,
                    'admin_email': admin.email,
                    'user_email': admin.user.email,
                    'contact_email': admin.contact_email,
                    'position': admin.position,
                    'hospital_name': admin.hospital.name,
                    'hospital_id': admin.hospital.id,
                    'hospital_type': admin.hospital.hospital_type,
                    'hospital_verified': admin.hospital.is_verified,
                    'address': f"{admin.hospital.city}, {admin.hospital.state}",
                    'country': admin.hospital.country,
                    'phone': admin.user.phone,
                    'last_login': admin.user.last_login,
                    'date_joined': admin.user.date_joined,
                    'is_active': admin.user.is_active,
                    'status': 'active' if admin.user.is_active else 'inactive'
                }
                contacts_data['recently_active'].append(admin_data)
            
            # Organize all admins by hospital type
            for admin in hospital_admins:
                hospital_type = admin.hospital.hospital_type.lower() if admin.hospital.hospital_type else 'clinic'
                if hospital_type in contacts_data['by_hospital_type']:
                    admin_data = {
                        'id': admin.id,
                        'user_id': admin.user.id,
                        'name': admin.name,
                        'admin_email': admin.email,
                        'user_email': admin.user.email,
                        'contact_email': admin.contact_email,
                        'position': admin.position,
                        'hospital_name': admin.hospital.name,
                        'hospital_type': admin.hospital.hospital_type,
                        'hospital_verified': admin.hospital.is_verified,
                        'address': f"{admin.hospital.city}, {admin.hospital.state}",
                        'phone': admin.user.phone,
                        'last_login': admin.user.last_login,
                        'is_active': admin.user.is_active,
                        'status': 'active' if admin.user.is_active else 'inactive'
                    }
                    contacts_data['by_hospital_type'][hospital_type].append(admin_data)
            
            # Organize by region
            for admin in hospital_admins:
                region = f"{admin.hospital.state}, {admin.hospital.country}" if admin.hospital.state else admin.hospital.country
                if region not in contacts_data['by_region']:
                    contacts_data['by_region'][region] = []
                
                contacts_data['by_region'][region].append({
                    'id': admin.id,
                    'user_id': admin.user.id,
                    'name': admin.name,
                    'admin_email': admin.email,
                    'hospital_name': admin.hospital.name,
                    'hospital_type': admin.hospital.hospital_type,
                    'city': admin.hospital.city,
                    'is_active': admin.user.is_active,
                    'last_login': admin.user.last_login
                })
            
            # All admins list
            for admin in hospital_admins:
                admin_data = {
                    'id': admin.id,
                    'user_id': admin.user.id,
                    'name': admin.name,
                    'admin_email': admin.email,
                    'user_email': admin.user.email,
                    'contact_email': admin.contact_email,
                    'position': admin.position,
                    'hospital_name': admin.hospital.name,
                    'hospital_type': admin.hospital.hospital_type,
                    'hospital_verified': admin.hospital.is_verified,
                    'address': f"{admin.hospital.city}, {admin.hospital.state}",
                    'country': admin.hospital.country,
                    'phone': admin.user.phone,
                    'last_login': admin.user.last_login,
                    'date_joined': admin.user.date_joined,
                    'is_active': admin.user.is_active,
                    'status': 'active' if admin.user.is_active else 'inactive'
                }
                contacts_data['all_admins'].append(admin_data)
                
                # Active admins only
                if admin.user.is_active:
                    contacts_data['active_admins'].append(admin_data)
            
            # Summary statistics
            total_admins = hospital_admins.count()
            active_admins = hospital_admins.filter(user__is_active=True).count()
            verified_hospital_admins = hospital_admins.filter(hospital__is_verified=True).count()
            
            # Get actual hospital counts by type (not admin counts)
            from api.models.medical.hospital import Hospital
            
            # Count unique hospitals by type
            hospital_type_counts = {
                'public': Hospital.objects.filter(hospital_type='public').count(),
                'private': Hospital.objects.filter(hospital_type='private').count(),
                'specialist': Hospital.objects.filter(hospital_type='specialist').count(),
                'teaching': Hospital.objects.filter(hospital_type='teaching').count(),
                'clinic': Hospital.objects.filter(hospital_type='clinic').count(),
                'research': Hospital.objects.filter(hospital_type='research').count()
            }
            
            # Also provide admin counts for reference
            admin_type_counts = {
                'public': len(contacts_data['by_hospital_type']['public']),
                'private': len(contacts_data['by_hospital_type']['private']),
                'specialist': len(contacts_data['by_hospital_type']['specialist']),
                'teaching': len(contacts_data['by_hospital_type']['teaching']),
                'clinic': len(contacts_data['by_hospital_type']['clinic']),
                'research': len(contacts_data['by_hospital_type']['research'])
            }
            
            summary = {
                'total_admins': total_admins,
                'active_admins': active_admins,
                'inactive_admins': total_admins - active_admins,
                'verified_hospital_admins': verified_hospital_admins,
                'pending_hospital_admins': total_admins - verified_hospital_admins,
                'recent_logins': hospital_admins.filter(
                    user__last_login__gte=timezone.now() - timedelta(days=7)
                ).count(),
                'regions': len(contacts_data['by_region']),
                'hospital_types': hospital_type_counts,  # Show actual hospital counts
                'admin_types': admin_type_counts  # Keep admin counts available if needed
            }
            
            return Response({
                'contacts': contacts_data,
                'summary': summary
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to fetch hospital admin contacts: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )