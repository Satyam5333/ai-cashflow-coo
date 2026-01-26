import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import timedelta

# -----------------------------
# Page config
# -----------------------------
st.set_page_config(page_title="AI Cash-Flow COO", layout="centered")

# -----------------------------
# Header
# -----------------------------
st.title("🧠 Cash-Flow Early Warning System for SMEs")
st.write(
    "Know when your business may face cash trouble — and **what to do next**.\n\n"
    "**No dashboards. No jargon. Just decisions.**"
)

st.divider()

# -----------------------------
# What this tool does
# -----------------------------
st.subheader("What this tool does")
st.markdown(
    """
This system:

- Analyzes your real transaction data  
- Forecasts cash runway and cash-out date  
- Flags overspending and cost concentration risks  
- Tells you **what to cut first** when cash is tight  

*(No dashboards. No jargon. Just decisions.)*
"""
)

st.divider()

# -----------------------------
# Sample CSV download (FIXED)
# -----------------------------
sample_csv_text = """date,amount,type,description
2025-01-01,42000,Inflow,Sales
2025-01-02,-15000,Outflow,Facebook Ads
2025-01-03,-8000,Outflow,Salary
2025-01-04,-5000,Outflow,Rent
"""

st.download_button(
    label="📥 Download sample transactions CSV",
    data=sample_csv_text.encode("utf-8"),
    file_name="sample_transactions.csv",
    mime="text/csv",
)

st.divider()

# -----------------------------
# Upload CSV
# -----------------------------
uploaded_file = st.file_uploader(
    "Upload your transactions CSV (bank / accounting / POS export)",
    type=["csv"]
)

if not uploaded_file:
    st.stop()

# -----------------------------
# Load & validate data
# -----------------------------
df = pd.read_csv(uploaded_file)

required_cols = {"date", "amount", "type", "description"}
if not required_cols.issubset(df.columns):
    st.error("CSV must contain: date, amount, type, description")
    st.stop()

df["date"] = pd.to_datetime(df["date"])
df["amount"] = df["amount"].astype(float)

# -----------------------------
# Core metrics
# -----------------------------
cash_today = df["amount"].sum()

inflows = df[df["amount"] > 0]["amount"].sum()
outflows = abs(df[df["amount"] < 0]["amount"].sum())

daily_burn = (
    df[df["amount"] < 0]
    .groupby(df["date"].dt.date)["amount"]
    .sum()
    .abs()
    .mean()
)

runway_days = int(cash_today / daily_burn) if daily_burn > 0 else 999
cash_out_date = df["date"].max() + timedelta(days=runway_days)

# -----------------------------
# Advertising spend
# -----------------------------
ads_mask = df["description"].str.contains(
    "ad|facebook|google|instagram", case=False, na=False
)
ad_spend = abs(df[ads_mask & (df["amount"] < 0)]["amount"].sum())
ad_ratio = (ad_spend / inflows * 100) if inflows > 0 else 0

# -----------------------------
# AI COO Summary (meaningful)
# -----------------------------
st.subheader("📊 AI COO Summary")

st.markdown(
    f"""
**Cash today:** ₹{cash_today:,.0f}  

You are spending **₹{daily_burn:,.0f} per day**, giving you a runway of  
**~{runway_days} days**.

If nothing changes, cash may run out around:  
🧨 **{cash_out_date.date()}**

**Advertising intensity:**  
Ads consume **{ad_ratio:.1f}% of revenue**.
"""
)

if ad_ratio > 25:
    st.warning(
        "High dependence on advertising. "
        "If sales slow down, cash pressure will increase rapidly."
    )

st.divider()

# -----------------------------
# Expense category breakdown (simple & clean)
# -----------------------------
st.subheader("📉 Expense category breakdown")

expense_df = df[df["amount"] < 0].copy()
expense_df["abs_amount"] = expense_df["amount"].abs()

def map_category(desc):
    d = desc.lower()
    if "ad" in d or "facebook" in d or "google" in d or "instagram" in d:
        return "Advertising"
    if "salary" in d:
        return "Salary"
    if "rent" in d:
        return "Rent"
    return "Other"

expense_df["category"] = expense_df["description"].apply(map_category)

expense_breakdown = (
    expense_df.groupby("category")["abs_amount"]
    .sum()
    .sort_values(ascending=False)
)

fig, ax = plt.subplots(figsize=(4, 4))
ax.pie(
    expense_breakdown.values,
    labels=None,
    autopct="%1.0f%%",
    pctdistance=0.75,
    textprops={"fontsize": 9},
)
ax.legend(
    expense_breakdown.index,
    loc="center left",
    bbox_to_anchor=(1.05, 0.5),
    fontsize=9,
)
ax.axis("equal")

st.pyplot(fig)

# -----------------------------
# Cost concentration risk
# -----------------------------
top_two = expense_breakdown.iloc[:2].sum()
total_exp = expense_breakdown.sum()
share = top_two / total_exp * 100

if share > 65:
    st.warning(
        f"⚠️ Cost concentration risk: "
        f"Top 2 categories make up {share:.0f}% of total expenses."
    )

# -----------------------------
# What should I cut first
# -----------------------------
st.subheader("✂️ What should you cut first?")

largest_cost = expense_breakdown.index[0]

st.markdown(
    f"""
**Primary cut candidate:** **{largest_cost}**

This category gives the **fastest cash relief** with the least operational damage.

**Recommended order:**
1. Reduce variable costs (ads, discretionary spend)
2. Renegotiate fixed costs only if runway < 60 days
3. Re-evaluate after 7 days
"""
)
