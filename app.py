import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import timedelta

# -----------------------------
# Page config
# -----------------------------
st.set_page_config(page_title="AI Cash-Flow COO", layout="centered")

# -----------------------------
# Title
# -----------------------------
st.title("🧠 Cash-Flow Early Warning System for SMEs")
st.write(
    "Know when your business may face cash trouble — and **what to do next**.\n\n"
    "**No dashboards. No jargon. Just decisions.**"
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
# Load data
# -----------------------------
df = pd.read_csv(uploaded_file)

required_cols = {"date", "amount", "type", "description"}
if not required_cols.issubset(df.columns):
    st.error("CSV must contain: date, amount, type, description")
    st.stop()

df["date"] = pd.to_datetime(df["date"])
df["amount"] = df["amount"].astype(float)
df["type"] = df["type"].str.lower()

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

# -----------------------------
# Advertising spend
# -----------------------------
ads_mask = df["description"].str.contains(
    "ad|facebook|google|instagram", case=False, na=False
)

ad_spend = abs(df[ads_mask & (df["amount"] < 0)]["amount"].sum())
ad_ratio = (ad_spend / inflows * 100) if inflows > 0 else 0

# -----------------------------
# Cash-out date
# -----------------------------
cash_out_date = (
    df["date"].max() + timedelta(days=runway_days)
    if daily_burn > 0 else None
)

# -----------------------------
# AI COO SUMMARY (DETAILED)
# -----------------------------
st.subheader("📊 AI COO Summary")

st.markdown(
    f"""
**Current cash balance:** ₹{cash_today:,.0f}  

Your business is currently spending **₹{daily_burn:,.0f} per day on average**, 
which gives you a **cash runway of approximately {runway_days} days**.

**Advertising efficiency:**  
You are spending **{ad_ratio:.1f}% of your revenue on advertising**.
"""
)

if ad_ratio > 25:
    st.warning(
        "Advertising is consuming a significant share of revenue. "
        "If growth does not justify this spend, margins will compress quickly."
    )
elif ad_ratio < 10:
    st.info(
        "Advertising spend is conservative. Growth may be constrained "
        "if customer acquisition relies heavily on paid channels."
    )

if cash_out_date:
    st.markdown(
        f"🧨 **If nothing changes, cash may run out around:** **{cash_out_date.date()}**"
    )

st.divider()

# -----------------------------
# Key risks
# -----------------------------
st.subheader("⚠️ Key risks")

risks = []

if runway_days < 90:
    risks.append("Cash runway is under 3 months — margin for error is low.")
if ad_ratio > 30:
    risks.append("High dependence on advertising for revenue generation.")

if not risks:
    st.success("No immediate financial red flags detected.")
else:
    for r in risks:
        st.warning(r)

st.divider()

# -----------------------------
# What should I cut first
# -----------------------------
st.subheader("✂️ What should you cut first?")

expense_df = df[df["amount"] < 0].copy()
expense_df["abs_amount"] = expense_df["amount"].abs()

expense_rank = (
    expense_df.groupby("description")["abs_amount"]
    .sum()
    .sort_values(ascending=False)
)

if ad_ratio > 20:
    st.write(
        "• **Advertising spend** is the fastest lever to pull for immediate cash relief."
    )

if not expense_rank.empty:
    st.write(
        f"• **{expense_rank.index[0]}** is your single largest expense category."
    )

st.divider()

# -----------------------------
# Expense category breakdown (FIXED PIE)
# -----------------------------
st.subheader("📉 Expense category breakdown")

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

top = expense_breakdown.head(5)
other = expense_breakdown.iloc[5:].sum()

if other > 0:
    top["Other"] = other

fig, ax = plt.subplots(figsize=(4.5, 4.5))

wedges, texts, autotexts = ax.pie(
    top.values,
    autopct="%1.1f%%",
    startangle=90,
    pctdistance=0.7,
    textprops={"fontsize": 9}
)

ax.legend(
    wedges,
    top.index,
    title="Expense category",
    loc="center left",
    bbox_to_anchor=(1, 0.5),
    fontsize=9
)

ax.axis("equal")
st.pyplot(fig)

# -----------------------------
# Cost concentration warning
# -----------------------------
top_two_share = top.values[:2].sum() / top.values.sum() * 100

if top_two_share > 65:
    st.warning(
        f"⚠️ **Cost concentration risk:** Top 2 categories account for "
        f"{top_two_share:.0f}% of total expenses."
    )

st.divider()

# -----------------------------
# Executive recommendation
# -----------------------------
st.subheader("✅ Executive recommendation")

st.markdown(
    """
Maintain **tight control on discretionary costs**, especially advertising.

If revenue growth slows, **pause or optimize ad campaigns first**  
before touching fixed costs like salary or rent.

Reassess cash position **every 7 days**.
"""
)
