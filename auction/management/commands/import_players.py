"""
Django management command to import IPL 2025 players from Excel
Usage: python manage.py import_players
"""

from django.core.management.base import BaseCommand
from auction.models import Player
import pandas as pd
import os


class Command(BaseCommand):
    help = 'Import players from IPL_2025_List.csv.xlsx'

    def handle(self, *args, **options):
        # File path
        file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                 'IPL_2025_List.csv.xlsx')
        
        self.stdout.write(f"Reading file: {file_path}")
        
        # Read Excel
        df = pd.read_excel(file_path)
        
        self.stdout.write(f"Found {len(df)} players in file")
        self.stdout.write(f"Columns: {', '.join(df.columns.tolist())}")
        
        # Show first row for verification
        self.stdout.write("\nFirst row sample:")
        for col in df.columns:
            self.stdout.write(f"  {col}: {df.iloc[0][col]}")
        
        # Ask for confirmation
        response = input("\nDelete ALL existing players and import fresh? (yes/no): ")
        
        if response.lower() == 'yes':
            deleted = Player.objects.all().delete()
            self.stdout.write(f"Deleted {deleted[0]} existing players")
        
        # Import players
        # ADJUST THESE COLUMN NAMES based on what you see above!
        count = 0
        errors = 0
        
        for index, row in df.iterrows():
            try:
                # YOU NEED TO ADJUST THESE COLUMN NAMES!
                # Check the column names printed above and modify accordingly
                Player.objects.create(
                    name=str(row.get('PLAYER', row.get('Name', row.get('name', '')))).strip(),
                    role=str(row.get('Type', row.get('Role', row.get('role', 'BAT')))).strip()[:20],
                    country=str(row.get('Country', row.get('country', 'India'))).strip(),
                    base_price=int(row.get('Base Price', row.get('base_price', row.get('Price', 200)))),
                    set_no=int(row.get('S.No', row.get('Set No', row.get('set_no', index))))
                )
                count += 1
                
                if count % 100 == 0:
                    self.stdout.write(f"Imported {count} players...")
                    
            except Exception as e:
                errors += 1
                if errors <= 5:  # Only show first 5 errors
                    self.stdout.write(self.style.ERROR(f"Error at row {index}: {e}"))
                    self.stdout.write(f"Row data: {dict(row)}")
        
        self.stdout.write(self.style.SUCCESS(f"\n✓ Imported {count} players successfully!"))
        if errors > 0:
            self.stdout.write(self.style.WARNING(f"✗ {errors} errors occurred"))
        
        self.stdout.write(f"\nTotal players in database: {Player.objects.count()}")
        
        # Show first 5 players by set_no
        self.stdout.write("\nFirst 5 players:")
        for p in Player.objects.all().order_by('set_no')[:5]:
            self.stdout.write(f"  {p.set_no}: {p.name} ({p.role}) - ₹{p.base_price}")
