import pandas as pd
from pathlib import Path

raw_data_path = Path("data/raw")
csv_files = list(raw_data_path.glob("*.csv"))

for file in csv_files:
    df = pd.read_csv(file)

    print("\n" + "=" * 60)
    print(f"FILE: {file.name}")
    print("Shape:", df.shape)
    print("\nData Types:")
    print(df.dtypes)
    print("\nFirst 5 Rows:")
    print(df.head())