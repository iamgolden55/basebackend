# PHB Hospital System - Backend

[![License: CC BY-NC-SA 4.0](https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc-sa/4.0/)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Django](https://img.shields.io/badge/Django-4.2+-green.svg)](https://djangoproject.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://docker.com)

## ⚖️ **IMPORTANT: NON-COMMERCIAL LICENSE**

**This software is licensed under CC BY-NC-SA 4.0 - Commercial use is strictly prohibited.**

- ✅ **Educational and personal use allowed**
- ✅ **Must provide attribution to Golden/PHB**
- ✅ **Must share improvements under same license**
- ❌ **NO commercial use without explicit written permission**
- ⚖️ **Violations subject to legal action and damages**

For commercial licensing inquiries, contact the copyright holder.

## 🏥 About PHB Hospital System

Advanced hospital management system built with Django, featuring comprehensive patient care, medical records, appointment scheduling, and payment integration.

## Docker Setup Guide

This project has been containerized with Docker to simplify setup and development. Follow these instructions to get the application running quickly.

### Prerequisites

- [Docker](https://www.docker.com/products/docker-desktop/) installed on your system
- [Docker Compose](https://docs.docker.com/compose/install/) (usually included with Docker Desktop)
- Git (to clone the repository)

### Getting Started

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd basebackend
   ```

2. **Setup Environment Variables**

   Copy the example environment file and modify as needed:

   ```bash
   cp .env.example .env
   ```

   Edit the `.env` file with your specific configurations if needed.

3. **Build and Start the Containers**

   ```bash
   docker-compose up --build
   ```

   This will:
   - Build the Docker images
   - Start the Django web server
   - Start PostgreSQL database
   - Start Redis for caching
   - Run migrations automatically
   - Collect static files

4. **Access the Application**

   - Web application: http://localhost:8000
   - API endpoints: http://localhost:8000/api/
   - Admin interface: http://localhost:8000/admin/

### Security Features

This system implements several security measures:

1. **Hospital Admin Security**
   - Dedicated hospital admin login flow separate from regular users
   - Domain validation for hospital email addresses
   - Required hospital code verification
   - Mandatory 2FA for all hospital admins
   - Enhanced security with trusted device tracking

2. **Login Protection**
   - IP-based rate limiting after 3 failed attempts
   - Account lockout for 15 minutes after 5 failed attempts
   - Email alerts sent after 3 failed login attempts
   - Account lockout is automatically cleared after successful password reset
   - Comprehensive logging of security events

3. **Hospital Registration**
   - Automatic administrator account generation with secure credentials
   - Welcome email with login instructions and credentials
   - Hospital code provided for secure login process

### Development Workflow

- **View logs**
  ```bash
  docker-compose logs -f
  ```

- **Access a container shell**
  ```bash
  docker-compose exec web bash
  ```

- **Run Django management commands**
  ```bash
  docker-compose exec web python manage.py <command>
  ```

- **Create a superuser**
  ```bash
  docker-compose exec web python manage.py createsuperuser
  ```

### Stopping the Application

```bash
docker-compose down
```

To completely clean up volumes as well:

```bash
docker-compose down -v
```

### Troubleshooting

1. **Database connection issues**
   - Check that the database container is running: `docker-compose ps`
   - Verify the database credentials in your `.env` file

2. **Redis connection issues**
   - Ensure the Redis container is running: `docker-compose ps`
   - Check the Redis URL configuration

## 📄 License

Copyright (c) 2025 Golden (Public Health Bureau)

This project is licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License. See the [LICENSE](LICENSE) file for details.

**Commercial use is strictly prohibited.** Contact the copyright holder for commercial licensing.