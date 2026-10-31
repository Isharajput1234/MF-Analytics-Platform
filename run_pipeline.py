
"""
Bluestock Mutual Fund Analytics - Master ETL Pipeline

Execution order:
1. Validate raw datasets
2. Clean raw CSV files
3. Rebuild SQLite database
4. Load SIP inflow data
5. Verify database tables

Existing database is backed up before rebuilding.
If any step fails, the previous database is restored.
"""

from pathlib import Path
import subprocess
import sys
import shutil

BASE_DIR = Path(__file__).resolve().parent
DB_DIR = BASE_DIR / "db"
DB_FILE = DB_DIR / "bluestock_mf.db"
BACKUP_FILE = DB_DIR / "bluestock_mf_backup.db"

SCRIPTS = [
    ("Data validation", "validate_data.py"),
    ("Data cleaning", "clean_data.py"),
    ("Database loading", "load_database.py"),
    ("SIP data loading", "add_sip_data.py"),
]


def run_script(label, filename):
    script_path = BASE_DIR / filename

    if not script_path.exists():
        raise FileNotFoundError(f"Script not found: {script_path}")

    print(f"\n{'=' * 60}")
    print(f"RUNNING: {label}")
    print(f"{'=' * 60}")

    subprocess.run(
        [sys.executable, str(script_path)],
        cwd=BASE_DIR,
        check=True
    )

    print(f"SUCCESS: {label}")


def verify_database():
    import sqlite3

    required_tables = [
        "dim_fund",
        "dim_date",
        "fact_nav",
        "fact_transactions",
        "fact_performance",
        "fact_aum",
        "fact_sip_inflows"
    ]

    print("\nDATABASE VERIFICATION")

    with sqlite3.connect(DB_FILE) as connection:
        existing = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }

        missing = set(required_tables) - existing

        if missing:
            raise RuntimeError(
                f"Missing database tables: {sorted(missing)}"
            )

        for table in required_tables:
            count = connection.execute(
                f"SELECT COUNT(*) FROM {table}"
            ).fetchone()[0]

            print(f"{table}: {count:,} rows")

            if count == 0:
                raise RuntimeError(
                    f"Table {table} is empty."
                )

        violations = connection.execute(
            "PRAGMA foreign_key_check"
        ).fetchall()

        print("Foreign key violations:", len(violations))

        if violations:
            raise RuntimeError(
                "Foreign key violations detected."
            )


def main():
    DB_DIR.mkdir(parents=True, exist_ok=True)

    # Preserve the existing database before rebuilding
    had_database = DB_FILE.exists()

    if had_database:
        shutil.copy2(DB_FILE, BACKUP_FILE)
        print("Existing database backed up.")

    try:
        # Remove old database so append-based loaders
        # cannot create duplicate records.
        if DB_FILE.exists():
            DB_FILE.unlink()

        for label, filename in SCRIPTS:
            run_script(label, filename)

        verify_database()

        if BACKUP_FILE.exists():
            BACKUP_FILE.unlink()

        print("\n" + "=" * 60)
        print("ETL PIPELINE COMPLETED SUCCESSFULLY")
        print("=" * 60)
        print("Database:", DB_FILE)

    except Exception as error:
        print("\nETL PIPELINE FAILED:", error)

        # Restore previous database if available
        if BACKUP_FILE.exists():
            if DB_FILE.exists():
                DB_FILE.unlink()

            shutil.move(BACKUP_FILE, DB_FILE)
            print("Previous database restored.")

        elif DB_FILE.exists():
            DB_FILE.unlink()

        raise


if __name__ == "__main__":
    main()
