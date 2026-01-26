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

# Normalize
df["type"] = df["type"].str.lower()

# -----------------------------
# Core metrics
# -----------------------------
today_cash = df["amount"].sum()

inflows = df[df["amount"] > 0]["amount"].sum()
outflows = abs(df[df["amount"] < 0]["amount"].sum())

daily_burn = (
    df[df["amount"] < 0]
    .groupby(df["date"].dt.date)["amount"]
    .sum()
    .abs()
    .mean()
)

runway_days = int(today_cash / daily_burn) if daily_burn > 0 else 999

# -----------------------------
# Advertising spend
# -----------------------------
ads_mask = df["description"].str.contains(
    "ad|facebook|google|instagram", case=False, na=False
)

ad_spend = abs(df[ads_mask & (df["amount"] < 0)]["amount"].sum())
ad_ratio = (ad_spend / inflows * 100) if inflows > 0 else 0

# -----------------------------
# Cash-out date prediction
# -----------------------------
if daily_burn > 0:
    cash_out_date = df["date"].max() + timedelta(days=runway_days)
else:
    cash_out_date = None

# -----------------------------
# AI COO SUMMARY
# -----------------------------
st.subheader("📊 AI COO Summary")

st.markdown(
    f"""
**Cash today:** ₹{today_cash:,.0f}  
**Runway:** {runway_days} days  

**Advertising spend:** {ad_ratio:.1f}% of revenue  
"""
)

if cash_out_date:
    st.markdown(
        f"🧨 **Projected cash-out date:** **{cash_out_date.date()}**"
    )

st.divider()

# -----------------------------
# Key risks
# -----------------------------
st.subheader("⚠️ Key risks")

risks = []

if ad_ratio > 25:
    risks.append("Advertising spend is consuming a high share of revenue.")
if runway_days < 90:
    risks.append("Cash runway is under 3 months.")

if not risks:
    st.success("No major financial risks detected.")
else:
    for r in risks:
        st.warning(r)

st.divider()

# -----------------------------
# WHAT SHOULD I CUT FIRST
# -----------------------------
st.subheader("✂️ What should you cut first?")

expense_df = df[df["amount"] < 0].copy()
expense_df["abs_amount"] = expense_df["amount"].abs()

cut_suggestions = []

if ad_ratio > 20:
    cut_suggestions.append(
        "Reduce advertising spend — it is the fastest lever with immediate cash impact."
    )

top_expense = (
    expense_df.groupby("description")["abs_amount"]
    .sum()
    .sort_values(ascending=False)
)

if not top_expense.empty:
    biggest = top_expense.index[0]
    cut_suggestions.append(
        f"Review **{biggest}** — it is your single largest cost driver."
    )

for c in cut_suggestions:
    st.write("•", c)

st.divider()

# -----------------------------
# Expense category breakdown (PIE)
# -----------------------------
st.subheader("📉 Expense category breakdown")

# Group ads into single bucket
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

# Limit small slices
top = expense_breakdown.head(5)
other = expense_breakdown.iloc[5:].sum()

if other > 0:
    top["Other"] = other

fig, ax = plt.subplots(figsize=(5, 5))
ax.pie(
    top.values,
    labels=top.index,
    autopct="%1.1f%%",
    startangle=90,
    textprops={"fontsize": 9}
)
ax.axis("equal")

st.pyplot(fig)

# -----------------------------
# Cost concentration warning
# -----------------------------
top_two_share = top.values[:2].sum() / top.values.sum() * 100

if top_two_share > 65:
    st.warning(
        f"⚠️ **Cost concentration risk:** Top 2 expense categories make up "
        f"{top_two_share:.0f}% of total costs."
    )

st.divider()

# -----------------------------
# Final recommendation
# -----------------------------
st.subheader("✅ Executive recommendation")

st.markdown(
    """
Focus on **reducing discretionary spend first (ads & variable costs)**  
before touching fixed costs like salary or rent.

Re-check cash position every **7 days**.
"""
)
