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

# PART 2: PAGE CONFIG & HARDCORE CSS
st.set_page_config(page_title="Hardcore AI COO", layout="wide")
st.markdown("""
<style>
    .kpi-card { background: #ffffff; padding: 1.2rem; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.08); border-left: 5px solid #6366f1; }
    .kpi-title { font-size: 0.85rem; color: #6b7280; font-weight: 600; text-transform: uppercase; }
    .kpi-value { font-size: 1.8rem; font-weight: 700; margin-top: 0.5rem; }
    .coo-summary-box { background-color: #f0f9ff; padding: 2rem; border-radius: 15px; border: 2px solid #bae6fd; margin-bottom: 2rem; }
    .summary-line { font-size: 1.1rem; margin-bottom: 0.8rem; border-bottom: 1px solid #e0f2fe; padding-bottom: 0.5rem; }
    .paid-plan { background-color: #f8fafc; padding: 2rem; border-radius: 15px; border: 2px solid #e2e8f0; border-left: 10px solid #1e293b; }
</style>
""", unsafe_allow_html=True)

# PART 3: UNIVERSAL HEADER & MANDATE (RESTORED)
st.title("🧠 Hardcore AI COO & Investor Dashboard")
st.subheader("Professional Liquidity Management for SMEs")

st.markdown("""
### What this tool does
- **Multi-Bank Support**: Detects ICICI (Amount/Type) and Axis (Withdrawals/Deposits)
- **Categorizes** spending into Ads, Salary, and Rent heuristics
- **Forecasts** cash position for the next 60 days
- **Generates** Founder Action Plans & Investor Reports
""")

# PART 4: SAMPLE CSV DOWNLOAD (RESTORED)
sample_data = """Date,Debit,Credit,Activity
31/12/2025,,150000,Shopify Payout
31/12/2025,45000,,Meta Ads - Facebook/Insta
30/12/2025,12000,,Office Rent
28/12/2025,25000,,Staff Salary
"""
st.download_button("📥 Download Compatible Sample CSV", data=sample_data, file_name="sample_coo_data.csv", mime="text/csv")
st.markdown("---")

# PART 5: SIDEBAR CONTROLS
st.sidebar.header("🕹️ Simulation Controls")
opening_balance = st.sidebar.number_input("Starting Balance (INR)", value=200000)
cod_delay = st.sidebar.slider("Payment Delay (Days)", 0, 30, 7)
show_search = st.sidebar.toggle("Enable Deep-Dive Search", value=True)

# PART 6: DATA INGESTION & AGGRESSIVE CLEANING
uploaded_file = st.file_uploader("Upload Transaction Data", type=["csv", "xlsx", "xls"])

