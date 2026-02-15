"""
Simple script to import all IPL 2025 players
Run: python import_all_players.py
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
print("IPL 2025 PLAYER IMPORT SCRIPT")
print("=" * 70)

# File path - RIGHT IN THIS DIRECTORY
file_path = os.path.join(os.path.dirname(__file__), 'IPL_2025_List.csv.xlsx')

if not os.path.exists(file_path):
    print(f"ERROR: File not found at {file_path}")
    sys.exit(1)

print(f"\n✓ Found file: {file_path}")

# Read Excel
try:
    df = pd.read_excel(file_path)
    print(f"✓ File loaded successfully")
    print(f"✓ Found {len(df)} rows")
except Exception as e:
    print(f"ERROR reading file: {e}")
    sys.exit(1)

# Show columns
print(f"\nColumns in file: {', '.join(df.columns.tolist())}")

# Show first row
print("\nFirst player sample:")
first_row = df.iloc[0]
for col in df.columns:
    print(f"  {col}: {first_row[col]}")

# Confirm
if not os.environ.get('RENDER'):
    response = input("Delete ALL existing players and import these? (y/yes): ")

    if response.lower() not in ['y', 'yes']:
        print("Import cancelled")
        sys.exit(0)
else:
    print("Running in Render environment - skipping confirmation prompt.")

# Delete existing
deleted_count = Player.objects.count()
Player.objects.all().delete()
print(f"\n✓ Deleted {deleted_count} existing players")

# Import
print("\nImporting players...")
count = 0
errors = []

# Detect column names - SPECIFIC to IPL_2025_List.csv.xlsx
first_name_col = None
surname_col = None
role_col = None
country_col = None
price_col = None
set_col = None
age_col = None
hand_col = None
bowling_col = None

for col in df.columns:
    col_lower = col.lower().strip()
    
    if 'first' in col_lower and 'name' in col_lower:
        first_name_col = col
    elif 'surname' in col_lower:
        surname_col = col
    elif 'specialism' in col_lower or 'type' in col_lower or 'role' in col_lower:
        role_col = col
    elif 'country' in col_lower:
        country_col = col
    elif 'price' in col_lower:
        price_col = col
    elif 'set' in col_lower and 'no' in col_lower:
        set_col = col
    elif 'age' in col_lower:
        age_col = col
    elif 'hand' in col_lower:
        hand_col = col
    elif 'bowling' in col_lower:
        bowling_col = col

print(f"\nDetected columns:")
print(f"  First Name: {first_name_col}")
print(f"  Surname: {surname_col}")
print(f"  Role/Specialism: {role_col}")
print(f"  Country: {country_col}")
print(f"  Price: {price_col}")
print(f"  Set No: {set_col}")
print(f"  Age: {age_col}")
print(f"  Hand: {hand_col}")
print(f"  Bowling: {bowling_col}\n")

for index, row in df.iterrows():
    try:
        # Combine First Name + Surname
        first = str(row[first_name_col] if first_name_col else '').strip()
        last = str(row[surname_col] if surname_col else '').strip()
        name = f"{first} {last}".strip()
        
        if not name:
            name = f"Player_{index}"
        
        # Role/Specialism
        role = str(row[role_col] if role_col else 'BAT').strip()[:20]
        if not role or role == 'nan':
            role = 'BAT'
        
        # Country
        country = str(row[country_col] if country_col else 'India').strip()
        if not country or country == 'nan':
            country = 'India'
        
        # Parse price
        try:
            price_val = row[price_col] if price_col else 200
            if isinstance(price_val, str):
                price_val = price_val.replace(',', '').replace('₹', '').strip()
            base_price = int(float(price_val))
        except:
            base_price = 200
        
        # Parse set_no
        try:
            set_no = int(row[set_col] if set_col else index + 1)
        except:
            set_no = index + 1
        
        # Parse Age
        try:
            age = int(row[age_col]) if age_col and pd.notna(row[age_col]) else None
        except:
            age = None

        # Parse Hand
        hand = str(row[hand_col]).strip() if hand_col and pd.notna(row[hand_col]) else None
        
        # Parse Bowling
        bowling = str(row[bowling_col]).strip() if bowling_col and pd.notna(row[bowling_col]) else None

        Player.objects.create(
            name=name,
            role=role,
            country=country,
            base_price=base_price,
            set_no=set_no,
            age=age,
            hand=hand,
            bowling=bowling
        )
        count += 1
        
        if count % 100 == 0:
            print(f"  Imported {count} players...")
            
    except Exception as e:
        errors.append((index, str(e), dict(row)))
        if len(errors) <= 3:
            print(f"  ERROR at row {index}: {e}")

print("\n" + "=" * 70)
print(f"✓ Successfully imported {count} players!")

if errors:
    print(f"✗ {len(errors)} errors occurred")
    if len(errors) <= 5:
        for idx, err, data in errors:
            print(f"  Row {idx}: {err}")

print(f"\nTotal players in database: {Player.objects.count()}")

# Show first 10
print("\nFirst 10 players by set_no:")
for p in Player.objects.all().order_by('set_no')[:10]:
    print(f"  {p.set_no:3d}. {p.name:30s} ({p.role:4s}) - ₹{p.base_price}")

print("\n" + "=" * 70)
print("IMPORT COMPLETE! Restart your Django server and test the auction.")
print("=" * 70)
