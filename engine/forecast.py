import pandas as pd
from datetime import timedelta

def forecast_cashflow(
    cash_today: float,
    start_date: pd.Timestamp,
    days: int,
    avg_daily_sales: float,
    avg_daily_ad_spend: float,
    avg_daily_fixed_cost: float,
    cod_delay_days: int,
    return_rate: float
) -> pd.DataFrame:
    """
    Replicates Excel Cash_Forecast_60_Days logic
    """

    rows = []
    current_cash = cash_today

    for day in range(1, days + 1):
        forecast_date = start_date + timedelta(days=day)

        # Inflows after COD delay
        if day <= cod_delay_days:
            inflow = 0.0
        else:
            inflow = avg_daily_sales * (1 - return_rate)

        # Daily outflows
        outflow = avg_daily_ad_spend + avg_daily_fixed_cost

        closing_cash = current_cash + inflow - outflow

        rows.append({
            "date": forecast_date,
            "opening_cash": current_cash,
            "inflows": inflow,
            "outflows": outflow,
            "closing_cash": closing_cash
        })

        current_cash = closing_cash

    return pd.DataFrame(rows)
