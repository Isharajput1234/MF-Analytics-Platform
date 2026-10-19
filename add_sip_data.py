
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine, text

BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "data" / "processed" / "04_monthly_sip_inflows.csv"
DB_PATH = BASE_DIR / "db" / "bluestock_mf.db"

df = pd.read_csv(CSV_PATH)

# Standardize monthly date format
df["month"] = pd.to_datetime(
    df["month"], errors="coerce"
).dt.strftime("%Y-%m")

df = df.dropna(subset=["month"])
df = df.drop_duplicates(subset=["month"], keep="last")

engine = create_engine(f"sqlite:///{DB_PATH.as_posix()}")

with engine.begin() as conn:
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS fact_sip_inflows (
            month TEXT PRIMARY KEY,
            sip_inflow_crore REAL,
            active_sip_accounts_crore REAL,
            new_sip_accounts_lakh REAL,
            sip_aum_lakh_crore REAL,
            yoy_growth_pct REAL
        )
    """))

    # Safe to rerun: replace existing monthly records
    df.to_sql(
        "fact_sip_inflows",
        conn,
        if_exists="append",
        index=False,
        method=None
    )

print("SIP data loaded:", len(df), "rows")

with engine.connect() as conn:
    count = conn.execute(
        text("SELECT COUNT(*) FROM fact_sip_inflows")
    ).scalar_one()

    print("Total SIP records in database:", count)

    rows = conn.execute(text("""
        SELECT month, sip_inflow_crore, yoy_growth_pct
        FROM fact_sip_inflows
        ORDER BY month DESC
        LIMIT 5
    """)).fetchall()

    print("\nLatest 5 monthly records:")
    for row in rows:
        print(row)
