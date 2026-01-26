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
    .risk-box {
        padding: 1rem; border-radius: 10px; background-color: #fff5f5; border: 1px solid #feb2b2; color: #c53030;
    }
    .decision-block {
        padding: 1.2rem; border-radius: 12px; background-color: #f0fdf4; border: 1px solid #bbf7d0; color: #166534;
    }
</style>
""", unsafe_allow_html=True)

# =================================================
# ---------------- HEADER ----------------
# =================================================
st.title("🧠 Cash-Flow Early Warning System for SMEs")
st.subheader("Know when your business may face cash trouble — and what to do next.")

st.markdown("""
### What this tool does
- **Analyzes** real transaction data to find your "True Burn"
- **Categorizes** spending into Ads, Salary, and Rent heuristics
- **Forecasts** cash position for the next 60 days
""")

st.markdown("---")

# =================================================
# 📥 SAMPLE CSV DOWNLOAD
# =================================================
sample_data = """date,amount,description
2026-01-01,150000,Shopify Payout
2026-01-02,-45000,Meta Ads - Facebook/Insta
2026-01-05,-12000,Office Rent
2026-01-10,-25000,Staff Salary
2026-01-12,-5000,Shopify Subscription
2026-01-15,120000,Shopify Payout
2026-01-18,-8000,Customer Refund
2026-01-20,-35000,Meta Ads - Retargeting
2026-01-25,-4000,Google Workspace Tool
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
        # 1. LOAD DATA
        df = load_transactions(uploaded_file)
        
        # Smart Sign Correction
        def reconcile_signs(row):
            desc = str(row['description']).lower()
            val = abs(row['amount'])
            if any(k in desc for k in ["ad", "facebook", "meta", "google", "rent", "salary", "refund", "payout fee"]):
                return -val
            if any(k in desc for k in ["payout", "sale", "deposit", "credit"]):
                return val
            return row['amount']
        
        df['amount'] = df.apply(reconcile_signs, axis=1)

        # 2. RUN METRICS
        metrics = calculate_business_metrics(df)
        cash_now = opening_balance + df["amount"].sum()

        # 3. KPI CARDS
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Cash Today</div><div class='kpi-value'>₹{cash_now:,.0f}</div></div>", unsafe_allow_html=True)
        with c2: st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Runway</div><div class='kpi-value'>{metrics['runway_months']} Mo</div></div>", unsafe_allow_html=True)
        with c3: st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Ad Spend %</div><div class='kpi-value'>{metrics['ad_spend_pct']*100:.1f}%</div></div>", unsafe_allow_html=True)
        with c4: st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Returns</div><div class='kpi-value'>{metrics['return_rate']*100:.1f}%</div></div>", unsafe_allow_html=True)

        # NEW: 🚀 CASH-OUT DATE PREDICTION
        st.divider()
        if metrics['runway_months'] < 99:
            cash_out_date = (datetime.now() + timedelta(days=int(metrics['runway_months'] * 30))).strftime('%d %b %Y')
            st.error(f"⚠️ **Estimated Cash-out Date: {cash_out_date}**")
            st.write("This is the date your bank balance is projected to hit zero based on current burn.")
        else:
            st.success("✅ **Sustainable Growth:** No cash-out date projected based on current inflows.")

        # 4. EXPENSE BREAKDOWN
        st.divider()
        st.subheader("📊 Spend Analysis")
        def categorize(desc):
            d = str(desc).lower()
            if any(x in d for x in ["ad", "facebook", "meta", "google"]): return "Ads"
            if any(x in d for x in ["salary", "wage"]): return "Salary"
            if any(x in d for x in ["rent", "office"]): return "Rent"
            return "Other"

        expenses = df[df["amount"] < 0].copy()
        expenses["Category"] = expenses["description"].apply(categorize)
        cat_df = expenses.groupby("Category")["amount"].sum().abs().reset_index()
        
        col_pie, col_table = st.columns([2, 1])
        with col_pie:
            st.plotly_chart(px.pie(cat_df, values='amount', names='Category', hole=0.4), use_container_width=True)
        with col_table:
            st.table(cat_df.sort_values(by="amount", ascending=False))

        # NEW: ✅ “WHAT SHOULD I CUT FIRST?” DECISION BLOCK
        st.divider()
        st.subheader("🎯 What should I cut first?")
        st.markdown("""
        <div class='decision-block'>
            <strong>Priority 1: Underperforming Ad Sets</strong><br>
            Check Meta/Google ROAS. Any campaign with ROAS < 1.5 is burning cash without return.<br><br>
            <strong>Priority 2: Subscription Leaks</strong><br>
            Review 'Other' expenses for SaaS tools you haven't used in 30 days.<br><br>
            <strong>Priority 3: Return Management</strong><br>
            If Returns > 15%, investigate shipping or quality issues before spending more on ads.
        </div>
        """, unsafe_allow_html=True)

        # 5. 60-DAY FORECAST
        st.divider()
        st.subheader(f"📉 {forecast_horizon}-Day Cash Forecast")
        f_df = forecast_cashflow(
            cash_today=cash_now, start_date=df["date"].max(), days=forecast_horizon,
            avg_daily_sales=metrics["avg_daily_sales"], 
            avg_daily_ad_spend=metrics["avg_daily_ad_spend"], 
            avg_daily_fixed_cost=metrics["avg_daily_fixed_cost"], 
            cod_delay_days=cod_delay, return_rate=metrics["return_rate"]
        )
        
        fig = px.line(f_df, x="date", y="closing_cash", title="Liquidity Position")
        fig.add_hline(y=0, line_dash="dash", line_color="red", annotation_text="Insolvency Point")
        st.plotly_chart(fig, use_container_width=True)

        # 6. AI ADVICE
        st.divider()
        st.subheader("🤖 Executive Strategy Report")
        advice_text = generate_coo_advice(
            cash_today=cash_now, 
            runway_days=metrics["runway_months"], 
            ad_spend_pct=metrics["ad_spend_pct"], 
            return_rate=metrics["return_rate"], 
            decisions=generate_decisions(metrics)
        )
        st.info(advice_text)
        
    except Exception as e:
        st.error(f"Analysis Error: {e}")
else:
    st.info("👋 Welcome! Please upload your Shopify or Bank statement CSV to begin.")