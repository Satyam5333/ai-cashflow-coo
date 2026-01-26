import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from datetime import timedelta
from io import BytesIO
import re
import pdfplumber

# =================================================
# PAGE CONFIG
# =================================================
st.set_page_config(page_title="AI Cash-Flow COO", layout="centered")

# =================================================
# UI POLISH (ADD-ONLY, SAFE)
# =================================================
st.markdown("""<style>
html, body { background: linear-gradient(180deg,#eef2ff 0%,#f8fafc 40%,#ffffff 100%); }
section.main > div { padding-top: 1.5rem; }
h1 { letter-spacing: -0.02em; }
h2, h3 { letter-spacing: -0.01em; }
p { line-height: 1.55; font-size: 0.95rem; }
div[data-testid="stAlert"] { border-radius: 10px; }
button { border-radius: 8px !important; font-weight: 600 !important; }
div[data-testid="stFileUploader"] {
    padding: 1rem; border-radius: 10px;
    background-color: #ffffff;
    box-shadow: 0 4px 14px rgba(0,0,0,0.05);
}
.kpi-card {
    background: #ffffff;
    padding: 1rem 1.2rem;
    border-radius: 12px;
    box-shadow: 0 6px 18px rgba(0,0,0,0.06);
    border-left: 5px solid #6366f1;
}
.kpi-title { font-size: 0.75rem; color: #6b7280; font-weight: 600; text-transform: uppercase; }
.kpi-value { font-size: 1.5rem; font-weight: 700; margin-top: 0.25rem; }
.kpi-sub { font-size: 0.8rem; color: #6b7280; margin-top: 0.25rem; }
</style>""", unsafe_allow_html=True)

# =================================================
# HEADER
# =================================================
st.title("🧠 Cash-Flow Early Warning System for SMEs")
st.write("Know when your business may face cash trouble — **and exactly what to do next**.")
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
# 🔧 FIX 1 — FILE UPLOADER (MISSING)
# =================================================
uploaded_file = st.file_uploader(
    "Upload transactions (CSV / Excel / PDF)",
    type=["csv", "xlsx", "pdf"]
)

if not uploaded_file:
    st.stop()

# =================================================
# PDF BANK STATEMENT PARSER
# =================================================
def parse_bank_pdf(uploaded_file):
    rows = []
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables() or []:
                headers = [str(h).lower().strip() if h else "" for h in table[0]]
                for row in table[1:]:
                    if len(row) == len(headers):
                        rows.append(dict(zip(headers, row)))

    if not rows:
        raise ValueError("No readable tables found")

    df = pd.DataFrame(rows)
    df.columns = [c.lower().strip() for c in df.columns]

    col_map = {}
    for c in df.columns:
        if "date" in c: col_map[c] = "date"
        elif "desc" in c or "narration" in c: col_map[c] = "description"
        elif "debit" in c: col_map[c] = "debit"
        elif "credit" in c: col_map[c] = "credit"
        elif "amount" in c: col_map[c] = "amount"

    df = df.rename(columns=col_map)

    if "amount" not in df.columns:
        df["amount"] = (
            pd.to_numeric(df.get("credit", 0), errors="coerce").fillna(0)
            - pd.to_numeric(df.get("debit", 0), errors="coerce").fillna(0)
        )

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df["description"] = df.get("description", "Transaction")

    return df.dropna(subset=["date", "amount"])[["date", "amount", "description"]]

# =================================================
# READ FILE (CSV / EXCEL / PDF)
# =================================================
if uploaded_file.name.lower().endswith(".pdf"):
    df = parse_bank_pdf(uploaded_file)
elif uploaded_file.name.lower().endswith(".csv"):
    df = pd.read_csv(uploaded_file)
else:
    df = pd.read_excel(uploaded_file)

# =================================================
# 🔧 FIX 2 — REMOVED DUPLICATE READ FILE BLOCK
# (Nothing else touched below)
# =================================================

df.columns = [c.lower().strip() for c in df.columns]

# =================================================
# UNIVERSAL NORMALIZATION LAYER (ADD-ONLY)
# =================================================

# --- Detect date column
if "date" not in df.columns:
    for c in df.columns:
        if "date" in c:
            df["date"] = df[c]
            break

# --- Detect description column
if "description" not in df.columns:
    for c in ["activity", "narration", "comment", "remarks", "particulars"]:
        if c in df.columns:
            df["description"] = df[c]
            break

if "description" not in df.columns:
    df["description"] = "Transaction"

# --- Detect / build amount column
if "amount" not in df.columns:
    debit_col = next((c for c in df.columns if "debit" in c), None)
    credit_col = next((c for c in df.columns if "credit" in c), None)

    if debit_col or credit_col:
        df[debit_col] = pd.to_numeric(df.get(debit_col, 0), errors="coerce").fillna(0)
        df[credit_col] = pd.to_numeric(df.get(credit_col, 0), errors="coerce").fillna(0)
        df["amount"] = df[credit_col] - df[debit_col]

# --- Final cleanup
df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
df["date"] = pd.to_datetime(df["date"], errors="coerce")
df = df.dropna(subset=["date", "amount"])

