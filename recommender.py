"""Mutual fund recommender with three broad risk buckets."""
from pathlib import Path
import pandas as pd
BASE = Path(__file__).resolve().parent
DATA = BASE / "data" / "processed" / "07_scheme_performance.csv"
RISK_MAP = {"low": "Low", "moderate": "Moderate", "moderately high": "High", "high": "High", "very high": "High"}
def recommend(risk_bucket, top_n=3):
          df = pd.read_csv(DATA)
          df["sharpe_ratio"] = pd.to_numeric(df["sharpe_ratio"], errors="coerce")
          df["risk_bucket"] = df["risk_grade"].astype(str).str.strip().str.lower().map(RISK_MAP)
          result = df[df["risk_bucket"].astype(str).str.lower() == str(risk_bucket).lower()]
          return result.dropna(subset=["sharpe_ratio"]).sort_values("sharpe_ratio", ascending=False).head(top_n)
if __name__ == "__main__":
          for bucket in ["Low", "Moderate", "High"]:
                    print("\
" + bucket + " Risk Funds")
                    print(recommend(bucket).to_string(index=False))
