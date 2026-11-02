"""Clean raw Bluestock mutual-fund CSV files into the processed data folder.

The script intentionally raises errors instead of silently continuing. This allows
run_pipeline.py to stop and restore the previous database if any input fails.
"""

from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

SPECIAL_COLUMNS = {
    "02_nav_history.csv": {
        "amfi_code", "date", "nav"
    },
    "08_investor_transactions.csv": {
        "investor_id", "transaction_date", "amfi_code",
        "transaction_type", "amount_inr", "kyc_status"
    },
    "07_scheme_performance.csv": {
        "amfi_code", "scheme_name", "expense_ratio_pct",
        "return_1yr_pct", "return_3yr_pct", "return_5yr_pct",
        "benchmark_3yr_pct", "alpha", "beta", "sharpe_ratio",
        "sortino_ratio", "std_dev_ann_pct", "max_drawdown_pct",
        "aum_crore", "morningstar_rating"
    },
    "03_aum_by_fund_house.csv": set(),
}


def require_columns(df: pd.DataFrame, required: set, filename: str) -> None:
    """Raise a clear error when required columns are absent."""
    missing = required - set(df.columns)
    if missing:
        raise ValueError(
            f"{filename} is missing required columns: {sorted(missing)}"
        )


def clean_csv(file_path: Path) -> tuple[int, int]:
    """Clean one CSV file and save it in the processed folder."""
    df = pd.read_csv(file_path)
    original_rows = len(df)

    required = SPECIAL_COLUMNS.get(file_path.name, set())
    require_columns(df, required, file_path.name)

    df = df.drop_duplicates()

    # 1. NAV history
    if file_path.name == "02_nav_history.csv":
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df["nav"] = pd.to_numeric(df["nav"], errors="coerce")
        df["amfi_code"] = df["amfi_code"].astype("string")
        df = df.dropna(subset=["amfi_code", "date", "nav"])
        df = df[df["nav"] > 0]
        df = df.sort_values(["amfi_code", "date"])
        df = df.drop_duplicates(
            subset=["amfi_code", "date"], keep="last"
        )
        df["date"] = df["date"].dt.strftime("%Y-%m-%d")

    # 2. Investor transactions
    elif file_path.name == "08_investor_transactions.csv":
        df["transaction_date"] = pd.to_datetime(
            df["transaction_date"], errors="coerce"
        )
        df["amount_inr"] = pd.to_numeric(
            df["amount_inr"], errors="coerce"
        )
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

    # 3. Scheme performance
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

        df = df.dropna(
            subset=["amfi_code", "scheme_name", "expense_ratio_pct"]
        )
        df = df[df["expense_ratio_pct"].between(0.1, 2.5)]

    # 4. AUM: remove exact duplicates only; preserve supplied observations.

    output_path = PROCESSED_DIR / file_path.name
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)

    cleaned_rows = len(df)
    print(f"{file_path.name}: {original_rows:,} -> {cleaned_rows:,} rows")
    return original_rows, cleaned_rows


def main() -> None:
    """Clean all raw CSVs; stop immediately if any file fails."""
    if not RAW_DIR.exists():
        raise FileNotFoundError(f"Raw data folder not found: {RAW_DIR}")

    csv_files = sorted(RAW_DIR.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in: {RAW_DIR}")

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Found {len(csv_files)} CSV files.\n")

    total_before = 0
    total_after = 0

    # Deliberately do not catch per-file exceptions. A failed file must fail
    # the master ETL pipeline rather than silently leave stale processed data.
    for file_path in csv_files:
        before, after = clean_csv(file_path)
        total_before += before
        total_after += after

    print("\nDATA CLEANING COMPLETED SUCCESSFULLY")
    print(f"Files processed: {len(csv_files)}")
    print(f"Rows before cleaning: {total_before:,}")
    print(f"Rows after cleaning:  {total_after:,}")
    print(f"Processed folder: {PROCESSED_DIR}")


if __name__ == "__main__":
    main()
