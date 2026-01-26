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
    .confidence-score {
        font-size: 2rem; font-weight: 800; color: #059669;
    }
    .warning-text { color: #dc2626; font-weight: 700; }
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
- **Generates** Founder Action Plans & Investor Reports
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
        df = load_transactions(uploaded_file)
        
        def reconcile_signs(row):
            desc = str(row['description']).lower()
            val = abs(row['amount'])
            if any(k in desc for k in ["ad", "facebook", "meta", "google", "rent", "salary", "refund", "payout fee"]):
                return -val
            if any(k in desc for k in ["payout", "sale", "deposit", "credit"]):
                return val
            return row['amount']
        
        df['amount'] = df.apply(reconcile_signs, axis=1)

        metrics = calculate_business_metrics(df)
        cash_now = opening_balance + df["amount"].sum()

        # 1. KPI CARDS
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Cash Today</div><div class='kpi-value'>₹{cash_now:,.0f}</div></div>", unsafe_allow_html=True)
        with c2: st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Runway</div><div class='kpi-value'>{metrics['runway_months']} Mo</div></div>", unsafe_allow_html=True)
        with c3: st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Ad Spend %</div><div class='kpi-value'>{metrics['ad_spend_pct']*100:.1f}%</div></div>", unsafe_allow_html=True)
        with c4: st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Returns</div><div class='kpi-value'>{metrics['return_rate']*100:.1f}%</div></div>", unsafe_allow_html=True)

        # 2. CASH-OUT PREDICTION
        st.divider()
        cash_out_str = "Sustainable"
        if metrics['runway_months'] < 99:
            cash_out_date = (datetime.now() + timedelta(days=int(metrics['runway_months'] * 30)))
            cash_out_str = cash_out_date.strftime('%d %b %Y')
            st.error(f"⚠️ **Estimated Cash-out Date: {cash_out_str}**")
        else:
            st.success("✅ **Sustainable Growth Projected**")

        # 3. SPEND ANALYSIS
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

        # 4. FORECAST
        st.divider()
        st.subheader(f"📉 {forecast_horizon}-Day Cash Forecast")
        f_df = forecast_cashflow(
            cash_today=cash_now, start_date=df["date"].max(), days=forecast_horizon,
            avg_daily_sales=metrics["avg_daily_sales"], avg_daily_ad_spend=metrics["avg_daily_ad_spend"], 
            avg_daily_fixed_cost=metrics["avg_daily_fixed_cost"], cod_delay_days=cod_delay, return_rate=metrics["return_rate"]
        )
        st.plotly_chart(px.line(f_df, x="date", y="closing_cash", title="Liquidity Position"), use_container_width=True)

        # NEW: 🏆 FOUNDER ACTION PLAN (PAID-FEEL)
        st.divider()
        st.subheader("📋 Executive Strategic Action Plan")
        st.markdown("<div class='paid-plan'>", unsafe_allow_html=True)
        
        col_plan_a, col_plan_b = st.columns([2, 1])
        with col_plan_a:
            st.markdown("### 🎯 Top 3 Actions (Next 30 Days)")
            st.markdown(f"1. **Audit ROAS by Ad Set:** Target a ROAS > 1.8 to reduce your {metrics['ad_spend_pct']*100:.1f}% spend intensity.")
            st.markdown(f"2. **Freeze Non-Core 'Other' Spending:** Your unclassified expenses total ₹{cat_df[cat_df['Category']=='Other']['amount'].sum() if not cat_df[cat_df['Category']=='Other'].empty else 0:,.0f}; cut this by 50% immediately.")
            st.markdown(f"3. **COD Verification:** Implement RTO calling/IVR to lower the {metrics['return_rate']*100:.1f}% return rate before the next scale-up.")
            
            st.markdown("### 🛑 What NOT to do")
            st.markdown("- **Do NOT** launch new SKUs or enter new markets until the cash-out date is pushed back at least 90 days.")
            st.markdown("- **Do NOT** increase Meta/Google daily budget based on 'one good day' of sales.")
        
        with col_plan_b:
            # Confidence Score Heuristic
            confidence = 85 if len(df) > 20 else 60
            st.markdown("### Decision Confidence")
            st.markdown(f"<div class='confidence-score'>{confidence}%</div>", unsafe_allow_html=True)
            st.write("Score based on data density and transaction history.")
            
            st.markdown("### 📉 The Cost of Inaction")
            if metrics['runway_months'] < 99:
                st.markdown(f"<span class='warning-text'>Failure to act will result in complete liquidity exhaustion by {cash_out_str}.</span>", unsafe_allow_html=True)
            else:
                st.markdown("<span class='warning-text'>Failure to act will reduce your current surplus and erode growth capital.</span>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

        # 5. INVESTOR PDF
        st.divider()
        def generate_investor_pdf():
            buffer = BytesIO()
            with PdfPages(buffer) as pdf:
                fig = plt.figure(figsize=(8.5, 11))
                plt.axis("off")
                content = f"CASH-FLOW REPORT\nCash: ₹{cash_now:,.0f}\nRunway: {metrics['runway_months']} Mo\nCash-out: {cash_out_str}\n\nTop Expenses:\n{cat_df.to_string(index=False)}"
                plt.text(0.1, 0.95, content, fontsize=11, family='monospace', va='top')
                pdf.savefig(fig)
                plt.close(fig)
            buffer.seek(0)
            return buffer
        st.download_button("📥 Download Investor PDF", data=generate_investor_pdf(), file_name="COO_Report.pdf", mime="application/pdf")

        # 6. AI ADVICE
        st.divider()
        advice_text = generate_coo_advice(cash_now, metrics['runway_months'], metrics['ad_spend_pct'], metrics['return_rate'], generate_decisions(metrics))
        st.info(advice_text)
        
    except Exception as e:
        st.error(f"Analysis Error: {e}")
else:
    st.info("👋 Upload data to begin.")