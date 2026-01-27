"""
Quick check script to verify Excel columns
"""
import pandas as pd

file_path = r'C:\Users\Lenovo\auction_web\IPL_2025_List.csv.xlsx'
df = pd.read_excel(file_path)

print("=" * 80)
print("EXCEL FILE STRUCTURE")
print("=" * 80)
print(f"\nTotal rows: {len(df)}")
print(f"\nExact column names (copy these!):")
for i, col in enumerate(df.columns, 1):
    print(f"  {i}. '{col}'")

print("\n" + "=" * 80)
print("FIRST 3 PLAYERS:")
print("=" * 80)
for i in range(min(3, len(df))):
    row = df.iloc[i]
    print(f"\nPlayer {i+1}:")
    for col in df.columns:
        print(f"  {col}: {row[col]}")
