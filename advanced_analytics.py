from pathlib import Path

import numpy as np

import pandas as pd

import matplotlib.pyplot as plt

import nbformat as nbf



# =========================================================

# CONFIGURATION

# =========================================================



BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data" / "processed"

REPORT_DIR = BASE_DIR / "reports"

NOTEBOOK_DIR = BASE_DIR / "notebooks"



REPORT_DIR.mkdir(parents=True, exist_ok=True)

NOTEBOOK_DIR.mkdir(parents=True, exist_ok=True)



RISK_FREE_RATE = 0.065

TRADING_DAYS = 252

ROLLING_WINDOW = 90

MIN_SIP_TRANSACTIONS = 6

SIP_GAP_DAYS = 35





# =========================================================

# HELPER FUNCTIONS

# =========================================================



def load_csv(filename):

          path = DATA_DIR / filename



          if not path.exists():

                    raise FileNotFoundError(f"Missing dataset: {path}")



          return pd.read_csv(path)





def save_csv(df, filename):

          path = REPORT_DIR / filename

          df.to_csv(path, index=False)

          print(f"Saved {filename}: {len(df):,} rows")





# =========================================================

# LOAD DATA

# =========================================================



print("\nLoading datasets...")



nav = load_csv("02_nav_history.csv")

tx = load_csv("08_investor_transactions.csv")

holdings = load_csv("09_portfolio_holdings.csv")

performance = load_csv("07_scheme_performance.csv")

fund_master = load_csv("01_fund_master.csv")





# =========================================================

# DATA PREPARATION

# =========================================================



nav["date"] = pd.to_datetime(nav["date"], errors="coerce")

nav["nav"] = pd.to_numeric(nav["nav"], errors="coerce")

nav["amfi_code"] = pd.to_numeric(nav["amfi_code"], errors="coerce")



nav = nav.dropna(

          subset=["date", "nav", "amfi_code"]

)



nav = nav[nav["nav"] > 0].copy()

nav["amfi_code"] = nav["amfi_code"].astype(int)



nav = nav.drop_duplicates(

          ["amfi_code", "date"]

)



nav = nav.sort_values(

          ["amfi_code", "date"]

)



nav["daily_return"] = (

          nav.groupby("amfi_code")["nav"].pct_change()

)





tx["transaction_date"] = pd.to_datetime(

          tx["transaction_date"],

          errors="coerce"

)



tx["amount_inr"] = pd.to_numeric(

          tx["amount_inr"],

          errors="coerce"

)



tx = tx.dropna(

          subset=["investor_id", "transaction_date"]

).copy()





holdings["portfolio_date"] = pd.to_datetime(

          holdings["portfolio_date"],

          errors="coerce"

)



holdings["weight_pct"] = pd.to_numeric(

          holdings["weight_pct"],

          errors="coerce"

)



holdings["amfi_code"] = pd.to_numeric(

          holdings["amfi_code"],

          errors="coerce"

)



holdings = holdings.dropna(

          subset=[

                    "portfolio_date",

                    "weight_pct",

                    "amfi_code",

                    "sector"

          ]

).copy()



holdings["amfi_code"] = holdings["amfi_code"].astype(int)





performance["amfi_code"] = pd.to_numeric(

          performance["amfi_code"],

          errors="coerce"

)



performance["sharpe_ratio"] = pd.to_numeric(

          performance["sharpe_ratio"],

          errors="coerce"

)



performance["return_3yr_pct"] = pd.to_numeric(

          performance["return_3yr_pct"],

          errors="coerce"

)





fund_master["amfi_code"] = pd.to_numeric(

          fund_master["amfi_code"],

          errors="coerce"

)





# =========================================================

# 1. HISTORICAL VAR AND CVAR

# =========================================================



print("\n1. Calculating Historical VaR and CVaR...")



var_rows = []



for code, group in nav.groupby("amfi_code"):



          returns = group["daily_return"].dropna()



          if len(returns) < 30:

                    continue



          var95 = returns.quantile(0.05)



          cvar95 = returns[

                    returns <= var95

          ].mean()



          var_rows.append({

                    "amfi_code": int(code),

                    "observations": int(len(returns)),

                    "VaR_95_pct": float(var95 * 100),

                    "CVaR_95_pct": float(cvar95 * 100)

          })





