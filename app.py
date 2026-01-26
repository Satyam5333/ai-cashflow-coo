import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from datetime import timedelta
from io import BytesIO
import pdfplumber

# =================================================
# PAGE CONFIG
# =================================================
st.set_page_config(page_title="AI Cash-Flow COO", layout="centered")

# =================================================
# UI POLISH (UNCHANGED)
# =================================================
st.markdown("""
<style>
html, body {
    background: linear-gradient(180deg,#0f172a 0%,#020617 100%);
    color: #e5e7eb;
}
section.main > div { padding-top: 1.5rem; }
h1,h2,h3 { letter-spacing:-0.02em; }
.kpi-card {
    background:#020617;
    padding:1rem;
    border-radius:12px;
    border-left:4px solid #6366f1;
}
.kpi-title { font-size:0.7rem;color:#9ca3af;text-transform:uppercase;font-weight:600; }
.kpi-value { font-size:1.4rem;font-weight:700; }
.kpi-sub { font-size:0.8rem;color:#9ca3af; }
div[data-testid="stAlert"] { border-radius:10px; }
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

It:
- Reads real transaction data (CSV / Excel / supported PDFs)
- Identifies what is actually driving cash burn
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
st.download_button("📥 Download sample transactions CSV", sample_csv, "sample_transactions.csv")
st.divider()

# =================================================
# UPLOAD TYPE
# =================================================
upload_type = st.selectbox(
    "What are you uploading?",
    ["Bank Statement CSV", "Bank Statement PDF (ICICI only – text based)"]
)

uploaded_file = st.file_uploader(
    "Upload file",
    type=["csv", "pdf"]
)

if not uploaded_file:
    st.stop()

# =================================================
# PDF PARSER — ICICI BANK ONLY (STABLE)
# =================================================
def parse_icici_pdf(file):
    rows = []

    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if not table:
                continue

            for row in table[1:]:
                if not row or len(row) < 4:
                    continue

                date, desc, amt, txn_type = row[:4]

                try:
                    amount = float(str(amt).replace(",", "").strip())
                except:
                    continue

                if txn_type.strip().upper() == "DR":
                    amount = -amount

                rows.append({
                    "date": date.strip(),
                    "amount": amount,
                    "description": desc.strip()
                })

    if not rows:
        return None

    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date", "amount"])
    return df

# =================================================
# LOAD DATA
# =================================================
if upload_type == "Bank Statement CSV":
    try:
        df = pd.read_csv(uploaded_file)
    except UnicodeDecodeError:
        df = pd.read_csv(uploaded_file, encoding="latin1")

elif upload_type == "Bank Statement PDF (ICICI only – text based)":
    if "icici" not in uploaded_file.name.lower():
        st.error("Only ICICI Bank PDFs are supported currently. Please upload CSV.")
        st.stop()

    df = parse_icici_pdf(uploaded_file)
    if df is None or df.empty:
        st.error("Unable to parse ICICI PDF. Please upload CSV for guaranteed accuracy.")
        st.stop()

# =================================================
# NORMALIZE DATA (UNCHANGED LOGIC)
# =================================================
df["amount"] = df["amount"].astype(float)
df["date"] = pd.to_datetime(df["date"])

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

daily_burn = daily_burn if daily_burn > 0 else 1
runway_days = int(cash_today / daily_burn)
cash_out_date = df["date"].max() + timedelta(days=runway_days)

ads_mask = df["description"].str.contains("ad|facebook|google|instagram", case=False, na=False)
ad_spend = abs(df[ads_mask & (df["amount"] < 0)]["amount"].sum())
ad_ratio = (ad_spend / inflows * 100) if inflows > 0 else 0

# =================================================
# KPI CARDS
# =================================================
risk = "Low"
if runway_days < 90 or ad_ratio > 40:
    risk = "High"
elif runway_days < 150 or ad_ratio > 25:
    risk = "Medium"

c1,c2,c3,c4 = st.columns(4)

with c1:
    st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Cash</div><div class='kpi-value'>₹{cash_today:,.0f}</div></div>", unsafe_allow_html=True)
with c2:
    st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Runway</div><div class='kpi-value'>{runway_days} days</div></div>", unsafe_allow_html=True)
with c3:
    st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Daily Burn</div><div class='kpi-value'>₹{daily_burn:,.0f}</div></div>", unsafe_allow_html=True)
with c4:
    st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Risk</div><div class='kpi-value'>{risk}</div></div>", unsafe_allow_html=True)

st.divider()

# =================================================
# AI COO ANALYSIS (UNCHANGED)
# =================================================
st.subheader("🧠 AI COO Analysis")
st.markdown(f"""
You currently hold **₹{cash_today:,.0f}** in cash.

Average daily burn is **₹{daily_burn:,.0f}**, giving you **~{runway_days} days of runway**.

Expected cash-out date: **{cash_out_date.date()}**
""")

st.markdown(f"""
Advertising consumes **{ad_ratio:.1f}% of revenue**.

**What to cut first:**
1. Advertising spend
2. Variable vendors
3. Discretionary costs

Protect salaries & core operations.
""")

# =================================================
# INVESTOR PDF (UNCHANGED)
# =================================================
def generate_pdf():
    buffer = BytesIO()
    with PdfPages(buffer) as pdf:
        fig = plt.figure(figsize=(8.27,11.69))
        plt.axis("off")
        plt.text(0.02,0.98,f"""
CASH-FLOW INVESTOR SUMMARY

Cash: ₹{cash_today:,.0f}
Daily burn: ₹{daily_burn:,.0f}
Runway: {runway_days} days
Cash-out date: {cash_out_date.date()}
Risk level: {risk}
""",va="top",fontsize=11)
        pdf.savefig(fig)
        plt.close(fig)
    buffer.seek(0)
    return buffer

st.download_button(
    "📥 Download Investor PDF",
    generate_pdf(),
    "cashflow_investor_summary.pdf",
    mime="application/pdf"
)
