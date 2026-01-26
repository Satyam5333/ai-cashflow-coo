import streamlit as st
import pandas as pd
import tempfile
import os

from engine.loader import load_transactions
from engine.cashflow import calculate_daily_cashflow, get_latest_cash
from engine.forecast import forecast_cashflow
from engine.metrics import calculate_business_metrics
from engine.decisions import evaluate_coo_decisions
from engine.advice import generate_coo_advice

# ---------------- CONFIG ----------------
OPENING_CASH = 200000
COD_DELAY_DAYS = 7
FORECAST_DAYS = 60
# ----------------------------------------


st.set_page_config(
    page_title="Cash-Flow Early Warning System",
    page_icon="🧠",
    layout="centered"
)

# ---------------- HEADER ----------------
st.title("🧠 Cash-Flow Early Warning System for SMEs")
st.subheader(
    "Know when your business may face cash trouble — and what to do next."
)

st.markdown("""
### What this tool does
This system:
- Analyzes your real transaction data
- Forecasts cash position for the next 60 days
- Flags overspending and cash risks
- Gives clear, actionable recommendations  
*(No dashboards. No jargon. Just decisions.)*
""")

st.markdown("---")

# ---------------- FILE UPLOAD ----------------
uploaded_file = st.file_uploader(
    "Upload your transactions CSV (bank / accounting / POS export)",
    type=["csv"]
)

# -------- SAMPLE CSV DOWNLOAD ----------
with st.expander("📥 Need a sample CSV format?"):
    st.download_button(
        label="Download sample transactions CSV",
        data="""date,type,description,amount
2026-01-01,Inflow,Sales,52000
2026-01-01,Outflow,Facebook Ads,-18000
2026-01-02,Outflow,Salary,-8000
2026-01-03,Inflow,COD Settlement,34000
""",
        file_name="sample_transactions.csv",
        mime="text/csv"
    )

# ---------------- PROCESSING ----------------
if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
        tmp.write(uploaded_file.getbuffer())
        tmp_path = tmp.name

    try:
        df = load_transactions(tmp_path)

        daily_cashflow = calculate_daily_cashflow(
            df=df,
            opening_cash=OPENING_CASH
        )
        cash_today = get_latest_cash(daily_cashflow)

        metrics = calculate_business_metrics(df)

        avg_sales = metrics["avg_daily_sales"]
        avg_ads = metrics["avg_daily_ad_spend"]
        avg_fixed = metrics["avg_daily_fixed_cost"]
        return_rate = metrics["return_rate"]

        forecast_df = forecast_cashflow(
            cash_today=cash_today,
            start_date=daily_cashflow["date"].iloc[-1],
            days=FORECAST_DAYS,
            avg_daily_sales=avg_sales,
            avg_daily_ad_spend=avg_ads,
            avg_daily_fixed_cost=avg_fixed,
            cod_delay_days=COD_DELAY_DAYS,
            return_rate=return_rate
        )

        avg_daily_burn = avg_ads + avg_fixed - (avg_sales * (1 - return_rate))

        if avg_daily_burn <= 0:
            runway_days = "Cash Positive"
        else:
            runway_days = int(cash_today / avg_daily_burn)

        ad_spend_pct = avg_ads / avg_sales if avg_sales > 0 else 0

        decisions = evaluate_coo_decisions(
            cash_today=cash_today,
            avg_daily_burn=avg_daily_burn,
            runway_days=runway_days,
            ad_spend_pct=ad_spend_pct,
            return_rate=return_rate
        )

        advice = generate_coo_advice(
            cash_today=cash_today,
            runway_days=runway_days,
            ad_spend_pct=ad_spend_pct,
            return_rate=return_rate,
            decisions=decisions
        )

        # ---------------- OUTPUT ----------------
        st.success("AI COO Analysis Ready")

        col1, col2, col3 = st.columns(3)
        col1.metric("Cash Today", f"₹{cash_today:,.0f}")
        col2.metric("Runway", runway_days)
        col3.metric("Ad Spend %", f"{ad_spend_pct*100:.1f}%")

        st.markdown("### 🧠 COO Advice")
        st.text(advice)

    except Exception as e:
        st.error("Error processing file")
        st.code(str(e))

    finally:
        os.remove(tmp_path)

st.markdown("---")
st.caption(
    "Disclaimer: This tool provides decision support based on uploaded data. "
    "It does not replace professional financial or accounting advice."
)
