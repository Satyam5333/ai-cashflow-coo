import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# IMPORT YOUR ENGINES
from engine.loader import load_transactions
from engine.metrics import calculate_business_metrics
from engine.decisions import generate_decisions
from engine.forecast import forecast_cashflow
from engine.advice import generate_coo_advice

# =================================================
# PAGE CONFIG & STYLING
# =================================================
st.set_page_config(page_title="AI Cash-Flow COO", layout="wide")

st.markdown("""
<style>
    .kpi-card {
        background: #ffffff; padding: 1.2rem; border-radius: 12px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.08); border-left: 5px solid #6366f1;
    }
    .kpi-title { font-size: 0.85rem; color: #6b7280; font-weight: 600; text-transform: uppercase; }
    .kpi-value { font-size: 1.8rem; font-weight: 700; margin-top: 0.5rem; }
</style>
""", unsafe_allow_html=True)

# =================================================
# ---------------- HEADER ----------------
# =================================================
st.title("🧠 Cash-Flow Early Warning System for SMEs")
st.subheader("Know when your business may face cash trouble — and what to do next.")

st.markdown("""
### What this tool does
- **Analyzes** real transaction data
- **Breakdown** expenses into Ads, Salary, and Rent
- **Forecasts** cash for the next 60 days
""")

# =================================================
# 📥 SAMPLE CSV DOWNLOAD
# =================================================
sample_data = """date,amount,type,description
2026-01-01,150000,inflow,Shopify Payout
2026-01-02,-45000,outflow,Meta Ads - Facebook/Insta
2026-01-05,-12000,outflow,Office Rent
2026-01-10,-25000,outflow,Staff Salary
2026-01-12,-5000,outflow,Shopify Subscription
2026-01-15,120000,inflow,Shopify Payout
2026-01-18,-8000,outflow,Customer Refund
2026-01-20,-35000,outflow,Meta Ads - Retargeting
2026-01-25,-4000,outflow,Google Workspace Tool
"""

st.download_button("📥 Download Sample D2C Transactions CSV", data=sample_data, file_name="sample_d2c_transactions.csv", mime="text/csv")

st.markdown("---")

# =================================================
# SIDEBAR CONTROLS
# =================================================
st.sidebar.header("🕹️ COO Simulation")
opening_balance = st.sidebar.number_input("Starting Bank Balance (INR)", value=200000)
cod_delay = st.sidebar.slider("Avg COD Payment Delay (Days)", 0, 30, 7)
forecast_horizon = st.sidebar.slider("Forecast Look-ahead (Days)", 30, 90, 60)

# =================================================
# MAIN LOGIC
# =================================================
uploaded_file = st.file_uploader("Upload Transactions", type=["csv", "pdf"])

if uploaded_file:
    try:
        df = load_transactions(uploaded_file)
        metrics = calculate_business_metrics(df)
        cash_now = opening_balance + df["amount"].sum()

        # 1. KPI CARDS
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Cash</div><div class='kpi-value'>₹{cash_now:,.0f}</div></div>", unsafe_allow_html=True)
        with c2: st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Runway</div><div class='kpi-value'>{metrics['runway_months']} Mo</div></div>", unsafe_allow_html=True)
        with c3: st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Ad Spend %</div><div class='kpi-value'>{metrics['ad_spend_pct']*100:.1f}%</div></div>", unsafe_allow_html=True)
        with c4: st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Returns</div><div class='kpi-value'>{metrics['return_rate']*100:.1f}%</div></div>", unsafe_allow_html=True)

        # 2. EXPENSE BREAKDOWN SECTION (NEW)
        st.divider()
        st.subheader("📊 Expense Category Breakdown")
        
        # Categorization Logic
        def categorize(desc):
            d = str(desc).lower()
            if any(x in d for x in ["ad", "facebook", "meta", "google", "marketing"]): return "Ads"
            if any(x in d for x in ["salary", "wage", "payroll"]): return "Salary"
            if any(x in d for x in ["rent", "office", "lease"]): return "Rent"
            if any(x in d for x in ["software", "saas", "tool", "aws", "shopify"]): return "Software/SaaS"
            return "Other Expenses"

        expenses = df[df["amount"] < 0].copy()
        expenses["Category"] = expenses["description"].apply(categorize)
        cat_df = expenses.groupby("Category")["amount"].sum().abs().reset_index()

        col_a, col_b = st.columns([1, 1])
        with col_a:
            fig_pie = px.pie(cat_df, values='amount', names='Category', hole=0.4, title="Spend Distribution")
            st.plotly_chart(fig_pie, use_container_width=True)
        with col_b:
            st.write("### Expense Details")
            st.table(cat_df.sort_values(by="amount", ascending=False))

        # 3. FORECAST
        st.divider()
        st.subheader(f"📉 {forecast_horizon}-Day Cash Forecast")
        f_df = forecast_cashflow(cash_today=cash_now, start_date=df["date"].max(), days=forecast_horizon,
                               avg_daily_sales=metrics["avg_daily_sales"], avg_daily_ad_spend=metrics["avg_daily_ad_spend"], 
                               avg_daily_fixed_cost=metrics["avg_daily_fixed_cost"], cod_delay_days=cod_delay, return_rate=metrics["return_rate"])
        st.plotly_chart(px.line(f_df, x="date", y="closing_cash"), use_container_width=True)

        # 4. ADVICE
        st.divider()
        st.subheader("🤖 Executive Strategy Report")
        advice_text = generate_coo_advice(cash_today=cash_now, runway_days=metrics["runway_months"], 
                                         ad_spend_pct=metrics["ad_spend_pct"], return_rate=metrics["return_rate"], decisions=generate_decisions(metrics))
        st.info(advice_text)
        
    except Exception as e:
        st.error(f"Error: {e}")
else:
    st.info("Upload data to begin.")