if uploaded_file:
    try:
        df = load_transactions(uploaded_file)
        if not df.empty:
            metrics = calculate_business_metrics(df)
            cash_now = opening_balance + df["amount"].sum()
            net_burn = df[df['amount'] < 0]['amount'].sum()
            net_rev = df[df['amount'] > 0]['amount'].sum()
            burn_mult = abs(net_burn / net_rev) if net_rev != 0 else 0

            # --- RISK ENGINE ---
            total_outflow = abs(net_burn)
            vendor_risks = []
            if total_outflow > 0:
                def categorize(desc):
                    d = str(desc).lower()
                    if any(x in d for x in ["facebook", "ads", "meta", "google"]): return "Marketing"
                    if any(x in d for x in ["salary", "payroll"]): return "Payroll"
                    if any(x in d for x in ["rent", "office"]): return "Fixed Costs"
                    return "Operations"
                df["Category"] = df["description"].apply(categorize)
                cat_df = df[df["amount"] < 0].groupby("Category")["amount"].sum().abs().reset_index()
                
                for _, row in cat_df.iterrows():
                    if row['amount'] / total_outflow > 0.35:
                        vendor_risks.append(f"⚠️ HIGH EXPOSURE: {row['Category']} is {(row['amount']/total_outflow)*100:.1f}% of spend.")
                
                vendor_df = df[df['amount'] < 0].groupby('description')['amount'].sum().abs().reset_index()
                if not vendor_df.empty:
                    top_v = vendor_df.sort_values(by='amount', ascending=False).iloc[0]
                    if top_v['amount'] / total_outflow > 0.30:
                        vendor_risks.append(f"🚩 VENDOR RISK: '{top_v['description']}' is {(top_v['amount']/total_outflow)*100:.1f}% of outflows.")

            # PART 7: 8-POINT AI COO SUMMARY (MAIN BRAIN)
            st.markdown("<div class='coo-summary-box'>", unsafe_allow_html=True)
            st.subheader("📋 Main AI COO Executive Summary")
            col_s1, col_s2 = st.columns(2)
            with col_s1:
                st.markdown(f"<div class='summary-line'>✅ **1. Liquidity:** ₹{cash_now:,.0f}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='summary-line'>📉 **2. Efficiency:** {burn_mult:.2f}x Burn Multiple</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='summary-line'>⏳ **3. Runway:** {metrics['runway_months']} Months</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='summary-line'>📢 **4. Ad Intensity:** {metrics.get('ad_spend_pct', 0)*100:.1f}% spend</div>", unsafe_allow_html=True)
            with col_s2:
                st.markdown(f"<div class='summary-line'>🚩 **5. Risks:** {len(vendor_risks)} Operational Flags</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='summary-line'>📦 **6. Returns:** {metrics.get('return_rate', 0)*100:.1f}% Rate</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='summary-line'>📅 **7. Low-Point:** Predicted in {cod_delay + 30} Days</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='summary-line'>🎯 **8. Verdict:** {'Sustainable' if burn_mult < 1.5 else 'Audit Required'}</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

            # PART 8: KPI DASHBOARD & VISUALS
            c1, c2, c3, c4 = st.columns(4)
            with c1: st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Net Cash</div><div class='kpi-value'>₹{cash_now:,.0f}</div></div>", unsafe_allow_html=True)
            with c2: st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Runway</div><div class='kpi-value'>{metrics['runway_months']} Mo</div></div>", unsafe_allow_html=True)
            with c3: st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Burn Multiple</div><div class='kpi-value'>{burn_mult:.2f}x</div></div>", unsafe_allow_html=True)
            with c4: st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Ad Spend %</div><div class='kpi-value'>{metrics.get('ad_spend_pct', 0)*100:.1f}%</div></div>", unsafe_allow_html=True)

            # SPEND ANALYSIS & SEARCH
            st.divider()
            col_pie, col_table = st.columns([2, 1])
            with col_pie: st.plotly_chart(px.pie(cat_df, values='amount', names='Category', hole=0.4), use_container_width=True)
            with col_table: st.write("### Flow Details"); st.table(cat_df.sort_values(by="amount", ascending=False))

            if show_search:
                st.divider()
                st.subheader("🔍 Deep-Dive Strategic Search")
                q = st.text_input("Audit records (e.g. 'total rent')")
                if q:
                    val = df[df['description'].str.contains(q.lower(), case=False, na=False)]['amount'].abs().sum()
                    st.write(f"📊 **Audit Result:** Total found for '{q}' is ₹{val:,.0f}")

            # FINAL ACTION PLAN
            st.divider()
            st.subheader("📋 Executive Strategic Action Plan")
            st.markdown("<div class='paid-plan'>", unsafe_allow_html=True)
            if vendor_risks:
                for risk in vendor_risks: st.error(risk)
            st.markdown(f"**Priority 1:** Address the {burn_mult:.2f}x Burn Multiple.")
            st.markdown(f"**Priority 2:** Audit top categories consuming >35% of liquidity.")
            st.markdown("</div>", unsafe_allow_html=True)

    except Exception as e: st.error(f"Analysis Error: {e}")
else: st.info("👋 Upload data to begin.")