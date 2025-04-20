import requests
from django.conf import settings

def get_location_from_ip(ip_address):
    """
    Get location information from IP address using ipapi.co service.
    Returns dict with latitude, longitude, city, country.
    """
    try:
        response = requests.get(f'https://ipapi.co/{ip_address}/json/')
        if response.status_code == 200:
            data = response.json()
            return {
                'latitude': data.get('latitude'),
                'longitude': data.get('longitude'),
                'city': data.get('city'),
                'country': data.get('country_name')
            }
    except Exception:
        pass
    
    return None 