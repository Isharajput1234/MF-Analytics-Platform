
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# ---------------- CONFIGURATION ----------------
DATA = Path("data/processed")
OUT = Path("reports/eda_charts")
OUT.mkdir(parents=True, exist_ok=True)
Path("reports").mkdir(exist_ok=True)

sns.set_theme(style="darkgrid")
plt.rcParams["figure.figsize"] = (12, 6)
plt.rcParams["figure.dpi"] = 120

def load(name):
    return pd.read_csv(DATA / name)

def save(name):
    plt.tight_layout()
    plt.savefig(OUT / name, bbox_inches="tight")
    plt.close()

def numeric(df, columns):
    for col in columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

# ---------------- LOAD DATA ----------------
funds = load("01_fund_master.csv")
nav = load("02_nav_history.csv")
aum = load("03_aum_by_fund_house.csv")
sip = load("04_monthly_sip_inflows.csv")
category = load("05_category_inflows.csv")
folios = load("06_industry_folio_count.csv")
performance = load("07_scheme_performance.csv")
tx = load("08_investor_transactions.csv")
holdings = load("09_portfolio_holdings.csv")
bench = load("10_benchmark_indices.csv")

# ---------------- CLEAN TYPES ----------------
date_columns = [
    (nav, "date"), (aum, "date"), (sip, "month"),
    (category, "month"), (folios, "month"),
    (tx, "transaction_date"), (bench, "date"),
    (holdings, "portfolio_date")
]

for df, col in date_columns:
    df[col] = pd.to_datetime(df[col], errors="coerce")

numeric(nav, ["nav"])
numeric(aum, ["aum_lakh_crore", "aum_crore", "num_schemes"])
numeric(sip, ["sip_inflow_crore", "active_sip_accounts_crore",
              "new_sip_accounts_lakh", "sip_aum_lakh_crore",
              "yoy_growth_pct"])
numeric(category, ["net_inflow_crore"])
numeric(folios, ["total_folios_crore", "equity_folios_crore",
                 "debt_folios_crore", "hybrid_folios_crore",
                 "others_folios_crore"])
numeric(performance, ["return_1yr_pct", "return_3yr_pct",
                      "return_5yr_pct", "benchmark_3yr_pct",
                      "alpha", "beta", "sharpe_ratio",
                      "sortino_ratio", "std_dev_ann_pct",
                      "max_drawdown_pct", "aum_crore",
                      "expense_ratio_pct"])
numeric(tx, ["amount_inr", "annual_income_lakh"])
numeric(holdings, ["weight_pct", "market_value_cr",
                   "current_price_inr"])
numeric(bench, ["close_value"])

findings = []

# 1. NAV trends - all schemes
pivot = nav.pivot_table(index="date", columns="amfi_code", values="nav")
pivot.plot(legend=False, alpha=0.35)
plt.title("NAV Trends - All Mutual Fund Schemes")
plt.xlabel("Date")
plt.ylabel("NAV")
save("01_all_scheme_nav_trends.png")

# 2. NAV trends - 10 selected schemes
latest_nav = nav.sort_values("date").groupby("amfi_code").tail(1)
top_codes = latest_nav.nlargest(10, "nav")["amfi_code"]
selected_nav = nav[nav["amfi_code"].isin(top_codes)]
selected_nav.pivot(index="date", columns="amfi_code",
                   values="nav").plot()
plt.title("NAV Trends - 10 Selected Schemes")
plt.ylabel("NAV")
save("02_top10_nav_trends.png")

# 3. Schemes by category
funds["category"].value_counts().plot(kind="bar")
plt.title("Number of Schemes by Category")
plt.ylabel("Schemes")
plt.xticks(rotation=45, ha="right")
save("03_schemes_by_category.png")

# 4. Schemes by fund house
funds["fund_house"].value_counts().plot(kind="bar")
plt.title("Number of Schemes by Fund House")
plt.ylabel("Schemes")
plt.xticks(rotation=45, ha="right")
save("04_schemes_by_fund_house.png")

# 5. AUM by fund house and year
aum["year"] = aum["date"].dt.year
aum_year = aum.groupby(["year", "fund_house"], as_index=False)[
    "aum_lakh_crore"
].mean()
sns.barplot(data=aum_year, x="year", y="aum_lakh_crore",
            hue="fund_house")
