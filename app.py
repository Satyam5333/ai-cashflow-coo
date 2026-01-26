import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import StringIO

# -------------------------
# Page config
# -------------------------
st.set_page_config(
    page_title="AI Cash-Flow COO",
    page_icon="🧠",
    layout="centered"
)

# -------------------------
# Title & intro
# -------------------------
st.title("🧠 Cash-Flow Early Warning System for SMEs")

st.markdown(
    "Know when your business may face cash trouble — **and what to do next.**\n\n"
    "**No dashboards. No jargon. Just decisions.**"
)

st.divider()

# -------------------------
# What this tool does
# -------------------------
st.header("What this tool does")
st.markdown(
    """
This system:
- Analyzes your real transaction data  
- Forecasts cash position for the next **60 days**  
- Flags overspending and cash risks  
- Gives **clear, COO-level recommendations**
"""
)

st.divider()

# -------------------------
# Sample CSV download (REAL FILE)
# -------------------------
sample_csv = """date,amount,type,description
2025-01-01,42000,Inflow,Sales
2025-01-02,-15000,Outflow,Facebook Ads
2025-01-03,-8000,Outflow,Salary
2025-01-04,-6000,Outflow,Rent
2025-01-05,38000,Inflow,Sales
"""

st.download_button(
    label="📥 Download sample CSV format",
    data=sample_csv,
    file_name="sample_transactions.csv",
    mime="text/csv"
)

st.divider()

# -------------------------
# Upload CSV
# -------------------------
uploaded_file = st.file_uploader(
    "Upload your transactions CSV (bank / accounting / POS export)",
    type=["csv"]
)

# -------------------------
# Main processing
# -------------------------
if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)

        # Normalize columns
        df.columns = df.columns.str.lower().str.strip()
        df["date"] = pd.to_datetime(df["date"])
        df["amount"] = df["amount"].astype(float)
        df["description"] = df["description"].astype(str)

        # -------------------------
        # Core metrics
        # -------------------------
        total_cash = df["amount"].sum()
        inflow = df[df["amount"] > 0]["amount"].sum()
        outflow = abs(df[df["amount"] < 0]["amount"].sum())

        daily_burn = outflow / max(len(df["date"].dt.date.unique()), 1)
        runway_days = int(total_cash / daily_burn) if daily_burn > 0 else 999

        ad_spend = abs(
            df[df["description"].str.contains("ad", case=False, na=False)]["amount"].sum()
        )

        ad_ratio = (ad_spend / inflow) * 100 if inflow > 0 else 0

        # -------------------------
        # AI COO SUMMARY
        # -------------------------
        st.header("📊 AI COO Summary")

        st.markdown(f"""
**Cash today:** ₹{total_cash:,.0f}  
**Runway:** {runway_days} days  
**Advertising spend:** {ad_ratio:.1f}% of sales  
""")

        st.divider()

        # -------------------------
        # Risks
        # -------------------------
        st.header("⚠️ Key risks")

        risks = []

        if runway_days < 60:
            risks.append("Cash runway below 60 days")

        if ad_ratio > 30:
            risks.append("High dependency on advertising spend")

        if not risks:
            st.success("No major financial risks detected.")
        else:
            for r in risks:
                st.warning(r)

        st.divider()

        # -------------------------
        # Recommendations
        # -------------------------
        st.header("✅ Recommended actions")

        actions = []

        if ad_ratio > 30:
            actions.append("Reduce low-ROI ad campaigns and test organic channels")

        if runway_days < 60:
            actions.append("Slow discretionary spending and preserve cash")

        if not actions:
            actions.append("Maintain current spending discipline")

        for a in actions:
            st.markdown(f"- {a}")

        st.divider()

        # -------------------------
        # Expense category breakdown (PIE)
        # -------------------------
        st.header("📉 Expense category breakdown")

        expenses = (
            df[df["amount"] < 0]
            .groupby("description")["amount"]
            .sum()
            .abs()
            .sort_values(ascending=False)
        )

        if not expenses.empty:
            fig, ax = plt.subplots()
            ax.pie(
                expenses,
                labels=expenses.index,
                autopct="%1.1f%%",
                startangle=90
            )
            ax.axis("equal")
            st.pyplot(fig)

            # -------------------------
            # Top 2 cost drivers
            # -------------------------
            top_two = expenses.head(2)
            concentration = top_two.sum() / expenses.sum() * 100

            st.markdown(
                f"**Top cost drivers:** {', '.join(top_two.index)} "
                f"({concentration:.1f}% of total expenses)"
            )

            if concentration > 60:
                st.warning(
                    "⚠️ **Cost concentration risk:** "
                    "Too much spend concentrated in few categories."
                )

        else:
            st.info("No expense data found.")

    except Exception as e:
        st.error(f"Error processing file: {e}")
        st.stop()
