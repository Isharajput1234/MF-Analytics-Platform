
from pathlib import Path
import sqlite3
import pandas as pd

from sqlalchemy import create_engine, text

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data" / "processed"
DB_DIR = BASE_DIR / "db"
SCHEMA_FILE = BASE_DIR / "sql" / "schema.sql"
DB_FILE = DB_DIR / "bluestock_mf.db"

DB_DIR.mkdir(parents=True, exist_ok=True)

engine = create_engine(f"sqlite:///{DB_FILE.as_posix()}")

# Source CSVs mapped to database tables
TABLE_FILES = {
    "dim_fund": "01_fund_master.csv",
    "fact_nav": "02_nav_history.csv",
    "fact_transactions": "08_investor_transactions.csv",
    "fact_performance": "07_scheme_performance.csv",
    "fact_aum": "03_aum_by_fund_house.csv",
}


def main():
    if not SCHEMA_FILE.exists():
        raise FileNotFoundError(f"Schema not found: {SCHEMA_FILE}")

    # Read and execute schema
    schema_sql = SCHEMA_FILE.read_text(encoding="utf-8")

    with sqlite3.connect(DB_FILE) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(schema_sql)

    print("Database and schema created.")

    # Load date dimension from all relevant source dates
    date_series = []

    for filename, date_column in [
        ("02_nav_history.csv", "date"),
        ("08_investor_transactions.csv", "transaction_date"),
        ("03_aum_by_fund_house.csv", "date"),
    ]:
        df = pd.read_csv(DATA_DIR / filename)
        dates = pd.to_datetime(df[date_column], errors="coerce").dropna()
        date_series.append(dates.dt.normalize())

    all_dates = pd.concat(date_series).drop_duplicates().sort_values()

    dim_date = pd.DataFrame({"date": all_dates.dt.strftime("%Y-%m-%d")})
    parsed = pd.to_datetime(dim_date["date"])

    dim_date["year"] = parsed.dt.year
    dim_date["month"] = parsed.dt.month
    dim_date["quarter"] = parsed.dt.quarter
    dim_date["day"] = parsed.dt.day
    dim_date["weekday"] = parsed.dt.dayofweek

    dim_date.to_sql(
        "dim_date", engine, if_exists="append", index=False
    )
    print(f"dim_date: {len(dim_date):,} rows loaded.")

    # Load remaining tables
    for table_name, filename in TABLE_FILES.items():
        df = pd.read_csv(DATA_DIR / filename)

        if table_name == "dim_fund":
            df["amfi_code"] = df["amfi_code"].astype(str)

        elif table_name == "fact_nav":
            df["amfi_code"] = df["amfi_code"].astype(str)
            df["date"] = pd.to_datetime(
                df["date"], errors="coerce"
            ).dt.strftime("%Y-%m-%d")

        elif table_name == "fact_transactions":
            df["amfi_code"] = df["amfi_code"].astype(str)
            df["transaction_date"] = pd.to_datetime(
                df["transaction_date"], errors="coerce"
            ).dt.strftime("%Y-%m-%d")

        elif table_name == "fact_performance":
            df["amfi_code"] = df["amfi_code"].astype(str)

        elif table_name == "fact_aum":
            df["date"] = pd.to_datetime(
                df["date"], errors="coerce"
            ).dt.strftime("%Y-%m-%d")

        df.to_sql(
            table_name, engine, if_exists="append", index=False
        )
        print(f"{table_name}: {len(df):,} rows loaded.")

    # Verify row counts and foreign-key integrity
    with engine.connect() as connection:
        print("\nDATABASE VERIFICATION")

        for table in [
            "dim_fund",
            "dim_date",
            "fact_nav",
            "fact_transactions",
            "fact_performance",
            "fact_aum",
        ]:
            count = connection.execute(
                text(f"SELECT COUNT(*) FROM {table}")
            ).scalar_one()
            print(f"{table}: {count:,} rows")

        for table in [
            "fact_nav",
            "fact_transactions",
            "fact_aum",
        ]:
            violations = connection.execute(
                text(f"PRAGMA foreign_key_check('{table}')")
            ).fetchall()
            print(f"{table} foreign-key violations: {len(violations)}")

    print(f"\nDatabase saved at: {DB_FILE}")


if __name__ == "__main__":
    main()
