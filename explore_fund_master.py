import pandas as pd
from pathlib import Path

raw_data_path = Path("data/raw")

df = pd.read_csv(raw_data_path / "01_fund_master.csv")

print("=" * 60)
print("FUND MASTER EXPLORATION")
print("=" * 60)

print("\nColumns:")
print(df.columns.tolist())

print("\nTotal Schemes:", len(df))

print("\nFund Houses:")
print(df["fund_house"].value_counts())

print("\nCategories:")
print(df["category"].value_counts())

print("\nSub-Categories:")
print(df["sub_category"].value_counts())

print("\nMissing Values:")
print(df.isnull().sum())