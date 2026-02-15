
import pandas as pd
import sys

try:
    df = pd.read_excel('IPL_2025_List.csv.xlsx')
    print("Columns found:")
    for col in df.columns.tolist():
        print(f" - {col}")
except Exception as e:
    print(f"Error: {e}")