var_df = pd.DataFrame(var_rows)



if not var_df.empty:

          var_df = var_df.sort_values("VaR_95_pct")



save_csv(

          var_df,

          "var_cvar_report.csv"

)





# =========================================================

# 2. ROLLING 90-DAY SHARPE RATIO

# TOP 5 FUNDS BY FULL-PERIOD SHARPE

# =========================================================



print("\n2. Calculating Rolling Sharpe Ratio...")



top_funds = (

          performance

          .dropna(subset=["amfi_code", "sharpe_ratio"])

          .sort_values("sharpe_ratio", ascending=False)

          .drop_duplicates("amfi_code")

          .head(5)

)



return_pivot = nav.pivot(

          index="date",

          columns="amfi_code",

          values="daily_return"

).sort_index()



rolling_results = {}

selected_rows = []



for _, fund in top_funds.iterrows():



          code = int(fund["amfi_code"])



          if code not in return_pivot.columns:

                    continue



          returns = return_pivot[code]



          rolling_mean = returns.rolling(

                    ROLLING_WINDOW,

                    min_periods=ROLLING_WINDOW

          ).mean()



          rolling_std = returns.rolling(

                    ROLLING_WINDOW,

                    min_periods=ROLLING_WINDOW

          ).std()



          rolling_sharpe = (

                    (

                              rolling_mean

                              - RISK_FREE_RATE / TRADING_DAYS

                    )

                    / rolling_std

          ) * np.sqrt(TRADING_DAYS)



          rolling_results[str(fund["scheme_name"])] = (

                    rolling_sharpe

          )



          selected_rows.append({

                    "amfi_code": code,

                    "scheme_name": fund["scheme_name"],

                    "full_period_sharpe": fund["sharpe_ratio"]

          })





rolling_df = pd.DataFrame(rolling_results)

rolling_df.index.name = "date"



rolling_df.to_csv(

          REPORT_DIR / "rolling_sharpe_values.csv"

)



selected_df = pd.DataFrame(selected_rows)



save_csv(

          selected_df,

          "rolling_sharpe_selected_funds.csv"

)





plt.figure(figsize=(14, 7))



for name in rolling_df.columns:

          plt.plot(

                    rolling_df.index,

                    rolling_df[name],

                    label=name,

                    linewidth=1.1

          )



plt.axhline(

          0,

          linestyle="--",

          linewidth=0.8

)



plt.title(

          "Rolling 90-Day Sharpe Ratio - Top 5 Funds"

)



plt.xlabel("Date")

plt.ylabel("Annualised Sharpe Ratio")



plt.legend(fontsize=8)

plt.tight_layout()



plt.savefig(

          REPORT_DIR / "rolling_sharpe_chart.png",

          dpi=160,

          bbox_inches="tight"

)



plt.close()





# =========================================================

# 3. INVESTOR COHORT ANALYSIS

# =========================================================



print("\n3. Performing Investor Cohort Analysis...")



tx["year"] = tx["transaction_date"].dt.year



first_year = (

          tx.groupby("investor_id")["year"].min()

)



tx["cohort_year"] = (

          tx["investor_id"].map(first_year)

)



cohort_tx = tx[

          tx["cohort_year"].isin([2024, 2025])

].copy()





activity = (

          cohort_tx

          .groupby(["cohort_year", "year"])["investor_id"]

          .nunique()

          .rename("active_investors")

          .reset_index()

)



activity["period_number"] = (

          activity["year"] - activity["cohort_year"]

)





cohort_pivot = activity.pivot(

          index="cohort_year",

          columns="period_number",

          values="active_investors"

)



cohort_sizes = (

          first_year[first_year.isin([2024, 2025])]

          .value_counts()

)



cohort_retention = (

          cohort_pivot.div(cohort_sizes, axis=0) * 100

)



cohort_retention.index.name = "cohort_year"



cohort_retention.columns = [

          f"period_{int(c)}_retention_pct"

          for c in cohort_retention.columns

]



cohort_retention = cohort_retention.reset_index()



