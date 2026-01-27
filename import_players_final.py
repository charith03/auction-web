"""
IPL 2025 Player Import - FIXED with EXACT column names
Run: python import_players_final.py
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auction_web.settings')
django.setup()

from auction.models import Player
import pandas as pd

print("=" * 70)
print("IPL 2025 PLAYER IMPORT - FINAL VERSION")
print("=" * 70)

file_path = r'C:\Users\Lenovo\auction_web\IPL_2025_List.csv.xlsx'

if not os.path.exists(file_path):
    print(f"ERROR: File not found at {file_path}")
    sys.exit(1)

print(f"\n✓ Found file")

# Read Excel
try:
    df = pd.read_excel(file_path)
    print(f"✓ Loaded {len(df)} rows")
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)

# Show first player as sample
print("\nSample - First player:")
first = df.iloc[0]
print(f"  Name: {first['First Name']} {first['Surname']}")
print(f"  Country: {first['Country']}")
print(f"  Role: {first['Specialism']}")
print(f"  Price: ₹{first['Price Rs']}")
print(f"  Set No: {first['Set No.']}")

# Confirm
print("\n" + "=" * 70)
response = input(f"Import all {len(df)} players? (y/n): ")

if response.lower() != 'y':
    print("Cancelled")
    sys.exit(0)

# Delete existing
Player.objects.all().delete()
print(f"\n✓ Cleared existing players")

# Import with EXACT column names
print("\nImporting...")
count = 0
errors = []

for index, row in df.iterrows():
    try:
        # Combine First Name + Surname
        first_name = str(row['First Name']).strip()
        surname = str(row['Surname']).strip()
        full_name = f"{first_name} {surname}".strip()
        
        # Get other fields
        country = str(row['Country']).strip()
        specialism = str(row['Specialism']).strip()[:20]  # Max 20 chars for role
        price = int(row['Price Rs'])
        set_no = int(row['Set No.'])
        
        # Additional fields
        try:
            age = int(row['Age'])
        except:
            age = None
        
        hand = str(row.get('Hand', '')).strip()[:10]
        if hand == 'nan' or not hand:
            hand = None
            
        bowling = str(row.get('Bowling', '')).strip()[:100]
        if bowling == 'nan' or not bowling:
            bowling = None
        
        #Create player with all fields
        Player.objects.create(
            name=full_name,
            role=specialism,
            country=country,
            base_price=price,
            set_no=set_no,
            age=age,
            hand=hand,
            bowling=bowling
        )
        count += 1
        
        if count % 100 == 0:
            print(f"  {count} players imported...")
            
    except Exception as e:
        errors.append((index + 1, str(e)))
        if len(errors) <= 3:
            print(f"  ERROR row {index + 1}: {e}")

print("\n" + "=" * 70)
print(f"✓ Successfully imported {count} players!")

if errors:
    print(f"✗ {len(errors)} errors")

print(f"\nTotal in database: {Player.objects.count()}")

# Show first 10
print("\nFirst 10 players:")
for p in Player.objects.all().order_by('set_no')[:10]:
    print(f"  {p.set_no:3d}. {p.name:30s} ({p.role:10s}) {p.country:10s} - ₹{p.base_price}")

print("\n" + "=" * 70)
print("DONE! Restart Django server and test the auction.")
print("=" * 70)
