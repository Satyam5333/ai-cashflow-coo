import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from datetime import datetime, timedelta
from io import BytesIO
import re

# PART 1: EXTERNAL ENGINE IMPORTS
from engine.loader import load_transactions
from engine.metrics import calculate_business_metrics
from engine.decisions import generate_decisions
from engine.forecast import forecast_cashflow
from engine.advice import generate_coo_advice

# PART 2: PAGE CONFIG & CSS STYLING
st.set_page_config(page_title="AI Cash-Flow COO", layout="wide")
st.markdown("""
<style>
    .kpi-card { background: #ffffff; padding: 1.2rem; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.08); border-left: 5px solid #6366f1; }
    .kpi-title { font-size: 0.85rem; color: #6b7280; font-weight: 600; text-transform: uppercase; }
    .kpi-value { font-size: 1.8rem; font-weight: 700; margin-top: 0.5rem; }
    .paid-plan { background-color: #f8fafc; padding: 2rem; border-radius: 15px; border: 2px solid #e2e8f0; border-left: 10px solid #1e293b; }
    .confidence-score { font-size: 2rem; font-weight: 800; color: #059669; }
</style>
""", unsafe_allow_html=True)

# PART 3: UNIVERSAL HEADER
st.title("🧠 AI Investor Flash Report & COO Dashboard")
st.subheader("Know when your business may face cash trouble — and exactly what to do next")

# PART 4: SIDEBAR CONTROLS
st.sidebar.header("🕹️ COO Simulation")
opening_balance = st.sidebar.number_input("Starting Bank Balance (INR)", value=200000)
cod_delay = st.sidebar.slider("Avg Payment Delay (Days)", 0, 30, 7)
forecast_horizon = st.sidebar.slider("Forecast Look-ahead (Days)", 30, 90, 60)

# PART 5: DATA INGESTION & AGGRESSIVE CLEANING
uploaded_file = st.file_uploader("Upload Transaction Data", type=["csv", "xlsx", "xls"])

if uploaded_file:
    try:
        # 1. LOAD DATA
        df = load_transactions(uploaded_file)
        
        if df.empty:
            st.error("No valid data detected. Ensure your file has 'Date' and 'Amount' columns.")
        else:
            # PART 6: METRICS & RISK ENGINE
            metrics = calculate_business_metrics(df)
            cash_now = opening_balance + df["amount"].sum()
            
            # VENTURE METRICS
            net_burn = df[df['amount'] < 0]['amount'].sum()
            net_rev = df[df['amount'] > 0]['amount'].sum()
            burn_mult = abs(net_burn / net_rev) if net_rev != 0 else 0

            # --- RISK ENGINE: CONCENTRATION & VENDOR AUDIT ---
            total_outflow = abs(net_burn)
            vendor_risks = []
            if total_outflow > 0:
                # Category Check (35% Threshold)
                def categorize(desc):
                    d = str(desc).lower()
                    if any(x in d for x in ["facebook", "google", "meta", "ads", "marketing"]): return "Marketing"
                    if any(x in d for x in ["salary", "wage", "payroll"]): return "Payroll"
                    if any(x in d for x in ["rent", "office"]): return "Fixed Costs"
                    return "Operations"
                
                df["Category"] = df["description"].apply(categorize)
                cat_df = df[df["amount"] < 0].groupby("Category")["amount"].sum().abs().reset_index()
                
                for _, row in cat_df.iterrows():
                    if row['amount'] / total_outflow > 0.35:
                        vendor_risks.append(f"⚠️ HIGH EXPOSURE: {row['Category']} is { (row['amount']/total_outflow)*100:.1f}% of spend.")

                # Vendor Check (30% Threshold)
                vendor_df = df[df['amount'] < 0].groupby('description')['amount'].sum().abs().reset_index()
                if not vendor_df.empty:
                    top_v = vendor_df.sort_values(by='amount', ascending=False).iloc[0]
                    if top_v['amount'] / total_outflow > 0.30:
                        vendor_risks.append(f"🚩 VENDOR RISK: '{top_v['description']}' is { (top_v['amount']/total_outflow)*100:.1f}% of outflows.")

            # DASHBOARD KPI CARDS
            c1, c2, c3, c4 = st.columns(4)
            with c1: st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Cash Today</div><div class='kpi-value'>₹{cash_now:,.0f}</div></div>", unsafe_allow_html=True)
            with c2: st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Runway</div><div class='kpi-value'>{metrics['runway_months']} Mo</div></div>", unsafe_allow_html=True)
            with c3: st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Burn Multiple</div><div class='kpi-value'>{burn_mult:.2f}x</div></div>", unsafe_allow_html=True)
            with c4: st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Ad Spend %</div><div class='kpi-value'>{metrics.get('ad_spend_pct', 0)*100:.1f}%</div></div>", unsafe_allow_html=True)

            # PART 7: VISUAL ANALYSIS & FOUNDER ACTION PLAN
            st.divider()
            st.subheader("📊 Spend Analysis")
            if not cat_df.empty:
                col_pie, col_table = st.columns([2, 1])
                with col_pie: st.plotly_chart(px.pie(cat_df, values='amount', names='Category', hole=0.4), use_container_width=True)
                with col_table: st.write("### Flow Details"); st.table(cat_df.sort_values(by="amount", ascending=False))

            # 📋 EXECUTIVE FOUNDER ACTION PLAN
            st.divider()
            st.subheader("📋 Executive Strategic Action Plan")
            st.markdown("<div class='paid-plan'>", unsafe_allow_html=True)
            col_pa, col_pb = st.columns([2, 1])
            with col_pa:
                st.markdown("### 🎯 Immediate Operational Priorities")
                if vendor_risks:
                    for risk in vendor_risks: st.error(risk)
                if burn_mult > 1.5:
                    st.markdown(f"1. **Capital Efficiency:** Burn Multiple is {burn_mult:.2f}x. Audit fixed overheads immediately.")
                else:
                    st.markdown(f"1. **Stable Efficiency:** Burn Multiple is {burn_mult:.2f}x. Focus on scaling unit economics.")
                st.markdown(f"2. **Survival Horizon:** Estimated runway is {metrics['runway_months']} months.")
            with col_pb:
                st.markdown("### Strategic Confidence"); st.markdown("<div class='confidence-score'>85%</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

            # 🔍 SEARCH AUDIT
            st.divider()
            st.subheader("🔍 Deep-Dive Analysis")
            q = st.text_input("Search records (e.g. 'total rent')")
            if q:
                query = q.lower()
                val = df[df['description'].str.contains(query, case=False, na=False)]['amount'].abs().sum()
                st.write(f"📊 **Search Result:** Total found for '{q}' is ₹{val:,.0f}")

    except Exception as e: st.error(f"Analysis Error: {e}")
else: st.info("👋 Upload transaction data to begin.")