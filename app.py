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
st.set_page_config(
    page_title="AI Cash-Flow COO",
    layout="centered"
)

# =================================================
# UI POLISH (ADD-ONLY, SAFE)
# =================================================
st.markdown("""
<style>
html, body {
    background: linear-gradient(180deg,#eef2ff 0%,#f8fafc 40%,#ffffff 100%);
}
section.main > div { padding-top: 1.5rem; }
h1 { letter-spacing: -0.02em; }
h2, h3 { letter-spacing: -0.01em; }
p { line-height: 1.55; font-size: 0.95rem; }

div[data-testid="stAlert"] { border-radius: 10px; }
button { border-radius: 8px !important; font-weight: 600 !important; }

div[data-testid="stFileUploader"] {
    padding: 1rem;
    border-radius: 10px;
    background-color: #ffffff;
    box-shadow: 0 4px 14px rgba(0,0,0,0.05);
}

/* 🔒 CRITICAL FIX: Prevent Streamlit from hiding sections */
div[data-testid="stMarkdown"],
div[data-testid="stSubheader"] {
    display: block !important;
    visibility: visible !important;
    opacity: 1 !important;
}

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
# WHAT THIS TOOL DOES (RESTORED – UNCHANGED)
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
# SAMPLE CSV DOWNLOAD (UNCHANGED)
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
# FILE UPLOAD (CSV / EXCEL / PDF)
# =================================================
uploaded_file = st.file_uploader(
    "Upload transactions (CSV / Excel / PDF)",
    type=["csv", "xlsx", "pdf"]
)

if not uploaded_file:
    st.stop()

# =================================================
# PDF BANK STATEMENT PARSER (TEXT-BASED)
# =================================================
def parse_bank_pdf(uploaded_file):
    rows = []

    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            if not tables:
                continue

            for table in tables:
                headers = [str(h).lower().strip() if h else "" for h in table[0]]

                for row in table[1:]:
                    if not row or len(row) != len(headers):
                        continue
                    rows.append(dict(zip(headers, row)))

    if not rows:
        raise ValueError("No readable tables found")

    df = pd.DataFrame(rows)
    df.columns = [c.lower().strip() for c in df.columns]

    col_map = {}
    for c in df.columns:
        if "date" in c:
            col_map[c] = "date"
        elif "desc" in c or "narration" in c or "particular" in c:
            col_map[c] = "description"
        elif "debit" in c or c == "dr":
            col_map[c] = "debit"
        elif "credit" in c or c == "cr":
            col_map[c] = "credit"
        elif "amount" in c:
            col_map[c] = "amount"

    df = df.rename(columns=col_map)

    if "amount" not in df.columns:
        df["debit"] = pd.to_numeric(df.get("debit", 0), errors="coerce").fillna(0)
        df["credit"] = pd.to_numeric(df.get("credit", 0), errors="coerce").fillna(0)
        df["amount"] = df["credit"] - df["debit"]

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df["description"] = df.get("description", "Transaction")

    df = df.dropna(subset=["date", "amount"])
    return df[["date", "amount", "description"]]

# =================================================
# READ FILE (SINGLE SOURCE OF TRUTH)
# =================================================
try:
    if uploaded_file.name.lower().endswith(".pdf"):
        df = parse_bank_pdf(uploaded_file)
        st.success("✅ PDF parsed successfully (text-based)")
    elif uploaded_file.name.lower().endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
except Exception:
    st.error("❌ Could not reliably read this file. Upload CSV / Excel for best accuracy.")
    st.stop()

# =================================================
# UNIVERSAL NORMALIZATION LAYER (BASE LOGIC KEPT)
# =================================================
df.columns = [c.lower().strip() for c in df.columns]

if "date" not in df.columns:
    for c in df.columns:
        if "date" in c:
            df["date"] = df[c]
            break

if "description" not in df.columns:
    for c in ["activity", "narration", "comment", "remarks", "particulars"]:
        if c in df.columns:
            df["description"] = df[c]
            break

if "description" not in df.columns:
    df["description"] = "Transaction"

if "amount" not in df.columns:
    debit_col = next((c for c in df.columns if "debit" in c), None)
    credit_col = next((c for c in df.columns if "credit" in c), None)

    if debit_col or credit_col:
        df[debit_col] = pd.to_numeric(df.get(debit_col, 0), errors="coerce").fillna(0)
        df[credit_col] = pd.to_numeric(df.get(credit_col, 0), errors="coerce").fillna(0)
        df["amount"] = df[credit_col] - df[debit_col]

df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
df["date"] = pd.to_datetime(df["date"], errors="coerce")
df = df.dropna(subset=["date", "amount"])

# =================================================
# 🔥 SAFE NORMALIZATION GUARD (DO NOT TOUCH)
# =================================================
if df["amount"].min() < 0 and df["amount"].max() > 0:
    pass
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
) or 1

runway_days = int(cash_today / daily_burn)
cash_out_date = df["date"].max() + timedelta(days=runway_days)

ads_mask = df["description"].str.contains("ad|facebook|google|instagram", case=False, na=False)
ad_spend = abs(df.loc[ads_mask & (df["amount"] < 0), "amount"].sum())
ad_ratio = (ad_spend / inflows * 100) if inflows > 0 else 0

# =================================================
# KPI CARDS
# =================================================
risk_label = "High" if runway_days < 90 else "Medium" if runway_days < 150 else "Low"
c1, c2, c3, c4 = st.columns(4)

for col, title, value in [
    (c1, "Cash on hand", f"₹{cash_today:,.0f}"),
    (c2, "Runway", f"{runway_days} days"),
    (c3, "Daily burn", f"₹{daily_burn:,.0f}"),
    (c4, "Risk level", risk_label),
]:
    with col:
        st.markdown(
            f"<div class='kpi-card'><div class='kpi-title'>{title}</div><div class='kpi-value'>{value}</div></div>",
            unsafe_allow_html=True
        )

st.divider()

# =================================================
# AI COO ANALYSIS (UNCHANGED)
# =================================================
st.subheader("🧠 AI COO Analysis")
st.markdown(f"""
You currently hold **₹{cash_today:,.0f}**.  
Daily burn is **₹{daily_burn:,.0f}** → **{runway_days} days runway**.  
Expected cash-out date: **{cash_out_date.date()}**
""")

# =================================================
# EXPENSE BREAKDOWN
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

Cash: ₹{cash_today:,.0f}
Daily burn: ₹{daily_burn:,.0f}
Runway: {runway_days} days
Cash-out date: {cash_out_date.date()}
Advertising: {ad_ratio:.1f}%
Risk level: {risk_label}
""",
            va="top"
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