save_csv(

          cohort_retention,

          "cohort_analysis.csv"

)





# =========================================================

# 4. SIP CONTINUITY ANALYSIS

# =========================================================



print("\n4. Performing SIP Continuity Analysis...")



sip = tx[

          tx["transaction_type"]

          .astype(str)

          .str.strip()

          .str.lower() == "sip"

].copy()



sip = sip.sort_values(

          ["investor_id", "transaction_date"]

)



sip["gap_days"] = (

          sip.groupby("investor_id")["transaction_date"]

          .diff()

          .dt.days

)





sip_summary = (

          sip.groupby("investor_id")

          .agg(

                    sip_transaction_count=("transaction_date", "count"),

                    average_gap_days=("gap_days", "mean"),

                    maximum_gap_days=("gap_days", "max"),

                    total_sip_amount_inr=("amount_inr", "sum")

          )

          .reset_index()

)





sip_summary["at_risk"] = (

          (sip_summary["sip_transaction_count"] >= MIN_SIP_TRANSACTIONS)

          &

          (sip_summary["maximum_gap_days"] > SIP_GAP_DAYS)

)





save_csv(

          sip_summary,

          "sip_continuity.csv"

)





# =========================================================

# 5. FUND RECOMMENDER

# THREE BROAD RISK BUCKETS

# =========================================================



print("\n5. Building Fund Recommender...")



risk_map = {

          "low": "Low",

          "moderate": "Moderate",

          "moderately high": "High",

          "high": "High",

          "very high": "High"

}





rec_data = performance.copy()



rec_data["risk_bucket"] = (

          rec_data["risk_grade"]

          .astype(str)

          .str.strip()

          .str.lower()

          .map(risk_map)

)



rec_data = rec_data.dropna(

          subset=[

                    "scheme_name",

                    "risk_bucket",

                    "sharpe_ratio"

          ]

)





rec_rows = []



for bucket in ["Low", "Moderate", "High"]:



          subset = rec_data[

                    rec_data["risk_bucket"] == bucket

          ]



          top = (

                    subset

                    .sort_values("sharpe_ratio", ascending=False)

                    .head(3)

          )



          for rank, (_, row) in enumerate(top.iterrows(), 1):



                    rec_rows.append({

                              "risk_bucket": bucket,

                              "rank": rank,

                              "scheme_name": row["scheme_name"],

                              "source_risk_grade": row["risk_grade"],

                              "sharpe_ratio": row["sharpe_ratio"],

                              "return_3yr_pct": row["return_3yr_pct"]

                    })





recommendations = pd.DataFrame(rec_rows)



save_csv(

          recommendations,

          "fund_recommendations.csv"

)





# Generate standalone recommender.py



recommender_lines = [

          '"""Mutual fund recommender with three broad risk buckets."""',

          "from pathlib import Path",

          "import pandas as pd",

          "BASE = Path(__file__).resolve().parent",

          'DATA = BASE / "data" / "processed" / "07_scheme_performance.csv"',

          'RISK_MAP = {"low": "Low", "moderate": "Moderate", "moderately high": "High", "high": "High", "very high": "High"}',

          "def recommend(risk_bucket, top_n=3):",

          "          df = pd.read_csv(DATA)",

          '          df["sharpe_ratio"] = pd.to_numeric(df["sharpe_ratio"], errors="coerce")',

          '          df["risk_bucket"] = df["risk_grade"].astype(str).str.strip().str.lower().map(RISK_MAP)',

          '          result = df[df["risk_bucket"].astype(str).str.lower() == str(risk_bucket).lower()]',

          '          return result.dropna(subset=["sharpe_ratio"]).sort_values("sharpe_ratio", ascending=False).head(top_n)',

          'if __name__ == "__main__":',

          '          for bucket in ["Low", "Moderate", "High"]:',

          '                    print("\\\n" + bucket + " Risk Funds")',

          '                    print(recommend(bucket).to_string(index=False))'

]



(BASE_DIR / "recommender.py").write_text(

          "\n".join(recommender_lines) + "\n",

          encoding="utf-8"

)





# =========================================================

# 6. SECTOR CONCENTRATION - HHI

