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
# PAGE CONFIG & STYLING (PRESERVED)
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
    .risk-box {
        padding: 1rem; border-radius: 10px; background-color: #fff5f5; border: 1px solid #feb2b2; color: #c53030;
    }
    .decision-block {
        padding: 1.2rem; border-radius: 12px; background-color: #f0fdf4; border: 1px solid #bbf7d0; color: #166534;
    }
    .paid-plan {
        background-color: #f8fafc; padding: 2rem; border-radius: 15px; 
        border: 2px solid #e2e8f0; border-left: 10px solid #1e293b;
    }
    .confidence-score { font-size: 2rem; font-weight: 800; color: #059669; }
    .warning-text { color: #dc2626; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

# =================================================
# ---------------- HEADER (PRESERVED) ----------------
# =================================================
st.title("🧠 Cash-Flow Early Warning System for SMEs")
st.subheader("Know when your business may face cash trouble — and what to do next.")

st.markdown("""
### What this tool does
- **Analyzes** real transaction data from Bank, Tally, or Shopify
- **Categorizes** spending into Ads, Salary, and Rent heuristics
- **Forecasts** cash position for the next 60 days
- **Generates** Investor-ready reports & Strategic Action Plans
""")

# =================================================
# 📥 SAMPLE CSV DOWNLOAD (PRESERVED)
# =================================================
sample_data = """date,amount,description
2026-01-01,150000,Shopify Payout
2026-01-02,-45000,Meta Ads - Facebook/Insta
2026-01-05,-12000,Office Rent
2026-01-10,-25000,Staff Salary
2026-01-18,-8000,Customer Refund
"""
st.download_button("📥 Download Sample D2C Transactions CSV", data=sample_data, file_name="sample_d2c_transactions.csv", mime="text/csv")
st.markdown("---")

# =================================================
# SIDEBAR CONTROLS (PRESERVED)
# =================================================
st.sidebar.header("🕹️ COO Simulation")
opening_balance = st.sidebar.number_input("Starting Bank Balance (INR)", value=opening_balance if 'opening_balance' in locals() else 200000)
cod_delay = st.sidebar.slider("Avg COD Payment Delay (Days)", 0, 30, 7)
forecast_horizon = st.sidebar.slider("Forecast Look-ahead (Days)", 30, 90, 60)

# =================================================
# MAIN LOGIC (PRESERVED FLOW)
# =================================================
uploaded_file = st.file_uploader("Upload Data (CSV, Excel, or PDF)", type=["csv", "xlsx", "xls", "pdf"])

if uploaded_file:
    try:
        # 1. LOAD DATA & HANDLE COLUMN MAPPING
        df = load_transactions(uploaded_file)
        
        # Ensure column names are standardized lowercase for the engine
        df.columns = [c.lower().strip() for c in df.columns]
        
        # Smart Sign Correction Layer
        def reconcile_signs(row):
            desc = str(row['description']).lower()
            val = abs(row['amount'])
            if any(k in desc for k in ["ad", "facebook", "meta", "google", "rent", "salary", "refund"]): return -val
            if any(k in desc for k in ["payout", "sale", "deposit", "credit"]): return val
            return row['amount']
        
        df['amount'] = df.apply(reconcile_signs, axis=1)

        # 2. RUN METRICS
        metrics = calculate_business_metrics(df)
        cash_now = opening_balance + df["amount"].sum()

        # 3. KPI CARDS (PRESERVED)
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Cash Today</div><div class='kpi-value'>₹{cash_now:,.0f}</div></div>", unsafe_allow_html=True)
        with c2: st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Runway</div><div class='kpi-value'>{metrics['runway_months']} Mo</div></div>", unsafe_allow_html=True)
        with c3: st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Ad Spend %</div><div class='kpi-value'>{metrics['ad_spend_pct']*100:.1f}%</div></div>", unsafe_allow_html=True)
        with c4: st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Returns</div><div class='kpi-value'>{metrics['return_rate']*100:.1f}%</div></div>", unsafe_allow_html=True)

        # 4. CASH-OUT PREDICTION (PRESERVED)
        st.divider()
        cash_out_str = "Sustainable"
        if metrics['runway_months'] < 99:
            cash_out_date = (datetime.now() + timedelta(days=int(metrics['runway_months'] * 30)))
            cash_out_str = cash_out_date.strftime('%d %b %Y')
            st.error(f"⚠️ **Estimated Cash-out Date: {cash_out_str}**")
        else:
            st.success("✅ **Sustainable Growth Projected**")

        # 5. SPEND ANALYSIS (PRESERVED)
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
            st.table(cat_df.sort_values(by="amount", ascending=False))

        # 6. RISK INSIGHTS & COST DRIVERS (PRESERVED)
        st.divider()
        st.subheader("⚠️ COO Risk Insights")
        top_drivers = cat_df.sort_values(by="amount", ascending=False).head(2)
        c_r1, c_r2 = st.columns(2)
        with c_r1:
            st.write("**Top 2 Cost Drivers:**")
            for idx, row in top_drivers.iterrows(): st.write(f"🔹 {row['Category']}: ₹{row['amount']:,.0f}")
        with c_r2:
            total_exp = cat_df['amount'].sum()
            primary_pct = (top_drivers.iloc[0]['amount'] / total_exp) * 100 if total_exp > 0 else 0
            if primary_pct > 50:
                st.markdown(f"<div class='risk-box'><strong>Cost Concentration Risk:</strong> {top_drivers.iloc[0]['Category']} is {primary_pct:.1f}% of spend.</div>", unsafe_allow_html=True)
            else: st.write("✅ **Cost Dispersion:** Your expenses are well diversified.")

        # 7. FORECAST CHART (PRESERVED)
        st.divider()
        st.subheader(f"📉 {forecast_horizon}-Day Cash Forecast")
        f_df = forecast_cashflow(cash_today=cash_now, start_date=df["date"].max(), days=forecast_horizon,
                               avg_daily_sales=metrics["avg_daily_sales"], avg_daily_ad_spend=metrics["avg_daily_ad_spend"], 
                               avg_daily_fixed_cost=metrics["avg_daily_fixed_cost"], cod_delay_days=cod_delay, return_rate=metrics["return_rate"])
        fig = px.line(f_df, x="date", y="closing_cash", title="Liquidity Position")
        fig.add_hline(y=0, line_dash="dash", line_color="red")
        st.plotly_chart(fig, use_container_width=True)

        # 8. PAID-FEEL ACTION PLAN (PRESERVED)
        st.divider()
        st.subheader("📋 Executive Strategic Action Plan")
        st.markdown("<div class='paid-plan'>", unsafe_allow_html=True)
        col_pa, col_pb = st.columns([2, 1])
        with col_pa:
            st.markdown("### 🎯 Top 3 Actions (Next 30 Days)")
            st.markdown(f"1. **Audit ROAS:** Target > 1.8 to reduce {metrics['ad_spend_pct']*100:.1f}% intensity.")
            st.markdown(f"2. **COD Verification:** Reduce {metrics['return_rate']*100:.1f}% return rate.")
            st.markdown("3. **Freeze Non-Core Spend.**")
        with col_pb:
            st.markdown("### Decision Confidence")
            st.markdown("<div class='confidence-score'>85%</div>", unsafe_allow_html=True)
            st.markdown(f"<span class='warning-text'>Inaction leads to cash exhaustion by {cash_out_str}.</span>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # 9. INVESTOR PDF GENERATOR (PRESERVED)
        st.divider()
        def generate_pdf():
            buf = BytesIO()
            with PdfPages(buf) as pdf:
                fig = plt.figure(figsize=(8.5, 11)); plt.axis("off")
                txt = f"CASH REPORT\nCash: ₹{cash_now:,.0f}\nRunway: {metrics['runway_months']} Mo\n\n{cat_df.to_string()}"
                plt.text(0.1, 0.95, txt, fontsize=10, family='monospace', va='top')
                pdf.savefig(fig); plt.close(fig)
            buf.seek(0); return buf
        st.download_button("📥 Download Investor PDF", data=generate_pdf(), file_name="COO_Report.pdf", mime="application/pdf")

        # 10. STRATEGIC Q&A (NEW HARDCORE ADDITION)
        st.divider()
        st.subheader("🔍 Deep-Dive Analysis")
        st.write("Analyze your Tally or Bank data by asking a question below:")
        q = st.text_input("Example: 'total rent' or 'highest expense'")
        if q:
            query = q.lower()
            if "rent" in query:
                val = df[df['description'].str.contains('rent', case=False, na=False)]['amount'].abs().sum()
                st.write(f"📊 **Audit Result:** Total Rent found is ₹{val:,.0f}")
            elif "highest" in query or "max" in query:
                top = df.sort_values(by='amount').iloc[0]
                st.write(f"🚩 **Top Expense:** {top['description']} (₹{abs(top['amount']):,.0f})")
            else:
                st.write("I am scanning for keywords like 'rent', 'salary', or 'highest'.")

        # 11. AI ADVICE (PRESERVED)
        st.divider()
        st.subheader("🤖 Strategy Report")
        st.info(generate_coo_advice(cash_now, metrics['runway_months'], metrics['ad_spend_pct'], metrics['return_rate'], generate_decisions(metrics)))

    except Exception as e:
        st.error(f"Analysis Error: {e}")
else:
    st.info("👋 Upload your Shopify/Bank CSV to begin.")