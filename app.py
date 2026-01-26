import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import pdfplumber

# IMPORT YOUR ENGINES
from engine.loader import load_transactions
from engine.metrics import calculate_business_metrics
from engine.decisions import generate_decisions
from engine.forecast import forecast_cashflow
from engine.advice import generate_coo_advice

# =================================================
# PAGE CONFIG & STYLING (Kept from your original)
# =================================================
st.set_page_config(page_title="AI Cash-Flow COO", layout="wide")

st.markdown("""
<style>
    .kpi-card {
        background: #ffffff; padding: 1rem; border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-left: 5px solid #6366f1;
    }
    .kpi-title { font-size: 0.8rem; color: #6b7280; font-weight: 600; }
    .kpi-value { font-size: 1.8rem; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

st.title("🧠 AI Cash-Flow COO")
st.write("Professional Early Warning System for SMEs")

# =================================================
# SIDEBAR CONTROLS
# =================================================
st.sidebar.header("🕹️ Simulation Settings")
opening_balance = st.sidebar.number_input("Current Bank Balance (INR)", value=200000)
cod_delay = st.sidebar.slider("COD Payment Delay (Days)", 0, 30, 7)
forecast_days = st.sidebar.slider("Forecast Horizon (Days)", 30, 90, 60)

# =================================================
# FILE UPLOADER
# =================================================
uploaded_file = st.file_uploader("Upload Transactions (CSV or PDF)", type=["csv", "pdf"])

if uploaded_file:
    # 1. LOAD DATA
    df = load_transactions(uploaded_file)
    
    # 2. CALCULATE METRICS
    metrics = calculate_business_metrics(df)
    
    # Update cash today based on user input + history
    cash_now = opening_balance + df["amount"].sum()
    runway = int(cash_now / metrics["daily_burn"]) if metrics["daily_burn"] > 0 else "∞"

    # 3. KPI DISPLAY
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Total Cash</div><div class='kpi-value'>₹{cash_now:,.0f}</div></div>", unsafe_allow_html=True)
    with c2: st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Runway</div><div class='kpi-value'>{runway} Days</div></div>", unsafe_allow_html=True)
    with c3: st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Ad Spend</div><div class='kpi-value'>{metrics['ad_spend_pct']*100:.1f}%</div></div>", unsafe_allow_html=True)
    with c4: st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Return Rate</div><div class='kpi-value'>{metrics['return_rate']*100:.1f}%</div></div>", unsafe_allow_html=True)

    # 4. FORECAST CHART (Plotly)
    st.subheader("📉 60-Day Cash Forecast")
    f_df = forecast_cashflow(
        cash_today=cash_now,
        start_date=df["date"].max(),
        days=forecast_days,
        avg_daily_sales=metrics["avg_daily_sales"],
        avg_daily_ad_spend=metrics["avg_daily_outflow"] * 0.4, # Estimate ads as 40% of outflow
        avg_daily_fixed_cost=metrics["avg_daily_outflow"] * 0.6,
        cod_delay_days=cod_delay,
        return_rate=metrics["return_rate"]
    )
    
    fig = px.line(f_df, x="date", y="closing_cash", title="Projected Cash Position")
    fig.add_hline(y=0, line_dash="dash", line_color="red") # The danger line
    st.plotly_chart(fig, use_container_width=True)

    # 5. AI COO ADVICE
    st.divider()
    st.subheader("🤖 Executive Strategy Report")
    
    # Get risks and actions from your engine
    decisions = generate_decisions(metrics)
    
    advice_text = generate_coo_advice(
        cash_today=cash_now,
        runway_days=runway,
        ad_spend_pct=metrics["ad_spend_pct"],
        return_rate=metrics["return_rate"],
        decisions=decisions
    )
    
    st.info(advice_text)
else:
    st.info("Please upload a CSV or PDF bank statement to begin analysis.")