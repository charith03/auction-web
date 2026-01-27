import pandas as pd

file_path = r'c:\Users\Lenovo\auction_web\IPL_2025_List.csv.xlsx'
df = pd.read_excel(file_path)

print("=" * 60)
print("FILE STRUCTURE ANALYSIS")
print("=" * 60)
print(f"\nTotal rows: {len(df)}")
print(f"\nColumn names:")
for i, col in enumerate(df.columns, 1):
    print(f"  {i}. {col}")

print("\n" + "=" * 60)
print("FIRST 3 ROWS:")
print("=" * 60)
print(df.head(3).to_string())

print("\n" + "=" * 60)
print("DATA TYPES:")
print("=" * 60)
print(df.dtypes)
