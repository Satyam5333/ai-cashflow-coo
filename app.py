import streamlit as st
import pandas as pd

from engine.loader import load_transactions
from engine.cashflow import calculate_cash_metrics
from engine.decisions import generate_decisions

# -----------------------
# Page config
# -----------------------
st.set_page_config(
    page_title="AI Cash-Flow COO",
    page_icon="🧠",
    layout="centered"
)

# -----------------------
# Header
# -----------------------
st.markdown("## 🧠 Cash-Flow Early Warning System for SMEs")

st.markdown(
    """
Know when your business may face cash trouble — **and what to do next.**

**No dashboards. No jargon. Just decisions.**
"""
)

st.divider()

# -----------------------
# What this tool does
# -----------------------
st.markdown("### What this tool does")

st.markdown(
    """
This system acts like a **virtual COO** for your business:

- Analyzes real transaction-level cash movements  
- Forecasts your cash position for the next **60 days**  
- Detects overspending and hidden cash risks  
- Produces **clear, business-first recommendations**
"""
)

st.divider()

# -----------------------
# Upload section
# -----------------------
st.markdown("### Upload your transactions CSV (bank / accounting / POS export)")

uploaded_file = st.file_uploader(
    "",
    type=["csv"],
    help="CSV must contain date, amount, and type columns"
)

# -----------------------
# Sample CSV (ONLY below upload)
# -----------------------
with st.expander("📥 Download sample CSV format"):
    sample_csv = """date,amount,type
2024-01-01,42000,sales
2024-01-02,-15000,ad_spend
2024-01-03,-8000,fixed_cost
2024-01-04,38000,sales
2024-01-05,-12000,ad_spend
"""
    st.download_button(
        label="Download sample transactions CSV",
        data=sample_csv,
        file_name="sample_transactions.csv",
        mime="text/csv"
    )

# -----------------------
# Processing logic
# -----------------------
if uploaded_file:
    try:
        df = load_transactions(uploaded_file)
        metrics = calculate_cash_metrics(df)
        decisions = generate_decisions(metrics)

        st.divider()

        # -----------------------
        # COO Summary (DETAILED, NOT METRIC DUMP)
        # -----------------------
        st.markdown("## 📊 COO Summary")

        st.markdown(
            f"""
**Current cash position**

You currently have **₹{metrics['cash_today']:,.0f}** available.

At the present burn rate, your business has approximately  
**{metrics['runway_days']} days of cash runway**, assuming no major changes.

**Spending behaviour**

Advertising spend represents **{metrics['ad_spend_pct']:.1f}% of sales**.  
Customer returns account for **{metrics['return_rate']:.1f}% of revenue**.

"""
        )

        # -----------------------
        # Risks
        # -----------------------
        st.markdown("## ⚠️ Key risks")

        if decisions["risks"]:
            for r in decisions["risks"]:
                st.markdown(f"- {r}")
        else:
            st.markdown("No immediate financial risks detected based on current data.")

        # -----------------------
        # Actions
        # -----------------------
        st.markdown("## ✅ Recommended actions")

        if decisions["actions"]:
            for a in decisions["actions"]:
                st.markdown(f"- {a}")
        else:
            st.markdown("No corrective action required at this time. Continue monitoring weekly.")

    except Exception as e:
        st.error("Error processing file")
        st.code(str(e))
