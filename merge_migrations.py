# Script to merge migrations without interactive prompt
import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

# Import necessary modules
from django.db.migrations.executor import MigrationExecutor
from django.db import connections, DEFAULT_DB_ALIAS

connection = connections[DEFAULT_DB_ALIAS]
executor = MigrationExecutor(connection)

# Get conflicting migrations
conflicts = executor.loader.detect_conflicts()
print("Conflicting migrations:")
for app_label, conflict in conflicts.items():
    print(f"App: {app_label}")
    for migration in conflict:
        print(f"  - {migration}")

# Generate merge migration
from django.core.management import call_command
print("\nGenerating merge migration...")
call_command('makemigrations', 'api', '--merge', '--noinput')
print("Merge migration created successfully!")

# Apply migrations
print("\nApplying migrations...")
call_command('migrate')
print("Migrations applied successfully!")
