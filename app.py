import streamlit as st
import pandas as pd

from engine.loader import load_transactions
from engine.decisions import generate_decisions

# ----------------------------
# Page config
# ----------------------------
st.set_page_config(
    page_title="AI Cash-Flow COO",
    layout="centered"
)

# ----------------------------
# Header
# ----------------------------
st.title("🧠 Cash-Flow Early Warning System for SMEs")
st.write(
    "Know when your business may face cash trouble — and what to do next.\n\n"
    "**No dashboards. No jargon. Just decisions.**"
)

st.markdown("---")

# ----------------------------
# Sample CSV download
# ----------------------------
st.subheader("Need a sample CSV format?")

sample_csv = """date,amount,type
2024-01-01,42000,sales
2024-01-02,-15000,ad_spend
2024-01-03,-8000,fixed_cost
2024-01-05,46000,sales
2024-01-08,-12000,ad_spend
2024-01-10,48000,sales
2024-01-15,-6000,return
2024-02-01,52000,sales
2024-02-05,-18000,ad_spend
2024-02-10,50000,sales
2024-03-01,60000,sales
2024-04-01,65000,sales
2024-05-01,70000,sales
2024-06-01,72000,sales
2024-07-01,74000,sales
2024-08-01,76000,sales
2024-09-01,78000,sales
2024-10-01,80000,sales
2024-11-01,82000,sales
2024-12-01,85000,sales
"""

st.download_button(
    label="📥 Download sample transactions CSV",
    data=sample_csv,
    file_name="sample_transactions.csv",
    mime="text/csv",
)

st.markdown("---")

# ----------------------------
# File uploader
# ----------------------------
st.subheader("Upload your transactions CSV (bank / accounting / POS export)")

uploaded_file = st.file_uploader(
    "",
    type=["csv"]
)

# ----------------------------
# Main logic
# ----------------------------
if uploaded_file is not None:
    try:
        # Load & normalize data
        df = load_transactions(uploaded_file)

        st.success("CSV uploaded successfully")

        # ----------------------------
        # Calculate metrics (INLINE – SAFE)
        # ----------------------------
        total_sales = df[df["amount"] > 0]["amount"].sum()
        total_spend = abs(df[df["amount"] < 0]["amount"].sum())

        ad_spend = abs(df[df["type"] == "ad_spend"]["amount"].sum())
        returns = abs(df[df["type"] == "return"]["amount"].sum())

        days = max((df["date"].max() - df["date"].min()).days, 1)

        avg_daily_burn = total_spend / days
        cash_today = total_sales - total_spend

        if avg_daily_burn <= 0:
            runway = "Cash Positive"
        else:
            runway = round(cash_today / avg_daily_burn, 1)

        metrics = {
            "cash_today": round(cash_today, 2),
            "avg_daily_burn": round(avg_daily_burn, 2),
            "runway_days": runway,
            "ad_spend_pct": round(ad_spend / total_sales, 3) if total_sales else 0,
            "return_rate": round(returns / total_sales, 3) if total_sales else 0,
        }

        # ----------------------------
        # Display summary
        # ----------------------------
        st.markdown("## 📊 Cash Snapshot")

        st.write(f"**Cash today:** ₹{metrics['cash_today']:,}")
        st.write(f"**Avg daily burn:** ₹{metrics['avg_daily_burn']:,}")
        st.write(f"**Runway:** {metrics['runway_days']}")
        st.write(f"**Ad spend % of sales:** {metrics['ad_spend_pct']*100:.1f}%")
        st.write(f"**Return rate:** {metrics['return_rate']*100:.1f}%")

        # ----------------------------
        # COO Decisions
        # ----------------------------
        decisions = generate_decisions(metrics)

        st.markdown("## 🚨 Key Risks")
        if decisions["risks"]:
            for r in decisions["risks"]:
                st.error(r)
        else:
            st.success("No immediate risks detected")

        st.markdown("## ✅ Recommended Actions")
        for a in decisions["actions"]:
            st.write(f"- {a}")

        st.markdown("---")
        st.info("📅 Review again in 7 days")

    except Exception as e:
        st.error("Error processing file")
        st.code(str(e))
