
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# ==================================================
# CONFIGURATION
# ==================================================

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data" / "processed"
REPORT_DIR = BASE_DIR / "reports"
REPORT_DIR.mkdir(exist_ok=True)

NAV_FILE = DATA_DIR / "02_nav_history.csv"
TX_FILE = DATA_DIR / "08_investor_transactions.csv"
HOLDINGS_FILE = DATA_DIR / "09_portfolio_holdings.csv"
PERFORMANCE_FILE = DATA_DIR / "07_scheme_performance.csv"

RISK_FREE_RATE = 0.065
TRADING_DAYS = 252


def load_csv(path):
    if not path.exists():
        raise FileNotFoundError(f"Missing dataset: {path}")
    return pd.read_csv(path)


# ==================================================
# LOAD DATA
# ==================================================

nav = load_csv(NAV_FILE)
tx = load_csv(TX_FILE)
holdings = load_csv(HOLDINGS_FILE)
performance = load_csv(PERFORMANCE_FILE)

nav["date"] = pd.to_datetime(nav["date"], errors="coerce")
tx["transaction_date"] = pd.to_datetime(
    tx["transaction_date"], errors="coerce"
)
holdings["portfolio_date"] = pd.to_datetime(
    holdings["portfolio_date"], errors="coerce"
)

nav["nav"] = pd.to_numeric(nav["nav"], errors="coerce")
tx["amount_inr"] = pd.to_numeric(tx["amount_inr"], errors="coerce")
holdings["weight_pct"] = pd.to_numeric(
    holdings["weight_pct"], errors="coerce"
)

nav = nav.dropna(subset=["amfi_code", "date", "nav"])
nav = nav[nav["nav"] > 0]
nav = nav.drop_duplicates(["amfi_code", "date"])
nav = nav.sort_values(["amfi_code", "date"])

# ==================================================
# 1. HISTORICAL VAR AND CVAR
# ==================================================

nav["daily_return"] = nav.groupby("amfi_code")["nav"].pct_change()

var_rows = []

for code, group in nav.groupby("amfi_code"):
    returns = group["daily_return"].dropna()

    if len(returns) < 30:
        continue

    var_95 = returns.quantile(0.05)
    cvar_95 = returns[returns <= var_95].mean()

    var_rows.append({
        "amfi_code": code,
        "observations": len(returns),
        "VaR_95_pct": var_95 * 100,
        "CVaR_95_pct": cvar_95 * 100
    })

var_df = pd.DataFrame(var_rows)
var_df.to_csv(REPORT_DIR / "var_cvar_report.csv", index=False)

# ==================================================
# 2. ROLLING 90-DAY SHARPE - TOP 5 FUNDS
# ==================================================

return_pivot = nav.pivot(
    index="date", columns="amfi_code", values="daily_return"
).sort_index()

fund_codes = list(return_pivot.columns[:5])
rolling_results = {}

for code in fund_codes:
    returns = return_pivot[code]

    rolling_mean = returns.rolling(90).mean()
    rolling_std = returns.rolling(90).std()

    rolling_sharpe = (
        (rolling_mean - RISK_FREE_RATE / TRADING_DAYS)
        / rolling_std
    ) * np.sqrt(TRADING_DAYS)

    rolling_results[str(code)] = rolling_sharpe

rolling_df = pd.DataFrame(rolling_results)

plt.figure(figsize=(13, 6))
for col in rolling_df.columns:
    plt.plot(rolling_df.index, rolling_df[col], label=col)

plt.title("Rolling 90-Day Sharpe Ratio - 5 Selected Funds")
plt.xlabel("Date")
plt.ylabel("Annualised Sharpe Ratio")
plt.legend(title="AMFI Code")
plt.tight_layout()
plt.savefig(
    REPORT_DIR / "rolling_sharpe_chart.png",
    dpi=150,
    bbox_inches="tight"
)
plt.close()

# ==================================================
# 3. INVESTOR COHORT ANALYSIS
# ==================================================

