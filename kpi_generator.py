import pandas as pd
from pathlib import Path

DATA_PATH = Path("data/monthly_financials.csv")

def load_data(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {path}")
    df = pd.read_csv(path)
    # month als Datum interpretieren
    df["month"] = pd.to_datetime(df["month"])
    df = df.sort_values("month").reset_index(drop=True)
    return df

def compute_kpis(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Grundgrößen
    df["gross_profit"] = df["revenue"] - df["cogs"]
    df["gross_margin_pct"] = df["gross_profit"] / df["revenue"] * 100

    df["ebitda"] = df["gross_profit"] - df["opex"]
    df["ebitda_margin_pct"] = df["ebitda"] / df["revenue"] * 100

    # Monatliches Revenue-Wachstum
    df["revenue_mom_growth_pct"] = df["revenue"].pct_change() * 100

    # Burn (negatives EBITDA) und Runway
    # Hier: Burn = -EBITDA, wenn EBITDA < 0, sonst 0
    df["burn"] = df["ebitda"].apply(lambda x: -x if x < 0 else 0)

    def calc_runway(row):
        burn = row["burn"]
        cash = row["cash_balance"]
        if burn > 0:
            return cash / burn
        return None

    df["runway_months"] = df.apply(calc_runway, axis=1)

    return df

def print_summary(df: pd.DataFrame) -> None:
    latest = df.iloc[-1]
    prev = df.iloc[-2] if len(df) >= 2 else None

    print("\n===== KPI SUMMARY (latest month) =====")
    print(f"Month:            {latest['month'].strftime('%Y-%m')}")
    print(f"Revenue:          {latest['revenue']:,.0f} €")
    print(f"Gross margin:     {latest['gross_margin_pct']:5.1f} %")
    print(f"EBITDA margin:    {latest['ebitda_margin_pct']:5.1f} %")
    if pd.notna(latest['runway_months']):
        print(f"Runway:           {latest['runway_months']:4.1f} months")
    else:
        print("Runway:           n/a (no burn)")

    if prev is not None:
        print("\nCompared to previous month:")
        print(f"Revenue MoM:      {latest['revenue_mom_growth_pct']:5.1f} %")

    print("\n===== FULL TABLE =====")
    display_cols = [
        "month", "revenue", "gross_margin_pct",
        "ebitda_margin_pct", "revenue_mom_growth_pct",
        "burn", "cash_balance", "runway_months"
    ]
    table = df[display_cols].copy()

    # numerische Spalten sauber in float umwandeln und runden
    num_cols = [
        "gross_margin_pct",
        "ebitda_margin_pct",
        "revenue_mom_growth_pct",
        "burn",
        "cash_balance",
        "runway_months",
    ]
    for col in num_cols:
        table[col] = pd.to_numeric(table[col], errors="coerce").round(1)

    print(table.to_string(index=False))
def main():
    print("Loading data from:", DATA_PATH)
    df = load_data(DATA_PATH)
    kpi_df = compute_kpis(df)
    print_summary(kpi_df)

if __name__ == "__main__":
    main()