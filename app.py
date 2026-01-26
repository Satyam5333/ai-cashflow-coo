import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from datetime import timedelta
from io import BytesIO

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
- Analyzes real transaction data  
- Forecasts runway and cash-out date  
- Detects cost concentration risk  
- Answers **“What should I cut first?”**  
"""
)

st.divider()

# -----------------------------
# Sample CSV download
# -----------------------------
sample_csv = """date,amount,type,description
2025-01-01,42000,Inflow,Sales
2025-01-02,-15000,Outflow,Facebook Ads
2025-01-03,-8000,Outflow,Salary
2025-01-04,-5000,Outflow,Rent
"""

st.download_button(
    "📥 Download sample transactions CSV",
    data=sample_csv,
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

daily_burn = (
    df[df["amount"] < 0]
    .groupby(df["date"].dt.date)["amount"]
    .sum()
    .abs()
    .mean()
)

runway_days = int(cash_today / daily_burn) if daily_burn > 0 else 999
cash_out_date = df["date"].max() + timedelta(days=runway_days)

ads_mask = df["description"].str.contains(
    "ad|facebook|google|instagram", case=False, na=False
)
ad_spend = abs(df[ads_mask & (df["amount"] < 0)]["amount"].sum())
ad_ratio = (ad_spend / inflows * 100) if inflows > 0 else 0

# -----------------------------
# AI COO Summary (DETAILED)
# -----------------------------
st.subheader("📊 AI COO Summary")

st.markdown(
    f"""
**Cash today:** ₹{cash_today:,.0f}  
**Average daily burn:** ₹{daily_burn:,.0f}  
**Runway:** ~{runway_days} days  
**Estimated cash-out date:** **{cash_out_date.date()}**

**Advertising dependency:** {ad_ratio:.1f}% of revenue
"""
)

if runway_days < 90:
    st.warning("⚠️ Runway under 90 days. Immediate cost control required.")

if ad_ratio > 30:
    st.warning("⚠️ Heavy dependence on advertising. Revenue volatility risk.")

st.divider()

# -----------------------------
# Expense breakdown (clean pie)
# -----------------------------
st.subheader("📉 Expense category breakdown")

expense_df = df[df["amount"] < 0].copy()
expense_df["abs"] = expense_df["amount"].abs()

def map_category(d):
    d = d.lower()
    if "ad" in d:
        return "Advertising"
    if "salary" in d:
        return "Salary"
    if "rent" in d:
        return "Rent"
    return "Other"

expense_df["category"] = expense_df["description"].apply(map_category)
expense_breakdown = expense_df.groupby("category")["abs"].sum().sort_values(ascending=False)

fig, ax = plt.subplots(figsize=(4, 4))
ax.pie(
    expense_breakdown.values,
    labels=expense_breakdown.index,
    autopct="%1.0f%%",
    startangle=90,
    textprops={"fontsize": 9},
)
ax.axis("equal")
st.pyplot(fig)

top_two_share = expense_breakdown.iloc[:2].sum() / expense_breakdown.sum() * 100
if top_two_share > 65:
    st.warning(f"⚠️ Cost concentration risk: top 2 costs = {top_two_share:.0f}%")

st.divider()

# -----------------------------
# Investor PDF (MATPLOTLIB SAFE)
# -----------------------------
st.subheader("📄 Investor-ready PDF")

def generate_pdf():
    buffer = BytesIO()
    with PdfPages(buffer) as pdf:
        fig = plt.figure(figsize=(8.27, 11.69))
        plt.axis("off")

        text = f"""
CASH-FLOW INVESTOR SUMMARY

Cash today: ₹{cash_today:,.0f}
Daily burn: ₹{daily_burn:,.0f}
Runway: ~{runway_days} days
Cash-out date: {cash_out_date.date()}

Advertising spend: {ad_ratio:.1f}% of revenue

TOP RISKS:
- Cost concentration risk: {top_two_share:.0f}%
- Runway pressure if revenue dips

WHAT TO CUT FIRST:
- Reduce {expense_breakdown.index[0]} before fixed costs
- Pause low-ROI ad channels
- Renegotiate variable vendors
"""
        plt.text(0.01, 0.99, text, va="top", fontsize=11)
        pdf.savefig(fig)
        plt.close(fig)

    buffer.seek(0)
    return buffer

pdf_buffer = generate_pdf()

st.download_button(
    "📥 Download Investor PDF",
    data=pdf_buffer,
    file_name="cashflow_investor_summary.pdf",
    mime="application/pdf",
)
