import os
import sys
import django

# Setup Django
sys.path.append(r'c:\Users\Lenovo\auction_web')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auction_web.settings')
django.setup()

from auction.models import Player
import pandas as pd

# Read Excel file
file_path = r'c:\Users\Lenovo\auction_web\IPL_2025_List.csv.xlsx'
print(f"Reading file: {file_path}")

df = pd.read_excel(file_path)

print(f"Total rows in file: {len(df)}")
print(f"Columns: {df.columns.tolist()}")
print("\nFirst 5 rows:")
print(df.head())

# Clear existing players first?
print("\nDo you want to:")
print("1. Keep Virat Kohli and add the rest (set_no will continue from current)")
print("2. DELETE ALL players and import fresh (recommended)")

choice = input("Enter 1 or 2: ")

if choice == "2":
    Player.objects.all().delete()
    print("Deleted all existing players")

# Import players
# You'll need to tell me the exact column names from your Excel file
# Common patterns:
# - 'Set No' or 'set_no' or 'Set' or 'S.No'
# - 'Name' or 'Player Name' or 'PLAYER'
# - 'Role' or 'Type' or 'Category'
# - 'Country' or 'Nationality'
# - 'Base Price' or 'Price' or 'Reserve Price'

# Example import (adjust column names):
count = 0
for index, row in df.iterrows():
    try:
        Player.objects.create(
            name=row['Name'],  # Adjust column name
            role=row['Role'],  # Adjust column name
            country=row['Country'],  # Adjust column name
            base_price=int(row['Base Price']),  # Adjust column name
            set_no=int(row['Set No'])  # Adjust column name
        )
        count += 1
        if count % 50 == 0:
            print(f"Imported {count} players...")
    except Exception as e:
        print(f"Error importing row {index}: {e}")
        print(f"Row data: {row}")
        break

print(f"\nSuccessfully imported {count} players!")
print(f"Total players in database: {Player.objects.count()}")
