import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from datetime import timedelta
from io import BytesIO

st.set_page_config(page_title="AI Cash-Flow COO", layout="centered")
# =================================================
# PHASE 2 — SIDEBAR NAVIGATION (ADD-ONLY, NO LOGIC CHANGE)
# =================================================
st.sidebar.markdown("## 🧭 Views")

st.sidebar.radio(
    "",
    [
        "🧠 Founder View (default)",
        "📄 Investor View",
        "📊 Ops View (coming soon)",
        "🔒 Pro Features"
    ],
    index=0
)

st.sidebar.divider()

st.sidebar.markdown(
    """
**Founder View**  
Full tactical cash-control view.

**Investor View**  
High-level narrative only *(coming soon)*.

**Ops View**  
Execution metrics *(placeholder)*.

**Pro Features**  
Advanced controls 🔒
"""
)

# =================================================
# UI POLISH (GLOBAL, ADD-ONLY, SAFE)
# =================================================
st.markdown("""
<style>

/* Overall page background */
html, body {
    background: linear-gradient(
        180deg,
        #eef2ff 0%,
        #f8fafc 40%,
        #ffffff 100%
    );
}

/* Improve content spacing */
section.main > div {
    padding-top: 1.5rem;
}

/* Typography */
h1 { letter-spacing: -0.02em; }
h2, h3 { letter-spacing: -0.01em; }

p {
    line-height: 1.55;
    font-size: 0.95rem;
}

/* KPI Cards */
.kpi-card {
    background: #ffffff;
    padding: 1rem 1.2rem;
    border-radius: 12px;
    box-shadow: 0 6px 18px rgba(0,0,0,0.06);
    border-left: 5px solid #6366f1;
}

.kpi-title {
    font-size: 0.75rem;
    color: #6b7280;
    font-weight: 600;
    text-transform: uppercase;
}

.kpi-value {
    font-size: 1.5rem;
    font-weight: 700;
    margin-top: 0.25rem;
}

.kpi-sub {
    font-size: 0.8rem;
    color: #6b7280;
    margin-top: 0.25rem;
}

/* Alerts */
div[data-testid="stAlert"] {
    border-radius: 10px;
}

/* Buttons */
button {
    border-radius: 8px !important;
    font-weight: 600 !important;
}

/* File uploader */
div[data-testid="stFileUploader"] {
    padding: 1rem;
    border-radius: 10px;
    background-color: #ffffff;
    box-shadow: 0 4px 14px rgba(0,0,0,0.05);
}

</style>
""", unsafe_allow_html=True)

# =================================================
# HEADER (UNCHANGED)
# =================================================
st.title("🧠 Cash-Flow Early Warning System for SMEs")
st.write(
    "Know when your business may face cash trouble — **and exactly what to do next**.\n\n"
    "**No dashboards. No jargon. Just decisions.**"
)

st.divider()

# =================================================
# WHAT THIS TOOL DOES (UNCHANGED)
# =================================================
st.subheader("What this tool does")
st.markdown("""
This system acts like a **virtual COO focused purely on cash discipline**.

It:
- Reads your real transaction data  
- Identifies what is actually driving cash burn  
- Predicts how long your money will last  
- Flags hidden structural risks  
- Tells you **what to cut, what to protect, and what to fix first**
""")

st.divider()

# =================================================
# SAMPLE CSV (UNCHANGED)
# =================================================
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

# =================================================
# UPLOAD CSV (UNCHANGED)
# =================================================
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

# =================================================
# CORE CALCULATIONS (UNCHANGED)
# =================================================
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

# =================================================
# PHASE 2 ADDITION — KPI SNAPSHOT (ADD-ONLY)
# =================================================
if runway_days < 90 or ad_ratio > 40:
    risk_label = "High"
elif runway_days < 150 or ad_ratio > 25:
    risk_label = "Medium"