# EQUITY FUNDS ONLY, LATEST HOLDINGS SNAPSHOT

# =========================================================



print("\n6. Calculating Sector HHI...")



equity_codes = set(

          fund_master.loc[

                    fund_master["category"]

                    .astype(str)

                    .str.strip()

                    .str.lower() == "equity",

                    "amfi_code"

          ]

          .dropna()

          .astype(int)

)





equity_holdings = holdings[

          holdings["amfi_code"].isin(equity_codes)

].copy()





latest_dates = (

          equity_holdings

          .groupby("amfi_code")["portfolio_date"]

          .transform("max")

)



equity_holdings = equity_holdings[

          equity_holdings["portfolio_date"] == latest_dates

]





sector_weights = (

          equity_holdings

          .groupby(["amfi_code", "sector"])["weight_pct"]

          .sum()

          .reset_index()

)





hhi_rows = []



for code, group in sector_weights.groupby("amfi_code"):



          total_weight = group["weight_pct"].sum()



          if total_weight <= 0:

                    continue



          normalized_weights = (

                    group["weight_pct"] / total_weight

          )



          hhi = (

                    normalized_weights ** 2

          ).sum() * 10000



          hhi_rows.append({

                    "amfi_code": int(code),

                    "sector_count": int(group["sector"].nunique()),

                    "sector_hhi": float(hhi)

          })





hhi_df = pd.DataFrame(hhi_rows)



if not hhi_df.empty:

          hhi_df = hhi_df.sort_values("sector_hhi")



save_csv(

          hhi_df,

          "sector_hhi.csv"

)





if not hhi_df.empty:



          plt.figure(figsize=(13, 6))



          plt.bar(

                    hhi_df["amfi_code"].astype(str),

                    hhi_df["sector_hhi"]

          )



          plt.title(

                    "Sector Concentration (HHI) - Equity Funds"

          )



          plt.xlabel("AMFI Code")

          plt.ylabel("Herfindahl-Hirschman Index")



          plt.xticks(rotation=90)

          plt.tight_layout()



          plt.savefig(

                    REPORT_DIR / "sector_hhi_chart.png",

                    dpi=160,

                    bbox_inches="tight"

          )



          plt.close()





# =========================================================

# 7. GENERATE ADVANCED ANALYTICS KEY INSIGHTS

# =========================================================



print("\n7. Generating Key Insights...")



eligible_sip = sip_summary[

          sip_summary["sip_transaction_count"] >= MIN_SIP_TRANSACTIONS

]



at_risk_sip = eligible_sip[

          eligible_sip["at_risk"]

]



risk_pct = (

          len(at_risk_sip) / len(eligible_sip) * 100

          if len(eligible_sip) else 0

)





insights = [

          (

                    f"Historical 95% VaR averages "

                    f"{var_df['VaR_95_pct'].mean():.2f}% "

                    f"across {len(var_df)} schemes."

          ),

          (

                    f"Historical 95% CVaR averages "

                    f"{var_df['CVaR_95_pct'].mean():.2f}% "

                    f"across the schemes."

          ),

          (

                    f"{len(at_risk_sip):,} of {len(eligible_sip):,} "

                    f"investors with at least six SIP transactions "

                    f"are flagged at risk ({risk_pct:.2f}%)."

          ),

          (

                    f"Sector HHI was calculated for {len(hhi_df)} "

                    f"Equity schemes using each fund's latest "

                    f"available holdings snapshot."

          ),

          (

                    f"The rolling Sharpe chart tracks "

                    f"{len(rolling_df.columns)} funds selected "

                    f"by full-period Sharpe ratio."

          )

]





cohort_2024 = cohort_retention[

          cohort_retention["cohort_year"] == 2024

]



if (

          not cohort_2024.empty

          and "period_1_retention_pct" in cohort_retention.columns

):



          retention = cohort_2024[

                    "period_1_retention_pct"

          ].iloc[0]



          if pd.notna(retention):



                    insights.append(

                              f"The 2024 investor cohort shows "

                              f"{retention:.2f}% activity retention "

                              f"in the following calendar year."

                    )





