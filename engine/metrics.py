import pandas as pd

def calculate_business_metrics(df: pd.DataFrame):
    # 1. Sales & Cash Position
    total_inflow = df[df["amount"] > 0]["amount"].sum()
    current_cash = df["amount"].sum()

    # 2. D2C Specifics: Marketing & Returns
    # These look for 'Shopify', 'Ads', or 'Refund' in your transaction descriptions
    ads_mask = df["description"].str.contains("ad|facebook|google|meta|marketing", case=False, na=False)
    ad_spend = df.loc[ads_mask & (df["amount"] < 0), "amount"].abs().sum()
    
    returns_mask = df["description"].str.contains("refund|return|reverse", case=False, na=False)
    returns = df.loc[returns_mask & (df["amount"] < 0), "amount"].abs().sum()

    # 3. Monthly Burn Rate
    # Calculates how much more you spend than you make each month
    last_date = df["date"].max()
    thirty_days_ago = last_date - pd.Timedelta(days=30)
    recent_df = df[df["date"] >= thirty_days_ago]
    
    daily_sales = recent_df[recent_df["amount"] > 0]["amount"].sum() / 30
    daily_outflow = recent_df[recent_df["amount"] < 0]["amount"].abs().sum() / 30
    
    monthly_burn = (daily_outflow - daily_sales) * 30

    # 4. Runway (How many months until zero cash)
    if monthly_burn > 0:
        runway_months = round(current_cash / monthly_burn, 1)
    else:
        runway_months = 99.0  # Business is currently generating surplus cash

    return {
        "cash_today": current_cash,
        "monthly_burn": monthly_burn,
        "runway_months": runway_months,
        "ad_spend_pct": (ad_spend / total_inflow) if total_inflow > 0 else 0,
        "return_rate": (returns / total_inflow) if total_inflow > 0 else 0,
        "avg_daily_sales": daily_sales,
        "avg_daily_outflow": daily_outflow
    }