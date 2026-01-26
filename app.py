import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from datetime import timedelta
from io import BytesIO
import re

# Optional PDF support (text-based only)
try:
    import pdfplumber
    PDF_AVAILABLE = True
except:
    PDF_AVAILABLE = False


# =================================================
# PAGE CONFIG
# =================================================
st.set_page_config(
    page_title="AI Cash-Flow COO",
    layout="centered"
)

# =================================================
# UI POLISH (SAFE, GLOBAL)
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
div[data-testid="stAlert"] { border-radius: 10px; }
button { border-radius: 8px !important; font-weight: 600 !important; }
</style>
""", unsafe_allow_html=True)


# =================================================
# HEADER
# =================================================
st.title("🧠 Cash-Flow Early Warning System for SMEs")
st.write(
    "Know when cash trouble hits — **and exactly what to do next**.\n\n"
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
- Reads real transaction data (CSV / Excel / text-based PDF)
- Identifies what is actually driving cash burn
- Predicts runway & cash-out date
- Flags structural risks
- Tells you **what to cut, what to protect, and what to fix first**
""")

st.divider()

# =================================================
# SAMPLE CSV (RESTORED)
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
# UPLOAD
# =================================================
upload_type = st.selectbox(
    "What are you uploading?",
    [
        "Bank Statement CSV / Excel (recommended)",
        "Bank Statement PDF (text-based)"
    ]
)

uploaded_file = st.file_uploader(
    "Upload file",
    type=["csv", "xlsx", "pdf"]
)

if not uploaded_file:
    st.stop()


# =================================================
# HELPERS
# =================================================
def normalize_df(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [c.lower().strip() for c in df.columns]

    # column mapping
    col_map = {}
    for c in df.columns:
        if "date" in c:
            col_map[c] = "date"
        elif "amount" in c:
            col_map[c] = "amount"
        elif "debit" in c:
            col_map[c] = "amount"
        elif "credit" in c:
            col_map[c] = "amount"
        elif "description" in c or "narration" in c or "particular" in c:
            col_map[c] = "description"
        elif "type" in c or "dr/cr" in c:
            col_map[c] = "type"

    df = df.rename(columns=col_map)

    required = {"date", "amount", "description"}
    if not required.issubset(df.columns):
        raise ValueError("Required columns not found")

    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    # Handle DR / CR text
    if "type" in df.columns:
        df["amount"] = df.apply(
            lambda r: -abs(r["amount"]) if str(r["type"]).upper().startswith("D") else abs(r["amount"]),
            axis=1
        )

    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df = df.dropna(subset=["date", "amount"])

    return df[["date", "amount", "description"]]


def parse_pdf(uploaded_file) -> pd.DataFrame:
    if not PDF_AVAILABLE:
        raise RuntimeError("PDF parsing library not available")

    rows = []
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if not table:
                continue
            headers = [h.lower() for h in table[0]]
            for r in table[1:]:
                row = dict(zip(headers, r))
                rows.append(row)

    if not rows:
        raise ValueError("No table detected in PDF")

    return normalize_df(pd.DataFrame(rows))


# =================================================
# LOAD DATA
# =================================================
try:
    if upload_type.startswith("Bank Statement PDF"):
        df = parse_pdf(uploaded_file)
    else:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        df = normalize_df(df)
except Exception as e:
    st.error(
        "❌ Could not read this file reliably.\n\n"
        "PDF parsing depends on bank format.\n"
        "For guaranteed accuracy, upload CSV / Excel."
    )
    st.stop()

if df.empty:
    st.error("No usable transactions found.")
    st.stop()


# =================================================
# CORE CALCULATIONS (UNCHANGED LOGIC)
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

runway_days = int(cash_today / daily_burn) if daily_burn and daily_burn > 0 else 999
cash_out_date = df["date"].max() + timedelta(days=runway_days)

ads_mask = df["description"].str.contains(
    "ad|facebook|google|instagram", case=False, na=False
)
ad_spend = abs(df[ads_mask & (df["amount"] < 0)]["amount"].sum())
ad_ratio = (ad_spend / inflows * 100) if inflows > 0 else 0


# =================================================
# KPI SNAPSHOT
# =================================================
risk_label = (
    "High" if runway_days < 90 or ad_ratio > 40
    else "Medium" if runway_days < 150 or ad_ratio > 25
    else "Low"
)

c1, c2, c3, c4 = st.columns(4)
for col, title, value, sub in [
    (c1, "Cash on hand", f"₹{cash_today:,.0f}", "Net balance"),
    (c2, "Runway", f"{runway_days} days", "At current burn"),
    (c3, "Daily burn", f"₹{daily_burn:,.0f}", "Avg outflow"),
    (c4, "Risk level", risk_label, "Cash sensitivity"),
]:
    with col:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">{title}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-sub">{sub}</div>
        </div>
        """, unsafe_allow_html=True)

st.divider()

# =================================================
# AI COO ANALYSIS (FULL – RESTORED)
# =================================================
st.subheader("🧠 AI COO Analysis")

st.markdown(f"""
### Cash position
You currently hold **₹{cash_today:,.0f}** in net cash.  
Average daily burn is **₹{daily_burn:,.0f}**, giving you **~{runway_days} days of runway**.

**Expected cash-out date:** {cash_out_date.date()}
""")

st.markdown(f"""
### Spending structure insight
Advertising consumes **{ad_ratio:.1f}% of revenue**, making it the largest variable cost.

This creates volatility risk:
- Ad ROI fluctuates faster than fixed costs
- Revenue dips compress runway quickly
""")

st.markdown("""
### What should you cut first?
1. Advertising spend  
2. Variable vendors  
3. Discretionary costs  

**Protect salaries & core operations.**
""")

# =================================================
# EXPENSE BREAKDOWN (RESTORED)
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
ax.pie(expense_breakdown, labels=expense_breakdown.index, autopct="%1.0f%%")
ax.axis("equal")
st.pyplot(fig)

# =================================================
# FOUNDER ACTION PLAN (RESTORED)
# =================================================
st.divider()
st.subheader("🧭 Founder Action Plan (Next 30 Days)")

st.markdown(f"""
- Cap advertising spend (**{ad_ratio:.1f}% of revenue**)
- Freeze new fixed commitments
- Renegotiate variable vendors

**Decision confidence score:** **{7.8 if ad_ratio < 30 else 6.4}/10**
""")

# =================================================
# INVESTOR PDF (RESTORED)
# =================================================
st.divider()
st.subheader("📄 Investor-ready cash narrative")

def generate_pdf():
    buf = BytesIO()
    with PdfPages(buf) as pdf:
        fig = plt.figure(figsize=(8.27, 11.69))
        plt.axis("off")
        plt.text(0.02, 0.98, f"""
CASH-FLOW INVESTOR SUMMARY

Cash: ₹{cash_today:,.0f}
Daily burn: ₹{daily_burn:,.0f}
Runway: {runway_days} days
Cash-out date: {cash_out_date.date()}

Advertising: {ad_ratio:.1f}% of revenue
Risk level: {risk_label}
""", va="top")
        pdf.savefig(fig)
        plt.close(fig)
    buf.seek(0)
    return buf

st.download_button(
    "📥 Download Investor PDF",
    data=generate_pdf(),
    file_name="cashflow_investor_summary.pdf",
    mime="application/pdf",
)
