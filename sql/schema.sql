
PRAGMA foreign_keys = ON;

-- 1. Fund dimension
CREATE TABLE IF NOT EXISTS dim_fund (
    amfi_code TEXT PRIMARY KEY,
    fund_house TEXT NOT NULL,
    scheme_name TEXT NOT NULL,
    category TEXT,
    sub_category TEXT,
    plan TEXT,
    launch_date TEXT,
    benchmark TEXT,
    expense_ratio_pct REAL,
    exit_load_pct REAL,
    min_sip_amount REAL,
    min_lumpsum_amount REAL,
    fund_manager TEXT,
    risk_category TEXT,
    sebi_category_code TEXT
);

-- 2. Date dimension
CREATE TABLE IF NOT EXISTS dim_date (
    date TEXT PRIMARY KEY,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    quarter INTEGER NOT NULL,
    day INTEGER NOT NULL,
    weekday INTEGER
);

-- 3. NAV fact table
CREATE TABLE IF NOT EXISTS fact_nav (
    amfi_code TEXT NOT NULL,
    date TEXT NOT NULL,
    nav REAL NOT NULL CHECK (nav > 0),
    PRIMARY KEY (amfi_code, date),
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code),
    FOREIGN KEY (date) REFERENCES dim_date(date)
);

-- 4. Investor transactions fact table
CREATE TABLE IF NOT EXISTS fact_transactions (
    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    investor_id TEXT NOT NULL,
    transaction_date TEXT NOT NULL,
    amfi_code TEXT NOT NULL,
    transaction_type TEXT NOT NULL
        CHECK (transaction_type IN ('SIP', 'Lumpsum', 'Redemption')),
    amount_inr REAL NOT NULL CHECK (amount_inr > 0),
    state TEXT,
    city TEXT,
    city_tier TEXT,
    age_group TEXT,
    gender TEXT,
    annual_income_lakh REAL,
    payment_mode TEXT,
    kyc_status TEXT,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code),
    FOREIGN KEY (transaction_date) REFERENCES dim_date(date)
);

-- 5. Scheme performance fact table
CREATE TABLE IF NOT EXISTS fact_performance (
    amfi_code TEXT PRIMARY KEY,
    scheme_name TEXT NOT NULL,
    fund_house TEXT,
    category TEXT,
    plan TEXT,
    return_1yr_pct REAL,
    return_3yr_pct REAL,
    return_5yr_pct REAL,
    benchmark_3yr_pct REAL,
    alpha REAL,
    beta REAL,
    sharpe_ratio REAL,
    sortino_ratio REAL,
    std_dev_ann_pct REAL,
    max_drawdown_pct REAL,
    aum_crore REAL,
    expense_ratio_pct REAL,
    morningstar_rating REAL,
    risk_grade TEXT,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code)
);

-- 6. AUM fact table by fund house and date
CREATE TABLE IF NOT EXISTS fact_aum (
    aum_id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    fund_house TEXT NOT NULL,
    aum_lakh_crore REAL,
    aum_crore REAL,
    num_schemes INTEGER,
    FOREIGN KEY (date) REFERENCES dim_date(date),
    UNIQUE (date, fund_house)
);

-- Useful indexes
CREATE INDEX IF NOT EXISTS idx_nav_date
ON fact_nav(date);

CREATE INDEX IF NOT EXISTS idx_transactions_date
ON fact_transactions(transaction_date);

CREATE INDEX IF NOT EXISTS idx_transactions_state
ON fact_transactions(state);

CREATE INDEX IF NOT EXISTS idx_transactions_fund
ON fact_transactions(amfi_code);