if not recommendations.empty:



          counts = recommendations[

                    "risk_bucket"

          ].value_counts().to_dict()



          insights.append(

                    "Recommendation counts by bucket: "

                    + ", ".join(

                              f"{key}={value}"

                              for key, value in sorted(counts.items())

                    )

          )





with open(

          REPORT_DIR / "advanced_key_insights.txt",

          "w",

          encoding="utf-8"

) as file:



          file.write(

                    "ADVANCED ANALYTICS - KEY INSIGHTS\n\n"

          )



          for i, insight in enumerate(insights, 1):

                    file.write(f"{i}. {insight}\n")





# =========================================================

# 8. GENERATE ADVANCED ANALYTICS NOTEBOOK

# =========================================================



print("\n8. Generating Advanced Analytics Notebook...")



nb = nbf.v4.new_notebook()



cells = [



          nbf.v4.new_markdown_cell(

                    "# Advanced Analytics — Bluestock Mutual Fund Platform\n\n"

                    "Risk, rolling Sharpe, investor cohorts, SIP continuity, "

                    "fund recommendations and sector concentration.\n\n"

                    "Annual risk-free rate: 6.5%. "

                    "Rolling window: 90 observed trading-day returns."

          ),



          nbf.v4.new_markdown_cell(

                    "## 1. Historical VaR and CVaR\n\n"

                    "VaR is the 5th percentile of observed daily NAV returns. "

                    "CVaR is the mean of returns at or below that threshold. "

                    "These are historical estimates, not forecasts."

          ),



          nbf.v4.new_code_cell(

                    "import pandas as pd\n"

                    "from pathlib import Path\n"

                    "from IPython.display import display, Image\n"

                    "PROJECT_DIR = Path.cwd()\n"

                    "if PROJECT_DIR.name == 'notebooks':\n"

                    "          PROJECT_DIR = PROJECT_DIR.parent\n"

                    "REPORT_DIR = PROJECT_DIR / 'reports'\n"

                    "var_df = pd.read_csv(REPORT_DIR / 'var_cvar_report.csv')\n"

                    "display(var_df.sort_values('VaR_95_pct').head(10))\n"

                    "display(var_df[['VaR_95_pct', 'CVaR_95_pct']].describe().round(3))"

          ),



          nbf.v4.new_markdown_cell(

                    "## 2. Rolling 90-Day Sharpe Ratio\n\n"

                    "The five schemes are selected by highest full-period "

                    "Sharpe ratios in the supplied performance dataset. "

                    "Rolling Sharpe uses 90 observed NAV return rows and "

                    "the 6.5% annual risk-free rate."

          ),



          nbf.v4.new_code_cell(

                    "selected = pd.read_csv(REPORT_DIR / 'rolling_sharpe_selected_funds.csv')\n"

                    "display(selected)\n"

                    "display(Image(filename=str(REPORT_DIR / 'rolling_sharpe_chart.png')))"

          ),



          nbf.v4.new_markdown_cell(

                    "## 3. Investor Cohort Analysis\n\n"

                    "Cohorts are based on each investor's first transaction year. "

                    "Retention means transaction activity in a subsequent calendar year. "

                    "Missing periods are unavailable observations, not zero retention."

          ),



          nbf.v4.new_code_cell(

                    "cohort = pd.read_csv(REPORT_DIR / 'cohort_analysis.csv')\n"

                    "display(cohort)"

          ),



          nbf.v4.new_markdown_cell(

                    "## 4. SIP Continuity\n\n"

                    "An investor is flagged only if they have at least six "

                    "recorded SIP transactions and a maximum gap between "

                    "consecutive recorded SIP transactions greater than 35 days. "

                    "This is a historical screening rule."

          ),



          nbf.v4.new_code_cell(

                    "sip = pd.read_csv(REPORT_DIR / 'sip_continuity.csv')\n"

                    "eligible = sip[sip['sip_transaction_count'] >= 6]\n"

                    "at_risk = eligible[eligible['at_risk'].astype(bool)]\n"

                    "print('Investors analysed:', len(sip))\n"

                    "print('Eligible investors:', len(eligible))\n"

                    "print('At-risk investors:', len(at_risk))\n"

                    "print('At-risk share:', round(len(at_risk)/len(eligible)*100, 2) if len(eligible) else 0, '%')\n"

                    "display(at_risk.sort_values('maximum_gap_days', ascending=False).head(10))"

          ),



          nbf.v4.new_markdown_cell(

                    "## 5. Fund Recommendations by Risk Bucket\n\n"

                    "Low remains Low; Moderate remains Moderate; "

                    "Moderately High, High and Very High are grouped into High. "

                    "Funds are ranked by Sharpe ratio within each bucket. "

                    "This is not personalised investment advice."

          ),



          nbf.v4.new_code_cell(

                    "recommendations = pd.read_csv(REPORT_DIR / 'fund_recommendations.csv')\n"

                    "for bucket in ['Low', 'Moderate', 'High']:\n"

                    "          print('\\\n' + bucket + ' Risk')\n"

                    "          display(recommendations[recommendations['risk_bucket'] == bucket])"

          ),



          nbf.v4.new_markdown_cell(

                    "## 6. Sector Concentration — HHI\n\n"

                    "HHI is the sum of squared normalised sector weights "

                    "multiplied by 10,000. Only Equity schemes are included, "

                    "using each fund's latest available holdings snapshot."

          ),



          nbf.v4.new_code_cell(

                    "hhi = pd.read_csv(REPORT_DIR / 'sector_hhi.csv')\n"

                    "display(hhi.sort_values('sector_hhi', ascending=False))\n"

                    "display(Image(filename=str(REPORT_DIR / 'sector_hhi_chart.png')))"

          ),



          nbf.v4.new_markdown_cell(

                    "## 7. Key Findings"

          ),



          nbf.v4.new_code_cell(

                    "print((REPORT_DIR / 'advanced_key_insights.txt').read_text(encoding='utf-8'))"

          ),



          nbf.v4.new_markdown_cell(

                    "## 8. Methodology and Limitations\n\n"

                    "- VaR/CVaR are historical estimates, not forecasts.\n"

                    "- Rolling Sharpe uses 90 observed NAV return rows, not calendar days.\n"

                    "- Cohort retention measures later-year transaction activity, not assets retained.\n"

                    "- SIP gaps are measured between recorded transactions; contractual due dates are not available.\n"

                    "- Recommendations rank supplied funds by Sharpe within broad risk buckets.\n"

                    "- HHI measures sector concentration in the latest supplied Equity holdings snapshot.\n"

                    "- Results depend on supplied data coverage and are not personalised investment advice."

          )

]



