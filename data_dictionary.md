
# Mutual Fund Analytics Platform — Data Dictionary

## Project Overview
This project analyzes mutual fund NAV, scheme performance, investor transactions, fund-house AUM, and SIP inflows using Python, Pandas, SQLAlchemy, and SQLite.

Database: `db/bluestock_mf.db`

## Database Tables

| Table | Purpose | Primary Key |
|---|---|---|
| dim_fund | Fund and scheme details | amfi_code |
| dim_date | Calendar information | date |
| fact_nav | Historical NAV records | amfi_code, date |
| fact_transactions | Investor transactions | transaction_id |
| fact_performance | Scheme performance metrics | amfi_code |
| fact_aum | Fund-house AUM by date | aum_id |
| fact_sip_inflows | Monthly SIP statistics | month |

## 1. dim_fund
Source: `01_fund_master.csv`

- `amfi_code`: Scheme identifier.
- `fund_house`: Mutual fund company.
- `scheme_name`: Scheme name.
- `category`: Fund category.
- `sub_category`: Fund subcategory.
- `plan`: Direct or Regular plan.
- `launch_date`: Scheme launch date.
- `benchmark`: Associated benchmark.
- `expense_ratio_pct`: Expense ratio percentage.
- `exit_load_pct`: Exit load percentage.
- `min_sip_amount`: Minimum SIP amount.
- `min_lumpsum_amount`: Minimum lump-sum amount.
- `fund_manager`: Fund manager.
- `risk_category`: Risk classification.
- `sebi_category_code`: SEBI category code.

## 2. dim_date

Generated from source dates.

- `date`: Date in YYYY-MM-DD format.
- `year`: Calendar year.
- `month`: Month number.
- `quarter`: Calendar quarter.
- `day`: Day of month.
- `weekday`: Weekday number; Monday = 0.

## 3. fact_nav
Source: `02_nav_history.csv`

- `amfi_code`: Scheme identifier.
- `date`: NAV observation date.
- `nav`: Net Asset Value.

Primary key: `amfi_code, date`.

## 4. fact_transactions
Source: `08_investor_transactions.csv`

- `transaction_id`: Database-generated transaction identifier.
- `investor_id`: Investor identifier.
- `transaction_date`: Transaction date.
- `amfi_code`: Scheme identifier.
- `transaction_type`: SIP, Lumpsum, or Redemption.
- `amount_inr`: Transaction amount in INR.
- `state`: Investor state.
- `city`: Investor city.
- `city_tier`: City classification.
- `age_group`: Investor age group.
- `gender`: Investor gender.
- `annual_income_lakh`: Annual income in lakh INR.
- `payment_mode`: Payment method.
- `kyc_status`: KYC status.

## 5. fact_performance
Source: `07_scheme_performance.csv`

- `amfi_code`: Scheme identifier.
- `scheme_name`: Scheme name.
- `fund_house`: Fund house.
- `category`: Fund category.
- `plan`: Investment plan.
- `return_1yr_pct`: One-year return percentage.
- `return_3yr_pct`: Three-year return percentage.
- `return_5yr_pct`: Five-year return percentage.
- `benchmark_3yr_pct`: Three-year benchmark return.
- `alpha`: Source-provided alpha.
- `beta`: Source-provided beta.
- `sharpe_ratio`: Source-provided Sharpe ratio.
- `sortino_ratio`: Source-provided Sortino ratio.
- `std_dev_ann_pct`: Annualized standard deviation percentage.
- `max_drawdown_pct`: Maximum drawdown percentage.
- `aum_crore`: Scheme AUM in crore INR.
- `expense_ratio_pct`: Expense ratio percentage.
- `morningstar_rating`: Source-provided rating.
- `risk_grade`: Source-provided risk grade.

## 6. fact_aum
Source: `03_aum_by_fund_house.csv`

- `aum_id`: Database-generated identifier.
- `date`: AUM observation date.
- `fund_house`: Fund house.
- `aum_lakh_crore`: AUM in lakh crore INR.
- `aum_crore`: AUM in crore INR.
- `num_schemes`: Number of schemes.

Unique combination: `date, fund_house`.

## 7. fact_sip_inflows
Source: `04_monthly_sip_inflows.csv`

- `month`: Reporting month in YYYY-MM format.
- `sip_inflow_crore`: Monthly SIP inflow in crore INR.
- `active_sip_accounts_crore`: Active SIP accounts in crore.
- `new_sip_accounts_lakh`: New SIP accounts in lakh.
- `sip_aum_lakh_crore`: SIP AUM in lakh crore INR.
- `yoy_growth_pct`: Source-reported year-over-year growth percentage.

## Data Quality Notes

- Exact duplicate rows were removed during the initial cleaning pass.
- NAV dates and values were parsed; non-positive NAV values were excluded.
- Transaction dates and amounts were validated; non-positive amounts were excluded.
- Transaction types were standardized.
- Performance numeric fields were converted to numeric values.
- Database verification reported zero foreign-key violations for NAV, transactions, and AUM.
- Holiday/weekend NAV forward-fill and full anomaly checks are not yet complete.
- Investor transaction data should be treated as synthetic where specified by the project documentation.

## Limitations

- Seven tables have been loaded into SQLite.
- Additional source datasets have not all been loaded into dedicated database tables.
- Performance and risk metrics are source-provided unless explicitly recalculated.

### Data Quality Note: SIP Year-over-Year Growth

- The `04_monthly_sip_inflows.csv` dataset contains missing `yoy_growth_pct` values for January–December 2022.
- The dataset starts in January 2022, so the corresponding months from 2021 are unavailable for calculating year-over-year growth.
- These missing values are intentionally retained as `NULL` rather than replaced with zero.
- From January 2023 onward, calculated YoY growth was checked against the source-reported values using SQL, and the displayed results matched.