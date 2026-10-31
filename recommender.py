"""Simple mutual fund recommender by risk grade."""
import pandas as pd
from pathlib import Path

BASE = Path(__file__).resolve().parent
DATA = BASE / 'data' / 'processed' / '07_scheme_performance.csv'

def recommend(risk_grade, top_n=3):
    df = pd.read_csv(DATA)
    df['sharpe_ratio'] = pd.to_numeric(df['sharpe_ratio'], errors='coerce')
    result = df[df['risk_grade'].astype(str).str.lower() == str(risk_grade).lower()]
    result = result.dropna(subset=['sharpe_ratio'])
    return result.sort_values('sharpe_ratio', ascending=False).head(top_n)

if __name__ == '__main__':
    for grade in ['Low', 'Moderate', 'High']:
        print(f'\n{grade} Risk Funds')
        print(recommend(grade).to_string(index=False))