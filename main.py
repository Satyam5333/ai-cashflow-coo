import pandas as pd

from engine.loader import load_transactions
from engine.cashflow import calculate_daily_cashflow, get_latest_cash
from engine.forecast import forecast_cashflow
from engine.metrics import calculate_business_metrics
from engine.decisions import evaluate_coo_decisions
from engine.advice import generate_coo_advice

# ---------------- CONFIG ----------------
OPENING_CASH = 200000          # Starting cash before CSV history
COD_DELAY_DAYS = 7             # Avg COD delay
FORECAST_DAYS = 60             # Forecast horizon
# ----------------------------------------


def main():
    # 1️⃣ Load transactions
    df = load_transactions("data/transactions.csv")

    # 2️⃣ Calculate daily cashflow from actuals
    daily_cashflow = calculate_daily_cashflow(
        df=df,
        opening_cash=OPENING_CASH
    )

    cash_today = get_latest_cash(daily_cashflow)

    # 3️⃣ Auto-calculate business metrics from CSV
    metrics = calculate_business_metrics(df)

    AVG_DAILY_SALES = metrics["avg_daily_sales"]
    AVG_DAILY_AD_SPEND = metrics["avg_daily_ad_spend"]
    AVG_DAILY_FIXED_COST = metrics["avg_daily_fixed_cost"]
    RETURN_RATE = metrics["return_rate"]

    # 4️⃣ Forecast future cashflow
    forecast_df = forecast_cashflow(
        cash_today=cash_today,
        start_date=daily_cashflow["date"].iloc[-1],
        days=FORECAST_DAYS,
        avg_daily_sales=AVG_DAILY_SALES,
        avg_daily_ad_spend=AVG_DAILY_AD_SPEND,
        avg_daily_fixed_cost=AVG_DAILY_FIXED_COST,
        cod_delay_days=COD_DELAY_DAYS,
        return_rate=RETURN_RATE
    )

    # 5️⃣ COO Metrics
    avg_daily_burn = (
        AVG_DAILY_AD_SPEND +
        AVG_DAILY_FIXED_COST -
        (AVG_DAILY_SALES * (1 - RETURN_RATE))
    )

    if avg_daily_burn <= 0:
        runway_days = "Cash Positive"
    else:
        runway_days = int(cash_today / avg_daily_burn)

    ad_spend_pct = (
        AVG_DAILY_AD_SPEND / AVG_DAILY_SALES
        if AVG_DAILY_SALES > 0 else 0
    )

    # 6️⃣ COO Decisions
    decisions = evaluate_coo_decisions(
        cash_today=cash_today,
        avg_daily_burn=avg_daily_burn,
        runway_days=runway_days,
        ad_spend_pct=ad_spend_pct,
        return_rate=RETURN_RATE
    )

    # 7️⃣ Generate COO Advice
    advice = generate_coo_advice(
        cash_today=cash_today,
        runway_days=runway_days,
        ad_spend_pct=ad_spend_pct,
        return_rate=RETURN_RATE,
        decisions=decisions
    )

    # 8️⃣ Output
    print("\nAI COO ADVICE:\n")
    print(advice)


if __name__ == "__main__":
    main()
