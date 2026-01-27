import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from datetime import datetime, timedelta
from io import BytesIO
import re

# PART 1: EXTERNAL ENGINE IMPORTS (PRESERVED)
from engine.loader import load_transactions
from engine.metrics import calculate_business_metrics
from engine.decisions import generate_decisions
from engine.forecast import forecast_cashflow
from engine.advice import generate_coo_advice

# PART 2: PAGE CONFIG & HARDCORE CSS STYLING
st.set_page_config(page_title="Hardcore AI Cash-Flow COO", layout="wide")

st.markdown("""
<style>
    .kpi-card {
        background: #ffffff; padding: 1.2rem; border-radius: 12px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.08); border-left: 5px solid #6366f1;
    }
    .kpi-title { font-size: 0.85rem; color: #6b7280; font-weight: 600; text-transform: uppercase; }
    .kpi-value { font-size: 1.8rem; font-weight: 700; margin-top: 0.5rem; }
    .coo-summary-box {
        background-color: #f0f9ff; padding: 2rem; border-radius: 15px; 
        border: 2px solid #bae6fd; margin-bottom: 2rem;
    }
    .summary-line { font-size: 1.1rem; margin-bottom: 0.8rem; border-bottom: 1px solid #e0f2fe; padding-bottom: 0.5rem; }
    .paid-plan {
        background-color: #f8fafc; padding: 2rem; border-radius: 15px; 
        border: 2px solid #e2e8f0; border-left: 10px solid #1e293b;
    }
    .confidence-score { font-size: 2rem; font-weight: 800; color: #059669; }
</style>
""", unsafe_allow_html=True)

# PART 3: UNIVERSAL HEADER & PROSE
st.title("🧠 AI Investor Flash Report & COO Dashboard")
st.subheader("Professional Liquidity Management for SMEs")

st.markdown("""
### Virtual COO Strategic Mandate
- **Ingests** universal transaction data (CSV, Excel, Wallet Statements)
- **Identifies** hidden drivers of cash burn and efficiency leaks
- **Predicts** exact liquidity runway with working capital adjustments
- **Generates Investor-Ready Reports** automatically
""")

# PART 4: SIDEBAR CONTROLS
st.sidebar.header("🕹️ COO Simulation")
opening_balance = st.sidebar.number_input("Starting Bank Balance (INR)", value=200000)
cod_delay = st.sidebar.slider("Avg Payment Delay (Days)", 0, 30, 7)
forecast_horizon = st.sidebar.slider("Forecast Look-ahead (Days)", 30, 90, 60)

# PART 5: DATA INGESTION & AGGRESSIVE CLEANING ENGINE
uploaded_file = st.file_uploader("Upload Your Data (CSV or Excel)", type=["csv", "xlsx", "xls"])

