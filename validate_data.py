import pandas as pd
from pathlib import Path

raw_data_path = Path("data/raw")

# Load fund master
fund_master = pd.read_csv(raw_data_path / "01_fund_master.csv")

# Get valid AMFI codes
master_codes = set(fund_master["amfi_code"])

print("Fund Master AMFI Codes:", len(master_codes))

# Files that should contain AMFI codes
files_to_check = [
    "02_nav_history.csv",
    "07_scheme_performance.csv",
    "08_investor_transactions.csv",
    "09_portfolio_holdings.csv"
]

for filename in files_to_check:

    df = pd.read_csv(raw_data_path / filename)

    dataset_codes = set(df["amfi_code"])

    missing_codes = dataset_codes - master_codes

    print("\n" + "=" * 60)
    print("FILE:", filename)
    print("Unique AMFI codes:", len(dataset_codes))
    print("Missing from fund master:", len(missing_codes))

    if missing_codes:
        print("Missing codes:", missing_codes)
    else:
        print("✓ All AMFI codes are valid")