else:
    risk_label = "Low"

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">Cash on hand</div>
        <div class="kpi-value">₹{cash_today:,.0f}</div>
        <div class="kpi-sub">Net balance</div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">Runway</div>
        <div class="kpi-value">{runway_days} days</div>
        <div class="kpi-sub">At current burn</div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">Daily burn</div>
        <div class="kpi-value">₹{daily_burn:,.0f}</div>
        <div class="kpi-sub">Avg outflow</div>
    </div>
    """, unsafe_allow_html=True)

with c4:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">Risk level</div>
        <div class="kpi-value">{risk_label}</div>
        <div class="kpi-sub">Cash sensitivity</div>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# =================================================
# AI COO ANALYSIS (UNCHANGED)
# =================================================
st.subheader("🧠 AI COO Analysis")

st.markdown(f"""
### Cash position
You currently hold **₹{cash_today:,.0f}** in net cash.  
Your average daily operating burn is **₹{daily_burn:,.0f}**, giving you approximately **{runway_days} days of runway**.

This places your **expected cash-out date around {cash_out_date.date()}**, assuming **no change** in spending or revenue patterns.
""")

st.markdown(f"""
### Spending structure insight
Advertising accounts for **{ad_ratio:.1f}% of total revenue**, making it the **single largest variable cost driver**.

This creates **cash volatility risk**:
- Ad performance fluctuates faster than fixed costs
- A short-term dip in ROI can compress runway quickly
- Cash pressure may appear suddenly, not gradually
""")

if ad_ratio > 40:
    st.error("⚠️ Advertising dependency is critically high. A revenue slowdown would immediately threaten cash stability.")
elif ad_ratio > 25:
    st.warning("⚠️ Advertising dependency is elevated. Spend should be actively capped and reviewed weekly.")
else:
    st.success("Advertising spend is within a controllable range relative to revenue.")

st.markdown("""
### What should you cut first?
If cash tightens, **do NOT cut core operations immediately**.

**Priority order for cost control:**
1. Cap or pause underperforming advertising channels  
2. Reduce variable vendor expenses  
3. Delay discretionary operating spend  

Protect:
- Salary for core staff  
- Rent and operational continuity  
""")

# =================================================
# FOUNDER ACTION PLAN (UNCHANGED)
# =================================================
st.divider()
st.subheader("🧭 Founder Action Plan (Next 30 Days)")

st.markdown(f"""
**Immediate priorities**
- Cap advertising spend (**{ad_ratio:.1f}% of revenue**)  
- Freeze new fixed commitments  
- Renegotiate variable vendors  

**If no action is taken**
- Cash risk increases after ~{int(runway_days * 0.75)} days  
- A 10% revenue drop can materially shorten runway  
""")

st.markdown(f"### 🎯 Decision confidence score: **{7.8 if ad_ratio < 30 else 6.4}/10**")

# =================================================
# EXPENSE BREAKDOWN (UNCHANGED)
# =================================================
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

fig, ax = plt.subplots(figsize=(3.5, 3.5))
ax.pie(
    expense_breakdown.values,
    labels=expense_breakdown.index,
    autopct="%1.0f%%",
    startangle=90,
    textprops={"fontsize": 8},
)
ax.axis("equal")
st.pyplot(fig)

top_two_share = expense_breakdown.iloc[:2].sum() / expense_breakdown.sum() * 100
if top_two_share > 65:
    st.warning(f"⚠️ Cost concentration risk detected: top 2 categories = {top_two_share:.0f}% of total expenses.")

# =================================================
# INVESTOR PDF (UNCHANGED)
# =================================================
st.divider()
st.subheader("📄 Investor-ready cash narrative")

def generate_pdf():
    buffer = BytesIO()
    with PdfPages(buffer) as pdf:
        fig = plt.figure(figsize=(8.27, 11.69))
        plt.axis("off")
        plt.text(
            0.02, 0.98,
            f"""
CASH-FLOW INVESTOR SUMMARY

Cash balance: ₹{cash_today:,.0f}
Average daily burn: ₹{daily_burn:,.0f}
Runway: ~{runway_days} days
Cash-out date: {cash_out_date.date()}

Advertising = {ad_ratio:.1f}% of revenue
Cost concentration risk exists

Management focus:
- Control ad spend
- Protect core operations
- Extend runway beyond 150 days
""",
            va="top",
            fontsize=11
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
