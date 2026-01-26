import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from datetime import timedelta
from io import BytesIO
import numpy as np

st.set_page_config(page_title="AI Cash-Flow COO", layout="centered")

# =================================================
# UI POLISH (GLOBAL, SAFE)
# =================================================
st.markdown("""
<style>
html, body {
    background: linear-gradient(180deg,#0f172a 0%,#020617 100%);
    color: #e5e7eb;
}
section.main > div { padding-top: 1.5rem; }
h1,h2,h3 { letter-spacing: -0.01em; }
p { line-height: 1.55; font-size: 0.95rem; }
.kpi-card {
    background:#020617;
    padding:1rem;
    border-radius:12px;
    border-left:4px solid #6366f1;
    box-shadow:0 6px 18px rgba(0,0,0,.4);
}
.kpi-title { font-size:.75rem; color:#94a3b8; text-transform:uppercase; }
.kpi-value { font-size:1.5rem; font-weight:700; }
.kpi-sub { font-size:.8rem; color:#94a3b8; }
div[data-testid="stAlert"] { border-radius:10px; }
button { border-radius:8px!important; font-weight:600!important; }
</style>
""", unsafe_allow_html=True)

# =================================================
# HEADER
# =================================================
st.title("🧠 Cash-Flow Early Warning System for SMEs")
st.write(
    "Know when your business may face cash trouble — **and exactly what to do next**.\n\n"
    "**No dashboards. No jargon. Just decisions.**"
)

st.divider()

# =================================================
# WHAT THIS TOOL DOES
# =================================================
st.subheader("What this tool does")
st.markdown("""
This system acts like a **virtual COO focused purely on cash discipline**.

- Reads real transaction data (CSV or text-based PDF)
- Identifies true cash burn drivers
- Predicts runway & cash-out date
- Flags structural risks
- Tells you what to cut first
""")

st.divider()

# =================================================
# SAMPLE CSV
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
# FILE UPLOAD
# =================================================
upload_type = st.selectbox(
    "What are you uploading?",
    ["Bank Statement CSV", "Bank Statement PDF (text-based)"]
)

uploaded_file = st.file_uploader(
    "Upload file",
    type=["csv", "pdf"]
)

if not uploaded_file:
    st.stop()

# =================================================
# LOAD DATA
# =================================================
df = None

try:
    if uploaded_file.name.lower().endswith(".csv"):
        df = pd.read_csv(uploaded_file)

    else:
        st.error("PDF parsing depends on bank format. Please upload CSV for guaranteed accuracy.")
        st.stop()

except Exception as e:
    st.error("Failed to read file. Please upload a clean CSV export.")
    st.stop()

required_cols = {"date", "amount", "description"}
if not required_cols.issubset(df.columns):
    st.error("CSV must contain at least: date, amount, description")
    st.stop()

df["date"] = pd.to_datetime(df["date"], errors="coerce")
df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
df = df.dropna(subset=["date", "amount"])

# =================================================
# CORE CALCULATIONS (SAFE)
# =================================================
cash_today = df["amount"].sum()
inflows = df[df["amount"] > 0]["amount"].sum()

expense_df = df[df["amount"] < 0]

if expense_df.empty:
    daily_burn = 0
    runway_days = 999
    cash_out_date = None
else:
    daily_burn = (
        expense_df
        .groupby(expense_df["date"].dt.date)["amount"]
        .sum()
        .abs()
        .mean()
    )
    if pd.isna(daily_burn) or daily_burn <= 0:
        daily_burn = 0
        runway_days = 999
        cash_out_date = None
    else:
        runway_days = int(cash_today / daily_burn)
        cash_out_date = df["date"].max() + timedelta(days=runway_days)

ads_mask = df["description"].str.contains(
    "ad|facebook|google|instagram", case=False, na=False
)
ad_spend = abs(df[ads_mask & (df["amount"] < 0)]["amount"].sum())
ad_ratio = (ad_spend / inflows * 100) if inflows > 0 else 0

# =================================================
# KPI SNAPSHOT
# =================================================
risk_label = "Low"
if runway_days < 90 or ad_ratio > 40:
    risk_label = "High"
elif runway_days < 150 or ad_ratio > 25:
    risk_label = "Medium"

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Cash</div><div class='kpi-value'>₹{cash_today:,.0f}</div></div>", unsafe_allow_html=True)
with c2:
    st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Runway</div><div class='kpi-value'>{'∞' if daily_burn==0 else str(runway_days)+' days'}</div></div>", unsafe_allow_html=True)
with c3:
    st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Daily Burn</div><div class='kpi-value'>₹{daily_burn:,.0f}</div></div>", unsafe_allow_html=True)
with c4:
    st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Risk</div><div class='kpi-value'>{risk_label}</div></div>", unsafe_allow_html=True)

st.divider()

# =================================================
# AI COO ANALYSIS
# =================================================
st.subheader("🧠 AI COO Analysis")

if daily_burn == 0:
    st.warning("No expense transactions detected. Runway cannot be calculated until outflows are present.")
else:
    st.markdown(f"""
You currently hold **₹{cash_today:,.0f}** in net cash.  
Average daily burn is **₹{daily_burn:,.0f}**, giving **~{runway_days} days of runway**.  

Expected cash-out date: **{cash_out_date.date()}**
""")

st.markdown(f"""
Advertising consumes **{ad_ratio:.1f}% of revenue**, making it the largest variable risk driver.
""")

# =================================================
# INVESTOR PDF
# =================================================
st.divider()
st.subheader("📄 Investor-ready summary")

def generate_pdf():
    buf = BytesIO()
    with PdfPages(buf) as pdf:
        fig = plt.figure(figsize=(8.27, 11.69))
        plt.axis("off")
        plt.text(
            0.02, 0.98,
            f"""
CASH-FLOW SUMMARY

Cash: ₹{cash_today:,.0f}
Daily burn: ₹{daily_burn:,.0f}
Runway: {'∞' if daily_burn==0 else str(runway_days)+' days'}

Ad spend: {ad_ratio:.1f}% of revenue
Risk level: {risk_label}
""",
            va="top",
            fontsize=11
        )
        pdf.savefig(fig)
        plt.close(fig)
    buf.seek(0)
    return buf

st.download_button(
    "📥 Download Investor PDF",
    data=generate_pdf(),
    file_name="cashflow_summary.pdf",
    mime="application/pdf",
)
