
from pathlib import Path
import nbformat as nbf

BASE_DIR = Path(__file__).resolve().parent
CHART_DIR = BASE_DIR / "reports" / "eda_charts"
FINDINGS_FILE = BASE_DIR / "reports" / "eda_key_findings.txt"
NOTEBOOK_DIR = BASE_DIR / "notebooks"

charts = sorted(CHART_DIR.glob("*.png"))

if len(charts) != 22:
    raise ValueError(f"Expected 22 charts, found {len(charts)}")

if not FINDINGS_FILE.exists():
    raise FileNotFoundError(FINDINGS_FILE)

nb = nbf.v4.new_notebook()
cells = []

cells.append(nbf.v4.new_markdown_cell("""
# Mutual Fund Industry — Exploratory Data Analysis

**Project:** Bluestock Fintech — Mutual Fund Analytics Platform  
**Analysis period:** January 2022 – May 2026 (NAV data)  
**Data sources:** Project CSV datasets

## Objectives
1. Explore mutual fund schemes and fund houses.
2. Analyze NAV trends and scheme performance.
3. Study AUM, SIP inflows, and folio growth.
4. Understand investor demographics and transaction patterns.
5. Examine category inflows, risk, returns, and sector allocation.

This notebook presents the project's EDA charts and data-derived findings.
"""))

cells.append(nbf.v4.new_markdown_cell("""
## 1. Environment and Project Paths

The notebook automatically detects the project root whether it is
executed from the project folder or the notebooks folder.
"""))

cells.append(nbf.v4.new_code_cell("""
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from IPython.display import display, Image, Markdown

PROJECT_DIR = Path.cwd()
if PROJECT_DIR.name == "notebooks":
    PROJECT_DIR = PROJECT_DIR.parent

PROCESSED_DIR = PROJECT_DIR / "data" / "processed"
CHART_DIR = PROJECT_DIR / "reports" / "eda_charts"
FINDINGS_FILE = PROJECT_DIR / "reports" / "eda_key_findings.txt"

print("Project directory:", PROJECT_DIR)
print("Processed data directory exists:", PROCESSED_DIR.exists())
print("Chart directory exists:", CHART_DIR.exists())
"""))

cells.append(nbf.v4.new_markdown_cell("""
## 2. Dataset Loading
"""))

cells.append(nbf.v4.new_code_cell("""
datasets = {
    "Fund Master": "01_fund_master.csv",
    "NAV History": "02_nav_history.csv",
    "AUM": "03_aum_by_fund_house.csv",
    "SIP Inflows": "04_monthly_sip_inflows.csv",
    "Category Inflows": "05_category_inflows.csv",
    "Folio Count": "06_industry_folio_count.csv",
    "Scheme Performance": "07_scheme_performance.csv",
    "Investor Transactions": "08_investor_transactions.csv",
    "Portfolio Holdings": "09_portfolio_holdings.csv",
    "Benchmark Indices": "10_benchmark_indices.csv"
}

data = {}
for name, filename in datasets.items():
    path = PROCESSED_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Missing processed dataset: {path}")
    data[name] = pd.read_csv(path)
    print(f"{name}: {data[name].shape[0]:,} rows × {data[name].shape[1]} columns")

fund_master = data["Fund Master"]
nav_history = data["NAV History"]
aum_data = data["AUM"]
sip_data = data["SIP Inflows"]
category_inflows = data["Category Inflows"]
folio_data = data["Folio Count"]
performance = data["Scheme Performance"]
transactions = data["Investor Transactions"]
holdings = data["Portfolio Holdings"]
benchmark = data["Benchmark Indices"]
"""))

cells.append(nbf.v4.new_markdown_cell("""
## 3. Data Quality and Coverage Overview
"""))

cells.append(nbf.v4.new_code_cell("""
overview = pd.DataFrame([
    {
        "Dataset": name,
        "Rows": len(df),
        "Columns": len(df.columns),
        "Duplicate Rows": int(df.duplicated().sum()),
        "Missing Cells": int(df.isna().sum().sum())
    }
    for name, df in data.items()
])

display(overview)

nav_history["date"] = pd.to_datetime(nav_history["date"], errors="coerce")
print("Unique schemes in NAV data:", nav_history["amfi_code"].nunique())
print("NAV date range:", nav_history["date"].min(), "to", nav_history["date"].max())
print("Fund houses:", fund_master["fund_house"].nunique())
print("Schemes:", fund_master["amfi_code"].nunique())
"""))

cells.append(nbf.v4.new_markdown_cell("""
## 4. Exploratory Data Visualizations

The following charts were generated from the processed project datasets.
Each chart is embedded below for review.
"""))

for chart in charts:
    title = chart.stem.replace("_", " ")
    cells.append(nbf.v4.new_markdown_cell(f"### {title}"))
    cells.append(nbf.v4.new_code_cell(
        f'from IPython.display import display, Image\n'
        f'display(Image(filename=str(CHART_DIR / "{chart.name}")))\n'
    ))

cells.append(nbf.v4.new_markdown_cell("""
## 5. Key Findings
"""))

cells.append(nbf.v4.new_code_cell("""
findings = FINDINGS_FILE.read_text(encoding="utf-8-sig")
print(findings)
"""))

cells.append(nbf.v4.new_markdown_cell("""
## 6. Methodology and Limitations

- Analysis uses the supplied processed CSV datasets.
- NAV analysis uses recorded trading-day observations.
- No synthetic weekend or holiday NAV values are introduced.
- SIP year-on-year growth for 2022 is unavailable where the 2021
  comparison base is missing.
- Portfolio holding weights may differ slightly from 100% because
  of rounding.
- Investor transaction data should be treated as supplied project
  data, not as verified industry-wide investor records.
- The charts are exploratory and do not establish causation.
- Findings describe the supplied dataset and its coverage period;
  they should not automatically be generalized to the entire market.

## Conclusion

This EDA establishes the descriptive foundation for the project's
performance analytics, advanced analytics, and dashboard work.
"""))

nb.cells = cells
nb.metadata = {
    "kernelspec": {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3"
    },
    "language_info": {"name": "python"}
}

output = NOTEBOOK_DIR / "EDA_Analysis.ipynb"
nbf.write(nb, output)

print(f"Notebook created: {output}")
print(f"Total cells: {len(nb.cells)}")
print(f"Charts embedded: {len(charts)}")
print("Findings included: Yes")
