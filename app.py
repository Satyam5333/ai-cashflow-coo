import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import timedelta
import io

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
# What this tool does (RESTORED)
# -----------------------------
st.subheader("What this tool does")
st.markdown(
    """
This system:

- Analyzes your real transaction data  
- Forecasts cash position and runway  
- Flags overspending and concentration risks  
- Tells you **what to cut first** when cash is tight  

*(No dashboards. No jargon. Just decisions.)*
"""
)

st.divider()

# -----------------------------
# Sample CSV download (REAL FILE)
# -----------------------------
sample_csv = io.StringIO()
sample_csv.write(
    "date,amount,type,description\n"
    "2025-01-01,42000,Inflow,Sales\n"
    "2025-01-02,-15000,Outflow,Facebook Ads\n"
    "2025-01-03,-8000,Outflow,Salary\n"
    "2025-01-04,-5000,Outflow,Rent\n"
)
sample_csv.seek(0)

st.download_button(
    "📥 Download sample transactions CSV",
    sample_csv,
    file_name="sample_transactions.csv",
    mime="text/csv"
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
# AI COO SUMMARY (DETAILED & REAL)
# -----------------------------
st.subheader("📊 AI COO Summary")

st.markdown(
    f"""
**Cash today:** ₹{cash_today:,.0f}  

Your business is burning approximately **₹{daily_burn:,.0f} per day**,  
giving you a **cash runway of ~{runway_days} days**.

If nothing changes, **cash may run out around:**  
🧨 **{cash_out_date.date()}**

**Advertising intensity:**  
Ads consume **{ad_ratio:.1f}% of your revenue**.
"""
)

if ad_ratio > 25:
    st.warning(
        "Growth is heavily dependent on advertising. "
        "If returns weaken, cash pressure will escalate quickly."
    )

st.divider()

# -----------------------------
# Expense category breakdown (FIXED PIE)
# -----------------------------
st.subheader("📉 Expense category breakdown")

expense_df = df[df["amount"] < 0].copy()
expense_df["abs_amount"] = expense_df["amount"].abs()

expense_df["category"] = expense_df["description"].apply(
    lambda x: "Advertising"
    if any(k in x.lower() for k in ["ad", "facebook", "google", "instagram"])
    else x
)

expense_breakdown = (
    expense_df.groupby("category")["abs_amount"]
    .sum()
    .sort_values(ascending=False)
)

# Group small items into "Other"
top = expense_breakdown.head(4)
other = expense_breakdown.iloc[4:].sum()
if other > 0:
    top["Other"] = other

# ----- CLEAN PIE (NO OVERLAP) -----
fig, ax = plt.subplots(figsize=(4, 4))
wedges, _ , _ = ax.pie(
    top.values,
    autopct="%1.0f%%",
    startangle=90,
    pctdistance=0.7,
    textprops={"fontsize": 9},
    labels=None
)

ax.legend(
    wedges,
    top.index,
    title="Category",
    loc="center left",
    bbox_to_anchor=(1.05, 0.5),
    fontsize=9
)

ax.axis("equal")
st.pyplot(fig)

# -----------------------------
# Cost concentration risk
# -----------------------------
top_two_share = top.values[:2].sum() / top.values.sum() * 100
if top_two_share > 65:
    st.warning(
        f"⚠️ **Cost concentration risk:** "
        f"Top 2 categories make up {top_two_share:.0f}% of total expenses."
    )

# -----------------------------
# What should I cut first
# -----------------------------
st.subheader("✂️ What should you cut first?")

largest_cost = expense_breakdown.index[0]

st.markdown(
    f"""
1️⃣ **{largest_cost}** is your biggest cash drain  
2️⃣ Advertising is the fastest lever for short-term relief  
3️⃣ Avoid cutting fixed costs unless runway < 60 days  

👉 **Action:** Reduce variable spend first and reassess in 7 days.
"""
)
