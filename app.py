import streamlit as st
import pandas as pd

from engine.loader import load_transactions
from engine.cashflow import calculate_cash_metrics
from engine.decisions import generate_decisions


# -----------------------------
# Page configuration
# -----------------------------
st.set_page_config(
    page_title="AI Cash-Flow COO",
    page_icon="🧠",
    layout="centered"
)

# -----------------------------
# Header
# -----------------------------
st.title("🧠 Cash-Flow Early Warning System for SMEs")

st.markdown(
    """
    Know when your business may face cash trouble — **and what to do next**.

    **What this tool does**
    - Analyzes your real transaction data
    - Forecasts cash position for the next 60 days
    - Flags overspending and cash risks
    - Gives clear, actionable recommendations  

    _No dashboards. No jargon. Just decisions._
    """
)

st.divider()

# -----------------------------
# File upload
# -----------------------------
st.subheader("Upload your transactions CSV (bank / accounting / POS export)")

uploaded_file = st.file_uploader(
    "",
    type=["csv"]
)

# -----------------------------
# Main logic
# -----------------------------
if uploaded_file is not None:
    try:
        # Read CSV
        df = pd.read_csv(uploaded_file)

        # Normalize column names
        df.columns = [c.strip().lower() for c in df.columns]

        # Load & clean transactions
        transactions = load_transactions(df)

        # Calculate cash metrics
        metrics = calculate_cash_metrics(transactions)

        # Generate COO decisions
        result = generate_decisions(metrics)

        st.divider()

        # -----------------------------
        # Key metrics
        # -----------------------------
        st.subheader("📊 Current status")

        st.write(f"**Cash today:** ₹{result['cash_today']:,.0f}")
        st.write(f"**Runway:** {result['runway_days']}")
        st.write(f"**Ad spend:** {result['ad_spend_pct'] * 100:.1f}% of sales")
        st.write(f"**Return rate:** {result['return_rate'] * 100:.1f}%")

        # -----------------------------
        # Risks
        # -----------------------------
        st.divider()
        st.subheader("⚠️ Key risks")

        if result["risks"]:
            for risk in result["risks"]:
                st.warning(risk)
        else:
            st.success("No major cash risks detected 🎉")

        # -----------------------------
        # Actions
        # -----------------------------
        st.divider()
        st.subheader("✅ Recommended actions")

        if result["actions"]:
            for action in result["actions"]:
                st.info(action)
        else:
            st.info("Continue current strategy and review again in 7 days.")

    except Exception as e:
        st.error("Error processing file")
        st.code(str(e))

else:
    st.info("Upload a CSV file to get started.")
