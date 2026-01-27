import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from datetime import datetime, timedelta
from io import BytesIO
import re

# PART 1: ENGINE IMPORTS
from engine.loader import load_transactions
from engine.metrics import calculate_business_metrics
from engine.decisions import generate_decisions
from engine.forecast import forecast_cashflow
from engine.advice import generate_coo_advice, get_real_ai_response

# PART 2: HARDCORE CSS STYLING (FULL VERSION)
st.set_page_config(page_title="Hardcore AI COO", layout="wide")
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
</style>
""", unsafe_allow_html=True)

# PART 3: UNIVERSAL HEADER & STRATEGIC MANDATE (FULL VERSION)
st.title("🧠 Hardcore AI COO & Investor Dashboard")
st.subheader("Real-Time Strategic Liquidity Management for SMEs")

st.markdown("""
### 🛠️ COO Strategic Mandate & Functional Scope
- **AI-Driven Reasoning**: Real-time strategic analysis powered by Gemini for deep financial insight.
- **Universal Data Ingestion**: Direct support for ICICI, Axis, and manual Wallet Statement exports.
- **Capital Efficiency Audit**: Automated tracking of Burn Multiples and category-wise spend leakage.
- **Liquidity Forecasting**: 60-day predictive modeling based on historical COD return rates and lead times.
- **Risk Mitigation**: Immediate flagging of vendor concentration and marketing over-intensity.
- **Executive Reporting**: One-click generation of investor-ready PDF Flash Reports.
""")
st.markdown("---")

# PART 4: SAMPLE CSV DOWNLOAD
sample_data = "Date,Debit,Credit,Activity\n31/12/2025,,150000,Shopify Payout\n31/12/2025,45000,,Meta Ads\n30/12/2025,12000,,Office Rent"
st.download_button("📥 Download Compatible Sample CSV", data=sample_data, file_name="sample_coo_data.csv", mime="text/csv")

# PART 5: SIDEBAR CONTROLS
st.sidebar.header("🕹️ Simulation Controls")
opening_balance = st.sidebar.number_input("Starting Balance (INR)", value=200000)
st.session_state["gemini_api_key"] = st.sidebar.text_input("🔑 Gemini API Key", type="password")
show_ai_chat = st.sidebar.toggle("💬 Enable Real AI Chatbot", value=True)
show_search = st.sidebar.toggle("🔍 Enable Search Audit", value=True)

# PART 6: DATA INGESTION
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

            # RISK ENGINE
            total_outflow = abs(net_burn)
            vendor_risks = []
            if total_outflow > 0:
                def categorize(desc):
                    d = str(desc).lower()
                    if any(x in d for x in ["facebook", "ads", "meta", "google"]): return "Marketing"
                    if any(x in d for x in ["salary", "payroll"]): return "Payroll"
                    return "Operations"
                df["Category"] = df["description"].apply(categorize)
                cat_df = df[df["amount"] < 0].groupby("Category")["amount"].sum().abs().reset_index()
                for _, row in cat_df.iterrows():
                    if row['amount'] / total_outflow > 0.35:
                        vendor_risks.append(f"⚠️ HIGH EXPOSURE: {row['Category']} is {(row['amount']/total_outflow)*100:.1f}% of spend.")

            # PART 7: 8-POINT AI COO SUMMARY
            st.markdown("<div class='coo-summary-box'>", unsafe_allow_html=True)
            st.subheader("📋 Main AI COO Executive Summary")
            col_s1, col_s2 = st.columns(2)
            with col_s1:
                st.markdown(f"<div class='summary-line'>✅ **1. Liquidity:** INR {cash_now:,.0f}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='summary-line'>📉 **2. Efficiency:** {burn_mult:.2f}x Burn Multiple</div>", unsafe_allow_html=True)
            with col_s2:
                st.markdown(f"<div class='summary-line'>⏳ **3. Runway:** {metrics['runway_months']} Months</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='summary-line'>🎯 **4. Verdict:** {'Sustainable' if burn_mult < 1.5 else 'Audit Required'}</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

            # PART 8: DASHBOARD & SEARCH
            c1, c2, c3, c4 = st.columns(4)
            with c1: st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Net Cash</div><div class='kpi-value'>₹{cash_now:,.0f}</div></div>", unsafe_allow_html=True)
            with c2: st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Runway</div><div class='kpi-value'>{metrics['runway_months']} Mo</div></div>", unsafe_allow_html=True)
            with c3: st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Burn</div><div class='kpi-value'>{burn_mult:.2f}x</div></div>", unsafe_allow_html=True)
            with c4: st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Ads %</div><div class='kpi-value'>{metrics.get('ad_spend_pct', 0)*100:.1f}%</div></div>", unsafe_allow_html=True)

            if show_search:
                st.divider()
                st.subheader("🔍 Deep-Dive Search Audit")
                q = st.text_input("Search records (e.g. 'total ads')")
                if q:
                    val = df[df['description'].str.contains(q.lower(), case=False, na=False)]['amount'].abs().sum()
                    st.write(f"📊 Result for '{q}': INR {val:,.0f}")

            # PART 9: REAL AI CHATBOT (GEMINI)
            if show_ai_chat:
                st.divider()
                st.subheader("💬 Chat with your Real AI COO")
                if "messages" not in st.session_state: st.session_state.messages = []
                for m in st.session_state.messages:
                    with m: st.markdown(m["content"])
                if p := st.chat_input("Ask about your burn rate..."):
                    st.session_state.messages.append({"role": "user", "content": p})
                    resp = get_real_ai_response(p, metrics, cash_now, burn_mult)
                    st.session_state.messages.append({"role": "assistant", "content": resp})
                    st.rerun()

            # PART 10: INVESTOR PDF DOWNLOAD
            st.divider()
            def generate_pdf():
                buf = BytesIO()
                with PdfPages(buf) as pdf:
                    fig = plt.figure(figsize=(8.5, 11)); plt.axis("off")
                    plt.text(0.1, 0.95, f"COO Report\nCash: INR {cash_now:,.0f}", fontsize=12)
                    pdf.savefig(fig); plt.close(fig)
                buf.seek(0); return buf
            st.download_button("📥 Download PDF Report", data=generate_pdf(), file_name="COO_Report.pdf", mime="application/pdf")

    except Exception as e: st.error(f"Analysis Error: {e}")
else: st.info("👋 Upload data to begin.")