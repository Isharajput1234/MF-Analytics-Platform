
import pandas as pd
from pathlib import Path

folder = Path("data/processed")

files = [
    "03_aum_by_fund_house.csv",
    "04_monthly_sip_inflows.csv",
    "05_category_inflows.csv",
    "06_industry_folio_count.csv",
    "09_portfolio_holdings.csv",
    "10_benchmark_indices.csv",
]

for filename in files:
    df = pd.read_csv(folder / filename)

    print(f"\n--- {filename} ---")
    print("Rows:", len(df))
    print("Duplicate rows:", df.duplicated().sum())
    print("Missing cells:", df.isna().sum().sum())
    print("Columns:", df.columns.tolist())

    for column in df.select_dtypes(include="number").columns:
        print(
            f"{column}: min={df[column].min()}, "
            f"max={df[column].max()}"
        )

# Check portfolio weight totals per fund
holdings = pd.read_csv(folder / "09_portfolio_holdings.csv")

weight_totals = (
    holdings.groupby("amfi_code")["weight_pct"]
    .sum()
    .round(2)
)

print("\n--- PORTFOLIO WEIGHT AUDIT ---")
print(weight_totals.to_string())
print("\nFunds checked:", len(weight_totals))
print(
    "Funds with total weight above 100%:",
    (weight_totals > 100).sum()
)
