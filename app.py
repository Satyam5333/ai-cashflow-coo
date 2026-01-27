import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from datetime import datetime, timedelta
from io import BytesIO
import re

# IMPORT YOUR ENGINES
from engine.loader import load_transactions
from engine.metrics import calculate_business_metrics
from engine.decisions import generate_decisions
from engine.forecast import forecast_cashflow
from engine.advice import generate_coo_advice

# =================================================
# PAGE CONFIG & STYLING
# =================================================
st.set_page_config(page_title="Universal Cash-Flow COO", layout="wide")

st.markdown("""
<style>
    .kpi-card {
        background: #ffffff; padding: 1.2rem; border-radius: 12px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.08); border-left: 5px solid #6366f1;
    }
    .kpi-title { font-size: 0.85rem; color: #6b7280; font-weight: 600; text-transform: uppercase; }
    .kpi-value { font-size: 1.8rem; font-weight: 700; margin-top: 0.5rem; }
    .paid-plan {
        background-color: #f8fafc; padding: 2rem; border-radius: 15px; 
        border: 2px solid #e2e8f0; border-left: 10px solid #1e293b;
    }
    .confidence-score { font-size: 2rem; font-weight: 800; color: #059669; }
</style>
""", unsafe_allow_html=True)

# ---------------- HEADER ----------------
st.title("🧠 AI Investor Flash Report & COO Dashboard")
st.subheader("Know when your business may face cash trouble — and exactly what to do next")

st.markdown("""
### This system acts like a **virtual COO focused purely on cash discipline**.
- **Reads** universal transaction data from any CSV or Excel export
- **Identifies** what is actually driving cash burn
- **Predicts** how long your money will last
- **Generates Investor-Ready "Flash" Reports** automatically
""")

st.markdown("---")

# 🕹️ SIDEBAR CONTROLS
st.sidebar.header("🕹️ COO Simulation")
opening_balance = st.sidebar.number_input("Starting Bank Balance", value=200000)
cod_delay = st.sidebar.slider("Avg Payment Delay (Days)", 0, 30, 7)
forecast_horizon = st.sidebar.slider("Forecast Look-ahead (Days)", 30, 90, 60)

# 📥 MAIN LOGIC
uploaded_file = st.file_uploader("Upload Your Data (CSV or Excel)", type=["csv", "xlsx", "xls"])

if uploaded_file:
    try:
        # 1. LOAD DATA
        df = load_transactions(uploaded_file)
        df.columns = [str(c).lower().strip() for c in df.columns]

        # AGGRESSIVE NUMBER CLEANING ENGINE
        def clean_val(val):
            if pd.isna(val) or val == "": return 0.0
            cleaned = re.sub(r'[^\d.-]', '', str(val))
            try: return float(cleaned)
            except: return 0.0

        # Universal Column Mapping
        if 'txn date' in df.columns: df = df.rename(columns={'txn date': 'date'})
        if 'activity' in df.columns: df = df.rename(columns={'activity': 'description'})

        # AGGRESSIVE ADAPTER: Looks for 'Amount' or 'Debit/Credit' columns automatically
        if 'amount' in df.columns:
            df['amount'] = df['amount'].apply(clean_val)
        elif 'debit' in df.columns and 'credit' in df.columns:
            df['amount'] = df['credit'].apply(clean_val) - df['debit'].apply(clean_val)
        elif 'withdrawals' in df.columns and 'deposits' in df.columns:
            df['amount'] = df['deposits'].apply(clean_val) - df['withdrawals'].apply(clean_val)

        # 2. RUN METRICS
        metrics = calculate_business_metrics(df)
        cash_now = opening_balance + df["amount"].sum()
        
        # 3. KPI CARDS
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Cash Today</div><div class='kpi-value'>₹{cash_now:,.0f}</div></div>", unsafe_allow_html=True)
        with c2: st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Runway</div><div class='kpi-value'>{metrics['runway_months']} Mo</div></div>", unsafe_allow_html=True)
        with c3:
            net_burn = df[df['amount'] < 0]['amount'].sum()
            net_new_rev = df[df['amount'] > 0]['amount'].sum()
            burn_multiple = abs(net_burn / net_new_rev) if net_new_rev != 0 else 0
            st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Burn Multiple</div><div class='kpi-value'>{burn_multiple:.2f}x</div></div>", unsafe_allow_html=True)
        with c4: st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Ad Spend %</div><div class='kpi-value'>{metrics.get('ad_spend_pct', 0)*100:.1f}%</div></div>", unsafe_allow_html=True)

        # 4. SPEND ANALYSIS
        st.divider()
        st.subheader("📊 Spend Analysis")
        def categorize(desc):
            d = str(desc).lower()
            if any(x in d for x in ["ad", "facebook", "meta", "google", "marketing"]): return "Marketing"
            if any(x in d for x in ["salary", "wage", "payroll"]): return "Payroll"
            if any(x in d for x in ["rent", "office", "utility"]): return "Fixed Costs"
            return "Operations"
        df["Category"] = df["description"].apply(categorize)
        cat_df = df[df["amount"] < 0].groupby("Category")["amount"].sum().abs().reset_index()
        
        if not cat_df.empty:
            col_pie, col_table = st.columns([2, 1])
            with col_pie: st.plotly_chart(px.pie(cat_df, values='amount', names='Category', hole=0.4), use_container_width=True)
            with col_table: st.write("### Flow Details"); st.table(cat_df.sort_values(by="amount", ascending=False))

        # 5. FORECAST CHART
        st.divider()
        st.subheader(f"📉 {forecast_horizon}-Day Forecast")
        f_df = forecast_cashflow(cash_today=cash_now, start_date=df["date"].max(), days=forecast_horizon,
                               avg_daily_sales=metrics.get("avg_daily_sales", 0), avg_daily_ad_spend=metrics.get("avg_daily_ad_spend", 0), 
                               avg_daily_fixed_cost=metrics.get("avg_daily_fixed_cost", 0), cod_delay_days=cod_delay, return_rate=metrics.get("return_rate", 0))
        st.plotly_chart(px.line(f_df, x="date", y="closing_cash", title="Predicted Liquidity"), use_container_width=True)

        # 6. DEEP-DIVE SEARCH
        st.divider()
        st.subheader("🔍 Deep-Dive Analysis")
        q = st.text_input("Ask about your records (e.g. 'total rent')")
        if q:
            query = q.lower()
            if "rent" in query:
                val = df[df['description'].str.contains('rent', case=False, na=False)]['amount'].abs().sum()
                st.write(f"📊 **Audit Result:** Total Rent found is ₹{val:,.0f}")

    except Exception as e: st.error(f"Analysis Error: {e}. Check if column names match 'Date', 'Debit', 'Credit'.")
else: st.info("👋 Upload any transaction file (CSV/Excel) to begin.")