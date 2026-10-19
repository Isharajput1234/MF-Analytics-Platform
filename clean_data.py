
from pathlib import Path
import pandas as pd

# Project folders
RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def clean_csv(file_path):
    """Clean one CSV file and save it in processed folder."""

    df = pd.read_csv(file_path)
    original_rows = len(df)

    # Remove completely duplicated rows
    df = df.drop_duplicates()

    # 1. Clean NAV history
    if file_path.name == "02_nav_history.csv":
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df["nav"] = pd.to_numeric(df["nav"], errors="coerce")
        df["amfi_code"] = df["amfi_code"].astype("string")

        df = df.dropna(subset=["amfi_code", "date", "nav"])
        df = df[df["nav"] > 0]
        df = df.sort_values(["amfi_code", "date"])

        # Keep one record per fund per date
        df = df.drop_duplicates(
            subset=["amfi_code", "date"],
            keep="last"
        )

        df["date"] = df["date"].dt.strftime("%Y-%m-%d")

    # 2. Clean investor transactions
    elif file_path.name == "08_investor_transactions.csv":
        df["transaction_date"] = pd.to_datetime(
            df["transaction_date"], errors="coerce"
        )
        df["amount_inr"] = pd.to_numeric(
            df["amount_inr"], errors="coerce"
        )

        # Standardize transaction type without changing SIP to Sip
        df["transaction_type"] = (
            df["transaction_type"].astype("string").str.strip().str.lower()
        )
        type_mapping = {
            "sip": "SIP",
            "lumpsum": "Lumpsum",
            "redemption": "Redemption",
        }
        df["transaction_type"] = df["transaction_type"].map(type_mapping)

        df["kyc_status"] = (
            df["kyc_status"].astype("string").str.strip().str.title()
        )

        df = df.dropna(
            subset=[
                "investor_id",
                "transaction_date",
                "amfi_code",
                "transaction_type",
                "amount_inr",
                "kyc_status",
            ]
        )
        df = df[df["amount_inr"] > 0]
        df = df[df["kyc_status"].isin(["Verified", "Pending"])]

        df["transaction_date"] = (
            df["transaction_date"].dt.strftime("%Y-%m-%d")
        )

    # 3. Clean scheme performance
    elif file_path.name == "07_scheme_performance.csv":
        numeric_columns = [
            "return_1yr_pct",
            "return_3yr_pct",
            "return_5yr_pct",
            "benchmark_3yr_pct",
            "alpha",
            "beta",
            "sharpe_ratio",
            "sortino_ratio",
            "std_dev_ann_pct",
            "max_drawdown_pct",
            "aum_crore",
            "expense_ratio_pct",
            "morningstar_rating",
        ]

        for column in numeric_columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")

        # Remove rows missing essential performance fields
        df = df.dropna(
            subset=["amfi_code", "scheme_name", "expense_ratio_pct"]
        )

        # Keep the assignment's specified expense ratio range
        df = df[df["expense_ratio_pct"].between(0.1, 2.5)]

    # 4. Clean monthly AUM
    elif file_path.name == "03_aum_by_fund_house.csv":
        # Keep rows after removing exact duplicates
        pass

    # Save processed file using the original filename
    output_path = PROCESSED_DIR / file_path.name
    df.to_csv(output_path, index=False)

    print(
        f"{file_path.name}: "
        f"{original_rows:,} -> {len(df):,} rows"
    )


def main():
    if not RAW_DIR.exists():
        print("ERROR: data/raw folder was not found.")
        return

    csv_files = sorted(RAW_DIR.glob("*.csv"))

    if not csv_files:
        print("ERROR: No CSV files found in data/raw.")
        return

    print(f"Found {len(csv_files)} CSV files.\n")

    for file_path in csv_files:
        try:
            clean_csv(file_path)
        except Exception as error:
            print(f"ERROR in {file_path.name}: {error}")

    print("\nInitial cleaning finished.")
    print(f"Processed files saved in: {PROCESSED_DIR.resolve()}")
    print(
        "Note: NAV holiday/weekend forward-fill and full data "
        "quality checks are not implemented yet."
    )


if __name__ == "__main__":
    main()
