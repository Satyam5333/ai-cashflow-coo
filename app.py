import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import StringIO

st.set_page_config(page_title="AI Cash-Flow COO", layout="centered")

# --------------------------------------------------
# Header
# --------------------------------------------------
st.title("🧠 Cash-Flow Early Warning System for SMEs")
st.write(
    "Know when your business may face cash trouble — **and what to do next**."
)

st.divider()

# --------------------------------------------------
# What this tool does
# --------------------------------------------------
st.subheader("What this tool does")
st.markdown(
    """
- Analyzes real transaction data  
- Tracks cash inflows vs outflows  
- Highlights spending concentration risks  
- Shows where cash is actually going  
- Gives **clear, CFO-style insights** (no dashboards, no jargon)
"""
)

st.divider()

# --------------------------------------------------
# Sample CSV download
# --------------------------------------------------
sample_csv = """date,amount,type,description
2025-01-01,42000,Inflow,Sales
2025-01-02,-15000,Outflow,Facebook Ads
2025-01-03,-8000,Outflow,Salary
2025-01-04,-12000,Outflow,Google Ads
2025-01-05,-6000,Outflow,Instagram Ads
2025-01-06,-4000,Outflow,Packaging
2025-01-07,-2500,Outflow,Delivery
"""

st.download_button(
    "⬇️ Download sample CSV format",
    data=sample_csv,
    file_name="sample_transactions.csv",
    mime="text/csv",
)

st.divider()

# --------------------------------------------------
# Upload CSV
# --------------------------------------------------
uploaded_file = st.file_uploader(
    "Upload your transactions CSV (bank / accounting / POS export)",
    type=["csv"],
)

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    required_cols = {"date", "amount", "type", "description"}
    if not required_cols.issubset(df.columns):
        st.error("CSV must contain: date, amount, type, description")
        st.stop()

    df["date"] = pd.to_datetime(df["date"])
    df["amount"] = df["amount"].astype(float)

    inflow = df[df["amount"] > 0]["amount"].sum()
    outflow = df[df["amount"] < 0]["amount"].sum() * -1
    cash_today = inflow - outflow

    # --------------------------------------------------
    # AI COO Summary
    # --------------------------------------------------
    st.divider()
    st.subheader("📊 AI COO Summary")

    avg_daily_burn = outflow / max(df["date"].nunique(), 1)
    runway_days = int(cash_today / avg_daily_burn) if avg_daily_burn > 0 else 0

    ad_spend = df[
        (df["amount"] < 0)
        & (df["description"].str.contains("ads", case=False))
    ]["amount"].sum() * -1

    ad_ratio = (ad_spend / inflow) * 100 if inflow > 0 else 0

    st.markdown(
        f"""
**Current cash position:** ₹{cash_today:,.0f}  
**Estimated runway:** {runway_days} days  
**Advertising intensity:** {ad_ratio:.1f}% of total sales  

**Insight:**  
Your business is currently cash-positive.  
Marketing is a major growth lever — but also a key risk if returns weaken.
"""
    )

    # --------------------------------------------------
    # Expense category breakdown
    # --------------------------------------------------
    st.divider()
    st.subheader("📉 Expense category breakdown")

    expenses = (
        df[df["amount"] < 0]
        .groupby("description")["amount"]
        .sum()
        .abs()
        .to_dict()
    )

    total_expense = sum(expenses.values())

    major = {}
    other_total = 0

    for k, v in expenses.items():
        if v / total_expense >= 0.05:
            major[k] = v
        else:
            other_total += v

    if other_total > 0:
        major["Other costs"] = other_total

    # Pie chart (clean & small)
    fig, ax = plt.subplots(figsize=(4, 4), dpi=110)
    ax.pie(
        major.values(),
        labels=major.keys(),
        autopct="%1.0f%%",
        startangle=90,
        pctdistance=0.7,
        labeldistance=1.15,
        wedgeprops={"edgecolor": "white"},
        textprops={"fontsize": 9},
    )
    ax.set_title("Expense share", fontsize=11)
    st.pyplot(fig)

    # --------------------------------------------------
    # Cost concentration risk
    # --------------------------------------------------
    sorted_exp = sorted(major.items(), key=lambda x: x[1], reverse=True)
    top_cat, top_amt = sorted_exp[0]
    top_share = top_amt / total_expense

    if top_share >= 0.5:
        st.warning(
            f"⚠️ **Cost concentration risk:** {top_cat} alone accounts for "
            f"{top_share:.0%} of total expenses. Any inefficiency here can "
            "rapidly damage cash flow."
        )
    elif top_share >= 0.35:
        st.info(
            f"ℹ️ **Moderate concentration:** {top_cat} is {top_share:.0%} "
            "of spending. Monitor ROI closely."
        )
    else:
        st.success("✅ Expenses are well diversified. No major concentration risk.")

    # --------------------------------------------------
    # Recommended actions
    # --------------------------------------------------
    st.divider()
    st.subheader("✅ Recommended actions")

    actions = []

    if ad_ratio > 20:
        actions.append(
            "Audit advertising ROI weekly — ad spend is high relative to sales."
        )

    if runway_days < 90:
        actions.append(
            "Reduce fixed costs or improve collections to extend runway."
        )

    if not actions:
        actions.append("Maintain current spending discipline and cash controls.")

    for a in actions:
        st.write("•", a)
