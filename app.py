import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import pdfplumber
from datetime import timedelta
from io import BytesIO

# =================================================
# PAGE CONFIG
# =================================================
st.set_page_config(page_title="AI Cash-Flow COO", layout="centered")

# =================================================
# GLOBAL UI POLISH (UNCHANGED)
# =================================================
st.markdown("""
<style>
html, body {
    background: linear-gradient(180deg,#0f172a 0%,#020617 100%);
    color: #e5e7eb;
}
.kpi-card {
    background:#020617;
    padding:1rem;
    border-radius:12px;
    border-left:5px solid #6366f1;
}
</style>
""", unsafe_allow_html=True)

# =================================================
# HEADER
# =================================================
st.title("🧠 Cash-Flow Early Warning System for SMEs")
st.write("Know when cash trouble hits — and exactly what to do next.")
st.divider()

# =================================================
# FILE TYPE SELECT
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
# PDF → BANK DETECTION (FIXED)
# =================================================
def detect_bank_from_pdf(text):
    t = text.lower()
    if "icici bank" in t:
        return "ICICI"
    if "axis bank" in t:
        return "AXIS"
    if "hdfc bank" in t:
        return "HDFC"
    return "UNKNOWN"

# =================================================
# ICICI PDF PARSER (ROBUST)
# =================================================
def parse_icici_pdf(file):
    rows = []
    with pdfplumber.open(file) as pdf:
        text = pdf.pages[0].extract_text()
        for page in pdf.pages:
            table = page.extract_table()
            if not table:
                continue
            for r in table[1:]:
                try:
                    rows.append({
                        "date": pd.to_datetime(r[0], dayfirst=True),
                        "description": r[1],
                        "amount": float(r[2]),
                        "type": "Inflow" if r[3] == "CR" else "Outflow"
                    })
                except:
                    pass
    return pd.DataFrame(rows)

# =================================================
# LOAD DATA
# =================================================
if upload_type == "Bank Statement PDF (text-based)":
    with pdfplumber.open(uploaded_file) as pdf:
        first_page_text = pdf.pages[0].extract_text()

    bank = detect_bank_from_pdf(first_page_text)

    if bank == "ICICI":
        df = parse_icici_pdf(uploaded_file)
    else:
        st.error("Unsupported bank PDF. Upload CSV for guaranteed accuracy.")
        st.stop()

else:
    df = pd.read_csv(uploaded_file)

# =================================================
# NORMALIZE
# =================================================
df["amount"] = df["amount"].astype(float)
df["date"] = pd.to_datetime(df["date"])

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

ads = df[df["description"].str.contains("ad|facebook|google|instagram", case=False, na=False)]
ad_ratio = abs(ads["amount"].sum()) / inflows * 100 if inflows else 0

# =================================================
# KPI CARDS
# =================================================
c1, c2, c3 = st.columns(3)
c1.metric("Cash on hand", f"₹{cash_today:,.0f}")
c2.metric("Runway", f"{runway_days} days")
c3.metric("Daily burn", f"₹{daily_burn:,.0f}")

st.divider()

# =================================================
# AI COO ANALYSIS (RESTORED)
# =================================================
st.subheader("🧠 AI COO Analysis")

st.markdown(f"""
You currently hold **₹{cash_today:,.0f}** in cash.

Average daily burn is **₹{daily_burn:,.0f}**, giving you **~{runway_days} days of runway**.

**Expected cash-out date:** `{cash_out_date.date()}`

Advertising consumes **{ad_ratio:.1f}% of revenue**.
""")

# =================================================
# WHAT TO CUT / PROTECT (RESTORED)
# =================================================
st.markdown("""
### What to cut first
1. Advertising spend  
2. Variable vendors  
3. Discretionary costs  

**Protect salaries & core operations.**
""")

# =================================================
# EXPENSE BIFURCATION (RESTORED)
# =================================================
st.subheader("📉 Expense Structure Insight")

expense_df = df[df["amount"] < 0].copy()
expense_df["abs"] = expense_df["amount"].abs()

expense_df["category"] = expense_df["description"].str.contains(
    "ad|facebook|google", case=False, na=False
).map({True: "Advertising", False: "Other"})

breakdown = expense_df.groupby("category")["abs"].sum()

st.markdown("""
This expense mix shows where cash pressure actually comes from.
High concentration increases fragility during revenue dips.
""")

fig, ax = plt.subplots()
ax.pie(breakdown.values, labels=breakdown.index, autopct="%1.0f%%")
st.pyplot(fig)

# =================================================
# INVESTOR PDF
# =================================================
st.download_button(
    "📥 Download Investor PDF",
    data="Investor summary coming next phase",
    file_name="investor_summary.txt"
)
