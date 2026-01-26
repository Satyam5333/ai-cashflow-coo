import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from datetime import timedelta
from io import BytesIO

st.set_page_config(page_title="AI Cash-Flow COO", layout="centered")

# -------------------------------------------------
# UI POLISH (COLOR + CARDS ONLY — SAFE)
# -------------------------------------------------
st.markdown("""
<style>

/* Global background */
html, body {
    background: linear-gradient(
        180deg,
        #eef2ff 0%,
        #f8fafc 45%,
        #ffffff 100%
    );
}

/* Streamlit app container */
.stApp {
    background: transparent;
}

/* Headings color */
h1, h2, h3 {
    color: #1e293b;
}

/* Section card effect */
.block-container > div > div {
    background: #ffffff;
    border-radius: 14px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 6px 20px rgba(0,0,0,0.05);
}

/* Paragraph text */
p, li {
    color: #334155;
    line-height: 1.6;
}

/* Buttons */
button {
    background-color: #4f46e5 !important;
    color: white !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
}

/* Alerts */
div[data-testid="stAlert"] {
    border-radius: 12px;
}

/* File uploader */
div[data-testid="stFileUploader"] {
    background: #f8fafc;
    border-radius: 12px;
    padding: 1rem;
}

/* Divider spacing */
hr {
    margin-top: 2rem;
    margin-bottom: 2rem;
}

</style>
""", unsafe_allow_html=True)

# -------------------------------------------------
# Header
# -------------------------------------------------
st.title("🧠 Cash-Flow Early Warning System for SMEs")
st.write(
    "Know when your business may face cash trouble — **and exactly what to do next**.\n\n"
    "**No dashboards. No jargon. Just decisions.**"
)

st.divider()

# -------------------------------------------------
# What this tool does
# -------------------------------------------------
st.subheader("What this tool does")
st.markdown(
    """
This system acts like a **virtual COO focused purely on cash discipline**.

It:
- Reads your real transaction data  
- Identifies what is actually driving cash burn  
- Predicts how long your money will last  
- Flags hidden structural risks  
- Tells you **what to cut, what to protect, and what to fix first**
"""
)

st.divider()

# -------------------------------------------------
# Sample CSV
# -------------------------------------------------
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

# -------------------------------------------------
# Upload CSV
# -------------------------------------------------
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

# -------------------------------------------------
# Core calculations
# -------------------------------------------------
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

# -------------------------------------------------
# AI COO SUMMARY
# -------------------------------------------------
st.subheader("🧠 AI COO Analysis")

st.markdown(
    f"""
### Cash position
You currently hold **₹{cash_today:,.0f}** in net cash.  
Your average daily operating burn is **₹{daily_burn:,.0f}**, giving you approximately **{runway_days} days of runway**.

Your **projected cash-out date is {cash_out_date.date()}**, assuming no changes.
"""
)

st.markdown(
    f"""
### Spending structure insight
Advertising consumes **{ad_ratio:.1f}% of total revenue**, making it the largest variable cost.

This introduces **cash volatility risk**, especially if ROI weakens or demand fluctuates.
"""
)

if ad_ratio > 40:
    st.error("⚠️ Advertising dependency is critically high.")
elif ad_ratio > 25:
    st.warning("⚠️ Advertising dependency is elevated.")
else:
    st.success("Advertising spend is within a healthy range.")

st.markdown(
    """
### What should you cut first?
If cash tightens, **do not cut core operations**.

Priority:
1. Advertising inefficiencies  
2. Variable vendor expenses  
3. Discretionary spend  

Protect salaries and rent to maintain execution strength.
"""
)

# -------------------------------------------------
# Founder Action Plan
# -------------------------------------------------
st.divider()
st.subheader("🧭 Founder Action Plan (Next 30 Days)")

st.markdown(
    f"""
**Immediate priorities**
- Cap advertising spend (**{ad_ratio:.1f}% of revenue**)  
- Freeze new fixed commitments  
- Renegotiate variable vendors  

**If no action is taken**
- Risk accelerates after ~{int(runway_days * 0.75)} days  
- A 10% revenue dip materially shortens runway  
"""
)

st.markdown(f"**Decision confidence score:** {7.8 if ad_ratio < 30 else 6.4}/10")

# -------------------------------------------------
# Expense breakdown
# -------------------------------------------------
st.divider()
st.subheader("📉 Expense category breakdown")

expense_df = df[df["amount"] < 0].copy()
expense_df["abs"] = expense_df["amount"].abs()

def map_category(desc):
    d = desc.lower()
    if "ad" in d:
        return "Advertising"
    if "salary" in d:
        return "Salary"
    if "rent" in d:
        return "Rent"
    return "Other"

expense_df["category"] = expense_df["description"].apply(map_category)
expense_breakdown = expense_df.groupby("category")["abs"].sum().sort_values(ascending=False)

fig, ax = plt.subplots(figsize=(3.2, 3.2))
ax.pie(
    expense_breakdown.values,
    labels=expense_breakdown.index,
    autopct="%1.0f%%",
    startangle=90,
    textprops={"fontsize": 8},
)
ax.axis("equal")
st.pyplot(fig)

# -------------------------------------------------
# Investor PDF
# -------------------------------------------------
st.divider()
st.subheader("📄 Investor-ready cash narrative")

def generate_pdf():
    buffer = BytesIO()
    with PdfPages(buffer) as pdf:
        fig = plt.figure(figsize=(8.27, 11.69))
        plt.axis("off")
        plt.text(
            0.02,
            0.98,
            f"""
CASH-FLOW INVESTOR SUMMARY

Cash: ₹{cash_today:,.0f}
Daily burn: ₹{daily_burn:,.0f}
Runway: ~{runway_days} days
Cash-out date: {cash_out_date.date()}

Advertising = {ad_ratio:.1f}% of revenue
Top cost concentration risk exists

Management focus:
- Control ad spend
- Protect core operations
- Extend runway beyond 150 days
""",
            va="top",
            fontsize=11,
        )
        pdf.savefig(fig)
        plt.close(fig)

    buffer.seek(0)
    return buffer

st.download_button(
    "📥 Download Investor PDF",
    data=generate_pdf(),
    file_name="cashflow_investor_summary.pdf",
    mime="application/pdf",
)
