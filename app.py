import streamlit as st
import pandas as pd
from io import StringIO
from datetime import datetime

st.set_page_config(page_title="AI Cash-Flow COO", layout="centered")

# --------------------------------------------------
# Title & Intro
# --------------------------------------------------
st.title("🧠 Cash-Flow Early Warning System for SMEs")

st.markdown("""
Know when your business may face cash trouble — **and what to do next**.

**No dashboards. No jargon. Just decisions.**
""")

st.divider()

# --------------------------------------------------
# What this tool does
# --------------------------------------------------
st.header("What this tool does")

st.markdown("""
This system:

- Analyzes your real transaction data  
- Identifies cash inflows vs outflows  
- Highlights overspending risks  
- Breaks down expenses by category  
- Produces **clear COO-level guidance**
""")

st.divider()

# --------------------------------------------------
# Sample CSV (DOWNLOADABLE)
# --------------------------------------------------
st.subheader("Need a sample CSV format?")

sample_csv = """date,amount,type,description
2025-01-01,42000,Inflow,Sales
2025-01-02,-15000,Outflow,Facebook Ads
2025-01-03,-8000,Outflow,Salary
2025-01-04,-6000,Outflow,Rent
2025-01-05,38000,Inflow,Sales
"""

st.download_button(
    label="📥 Download sample transactions CSV",
    data=sample_csv,
    file_name="sample_transactions.csv",
    mime="text/csv"
)

st.divider()

# --------------------------------------------------
# Upload CSV
# --------------------------------------------------
st.header("Upload your transactions CSV")

uploaded_file = st.file_uploader(
    "Upload CSV (bank / accounting / POS export)",
    type=["csv"]
)

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)

        required_cols = {"date", "amount", "type", "description"}
        if not required_cols.issubset(df.columns):
            st.error("CSV must contain columns: date, amount, type, description")
            st.stop()

        # Clean data
        df["date"] = pd.to_datetime(df["date"])
        df["amount"] = pd.to_numeric(df["amount"])
        df["type"] = df["type"].str.lower()
        df["description"] = df["description"].str.lower()

        inflow = df[df["amount"] > 0]["amount"].sum()
        outflow = df[df["amount"] < 0]["amount"].sum()
        cash_today = inflow + outflow

        monthly_burn = abs(outflow) / max(1, df["date"].dt.to_period("M").nunique())
        runway_days = int(cash_today / (monthly_burn / 30)) if monthly_burn > 0 else 999

        # Ad spend
        ad_spend = df[df["description"].str.contains("ad")]["amount"].abs().sum()
        ad_ratio = (ad_spend / inflow) * 100 if inflow > 0 else 0

        # Expense breakdown
        expenses = (
            df[df["amount"] < 0]
            .groupby("description")["amount"]
            .sum()
            .abs()
            .sort_values(ascending=False)
        )

        # --------------------------------------------------
        # AI COO SUMMARY (DETAILED)
        # --------------------------------------------------
        st.divider()
        st.header("📊 AI COO Summary")

        st.markdown(f"""
**Cash position today:** ₹{cash_today:,.0f}  

**Total inflows:** ₹{inflow:,.0f}  
**Total outflows:** ₹{abs(outflow):,.0f}  

**Average monthly burn:** ₹{monthly_burn:,.0f}  
**Estimated runway:** {runway_days} days  

**Advertising spend:** {ad_ratio:.1f}% of sales
""")

        # Plain English explanation
        st.markdown("### What this means")

        if runway_days < 60:
            st.warning(
                "Your cash runway is tightening. Without action, "
                "you may face liquidity stress within the next two months."
            )
        else:
            st.success(
                "Your cash position is stable. Current spending levels are sustainable."
            )

        if ad_ratio > 30:
            st.warning(
                "A large portion of revenue is being spent on advertising. "
                "Review campaign ROI and pause underperforming ads."
            )

        # --------------------------------------------------
        # Key Risks
        # --------------------------------------------------
        st.divider()
        st.header("⚠️ Key risks")

        if runway_days < 60:
            st.markdown("- Short cash runway")
        elif ad_ratio > 30:
            st.markdown("- High dependency on advertising spend")
        else:
            st.success("No major financial risks detected.")

        # --------------------------------------------------
        # Recommended Actions
        # --------------------------------------------------
        st.divider()
        st.header("✅ Recommended actions")

        actions = []

        if ad_ratio > 25:
            actions.append("Reduce or optimize ad spend")
        if runway_days < 90:
            actions.append("Improve collections and delay non-critical expenses")
        if not actions:
            actions.append("Maintain current spending discipline")

        for a in actions:
            st.markdown(f"- {a}")

        # --------------------------------------------------
        # Expense Category Breakdown
        # --------------------------------------------------
        st.divider()
        st.header("📉 Expense category breakdown")

        for cat, amt in expenses.items():
            st.markdown(f"- **{cat.title()}**: ₹{amt:,.0f}")

    except Exception as e:
        st.error(f"Error processing file: {e}")
