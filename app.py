import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import timedelta
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO

# -----------------------------
# Page config
# -----------------------------
st.set_page_config(page_title="AI Cash-Flow COO", layout="centered")

# -----------------------------
# Header
# -----------------------------
st.title("🧠 Cash-Flow Early Warning System for SMEs")
st.write(
    "Know when your business may face cash trouble — and **what to do next**.\n\n"
    "**No dashboards. No jargon. Just decisions.**"
)

st.divider()

# -----------------------------
# What this tool does
# -----------------------------
st.subheader("What this tool does")
st.markdown(
    """
This system:

- Analyzes real transaction data  
- Forecasts cash runway and cash-out date  
- Flags overspending & cost concentration risk  
- Tells you **what to cut first**  

*(Built for founders & investors)*
"""
)

st.divider()

# -----------------------------
# Sample CSV download
# -----------------------------
sample_csv = """date,amount,type,description
2025-01-01,42000,Inflow,Sales
2025-01-02,-15000,Outflow,Facebook Ads
2025-01-03,-8000,Outflow,Salary
2025-01-04,-5000,Outflow,Rent
"""

st.download_button(
    "📥 Download sample transactions CSV",
    data=sample_csv.encode("utf-8"),
    file_name="sample_transactions.csv",
    mime="text/csv",
)

st.divider()

# -----------------------------
# Upload CSV
# -----------------------------
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

# -----------------------------
# Core metrics
# -----------------------------
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

# -----------------------------
# AI COO Summary (on screen)
# -----------------------------
st.subheader("📊 AI COO Summary")

st.markdown(
    f"""
**Cash today:** ₹{cash_today:,.0f}  
**Daily burn:** ₹{daily_burn:,.0f}  
**Runway:** ~{runway_days} days  
**Estimated cash-out date:** {cash_out_date.date()}  

**Advertising spend:** {ad_ratio:.1f}% of revenue
"""
)

if ad_ratio > 25:
    st.warning("High dependency on advertising. Sales volatility = cash risk.")

st.divider()

# -----------------------------
# Expense breakdown (same logic)
# -----------------------------
st.subheader("📉 Expense category breakdown")

expense_df = df[df["amount"] < 0].copy()
expense_df["abs"] = expense_df["amount"].abs()

def map_category(d):
    d = d.lower()
    if "ad" in d or "facebook" in d or "google" in d or "instagram" in d:
        return "Advertising"
    if "salary" in d:
        return "Salary"
    if "rent" in d:
        return "Rent"
    return "Other"

expense_df["category"] = expense_df["description"].apply(map_category)
expense_breakdown = expense_df.groupby("category")["abs"].sum().sort_values(ascending=False)

fig, ax = plt.subplots(figsize=(4, 4))
ax.pie(
    expense_breakdown.values,
    autopct="%1.0f%%",
    pctdistance=0.7,
    textprops={"fontsize": 9},
)
ax.legend(
    expense_breakdown.index,
    loc="center left",
    bbox_to_anchor=(1.05, 0.5),
    fontsize=9,
)
ax.axis("equal")
st.pyplot(fig)

top_two_share = expense_breakdown.iloc[:2].sum() / expense_breakdown.sum() * 100
if top_two_share > 65:
    st.warning(f"⚠️ Cost concentration risk: Top 2 costs = {top_two_share:.0f}%")

# -----------------------------
# Investor PDF export
# -----------------------------
st.divider()
st.subheader("📄 Investor-ready PDF")

def generate_investor_pdf():
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    y = height - 40
    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, y, "Cash-Flow Investor Summary")

    y -= 30
    c.setFont("Helvetica", 11)
    c.drawString(40, y, f"Cash today: ₹{cash_today:,.0f}")
    y -= 18
    c.drawString(40, y, f"Daily burn: ₹{daily_burn:,.0f}")
    y -= 18
    c.drawString(40, y, f"Runway: ~{runway_days} days")
    y -= 18
    c.drawString(40, y, f"Cash-out date: {cash_out_date.date()}")

    y -= 30
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "Cost Structure")
    y -= 18
    c.setFont("Helvetica", 11)
    c.drawString(40, y, f"Advertising spend: {ad_ratio:.1f}% of revenue")

    y -= 30
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "Key Risks")
    y -= 18
    c.setFont("Helvetica", 11)
    if top_two_share > 65:
        c.drawString(40, y, "• High cost concentration risk")
        y -= 15
    if runway_days < 90:
        c.drawString(40, y, "• Runway below 90 days")

    y -= 30
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "COO Recommendation")
    y -= 18
    c.setFont("Helvetica", 11)
    c.drawString(40, y, f"Primary cut: {expense_breakdown.index[0]}")
    y -= 15
    c.drawString(40, y, "Reduce variable costs before touching fixed commitments.")

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

pdf_buffer = generate_investor_pdf()

st.download_button(
    "📥 Download Investor PDF",
    data=pdf_buffer,
    file_name="cashflow_investor_summary.pdf",
    mime="application/pdf",
)
