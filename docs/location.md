# GeoIP2 Database Setup

This application uses MaxMind's GeoIP2 database for IP geolocation. To set this up:

1. Create a free account at [MaxMind.com](https://www.maxmind.com/en/geolite2/signup)
2. Download the GeoLite2 City database (mmdb format)
3. Place the downloaded database file in the `geoip2` directory as `GeoLite2-City.mmdb`

The application expects the database file to be located at: `geoip2/GeoLite2-City.mmdb`

If you don't have the database file, the application will still work but will return "Unknown" for location information. 