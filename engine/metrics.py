import pandas as pd

def calculate_business_metrics(df: pd.DataFrame):
    """Calculates KPIs for the COO dashboard."""
    # 1. Basic Totals
    total_inflow = df[df["amount"] > 0]["amount"].sum()
    total_outflow = df[df["amount"] < 0]["amount"].abs().sum()
    current_cash = df["amount"].sum()

    # 2. Marketing & Returns (using your description logic)
    ads_mask = df["description"].str.contains("ad|facebook|google|instagram|meta", case=False, na=False)
    ad_spend = df.loc[ads_mask & (df["amount"] < 0), "amount"].abs().sum()
    
    returns_mask = df["description"].str.contains("refund|return", case=False, na=False)
    returns = df.loc[returns_mask & (df["amount"] < 0), "amount"].abs().sum()

    # 3. Daily Averages (for the forecast)
    # We look at the last 30 days of data to get a realistic 'current' burn
    last_date = df["date"].max()
    thirty_days_ago = last_date - pd.Timedelta(days=30)
    recent_df = df[df["date"] >= thirty_days_ago]
    
    daily_sales = recent_df[recent_df["amount"] > 0]["amount"].sum() / 30
    daily_outflow = recent_df[recent_df["amount"] < 0]["amount"].abs().sum() / 30
    daily_burn = daily_outflow - (daily_sales * 0.8) # Simple burn estimate

    return {
        "cash_today": current_cash,
        "daily_burn": daily_burn if daily_burn > 0 else 0,
        "ad_spend_pct": (ad_spend / total_inflow) if total_inflow > 0 else 0,
        "return_rate": (returns / total_inflow) if total_inflow > 0 else 0,
        "avg_daily_sales": daily_sales,
        "avg_daily_outflow": daily_outflow
    }