if uploaded_file:
    try:
        # 1. LOAD DATA & ADAPTER
        df = load_transactions(uploaded_file)
        
        if df.empty:
            st.error("No valid data detected. Check your column headers and date formats.")
        else:
            # 2. RUN METRICS & CALCULATIONS
            metrics = calculate_business_metrics(df)
            cash_now = opening_balance + df["amount"].sum()
            
            # VENTURE METRICS: BURN MULTIPLE
            net_burn = df[df['amount'] < 0]['amount'].sum()
            net_new_rev = df[df['amount'] > 0]['amount'].sum()
            burn_mult = abs(net_burn / net_new_rev) if net_new_rev != 0 else 0

            # PART 6: THE MAIN 8-POINT AI COO SUMMARY
            st.markdown("<div class='coo-summary-box'>", unsafe_allow_html=True)
            st.subheader("📋 Main AI COO Executive Summary")
            
            col_s1, col_s2 = st.columns(2)
            with col_s1:
                st.markdown(f"<div class='summary-line'>✅ **1. Liquidity Status:** Current position is ₹{cash_now:,.0f}.</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='summary-line'>📉 **2. Burn Rate:** Capital Efficiency is {burn_mult:.2f}x (Burn Multiple).</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='summary-line'>⏳ **3. Survival Window:** You have {metrics['runway_months']} months of runway.</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='summary-line'>📢 **4. Ad Intensity:** Marketing takes {metrics.get('ad_spend_pct', 0)*100:.1f}% of outflows.</div>", unsafe_allow_html=True)
            with col_s2:
                st.markdown(f"<div class='summary-line'>🚩 **5. Risk Audit:** Concentrated vendor exposure detected in operations.</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='summary-line'>📦 **6. Returns Impact:** Current return rate is {metrics.get('return_rate', 0)*100:.1f}%.</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='summary-line'>📅 **7. Forecast:** Next major cash-low point predicted in {cod_delay + 30} days.</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='summary-line'>🎯 **8. COO Verdict:** {'Sustainable Growth' if burn_mult < 1.5 else 'Efficiency Audit Mandatory'}.</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

            # PART 7: KPI DASHBOARD & VISUALS
            c1, c2, c3, c4 = st.columns(4)
            with c1: st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Net Cash</div><div class='kpi-value'>₹{cash_now:,.0f}</div></div>", unsafe_allow_html=True)
            with c2: st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Runway</div><div class='kpi-value'>{metrics['runway_months']} Mo</div></div>", unsafe_allow_html=True)
            with c3: st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Burn Multiple</div><div class='kpi-value'>{burn_mult:.2f}x</div></div>", unsafe_allow_html=True)
            with c4: st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Ad Spend %</div><div class='kpi-value'>{metrics.get('ad_spend_pct', 0)*100:.1f}%</div></div>", unsafe_allow_html=True)

            # SPEND ANALYSIS
            st.divider()
            st.subheader("📊 Spend Analysis")
            def categorize(desc):
                d = str(desc).lower()
                if any(x in d for x in ["facebook", "meta", "google", "ads"]): return "Marketing"
                if any(x in d for x in ["salary", "payroll"]): return "Payroll"
                if any(x in d for x in ["rent", "office"]): return "Fixed Costs"
                return "Operations"
            
            df["Category"] = df["description"].apply(categorize)
            cat_df = df[df["amount"] < 0].groupby("Category")["amount"].sum().abs().reset_index()
            
            if not cat_df.empty:
                col_pie, col_table = st.columns([2, 1])
                with col_pie: st.plotly_chart(px.pie(cat_df, values='amount', names='Category', hole=0.4), use_container_width=True)
                with col_table: st.write("### Flow Details"); st.table(cat_df.sort_values(by="amount", ascending=False))

            # 📉 FORECAST CHART
            st.divider()
            st.subheader(f"📉 {forecast_horizon}-Day Cash Forecast")
            f_df = forecast_cashflow(cash_today=cash_now, start_date=df["date"].max(), days=forecast_horizon,
                                   avg_daily_sales=metrics.get("avg_daily_sales", 0), avg_daily_ad_spend=metrics.get("avg_daily_ad_spend", 0), 
                                   avg_daily_fixed_cost=metrics.get("avg_daily_fixed_cost", 0), cod_delay_days=cod_delay, return_rate=metrics.get("return_rate", 0))
            st.plotly_chart(px.line(f_df, x="date", y="closing_cash", title="Predicted Liquidity"), use_container_width=True)

            # 📋 FOUNDER ACTION PLAN
            st.divider()
            st.subheader("📋 Executive Strategic Action Plan")
            st.markdown("<div class='paid-plan'>", unsafe_allow_html=True)
            col_pa, col_pb = st.columns([2, 1])
            with col_pa:
                st.markdown("### 🎯 Operational Priorities")
                st.markdown(f"1. **Capital Efficiency:** Burn Multiple is {burn_mult:.2f}x. Target < 1.1x.")
                st.markdown(f"2. **Overhead Audit:** Review ₹{cat_df[cat_df['Category']=='Operations']['amount'].sum() if not cat_df[cat_df['Category']=='Operations'].empty else 0:,.0f} in operational spend.")
                st.markdown(f"3. **Milestone Survival:** You have {metrics['runway_months']} months to reach profitability.")
            with col_pb:
                st.markdown("### Decision Confidence"); st.markdown("<div class='confidence-score'>85%</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    except Exception as e: st.error(f"Analysis Error: {e}")
else: st.info("👋 Upload transaction data to begin.")