plt.title("Average AUM by Fund House and Year")
plt.ylabel("AUM (Lakh Crore)")
plt.legend(bbox_to_anchor=(1.02, 1), loc="upper left")
save("05_aum_fund_house_year.png")

# 6. Monthly SIP inflows
sip = sip.sort_values("month")
plt.plot(sip["month"], sip["sip_inflow_crore"], marker="o")
plt.title("Monthly SIP Inflows")
plt.ylabel("SIP Inflow (₹ Crore)")
save("06_monthly_sip_inflows.png")

# 7. Active SIP accounts
plt.plot(sip["month"], sip["active_sip_accounts_crore"], marker="o")
plt.title("Active SIP Accounts Growth")
plt.ylabel("Accounts (Crore)")
save("07_active_sip_accounts.png")

# 8. SIP AUM
plt.plot(sip["month"], sip["sip_aum_lakh_crore"], marker="o")
plt.title("Monthly SIP AUM")
plt.ylabel("SIP AUM (Lakh Crore)")
save("08_sip_aum.png")

# 9. Category inflow heatmap
category["month_name"] = category["month"].dt.strftime("%b")
heat = category.pivot_table(
    index="category", columns="month_name",
    values="net_inflow_crore", aggfunc="mean"
)
month_order = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
heat = heat.reindex(columns=month_order)
sns.heatmap(heat, cmap="YlGnBu")
plt.title("Average Monthly Net Inflows by Category")
plt.xlabel("Month")
save("09_category_inflow_heatmap.png")

# 10. Total category inflows
category.groupby("category")["net_inflow_crore"].sum().sort_values().plot(
    kind="barh"
)
plt.title("Total Net Inflows by Category")
plt.xlabel("Net Inflow (₹ Crore)")
save("10_category_total_inflows.png")

# 11. Folio growth
folios = folios.sort_values("month")
plt.plot(folios["month"], folios["total_folios_crore"], marker="o")
plt.title("Industry Folio Growth")
plt.ylabel("Total Folios (Crore)")
save("11_folio_growth.png")

# 12. Folio composition
latest_folio = folios.iloc[-1]
folio_cols = [
    "equity_folios_crore", "debt_folios_crore",
    "hybrid_folios_crore", "others_folios_crore"
]
folio_values = pd.to_numeric(
    latest_folio[folio_cols], errors="coerce"
).fillna(0).astype(float)

plt.pie(folio_values, labels=folio_cols,
        autopct="%1.1f%%", startangle=90)
plt.title("Latest Folio Composition")
save("12_folio_composition.png")

# 13. Investor age distribution
tx["age_group"].value_counts().plot(kind="bar")
plt.title("Investor Transaction Count by Age Group")
plt.ylabel("Transactions")
plt.xticks(rotation=30)
save("13_investor_age_distribution.png")

# 14. SIP amount by age group
sip_tx = tx[
    tx["transaction_type"].astype(str).str.strip().str.lower() == "sip"
].copy()

sns.boxplot(data=sip_tx, x="age_group", y="amount_inr")
plt.title("SIP Transaction Amount by Age Group")
plt.ylabel("SIP Amount (₹)")
plt.xticks(rotation=30)
save("14_sip_amount_by_age.png")

# 15. SIP amount by state
sip_tx.groupby("state")["amount_inr"].sum().sort_values().tail(15).plot(
    kind="barh"
)
plt.title("Top 15 States by SIP Transaction Amount")
plt.xlabel("SIP Amount (₹)")
save("15_sip_by_state.png")

# 16. City tier distribution
tx["city_tier"].value_counts().plot(
    kind="pie", autopct="%1.1f%%"
)
plt.title("Investor Transactions by City Tier")
plt.ylabel("")
save("16_city_tier_distribution.png")

# 17. Transaction type distribution
tx["transaction_type"].value_counts().plot(
    kind="pie", autopct="%1.1f%%"
)
plt.title("Transaction Type Distribution")
plt.ylabel("")
save("17_transaction_type_distribution.png")

# 18. Monthly transaction volume
monthly_tx = tx.groupby(
    tx["transaction_date"].dt.to_period("M")
).size()
monthly_tx.index = monthly_tx.index.astype(str)
monthly_tx.plot()
plt.title("Monthly Investor Transaction Volume")
plt.xlabel("Month")
plt.ylabel("Transactions")
plt.xticks(rotation=45)
save("18_monthly_transaction_volume.png")

