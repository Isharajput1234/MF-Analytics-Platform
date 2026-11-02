# Bluestock Mutual Fund Analytics Platform

**Individual Capstone Project \| Bluestock Fintech**

An end-to-end mutual fund analytics project covering data ingestion,
cleaning, relational database design, exploratory analysis, fund
performance measurement, investor behaviour, and advanced risk
analytics.

## Project overview

The platform analyses Indian mutual fund scheme and industry data across
the following areas:

-   Scheme master data and historical NAV
-   Fund-house assets under management (AUM)
-   Monthly Systematic Investment Plan (SIP) inflows
-   Category-level net inflows and industry folio counts
-   Investor transactions and portfolio holdings
-   Scheme performance and benchmark indices
-   Risk, return, fund comparisons, and investor activity patterns

The core dataset includes 40 schemes and approximately 46,000 historical
NAV observations from January 2022 to May 2026. Industry and investor
datasets cover their respective periods in the supplied CSV files.

> **Data note:** Investor transaction and portfolio datasets are
> supplied project data and should not be interpreted as a
> representative sample of all Indian mutual fund investors. Analytics
> are descriptive and educational, not investment advice.

## Main capabilities

### 1. Data pipeline and database

-   CSV ingestion and validation
-   Data cleaning and preparation
-   SQLite relational database
-   Dimension and fact tables for funds, dates, NAV, transactions,
    performance, AUM, and SIP inflows
-   Foreign-key integrity checks

### 2. Exploratory data analysis

The EDA work includes 22 exported charts covering:

-   NAV trends and scheme distribution
-   Fund-house AUM
-   SIP inflows and SIP accounts
-   Category inflows
-   Folio growth and composition
-   Investor age, state, and city-tier distributions
-   Transaction types and monthly activity
-   Scheme-return correlations
-   Sector allocation and risk-return comparisons

Notebook: `notebooks/EDA_Analysis.ipynb`

### 3. Performance analytics

Performance analysis includes:

-   1-year and 3-year CAGR, where supported by available history
-   Risk and risk-adjusted return measures
-   Alpha and beta analysis
-   Maximum drawdown
-   Weighted fund scorecard
-   Benchmark comparison and tracking error

The risk-free rate used in the analysis is 6.5% annually. Five-year CAGR
is unavailable where the supplied NAV history does not provide a full
five-year observation window.

Notebook: `notebooks/04_performance_analytics.ipynb`

### 4. Advanced analytics

Advanced analysis includes:

-   Historical 95% Value at Risk (VaR) and Conditional VaR (CVaR)
-   Rolling 90-observation Sharpe ratio for selected schemes
-   Investor cohort activity analysis
-   SIP continuity screening
-   Low, Moderate, and High risk-bucket fund recommendations
-   Sector concentration using the Herfindahl-Hirschman Index (HHI)

Notebook: `notebooks/05_advanced_analytics.ipynb`

The SIP continuity flag is a screening rule based on recorded
transaction gaps; it does not establish that an investor has actually
discontinued a contractual SIP.

## Repository structure

``` text
MF-Analytics-Platform/
├── data/
│   ├── raw/
│   └── processed/
├── db/
│   └── bluestock_mf.db
├── notebooks/
│   ├── EDA_Analysis.ipynb
│   ├── 04_performance_analytics.ipynb
│   └── 05_advanced_analytics.ipynb
├── reports/
│   ├── eda_charts/
│   ├── fund_scorecard.csv
│   ├── performance_metrics_complete.csv
│   ├── alpha_beta.csv
│   ├── tracking_error.csv
│   ├── var_cvar_report.csv
│   ├── cohort_analysis.csv
│   ├── sip_continuity.csv
│   ├── fund_recommendations.csv
│   ├── sector_hhi.csv
│   ├── Final_Report.pdf
│   └── Bluestock_MF_Presentation.pptx
├── sql/
│   ├── schema.sql
│   └── queries.sql
├── data_ingestion.py
├── clean_data.py
├── validate_data.py
├── load_database.py
├── run_pipeline.py
├── advanced_analytics.py
├── recommender.py
├── requirements.txt
└── data_dictionary.md
```

The SQLite database is generated locally and is not intended to be
committed to Git.

## Tech stack

-   Python
-   Pandas and NumPy
-   Matplotlib
-   SQLite
-   SQL
-   Jupyter Notebook
-   Power BI

## Setup

Use Python 3.13 or a compatible Python version supported by the packages
in `requirements.txt`.

### 1. Clone the repository

``` bash
git clone https://github.com/Isharajput1234/MF-Analytics-Platform.git
cd MF-Analytics-Platform
```

### 2. Create and activate a virtual environment

Windows PowerShell:

``` powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

``` powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Run the data pipeline

``` powershell
python run_pipeline.py
```

The pipeline validates, cleans, and loads the processed datasets into
the SQLite database. Keep the supplied data files in their expected
`data/` locations.

### 5. Run advanced analytics

``` powershell
python advanced_analytics.py
```

To run the recommender separately:

``` powershell
python recommender.py
```

### 6. Open the notebooks

``` powershell
jupyter notebook
```

Open the notebooks under `notebooks/` and execute them after the
required datasets and reports have been generated.

## Key outputs

  Output                                     Description
  ------------------------------------------ --------------------------------------
  `reports/eda_charts/`                      Exported exploratory analysis charts
  `reports/fund_scorecard.csv`               Weighted scheme scorecard
  `reports/alpha_beta.csv`                   Alpha and beta estimates
  `reports/tracking_error.csv`               Benchmark tracking-error results
  `reports/var_cvar_report.csv`              Historical VaR and CVaR
  `reports/rolling_sharpe_chart.png`         Rolling Sharpe visualisation
  `reports/cohort_analysis.csv`              Investor cohort activity
  `reports/sip_continuity.csv`               SIP transaction-gap screening
  `reports/fund_recommendations.csv`         Risk-bucket recommendations
  `reports/sector_hhi.csv`                   Equity scheme sector concentration
  `reports/Final_Report.pdf`                 Project report
  `reports/Bluestock_MF_Presentation.pptx`   Project presentation

## Methodology and limitations

-   NAV returns are calculated from observed NAV records; non-trading
    days are not treated as actual NAV observations.
-   Metrics depend on the historical coverage and quality of the
    supplied data.
-   A five-year return should only be reported when a full five-year
    observation period is available.
-   Historical VaR and CVaR describe observed return distributions; they
    are not forecasts of future losses.
-   Cohort retention in this project means later-year transaction
    activity, not assets retained.
-   SIP continuity is inferred from recorded transaction dates and the
    stated screening threshold.
-   Fund recommendations rank supplied schemes within broad risk
    buckets; they are not personalised investment advice.
-   Sector HHI is calculated from the latest available holdings snapshot
    for each included equity scheme.

## Disclaimer

This project is for academic, analytical, and educational purposes only.
It is not financial, investment, tax, or legal advice. Past performance
and historical risk statistics do not guarantee future results. Users
should independently verify data and consult a qualified financial
adviser before making investment decisions.

## Author

**Isharajput1234**

GitHub:
[MF-Analytics-Platform](https://github.com/Isharajput1234/MF-Analytics-Platform)
