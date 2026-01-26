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
# UI POLISH (SAFE)
# =================================================
st.markdown("""
<style>
html, body {
    background: linear-gradient(180deg,#0f172a 0%,#020617 100%);
    color: #e5e7eb;
}
section.main > div { padding-top: 1.5rem; }
h1,h2,h3 { letter-spacing:-0.02em; }
p { line-height:1.6; font-size:0.95rem; }

.kpi-card{
    background:#020617;
    padding:1rem;
    border-radius:12px;
    border-left:4px solid #6366f1;
}
.kpi-title{font-size:0.7rem;color:#9ca3af;font-weight:700;}
.kpi-value{font-size:1.5rem;font-weight:700;}
.kpi-sub{font-size:0.8rem;color:#9ca3af;}

div[data-testid="stAlert"]{border-radius:10px;}
button{border-radius:8px!important;font-weight:600!important;}
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
# TOOL DESCRIPTION
# =================================================
st.subheader("What this tool does")
st.markdown("""
This system acts like a **virtual COO focused purely on cash discipline**.

It:
- Reads real transaction data (CSV or PDF)  
- Identifies what is driving cash burn  
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
# UPLOAD
# =================================================
upload_type = st.selectbox(
    "What are you uploading?",
    ["Bank Statement / Accounting CSV", "Bank Statement PDF (text-based)"]
)

uploaded_file = st.file_uploader(
    "Upload file",
    type=["csv", "pdf"]
)

if not uploaded_file:
    st.stop()

# =================================================
# PDF PARSER (FIXED)
# =================================================
def extract_table_from_pdf(uploaded_file):
    rows = []

    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages[:3]:
            table = page.extract_table()
            if table:
                rows.extend(table)

    if not rows or len(rows) < 2:
        return None

    headers = rows[0]
    header_len = len(headers)
    cleaned = []

    for row in rows[1:]:
        if not row:
            continue
        if len(row) < header_len:
            row = row + [None] * (header_len - len(row))
        elif len(row) > header_len:
            row = row[:header_len]
        cleaned.append(row)

    return pd.DataFrame(cleaned, columns=headers)

# =================================================
# LOAD DATA
# =================================================
if upload_type.startswith("Bank Statement PDF"):
    raw_df = extract_table_from_pdf(uploaded_file)
    if raw_df is None:
        st.error("Could not read table from PDF. Only text-based PDFs are supported.")
        st.stop()

    # VERY basic normalization (bank PDFs differ wildly)
    raw_df.columns = [c.lower() for c in raw_df.columns]

    # heuristic mapping
    date_col = next((c for c in raw_df.columns if "date" in c), None)
    amt_col = next((c for c in raw_df.columns if "amount" in c or "debit" in c or "credit" in c), None)
    desc_col = next((c for c in raw_df.columns if "desc" in c or "particular" in c), None)

    if not date_col or not amt_col:
        st.error("PDF format not recognized. Please upload CSV for this bank.")
        st.stop()

    df = pd.DataFrame()
    df["date"] = pd.to_datetime(raw_df[date_col], errors="coerce")
    df["amount"] = pd.to_numeric(raw_df[amt_col].str.replace(",", ""), errors="coerce")
    df["description"] = raw_df[desc_col] if desc_col else "Transaction"
    df["type"] = df["amount"].apply(lambda x: "Inflow" if x > 0 else "Outflow")

else:
    df = pd.read_csv(uploaded_file)

    required = {"date", "amount", "description"}
    if not required.issubset(df.columns):
        st.error("CSV must contain: date, amount, description")
        st.stop()

    df["date"] = pd.to_datetime(df["date"])
    df["amount"] = df["amount"].astype(float)

# =================================================
# CORE CALCULATIONS
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

runway_days = int(cash_today / daily_burn) if daily_burn else 999
cash_out_date = df["date"].max() + timedelta(days=runway_days)

ads_mask = df["description"].str.contains("ad|facebook|google|instagram", case=False, na=False)
ad_spend = abs(df[ads_mask & (df["amount"] < 0)]["amount"].sum())
ad_ratio = (ad_spend / inflows * 100) if inflows else 0

# =================================================
# KPI CARDS
# =================================================
risk = "Low"
if runway_days < 90 or ad_ratio > 40:
    risk = "High"
elif runway_days < 150 or ad_ratio > 25:
    risk = "Medium"

c1,c2,c3,c4 = st.columns(4)

def kpi(col,title,value,sub):
    with col:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">{title}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-sub">{sub}</div>
        </div>
        """, unsafe_allow_html=True)

kpi(c1,"Cash on hand",f"₹{cash_today:,.0f}","Net balance")
kpi(c2,"Runway",f"{runway_days} days","At current burn")
kpi(c3,"Daily burn",f"₹{daily_burn:,.0f}","Avg outflow")
kpi(c4,"Risk level",risk,"Cash sensitivity")

st.divider()

# =================================================
# AI COO ANALYSIS
# =================================================
st.subheader("🧠 AI COO Analysis")

st.markdown(f"""
**Cash position**  
You hold **₹{cash_today:,.0f}** with a daily burn of **₹{daily_burn:,.0f}**, giving **~{runway_days} days** runway.

Expected cash-out date: **{cash_out_date.date()}**

**Spending structure**
Advertising consumes **{ad_ratio:.1f}% of revenue**, making it the largest variable risk.

**What to cut first**
1. Advertising before fixed costs  
2. Variable vendors  
3. Discretionary spend  

Protect salaries and core ops.
""")

# =================================================
# INVESTOR PDF
# =================================================
st.divider()
st.subheader("📄 Investor-ready cash narrative")

def generate_pdf():
    buf = BytesIO()
    with PdfPages(buf) as pdf:
        fig = plt.figure(figsize=(8.27,11.69))
        plt.axis("off")
        plt.text(
            0.02,0.98,
            f"""
CASH-FLOW SUMMARY

Cash: ₹{cash_today:,.0f}
Daily burn: ₹{daily_burn:,.0f}
Runway: {runway_days} days
Cash-out date: {cash_out_date.date()}

Advertising share: {ad_ratio:.1f}%
Risk level: {risk}

Action:
- Control variable spend
- Extend runway >150 days
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
    generate_pdf(),
    "cashflow_investor_summary.pdf",
    mime="application/pdf"
)
