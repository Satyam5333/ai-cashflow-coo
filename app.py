import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import pdfplumber
from matplotlib.backends.backend_pdf import PdfPages
from datetime import timedelta
from io import BytesIO

st.set_page_config(page_title="AI Cash-Flow COO", layout="centered")

# =================================================
# HELPER FUNCTIONS (ADD-ONLY)
# =================================================
def detect_column(df, keywords):
    for col in df.columns:
        col_lower = col.lower()
        if any(k in col_lower for k in keywords):
            return col
    return None


def normalize_bank_statement(df):
    date_col = detect_column(df, ["date"])
    desc_col = detect_column(df, ["narration", "remark", "particular", "description"])
    debit_col = detect_column(df, ["debit", "withdrawal", "dr"])
    credit_col = detect_column(df, ["credit", "deposit", "cr"])
    amount_col = detect_column(df, ["amount"])

    rows = []

    for _, row in df.iterrows():
        try:
            date = row[date_col] if date_col else None
            desc = row[desc_col] if desc_col else "Bank transaction"

            if debit_col and pd.notna(row[debit_col]):
                amt = -abs(float(row[debit_col]))
            elif credit_col and pd.notna(row[credit_col]):
                amt = abs(float(row[credit_col]))
            elif amount_col and pd.notna(row[amount_col]):
                amt = float(row[amount_col])
            else:
                continue

            rows.append({
                "date": date,
                "amount": amt,
                "type": "Inflow" if amt > 0 else "Outflow",
                "description": str(desc)
            })
        except Exception:
            continue

    return pd.DataFrame(rows)


def extract_table_from_pdf(uploaded_file):
    rows = []
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages[:2]:
            table = page.extract_table()
            if table:
                rows.extend(table)

    if not rows or len(rows) < 2:
        return None

    headers = rows[0]
    data = rows[1:]
    return pd.DataFrame(data, columns=headers)

# =================================================
# UI POLISH (UNCHANGED)
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

.kpi-card {
    background: #ffffff;
    padding: 1rem 1.2rem;
    border-radius: 12px;
    box-shadow: 0 6px 18px rgba(0,0,0,0.06);
    border-left: 5px solid #6366f1;
}
.kpi-title { font-size: 0.75rem; color: #6b7280; font-weight: 600; }
.kpi-value { font-size: 1.5rem; font-weight: 700; margin-top: 0.25rem; }
.kpi-sub { font-size: 0.8rem; color: #6b7280; }

div[data-testid="stAlert"] { border-radius: 10px; }
button { border-radius: 8px !important; font-weight: 600 !important; }
div[data-testid="stFileUploader"] {
    padding: 1rem;
    border-radius: 10px;
    background-color: #ffffff;
    box-shadow: 0 4px 14px rgba(0,0,0,0.05);
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
# TOOL EXPLANATION
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
# SOURCE TYPE
# =================================================
source_type = st.selectbox(
    "What are you uploading?",
    ["Bank Statement", "Accounting / Tally Export", "Custom CSV (already formatted)"]
)

# =================================================
# FILE UPLOAD (CSV + PDF)
# =================================================
uploaded_file = st.file_uploader(
    "Upload bank statement (CSV or PDF)",
    type=["csv", "pdf"]
)

if not uploaded_file:
    st.stop()

# =================================================
# FILE READING LOGIC
# =================================================
if uploaded_file.name.lower().endswith(".pdf"):
    raw_df = extract_table_from_pdf(uploaded_file)
    if raw_df is None:
        st.error(
            "This PDF appears to be scanned or unreadable.\n\n"
            "Please upload a CSV or Excel bank statement."
        )
        st.stop()
else:
    raw_df = pd.read_csv(uploaded_file)

# =================================================
# NORMALIZATION
# =================================================
if source_type == "Bank Statement":
    df = normalize_bank_statement(raw_df)
    st.success(f"Bank statement processed: {len(df)} transactions understood.")
else:
    df = raw_df.copy()

required_cols = {"date", "amount", "type", "description"}
if not required_cols.issubset(df.columns):
    st.error("Uploaded file could not be understood.")
    st.stop()

df["date"] = pd.to_datetime(df["date"], errors="coerce")
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
# KPI SNAPSHOT
# =================================================
if runway_days < 90 or ad_ratio > 40:
    risk_label = "High"
elif runway_days < 150 or ad_ratio > 25:
    risk_label = "Medium"
else:
    risk_label = "Low"

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Cash</div><div class='kpi-value'>₹{cash_today:,.0f}</div></div>", unsafe_allow_html=True)
with c2:
    st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Runway</div><div class='kpi-value'>{runway_days} days</div></div>", unsafe_allow_html=True)
with c3:
    st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Daily Burn</div><div class='kpi-value'>₹{daily_burn:,.0f}</div></div>", unsafe_allow_html=True)
with c4:
    st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Risk</div><div class='kpi-value'>{risk_label}</div></div>", unsafe_allow_html=True)

st.divider()

# =================================================
# AI COO SUMMARY
# =================================================
st.subheader("🧠 AI COO Analysis")

st.markdown(f"""
You have **₹{cash_today:,.0f}** in net cash.

At the current burn of **₹{daily_burn:,.0f}/day**, your runway is **~{runway_days} days**  
Expected cash-out date: **{cash_out_date.date()}**

Advertising consumes **{ad_ratio:.1f}% of revenue**, making it the largest variable risk.
""")

# =================================================
# EXPENSE BREAKDOWN
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
expense_breakdown = expense_df.groupby("category")["abs"].sum()

fig, ax = plt.subplots(figsize=(3.5, 3.5))
ax.pie(expense_breakdown.values, labels=expense_breakdown.index, autopct="%1.0f%%")
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
CASH-FLOW SUMMARY

Cash: ₹{cash_today:,.0f}
Burn: ₹{daily_burn:,.0f}
Runway: {runway_days} days
Cash-out date: {cash_out_date.date()}
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