required_cols = {"date", "amount", "description"}
if not required_cols.issubset(df.columns):
    st.error("File must contain at least: date, amount, description")
    st.stop()

df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
df["date"] = pd.to_datetime(df["date"], errors="coerce")

# =================================================
# 🔥 SAFE NORMALIZATION GUARD (DO NOT TOUCH)
# =================================================
if df["amount"].min() < 0 and df["amount"].max() > 0:
    pass  # already normalized

elif "debit" in df.columns or "credit" in df.columns:
    df["amount"] = (
        df.get("credit", 0).fillna(0)
        - df.get("debit", 0).fillna(0)
    )

elif "type" in df.columns:
    df["type"] = df["type"].astype(str).str.lower()
    df["amount"] = df.apply(
        lambda r: -abs(r["amount"])
        if any(x in r["type"] for x in ["outflow", "dr", "debit"])
        else abs(r["amount"]),
        axis=1
    )

else:
    expense_keywords = [
        "rent","salary","ads","advertising","google","facebook",
        "emi","interest","gst","tax","electricity","internet",
        "aws","razorpay","office","travel"
    ]
    df["amount"] = df.apply(
        lambda r: -abs(r["amount"])
        if any(k in str(r["description"]).lower() for k in expense_keywords)
        else abs(r["amount"]),
        axis=1
    )

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

if pd.isna(daily_burn) or daily_burn == 0:
    daily_burn = 1

runway_days = int(cash_today / daily_burn)
cash_out_date = df["date"].max() + timedelta(days=runway_days)

ads_mask = df["description"].str.contains(
    "ad|facebook|google|instagram", case=False, na=False
)
ad_spend = abs(df.loc[ads_mask & (df["amount"] < 0), "amount"].sum())
ad_ratio = (ad_spend / inflows * 100) if inflows > 0 else 0

# =================================================
# KPI CARDS
# =================================================
risk_label = "High" if runway_days < 90 else "Medium" if runway_days < 150 else "Low"

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(
        f"<div class='kpi-card'><div class='kpi-title'>Cash on hand</div><div class='kpi-value'>₹{cash_today:,.0f}</div></div>",
        unsafe_allow_html=True
    )

with c2:
    st.markdown(
        f"<div class='kpi-card'><div class='kpi-title'>Runway</div><div class='kpi-value'>{runway_days} days</div></div>",
        unsafe_allow_html=True
    )

with c3:
    st.markdown(
        f"<div class='kpi-card'><div class='kpi-title'>Daily burn</div><div class='kpi-value'>₹{daily_burn:,.0f}</div></div>",
        unsafe_allow_html=True
    )

with c4:
    st.markdown(
        f"<div class='kpi-card'><div class='kpi-title'>Risk level</div><div class='kpi-value'>{risk_label}</div></div>",
        unsafe_allow_html=True
    )

st.divider()

# =================================================
# AI COO ANALYSIS
# =================================================
st.subheader("🧠 AI COO Analysis")

st.markdown(f"""
### Cash position
You currently hold **₹{cash_today:,.0f}** in net cash.  
Average daily burn is **₹{daily_burn:,.0f}**, giving **~{runway_days} days runway**.  
Expected cash-out date: **{cash_out_date.date()}**
""")

st.markdown(f"""
### Spending structure insight
Advertising consumes **{ad_ratio:.1f}% of revenue**.  
This creates volatility if ROI drops suddenly.
""")

st.markdown("""
### What to cut first
1. Advertising spend  
2. Variable vendors  
3. Discretionary costs  

Protect salaries and core operations.
""")

# =================================================
# FOUNDER ACTION PLAN
# =================================================
st.divider()
st.subheader("🧭 Founder Action Plan (Next 30 Days)")

st.markdown(f"""
- Cap advertising spend  
- Freeze new fixed commitments  
- Renegotiate variable vendors  

⚠️ No action → risk increases in ~{int(runway_days*0.75)} days
""")

st.markdown(f"### 🎯 Decision confidence score: **{7.8 if ad_ratio < 30 else 6.4}/10**")

# =================================================
# EXPENSE CATEGORY BREAKDOWN
# =================================================
st.divider()
st.subheader("📉 Expense category breakdown")

expense_df = df[df["amount"] < 0].copy()
expense_df["abs"] = expense_df["amount"].abs()

def map_category(desc):
    d = str(desc).lower()
    if "ad" in d or "facebook" in d or "google" in d:
        return "Advertising"
    if "salary" in d:
        return "Salary"
    if "rent" in d:
        return "Rent"
    return "Other"

expense_df["category"] = expense_df["description"].apply(map_category)
expense_breakdown = expense_df.groupby("category")["abs"].sum()

fig, ax = plt.subplots(figsize=(4,4))
ax.pie(expense_breakdown, labels=expense_breakdown.index, autopct="%1.0f%%")
ax.axis("equal")
st.pyplot(fig)

# =================================================
# INVESTOR PDF
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
Daily burn: ₹{daily_burn:,.0f}
Runway: {runway_days} days
Cash-out date: {cash_out_date.date()}

Advertising share: {ad_ratio:.1f}%
Risk level: {risk_label}
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
