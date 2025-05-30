# Docker Setup for Medical Collaboration Backend

This guide explains how to run the entire medical collaboration backend system using Docker, including all pre-populated database data.

## Prerequisites

- [Docker](https://www.docker.com/products/docker-desktop) installed on your system
- [Docker Compose](https://docs.docker.com/compose/install/) (usually included with Docker Desktop)

## Setup Instructions

### 1. Export Your Current Database (For Project Owner)

This step is only for the person who has the project with data already set up. It exports the existing database to a file:

```bash
# Navigate to the project directory
cd /path/to/basebackend

# Create the backup directory if it doesn't exist
mkdir -p backup

# Run the export script
./scripts/export_db.sh
```

The database will be exported to `backup/db_dump.dump`.

### 2. Running the Application (For Everyone)

```bash
# Navigate to the project directory
cd /path/to/basebackend

# Start the Docker containers
docker-compose up -d

# To see the logs
docker-compose logs -f
```

The application will automatically:

1. Import the database (if a `backup/db_dump.dump` file exists)
2. Run database migrations (if needed)
3. Collect static files
4. Start the web server

### 3. Accessing the Application

- Backend API: [http://localhost:8000/api/](http://localhost:8000/api/)
- Admin panel: [http://localhost:8000/admin/](http://localhost:8000/admin/)

### 4. Important Environment Variables

The `.env.example` file contains all the necessary environment variables with default values. For testing purposes, these defaults should work fine. In a production environment, you would need to update these with real values.

### 5. Default Hospital Admin Credentials

Following the hospital admin system design, the system automatically generates admin accounts when a hospital is registered. For development/testing purposes:

- Hospital code format: H-{random_hex}
- Admin login email format: admin.hospitalname@example.com
- Password: Generated securely in production, but uses predictable defaults in DEBUG mode

### 6. Security Features

The system includes several security features as detailed in the hospital admin login flow:

- Domain validation for hospital email addresses
- Required hospital code verification
- Rate limiting after 3 failed attempts
- Account lockout for 15 minutes after 5 failed attempts

### 7. Stopping the Application

```bash
# Stop the containers
docker-compose down

# To stop and remove volumes (this will delete all data)
docker-compose down -v
```

## Troubleshooting

### Database Issues

If you encounter database connection issues:

```bash
# Connect to the running web container
docker-compose exec web bash

# Run migrations manually
python manage.py migrate
```

### Missing Media Files

If media files are missing, ensure the media directory is properly mounted:

```bash
# Verify the volume mounts
docker-compose config
```

## Container Services

- **web**: Django application
- **db**: PostgreSQL database
- **redis**: Redis for caching and session management
