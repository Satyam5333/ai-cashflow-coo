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
# PAGE CONFIG & STYLING (PRESERVED)
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
- **Reads** universal transaction data (CSV, Excel, or structured exports)
- **Identifies** what is actually driving cash burn
- **Predicts** how long your money will last
- **Generates Investor-Ready "Flash" Reports** automatically
""")

# 📥 SAMPLE CSV DOWNLOAD
sample_data = """Date,Debit,Credit,Activity
31/12/2025,,150000,Sales Payout
31/12/2025,45000,,Marketing Ads
30/12/2025,12000,,Office Rent
28/12/2025,25000,,Staff Salary
"""
st.download_button("📥 Download Universal Sample CSV", data=sample_data, file_name="sample_cashflow_data.csv", mime="text/csv")
st.markdown("---")

# 🕹️ SIDEBAR CONTROLS
st.sidebar.header("🕹️ COO Simulation")
opening_balance = st.sidebar.number_input("Starting Bank Balance", value=200000)
cod_delay = st.sidebar.slider("Avg Payment Delay (Days)", 0, 30, 7)
forecast_horizon = st.sidebar.slider("Forecast Look-ahead (Days)", 30, 90, 60)

# 📥 MAIN LOGIC
uploaded_file = st.file_uploader("Upload Data (CSV or Excel preferred)", type=["csv", "xlsx", "xls", "pdf"])

if uploaded_file:
    try:
        # 1. LOAD DATA & ADAPTER
        df = load_transactions(uploaded_file)
        df.columns = [str(c).lower().strip() for c in df.columns]

        # AGGRESSIVE CLEANING logic restored to prevent 'str' absolute error
        def clean_val(val):
            if pd.isna(val) or val == "": return 0.0
            cleaned = re.sub(r'[^\d.-]', '', str(val))
            try: return float(cleaned)
            except: return 0.0

        if 'txn date' in df.columns: df = df.rename(columns={'txn date': 'date'})
        if 'activity' in df.columns: df = df.rename(columns={'activity': 'description'})

        if 'withdrawals' in df.columns and 'deposits' in df.columns:
            df['amount'] = df['deposits'].apply(clean_val) - df['withdrawals'].apply(clean_val)
        elif 'amount' in df.columns and 'type' in df.columns:
            df['temp_amt'] = df['amount'].apply(clean_val)
            df['amount'] = df.apply(lambda x: -abs(x['temp_amt']) if 'DR' in str(x['type']).upper() else abs(x['temp_amt']), axis=1)

        # 2. RUN METRICS
        metrics = calculate_business_metrics(df)
        cash_now = opening_balance + df["amount"].sum()
        
        # INVESTOR METRICS: BURN MULTIPLE
        net_burn = df[df['amount'] < 0]['amount'].sum()
        net_new_rev = df[df['amount'] > 0]['amount'].sum()
        burn_multiple = abs(net_burn / net_new_rev) if net_new_rev != 0 else 0

        # 3. KPI CARDS
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Cash Today</div><div class='kpi-value'>₹{cash_now:,.0f}</div></div>", unsafe_allow_html=True)
        with c2: st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Runway</div><div class='kpi-value'>{metrics['runway_months']} Mo</div></div>", unsafe_allow_html=True)
        with c3: st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Burn Multiple</div><div class='kpi-value'>{burn_multiple:.2f}x</div></div>", unsafe_allow_html=True)
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
        
        col_pie, col_table = st.columns([2, 1])
        with col_pie: st.plotly_chart(px.pie(cat_df, values='amount', names='Category', hole=0.4), use_container_width=True)
        with col_table: st.write("### Flow Details"); st.table(cat_df.sort_values(by="amount", ascending=False))

        # 5. FORECAST
        st.divider()
        st.subheader(f"📉 {forecast_horizon}-Day Forecast")
        f_df = forecast_cashflow(cash_today=cash_now, start_date=df["date"].max(), days=forecast_horizon,
                               avg_daily_sales=metrics.get("avg_daily_sales", 0), avg_daily_ad_spend=metrics.get("avg_daily_ad_spend", 0), 
                               avg_daily_fixed_cost=metrics.get("avg_daily_fixed_cost", 0), cod_delay_days=cod_delay, return_rate=metrics.get("return_rate", 0))
        st.plotly_chart(px.line(f_df, x="date", y="closing_cash", title="Predicted Liquidity"), use_container_width=True)

        # 6. ACTION PLAN
        st.divider()
        st.subheader("📋 Executive Strategic Action Plan")
        st.markdown("<div class='paid-plan'>", unsafe_allow_html=True)
        col_pa, col_pb = st.columns([2, 1])
        with col_pa:
            st.markdown("### 🎯 Efficiency Priorities")
            st.markdown(f"1. **Capital Efficiency:** Burn Multiple is {burn_multiple:.2f}x (VC Standard < 1.5x).")
            st.markdown(f"2. **Overhead Audit:** Review outflows in operational categories.")
            st.markdown(f"3. **Survival Horizon:** Estimated cash-out in {metrics['runway_months']} months.")
        with col_pb:
            st.markdown("### Strategic Confidence"); st.markdown("<div class='confidence-score'>85%</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # 7. INVESTOR PDF
        st.divider()
        def generate_universal_report():
            buf = BytesIO()
            with PdfPages(buf) as pdf:
                fig = plt.figure(figsize=(8.5, 11)); plt.axis("off")
                txt = (f"EXECUTIVE FINANCIAL FLASH REPORT\n"
                       f"Date: {datetime.now().strftime('%d %b %Y')}\n"
                       f"-----------------------------------\n"
                       f"Liquidity: ₹{cash_now:,.0f}\n"
                       f"Survival Months: {metrics['runway_months']}\n"
                       f"Burn Multiple: {burn_multiple:.2f}x\n"
                       f"Ad Intensity: {metrics.get('ad_spend_pct', 0)*100:.1f}%")
                plt.text(0.1, 0.95, txt, fontsize=10, family='monospace', va='top')
                pdf.savefig(fig); plt.close(fig)
            buf.seek(0); return buf
        
        st.download_button("📥 Download Universal Flash PDF", data=generate_universal_report(), file_name="Financial_Flash_Report.pdf", mime="application/pdf")

    except Exception as e: st.error(f"Analysis Error: {e}")
else: st.info("👋 Upload transaction data to begin.")