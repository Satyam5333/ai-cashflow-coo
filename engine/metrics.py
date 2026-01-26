import pandas as pd

def calculate_business_metrics(df: pd.DataFrame) -> dict:
    """
    Derives business metrics automatically from transaction data
    """

    # Ensure correct types
    df["date"] = pd.to_datetime(df["date"])
    df["amount"] = df["amount"].astype(float)

    # Separate inflows and outflows
    inflows = df[df["amount"] > 0].copy()
    outflows = df[df["amount"] < 0].copy()

    # --- Avg Daily Sales ---
    daily_sales = (
        inflows.groupby("date")["amount"]
        .sum()
    )
    avg_daily_sales = daily_sales.mean() if not daily_sales.empty else 0

    # --- Ad Spend ---
    ad_spend = outflows[
        outflows["description"].str.contains("ad", case=False, na=False)
    ]
    daily_ads = (
        ad_spend.groupby("date")["amount"]
        .sum()
        .abs()
    )
    avg_daily_ad_spend = daily_ads.mean() if not daily_ads.empty else 0

    # --- Fixed Costs (salary, rent, etc.) ---
    fixed_costs = outflows[
        outflows["description"].str.contains(
            "salary|rent|office|fixed", case=False, na=False
        )
    ]
    daily_fixed = (
        fixed_costs.groupby("date")["amount"]
        .sum()
        .abs()
    )
    avg_daily_fixed_cost = daily_fixed.mean() if not daily_fixed.empty else 0

    # --- Return Rate (heuristic) ---
    returns = inflows[
        inflows["description"].str.contains("return|refund", case=False, na=False)
    ]
    return_rate = (
        abs(returns["amount"].sum()) / inflows["amount"].sum()
        if inflows["amount"].sum() > 0
        else 0
    )

    return {
        "avg_daily_sales": round(avg_daily_sales, 2),
        "avg_daily_ad_spend": round(avg_daily_ad_spend, 2),
        "avg_daily_fixed_cost": round(avg_daily_fixed_cost, 2),
        "return_rate": round(return_rate, 2)
    }