tx = tx.dropna(subset=["investor_id", "transaction_date"])
tx["year"] = tx["transaction_date"].dt.year

first_year = tx.groupby("investor_id")["year"].min()
tx["cohort_year"] = tx["investor_id"].map(first_year)

cohort_activity = tx.groupby(
    ["cohort_year", "year"]
)["investor_id"].nunique().reset_index()

cohort_activity.columns = [
    "cohort_year", "activity_year", "active_investors"
]

cohort_activity["period_number"] = (
    cohort_activity["activity_year"] -
    cohort_activity["cohort_year"]
)

cohort_pivot = cohort_activity.pivot(
    index="cohort_year",
    columns="period_number",
    values="active_investors"
)

cohort_size = first_year.value_counts().sort_index()
cohort_retention = cohort_pivot.div(cohort_size, axis=0) * 100

cohort_retention.to_csv(
    REPORT_DIR / "cohort_analysis.csv"
)

# ==================================================
# 4. SIP CONTINUITY ANALYSIS
# ==================================================

sip_tx = tx[
    tx["transaction_type"].astype(str).str.strip().str.lower() == "sip"
].copy()

sip_tx = sip_tx.sort_values(["investor_id", "transaction_date"])

sip_tx["gap_days"] = (
    sip_tx.groupby("investor_id")["transaction_date"]
    .diff()
    .dt.days
)

sip_summary = sip_tx.groupby("investor_id").agg(
    sip_transaction_count=("transaction_date", "count"),
    average_gap_days=("gap_days", "mean"),
    maximum_gap_days=("gap_days", "max"),
    total_sip_amount_inr=("amount_inr", "sum")
).reset_index()

sip_summary["at_risk"] = (
    (sip_summary["sip_transaction_count"] >= 6) &
    (sip_summary["maximum_gap_days"] > 35)
)

sip_summary.to_csv(
    REPORT_DIR / "sip_continuity.csv",
    index=False
)

# ==================================================
# 5. FUND RECOMMENDER
# ==================================================

def create_recommender():
    required = [
        "scheme_name", "risk_grade",
        "sharpe_ratio", "return_3yr_pct"
    ]

    missing = [c for c in required if c not in performance.columns]
    if missing:
        raise ValueError(f"Missing performance columns: {missing}")

    data = performance.copy()

    data["sharpe_ratio"] = pd.to_numeric(
        data["sharpe_ratio"], errors="coerce"
    )

    data["return_3yr_pct"] = pd.to_numeric(
        data["return_3yr_pct"], errors="coerce"
    )

    data = data.dropna(
        subset=["scheme_name", "risk_grade", "sharpe_ratio"]
    )

    lines = [
        '"""Simple mutual fund recommender by risk grade."""',
        "import pandas as pd",
        "from pathlib import Path",
        "",
        "BASE = Path(__file__).resolve().parent",
        "DATA = BASE / 'data' / 'processed' / '07_scheme_performance.csv'",
        "",
        "def recommend(risk_grade, top_n=3):",
        "    df = pd.read_csv(DATA)",
        "    df['sharpe_ratio'] = pd.to_numeric(df['sharpe_ratio'], errors='coerce')",
        "    result = df[df['risk_grade'].astype(str).str.lower() == str(risk_grade).lower()]",
        "    result = result.dropna(subset=['sharpe_ratio'])",
        "    return result.sort_values('sharpe_ratio', ascending=False).head(top_n)",
        "",
        "if __name__ == '__main__':",
        "    for grade in ['Low', 'Moderate', 'High']:",
        "        print(f'\\n{grade} Risk Funds')",
        "        print(recommend(grade).to_string(index=False))"
    ]

    (BASE_DIR / "recommender.py").write_text(
        "\n".join(lines), encoding="utf-8"
    )

    recommendations = []
    for grade in data["risk_grade"].dropna().unique():
        subset = data[
            data["risk_grade"].astype(str).str.lower()
            == str(grade).lower()
        ]
        top = subset.nlargest(3, "sharpe_ratio")

        for rank, (_, row) in enumerate(top.iterrows(), 1):
            recommendations.append({
                "risk_grade": grade,
                "rank": rank,
                "scheme_name": row["scheme_name"],
                "sharpe_ratio": row["sharpe_ratio"],
                "return_3yr_pct": row["return_3yr_pct"]
            })

    pd.DataFrame(recommendations).to_csv(
        REPORT_DIR / "fund_recommendations.csv",
        index=False
    )


