#!/bin/bash
set -e

echo "Exporting database..."
PGPASSWORD=publichealth pg_dump -h localhost -U medic_db -d medic_db -F c -f ./backup/db_dump.dump

echo "Database exported to backup/db_dump.dump"
echo "This file will be automatically imported when your friends run the Docker setup."
