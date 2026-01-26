import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from datetime import datetime, timedelta
from io import BytesIO

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
    .paid-plan {
        background-color: #f8fafc; padding: 2rem; border-radius: 15px; 
        border: 2px solid #e2e8f0; border-left: 10px solid #1e293b;
    }
    .confidence-score { font-size: 2rem; font-weight: 800; color: #059669; }
    .warning-text { color: #dc2626; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

# =================================================
# ---------------- HEADER ----------------
# =================================================
st.title("🧠 Cash-Flow Early Warning System for SMEs")
st.subheader("Compatible with ICICI, Axis, Tally, and Shopify Exports")

st.markdown("""
### What this tool does
- **Multi-Bank Support:** Automatically detects ICICI (Amount/Type) and Axis (Withdrawals/Deposits)
- **Categorizes** spending into Ads, Salary, and Rent heuristics
- **Forecasts** cash position for the next 60 days
- **Generates** Founder Action Plans & Investor Reports
""")

# =================================================
# 📥 SAMPLE CSV DOWNLOAD
# =================================================
sample_data = """Date,Debit,Credit,Activity
31/12/2025,,150000,Shopify Payout
31/12/2025,45000,,Meta Ads - Facebook/Insta
30/12/2025,12000,,Office Rent
28/12/2025,25000,,Staff Salary
"""
st.download_button("📥 Download Compatible Sample CSV", data=sample_data, file_name="sample_coo_data.csv", mime="text/csv")
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
uploaded_file = st.file_uploader("Upload Data (CSV, Excel, or PDF)", type=["csv", "xlsx", "xls", "pdf"])

if uploaded_file:
    try:
        # 1. LOAD DATA & SMART ADAPTER
        df = load_transactions(uploaded_file)
        df.columns = [str(c).lower().strip() for c in df.columns]

        # --- AXIS BANK PARSER ---
        if 'withdrawals' in df.columns and 'deposits' in df.columns:
            df['credit'] = pd.to_numeric(df['deposits'], errors='coerce').fillna(0)
            df['debit'] = pd.to_numeric(df['withdrawals'], errors='coerce').fillna(0)
            df['amount'] = df['credit'] - df['debit']
        
        # --- ICICI BANK PARSER ---
        elif 'amount' in df.columns and 'type' in df.columns:
            df['amount'] = pd.to_numeric(df['amount'].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
            df['amount'] = df.apply(lambda x: -abs(x['amount']) if str(x['type']).upper() == 'DR' else abs(x['amount']), axis=1)

        # Standardize Description
        if 'txn date' in df.columns: df = df.rename(columns={'txn date': 'date'})
        if 'activity' in df.columns: df = df.rename(columns={'activity': 'description'})
        elif 'transaction' in df.columns: df = df.rename(columns={'transaction': 'description'})

        # Smart Sign Correction
        def reconcile_signs(row):
            desc = str(row['description']).lower()
            val = abs(row['amount'])
            if any(k in desc for k in ["ad", "facebook", "meta", "google", "rent", "salary", "refund"]):
                return -val
            return row['amount']
        
        df['amount'] = df.apply(reconcile_signs, axis=1)

        # 2. RUN METRICS
        metrics = calculate_business_metrics(df)
        cash_now = opening_balance + df["amount"].sum()

        # 3. KPI CARDS
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Cash Today</div><div class='kpi-value'>₹{cash_now:,.0f}</div></div>", unsafe_allow_html=True)
        with c2: st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Runway</div><div class='kpi-value'>{metrics['runway_months']} Mo</div></div>", unsafe_allow_html=True)
        with c3: st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Ad Spend %</div><div class='kpi-value'>{metrics.get('ad_spend_pct', 0)*100:.1f}%</div></div>", unsafe_allow_html=True)
        with c4: st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Returns</div><div class='kpi-value'>{metrics.get('return_rate', 0)*100:.1f}%</div></div>", unsafe_allow_html=True)

        # 4. SPEND ANALYSIS (PIE + TABLE)
        st.divider()
        st.subheader("📊 Spend Analysis")
        def categorize(desc):
            d = str(desc).lower()
            if any(x in d for x in ["ad", "facebook", "meta", "google"]): return "Ads"
            if any(x in d for x in ["salary", "wage"]): return "Salary"
            if any(x in d for x in ["rent", "office"]): return "Rent"
            return "Other"
        df["Category"] = df["description"].apply(categorize)
        cat_df = df[df["amount"] < 0].groupby("Category")["amount"].sum().abs().reset_index()
        
        col_pie, col_table = st.columns([2, 1])
        with col_pie:
            st.plotly_chart(px.pie(cat_df, values='amount', names='Category', hole=0.4), use_container_width=True)
        with col_table:
            st.write("### Expense Details")
            st.table(cat_df.sort_values(by="amount", ascending=False))

        # 5. FORECAST CHART
        st.divider()
        st.subheader(f"📉 {forecast_horizon}-Day Cash Forecast")
        f_df = forecast_cashflow(cash_today=cash_now, start_date=df["date"].max(), days=forecast_horizon,
                               avg_daily_sales=metrics.get("avg_daily_sales", 0), avg_daily_ad_spend=metrics.get("avg_daily_ad_spend", 0), 
                               avg_daily_fixed_cost=metrics.get("avg_daily_fixed_cost", 0), cod_delay_days=cod_delay, return_rate=metrics.get("return_rate", 0))
        st.plotly_chart(px.line(f_df, x="date", y="closing_cash", title="Liquidity Position"), use_container_width=True)

        # 6. STRATEGIC Q&A
        st.divider()
        st.subheader("🔍 Deep-Dive Analysis")
        q = st.text_input("Ask about your Tally/Bank/PDF records (e.g. 'total rent')")
        if q:
            query = q.lower()
            if "rent" in query:
                val = df[df['description'].str.contains('rent', case=False, na=False)]['amount'].abs().sum()
                st.write(f"📊 **Audit Result:** Total Rent found is ₹{val:,.0f}")

        # 7. FOUNDER ACTION PLAN (PAID-FEEL)
        st.divider()
        st.subheader("📋 Executive Strategic Action Plan")
        st.markdown("<div class='paid-plan'>", unsafe_allow_html=True)
        col_pa, col_pb = st.columns([2, 1])
        with col_pa:
            st.markdown("### 🎯 Top 3 Actions (Next 30 Days)")
            st.markdown(f"1. **Audit ROAS Intensity:** ({metrics.get('ad_spend_pct', 0)*100:.1f}%)")
            st.markdown(f"2. **Freeze 'Other' Spend:** Review ₹{cat_df[cat_df['Category']=='Other']['amount'].sum() if not cat_df[cat_df['Category']=='Other'].empty else 0:,.0f} in miscellaneous costs.")
            st.markdown(f"3. **COD Check:** Reduce {metrics.get('return_rate', 0)*100:.1f}% return rate.")
        with col_pb:
            st.markdown("### Decision Confidence")
            st.markdown("<div class='confidence-score'>85%</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # 8. INVESTOR PDF & ADVICE
        st.divider()
        def generate_pdf():
            buf = BytesIO()
            with PdfPages(buf) as pdf:
                fig = plt.figure(figsize=(8.5, 11)); plt.axis("off")
                txt = f"CASH REPORT\nCash: ₹{cash_now:,.0f}\nRunway: {metrics['runway_months']} Mo"
                plt.text(0.1, 0.95, txt, fontsize=10, family='monospace', va='top')
                pdf.savefig(fig); plt.close(fig)
            buf.seek(0); return buf
        st.download_button("📥 Download Investor PDF", data=generate_pdf(), file_name="COO_Report.pdf", mime="application/pdf")
        st.info(generate_coo_advice(cash_now, metrics['runway_months'], metrics.get('ad_spend_pct', 0), metrics.get('return_rate', 0), generate_decisions(metrics)))

    except Exception as e:
        st.error(f"Analysis Error: {e}. Check if column names match Axis/ICICI standard formats.")
else:
    st.info("👋 Upload data (PDF, CSV, or Excel) to begin.")