nb.cells = cells



nb.metadata = {

          "kernelspec": {

                    "display_name": "Python 3",

                    "language": "python",

                    "name": "python3"

          },

          "language_info": {

                    "name": "python"

          }

}



nbf.write(

          nb,

          NOTEBOOK_DIR / "05_advanced_analytics.ipynb"

)





# =========================================================

# COMPLETION SUMMARY

# =========================================================



print("\n" + "=" * 55)

print("ADVANCED ANALYTICS COMPLETED")

print("=" * 55)



print("VaR/CVaR schemes:", len(var_df))

print("Rolling Sharpe selected funds:", len(rolling_df.columns))

print("Cohort rows:", len(cohort_retention))

print("SIP investors analysed:", len(sip_summary))

print("SIP eligible investors:", len(eligible_sip))

print("SIP at-risk investors:", len(at_risk_sip))

print("Recommendations:", len(recommendations))

print("Equity funds with HHI:", len(hhi_df))

print("Key insights:", len(insights))

print("Notebook cells:", len(nb.cells))



print("\nGenerated files:")

print("- reports/var_cvar_report.csv")

print("- reports/rolling_sharpe_chart.png")

print("- reports/rolling_sharpe_values.csv")

print("- reports/rolling_sharpe_selected_funds.csv")

print("- reports/cohort_analysis.csv")

print("- reports/sip_continuity.csv")

print("- reports/fund_recommendations.csv")

print("- reports/sector_hhi.csv")

print("- reports/sector_hhi_chart.png")

print("- reports/advanced_key_insights.txt")

print("- recommender.py")

print("- notebooks/05_advanced_analytics.ipynb")



print("\nAdvanced Analytics pipeline finished.")
