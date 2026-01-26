import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from datetime import timedelta
from io import BytesIO
import pdfplumber

st.set_page_config(page_title="AI Cash-Flow COO", layout="centered")

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
.kpi-value { font-size: 1.5rem; font-weight: 700; }
.kpi-sub { font-size: 0.8rem; color: #6b7280; }
div[data-testid="stAlert"] { border-radius: 10px; }
button { border-radius: 8px !important; font-weight: 600 !important; }
</style>
""", unsafe_allow_html=True)

# =================================================
# HEADER
# =================================================
st.title("🧠 Cash-Flow Early Warning System for SMEs")
st.write("Know when cash trouble hits — and exactly what to do next.\n\n**No dashboards. No jargon. Just decisions.**")
st.divider()

# =================================================
# SAMPLE CSV DOWNLOAD (UNCHANGED)
# =================================================
sample_csv = """date,type,description,amount
2025-01-01,Inflow,Sales,42000
2025-01-02,Outflow,Facebook Ads,-15000
2025-01-03,Outflow,Salary,-8000
2025-01-04,Outflow,Rent,-5000
"""
st.download_button("📥 Download sample transactions CSV", sample_csv, "sample_transactions.csv", "text/csv")
st.divider()

# =================================================
# FILE UPLOAD
# =================================================
upload_type = st.selectbox(
    "What are you uploading?",
    ["Bank Statement CSV / Excel", "Bank Statement PDF (text-based)"]
)

uploaded_file = st.file_uploader(
    "Upload file",
    type=["csv", "xlsx", "pdf"]
)

if not uploaded_file:
    st.stop()

# =================================================
# PDF PARSER (NEW, REAL)
# =================================================
def parse_bank_pdf(file):
    rows = []
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if not table:
                continue
            headers = [h.lower() if h else "" for h in table[0]]
            for row in table[1:]:
                if len(row) < 4:
                    continue
                date, desc, amt, typ = row[:4]
                if not amt:
                    continue
                amt = float(str(amt).replace(",", ""))
                if typ.strip().upper() == "DR":
                    amt = -abs(amt)
                rows.append({
                    "date": date,
                    "description": desc,
                    "amount": amt,
                    "type": "Outflow" if amt < 0 else "Inflow"
                })
    return pd.DataFrame(rows)

# =================================================
# LOAD DATA SAFELY
# =================================================
if uploaded_file.name.endswith(".csv"):
    df = pd.read_csv(uploaded_file)

elif uploaded_file.name.endswith(".xlsx"):
    df = pd.read_excel(uploaded_file)

elif uploaded_file.name.endswith(".pdf"):
    st.warning("📄 PDF detected. Parsing text-based bank statement.")
    df = parse_bank_pdf(uploaded_file)
    if df.empty:
        st.error("❌ PDF parsed but no transactions found. Try CSV for guaranteed accuracy.")
        st.stop()

else:
    st.error("Unsupported file type")
    st.stop()

# =================================================
# NORMALIZE DATA (CRITICAL)
# =================================================
df.columns = [c.lower() for c in df.columns]

required = {"date", "description", "amount"}
if not required.issubset(df.columns):
    st.error("File must contain date, description, amount columns.")
    st.stop()

df["date"] = pd.to_datetime(df["date"], errors="coerce")
df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
df = df.dropna(subset=["amount"])

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

if daily_burn == 0 or pd.isna(daily_burn):
    st.error("Not enough expense data to calculate burn.")
    st.stop()

runway_days = int(cash_today / daily_burn)
cash_out_date = df["date"].max() + timedelta(days=runway_days)

# =================================================
# KPI CARDS
# =================================================
c1, c2, c3 = st.columns(3)
with c1:
    st.metric("Cash on hand", f"₹{cash_today:,.0f}")
with c2:
    st.metric("Daily burn", f"₹{daily_burn:,.0f}")
with c3:
    st.metric("Runway", f"{runway_days} days")

st.divider()

# =================================================
# AI COO ANALYSIS (RESTORED)
# =================================================
st.subheader("🧠 AI COO Analysis")
st.write(f"""
You currently hold **₹{cash_today:,.0f}** in cash.

Average daily burn is **₹{daily_burn:,.0f}**, giving you **~{runway_days} days of runway**.

Expected cash-out date: **{cash_out_date.date()}**
""")

# =================================================
# EXPENSE BREAKDOWN (FIXED)
# =================================================
st.subheader("📉 Expense category breakdown")

expense_df = df[df["amount"] < 0].copy()
expense_df["category"] = expense_df["description"].str.extract(
    "(salary|rent|facebook|google|ads|advertising)",
    expand=False
).fillna("Other").str.title()

summary = expense_df.groupby("category")["amount"].sum().abs()

if summary.empty:
    st.warning("No expense data found.")
else:
    fig, ax = plt.subplots()
    ax.pie(summary.values, labels=summary.index, autopct="%1.0f%%")
    ax.axis("equal")
    st.pyplot(fig)

# =================================================
# INVESTOR PDF (UNCHANGED)
# =================================================
def generate_pdf():
    buf = BytesIO()
    with PdfPages(buf) as pdf:
        fig = plt.figure(figsize=(8.27, 11.69))
        plt.axis("off")
        plt.text(0.02, 0.98, f"""
CASH-FLOW SUMMARY

Cash: ₹{cash_today:,.0f}
Daily burn: ₹{daily_burn:,.0f}
Runway: {runway_days} days
Cash-out date: {cash_out_date.date()}
""", va="top", fontsize=12)
        pdf.savefig(fig)
        plt.close()
    buf.seek(0)
    return buf

st.download_button(
    "📥 Download Investor PDF",
    generate_pdf(),
    "cashflow_investor_summary.pdf",
    "application/pdf"
)
