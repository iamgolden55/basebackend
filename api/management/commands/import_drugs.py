# api/management/commands/import_drugs.py

import csv
import json
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from api.models import DrugClassification


class Command(BaseCommand):
    help = 'Import drug classifications from CSV or JSON file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            required=True,
            help='Path to CSV or JSON file containing drug data',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing drug data before importing',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Validate data without actually importing',
        )

    def handle(self, *args, **options):
        file_path = options['file']
        clear_existing = options['clear']
        dry_run = options['dry_run']

        # Determine file type
        if file_path.endswith('.csv'):
            file_type = 'csv'
        elif file_path.endswith('.json'):
            file_type = 'json'
        else:
            raise CommandError('File must be either .csv or .json')

        self.stdout.write(self.style.SUCCESS(f'Starting Drug Import from {file_type.upper()} file'))
        self.stdout.write(f'File: {file_path}')

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))

        # Clear existing data if requested
        if clear_existing and not dry_run:
            count = DrugClassification.objects.count()
            DrugClassification.objects.all().delete()
            self.stdout.write(self.style.WARNING(f'Deleted {count} existing drugs'))

        # Import data
        try:
            if file_type == 'csv':
                drugs_data = self.read_csv(file_path)
            else:
                drugs_data = self.read_json(file_path)

            self.stdout.write(f'Found {len(drugs_data)} drugs to import')
            self.import_drugs(drugs_data, dry_run)

        except FileNotFoundError:
            raise CommandError(f'File not found: {file_path}')
        except Exception as e:
            raise CommandError(f'Import failed: {str(e)}')

    def read_json(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)

    def read_csv(self, file_path):
        drugs = []
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                drug_data = self.parse_csv_row(row)
                drugs.append(drug_data)
        return drugs

    def parse_csv_row(self, row):
        drug_data = {}
        # Required text fields (cannot be None)
        required_text_fields = ['generic_name']
        for field in required_text_fields:
            drug_data[field] = row.get(field, '').strip()

        # Optional text fields (can be empty string, but not None if blank=True without null=True)
        optional_text_fields = ['active_ingredients', 'nafdac_registration_number',
                               'nafdac_schedule', 'therapeutic_class', 'pharmacological_class',
                               'mechanism_of_action', 'monitoring_type',
                               'abuse_potential', 'pregnancy_category', 'food_interactions', 'notes']
        for field in optional_text_fields:
            drug_data[field] = row.get(field, '').strip()

        boolean_fields = ['nafdac_approved', 'who_essential_medicine', 'requires_physician_only',
                          'pharmacist_can_prescribe', 'is_controlled', 'is_high_risk',
                          'requires_monitoring', 'breastfeeding_safe', 'black_box_warning', 'is_active',
                          'addiction_risk']
        for field in boolean_fields:
            value = row.get(field, '').strip().lower()
            drug_data[field] = value in ['true', '1', 'yes']

        integer_fields = ['maximum_days_supply', 'monitoring_frequency_days', 'minimum_age', 'maximum_age']
        for field in integer_fields:
            value = row.get(field, '').strip()
            drug_data[field] = int(value) if value and value.isdigit() else None

        if row.get('nafdac_schedule_date', '').strip():
            try:
                drug_data['nafdac_schedule_date'] = datetime.strptime(
                    row['nafdac_schedule_date'].strip(), '%Y-%m-%d').date()
            except ValueError:
                drug_data['nafdac_schedule_date'] = None
        else:
            drug_data['nafdac_schedule_date'] = None

        list_fields = ['brand_names', 'major_contraindications', 'allergy_cross_reactions',
                       'major_drug_interactions', 'search_keywords', 'generic_variations',
                       'common_misspellings', 'safer_alternatives', 'cheaper_alternatives']
        for field in list_fields:
            value = row.get(field, '').strip()
            drug_data[field] = [item.strip() for item in value.split(',') if item.strip()] if value else []

        return drug_data

    @transaction.atomic
    def import_drugs(self, drugs_data, dry_run=False):
        success_count = 0
        error_count = 0

        for idx, drug_data in enumerate(drugs_data, 1):
            try:
                generic_name = drug_data.get('generic_name', 'Unknown')
                self.stdout.write(f'{idx}. {generic_name}... ', ending='')

                if dry_run:
                    drug = DrugClassification(**drug_data)
                    drug.clean()
                    self.stdout.write(self.style.SUCCESS('Valid'))
                    success_count += 1
                else:
                    drug, created = DrugClassification.objects.update_or_create(
                        generic_name=drug_data['generic_name'],
                        defaults=drug_data
                    )
                    if created:
                        self.stdout.write(self.style.SUCCESS('Created'))
                    else:
                        self.stdout.write(self.style.WARNING('Updated'))
                    success_count += 1

            except Exception as e:
                error_count += 1
                self.stdout.write(self.style.ERROR(f'Failed: {str(e)}'))

        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS(f'Successful: {success_count}'))
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f'Failed: {error_count}'))
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN: No data was imported'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Total drugs in database: {DrugClassification.objects.count()}'))
        self.stdout.write('='*60)