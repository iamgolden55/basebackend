import geoip2.database
import os
from django.conf import settings

def get_location_from_ip(ip_address):
    """
    Get location information from an IP address using MaxMind GeoIP2 database.
    Returns a dictionary containing country, city, and state information.
    """
    try:
        # Path to the GeoIP2 database file
        db_path = os.path.join(settings.BASE_DIR, 'geoip2', 'GeoLite2-City.mmdb')
        
        # Create a reader object
        with geoip2.database.Reader(db_path) as reader:
            # Get the location information
            response = reader.city(ip_address)
            
            return {
                'country': response.country.name,
                'city': response.city.name,
                'state': response.subdivisions.most_specific.name if response.subdivisions.most_specific else None
            }
    except Exception as e:
        # If there's any error, return None for all fields
        return {
            'country': None,
            'city': None,
            'state': None
        } 