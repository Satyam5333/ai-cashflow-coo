import streamlit as st
import pandas as pd

from engine.loader import load_transactions
from engine.cashflow import calculate_cash_metrics
from engine.decisions import generate_decisions


# --------------------------------
# Page config
# --------------------------------
st.set_page_config(
    page_title="AI Cash-Flow COO",
    layout="centered",
)

# --------------------------------
# Title & intro
# --------------------------------
st.title("🧠 Cash-Flow Early Warning System for SMEs")

st.markdown(
    """
Know when your business may face cash trouble — **and what to do next**.

**No dashboards. No jargon. Just decisions.**
"""
)

st.divider()

# --------------------------------
# What this tool does (RESTORED)
# --------------------------------
st.subheader("What this tool does")

st.markdown(
    """
This system:

- Analyzes your real transaction data  
- Forecasts cash position for the next **60 days**  
- Flags overspending and cash risks  
- Gives **clear, actionable COO-level recommendations**  

*(No dashboards. No jargon. Just decisions.)*
"""
)

st.divider()

# --------------------------------
# Upload CSV
# --------------------------------
st.subheader("Upload your transactions CSV (bank / accounting / POS export)")

uploaded_file = st.file_uploader(
    "",
    type=["csv"]
)

# --------------------------------
# CSV explanation (BELOW upload)
# --------------------------------
st.markdown("### 📄 Required CSV format")

st.info(
    """
Your CSV **must contain exactly these columns**:

• **date** → Transaction date (YYYY-MM-DD)  
• **amount** →  
  - Positive = money coming in  
  - Negative = money going out  
• **type** → One of:
  - `sales`
  - `ad_spend`
  - `fixed_cost`
  - `return`

Example rows:

date,amount,type  
2024-01-01,42000,sales  
2024-01-02,-15000,ad_spend  
2024-01-03,-8000,fixed_cost  
"""
)

# --------------------------------
# Sample CSV download (BELOW upload)
# --------------------------------
sample_csv = """date,amount,type
2024-01-01,42000,sales
2024-01-02,-15000,ad_spend
2024-01-03,-8000,fixed_cost
2024-01-04,38000,sales
2024-01-05,-12000,ad_spend
2024-01-06,-6000,return
"""

st.download_button(
    label="📥 Download sample transactions CSV",
    data=sample_csv,
    file_name="sample_transactions.csv",
    mime="text/csv",
)

st.divider()

# --------------------------------
# Process uploaded file
# --------------------------------
if uploaded_file is not None:
    try:
        df = load_transactions(uploaded_file)

        metrics = calculate_cash_metrics(df)
        decisions = generate_decisions(metrics)

        st.subheader("📊 AI COO Summary")

        st.markdown(f"**Cash today:** ₹{metrics['cash_today']:,.0f}")
        st.markdown(f"**Runway:** {metrics['runway_days']}")
        st.markdown(f"**Ad spend:** {metrics['ad_spend_pct']*100:.1f}% of sales")
        st.markdown(f"**Return rate:** {metrics['return_rate']*100:.1f}%")

        st.subheader("⚠️ Key risks")
        if decisions["risks"]:
            for r in decisions["risks"]:
                st.write(f"- {r}")
        else:
            st.write("No major risks detected.")

        st.subheader("✅ Recommended actions")
        for a in decisions["actions"]:
            st.write(f"- {a}")

    except Exception as e:
        st.error("Error processing file")
        st.code(str(e))