create_recommender()

# ==================================================
# 6. SECTOR CONCENTRATION - HHI
# ==================================================

holdings = holdings.dropna(
    subset=["amfi_code", "sector", "weight_pct"]
)

sector_weights = holdings.groupby(
    ["amfi_code", "sector"]
)["weight_pct"].sum().reset_index()

hhi_rows = []

for code, group in sector_weights.groupby("amfi_code"):
    total_weight = group["weight_pct"].sum()

    if total_weight <= 0:
        continue

    normalized_weights = group["weight_pct"] / total_weight
    hhi = (normalized_weights ** 2).sum() * 10000

    hhi_rows.append({
        "amfi_code": code,
        "sector_count": group["sector"].nunique(),
        "sector_hhi": hhi
    })

hhi_df = pd.DataFrame(hhi_rows)
hhi_df.to_csv(REPORT_DIR / "sector_hhi.csv", index=False)

if not hhi_df.empty:
    hhi_plot = hhi_df.sort_values("sector_hhi")

    plt.figure(figsize=(12, 6))
    plt.bar(
        hhi_plot["amfi_code"].astype(str),
        hhi_plot["sector_hhi"]
    )
    plt.title("Sector Concentration - HHI by Fund")
    plt.xlabel("AMFI Code")
    plt.ylabel("Herfindahl-Hirschman Index")
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.savefig(
        REPORT_DIR / "sector_hhi_chart.png",
        dpi=150,
        bbox_inches="tight"
    )
    plt.close()

# ==================================================
# 7. GENERATE ADVANCED ANALYTICS NOTEBOOK
# ==================================================

notebook = {
    "cells": [
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "# Advanced Analytics - Bluestock Mutual Fund Platform\n",
                "\n",
                "This notebook runs the advanced analytics pipeline and generates VaR/CVaR, rolling Sharpe, investor cohort, SIP continuity, fund recommendations and sector HHI outputs.\n"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## Methodology\n",
                "- Historical VaR and CVaR use the 5th percentile of daily NAV returns.\n",
                "- Rolling Sharpe uses a 90-observation window and a 6.5% annual risk-free rate.\n",
                "- Cohorts are assigned by each investor's first transaction year.\n",
                "- SIP continuity flags investors with at least six SIP transactions and a maximum observed gap above 35 days.\n",
                "- Sector HHI uses each fund's normalised sector weights.\n"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "from pathlib import Path\n",
                "import runpy\n",
                "runpy.run_path(str(Path('advanced_analytics.py').resolve()), run_name='__main__')\n"
            ]
        }
    ],
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3"
        },
        "language_info": {"name": "python"}
    },
    "nbformat": 4,
    "nbformat_minor": 5
}

(BASE_DIR / "notebooks").mkdir(exist_ok=True)

with open(
    BASE_DIR / "notebooks" / "05_advanced_analytics.ipynb",
    "w",
    encoding="utf-8"
) as f:
    json.dump(notebook, f, indent=2)

# ==================================================
# COMPLETION SUMMARY
# ==================================================

print("\nADVANCED ANALYTICS COMPLETED")
print("VaR/CVaR rows:", len(var_df))
print("Rolling Sharpe chart:", (REPORT_DIR / "rolling_sharpe_chart.png").exists())
print("Cohort rows:", len(cohort_activity))
print("SIP continuity investors:", len(sip_summary))
print("Sector HHI funds:", len(hhi_df))
print("Recommender created:", (BASE_DIR / "recommender.py").exists())
print("Notebook created:", (BASE_DIR / "notebooks" / "05_advanced_analytics.ipynb").exists())
print("Output folder:", REPORT_DIR)
