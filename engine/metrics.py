import pandas as pd
import numpy as np

def calculate_business_metrics(df: pd.DataFrame):
    """
    Acts as a Strategic COO: 
    Interprets data to find hidden health signals for D2C brands.
    """
    # 1. Standardize and Sort
    df = df.sort_values("date")
    total_days = (df["date"].max() - df["date"].min()).days or 1
    total_inflow = df[df["amount"] > 0]["amount"].sum()
    
    # --- HEURISTIC 1: AVG DAILY SALES ---
    # A COO looks at the last 30 days as the 'True' current performance
    recent_mask = df["date"] > (df["date"].max() - pd.Timedelta(days=30))
    recent_df = df[recent_mask]
    avg_daily_sales = recent_df[recent_df["amount"] > 0]["amount"].sum() / 30

    # --- HEURISTIC 2: AVG DAILY AD SPEND ---
    # Identifying Marketing 'Fuel' vs General overhead
    ads_keywords = "ad|facebook|google|meta|insta|marketing|influencer"
    ads_mask = df["description"].str.contains(ads_keywords, case=False, na=False)
    total_ad_spend = df.loc[ads_mask & (df["amount"] < 0), "amount"].abs().sum()
    avg_daily_ad_spend = total_ad_spend / total_days

    # --- HEURISTIC 3: AVG DAILY FIXED COST ---
    # COO Logic: Fixed costs are things like Rent and Salary that repeat
    fixed_keywords = "rent|salary|wage|office|internet|software|saas"
    fixed_mask = df["description"].str.contains(fixed_keywords, case=False, na=False)
    total_fixed = df.loc[fixed_mask & (df["amount"] < 0), "amount"].abs().sum()
    avg_daily_fixed_cost = total_fixed / total_days

    # --- HEURISTIC 4: RETURN RATE ---
    # Basic Heuristic: Outflows labeled 'refund' or 'return' vs Total Sales
    return_keywords = "refund|return|rto|reverse"
    return_mask = df["description"].str.contains(return_keywords, case=False, na=False)
    total_returns = df.loc[return_mask & (df["amount"] < 0), "amount"].abs().sum()
    return_rate = (total_returns / total_inflow) if total_inflow > 0 else 0

    # --- THE COO SUMMARY ---
    current_cash = df["amount"].sum()
    total_daily_outflow = (total_ad_spend + total_fixed + total_returns) / total_days
    
    # Net Burn = (Cash Out - Cash In)
    daily_net_burn = total_daily_outflow - (avg_daily_sales * 0.85) # Accounting for GST/Fees
    
    if daily_net_burn > 0:
        runway_months = round((current_cash / (daily_net_burn * 30)), 1)
    else:
        runway_months = 99.0 # Cash Flow Positive

    return {
        "cash_today": current_cash,
        "runway_months": runway_months,
        "avg_daily_sales": round(avg_daily_sales, 2),
        "avg_daily_ad_spend": round(avg_daily_ad_spend, 2),
        "avg_daily_fixed_cost": round(avg_daily_fixed_cost, 2),
        "return_rate": round(return_rate, 4),
        "ad_spend_pct": (total_ad_spend / total_inflow) if total_inflow > 0 else 0,
        "avg_daily_outflow": total_daily_outflow
    }