# 19. Daily return correlation - 10 schemes
returns = nav.sort_values(["amfi_code", "date"]).copy()
returns["daily_return"] = returns.groupby("amfi_code")["nav"].pct_change()
return_matrix = returns.pivot(
    index="date", columns="amfi_code", values="daily_return"
)
selected = list(return_matrix.columns[:10])
sns.heatmap(return_matrix[selected].corr(), annot=True,
            cmap="coolwarm", center=0, fmt=".2f")
plt.title("Daily Return Correlation - 10 Selected Schemes")
save("19_scheme_return_correlation.png")

# 20. Sector allocation
holdings.groupby("sector")["market_value_cr"].sum().sort_values().plot(
    kind="barh"
)
plt.title("Portfolio Sector Allocation by Market Value")
plt.xlabel("Market Value (₹ Crore)")
save("20_sector_allocation.png")

# 21. Top 10 schemes by 3-year return
performance.nlargest(10, "return_3yr_pct").plot(
    x="scheme_name", y="return_3yr_pct", kind="bar", legend=False
)
plt.title("Top 10 Schemes by 3-Year Return")
plt.ylabel("3-Year Return (%)")
plt.xticks(rotation=75, ha="right")
save("21_top_3yr_returns.png")

# 22. Risk vs return
sns.scatterplot(data=performance, x="std_dev_ann_pct",
                y="return_3yr_pct", hue="risk_grade")
plt.title("Risk vs 3-Year Return")
plt.xlabel("Annualised Standard Deviation (%)")
plt.ylabel("3-Year Return (%)")
save("22_risk_vs_return.png")

# ---------------- 10 DATA-BASED FINDINGS ----------------
latest_sip = sip.sort_values("month").iloc[-1]
latest_folios = folios.sort_values("month").iloc[-1]

latest_aum = aum.sort_values("date").groupby("fund_house").tail(1)
largest_amc = latest_aum.sort_values(
    "aum_lakh_crore", ascending=False
).iloc[0]

findings.append(
    f"NAV dataset covers {nav['amfi_code'].nunique()} schemes "
    f"from {nav['date'].min().date()} to {nav['date'].max().date()}."
)
findings.append(
    f"Latest recorded monthly SIP inflow is ₹{latest_sip['sip_inflow_crore']:,.0f} crore."
)
findings.append(
    f"Active SIP accounts range from "
    f"{sip['active_sip_accounts_crore'].min():.2f} to "
    f"{sip['active_sip_accounts_crore'].max():.2f} crore."
)
findings.append(
    f"Industry folios changed from "
    f"{folios.sort_values('month').iloc[0]['total_folios_crore']:.2f} "
    f"to {latest_folios['total_folios_crore']:.2f} crore."
)
findings.append(
    f"Largest fund house by latest recorded AUM is "
    f"{largest_amc['fund_house']}."
)
findings.append(
    f"Largest category by cumulative net inflow is "
    f"{category.groupby('category')['net_inflow_crore'].sum().idxmax()}."
)
findings.append(
    f"Most frequent investor age group is {tx['age_group'].mode().iloc[0]}."
)
findings.append(
    f"Highest SIP transaction amount by state is recorded in "
    f"{sip_tx.groupby('state')['amount_inr'].sum().idxmax()}."
)
findings.append(
    f"Most common transaction type is "
    f"{tx['transaction_type'].mode().iloc[0]}."
)
best_fund = performance.loc[performance["return_3yr_pct"].idxmax()]
findings.append(
    f"Highest 3-year return in the performance dataset is "
    f"{best_fund['scheme_name']} at "
    f"{best_fund['return_3yr_pct']:.2f}%."
)

with open("reports/eda_key_findings.txt", "w", encoding="utf-8") as f:
    f.write("EDA - 10 KEY FINDINGS\n\n")
    for i, finding in enumerate(findings, 1):
        f.write(f"{i}. {finding}\n")

print("\nEDA GENERATION COMPLETE")
print("Charts generated:", len(list(OUT.glob("*.png"))))
print("Chart folder:", OUT.resolve())
print("Findings file:", Path("reports/eda_key_findings.txt").resolve())
