import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import StringIO

# ---------------- Page config ----------------
st.set_page_config(
    page_title="Cash-Flow Early Warning System",
    layout="centered"
)

# ---------------- Title ----------------
st.title("🧠 Cash-Flow Early Warning System for SMEs")
st.write(
    "Know when your business may face cash trouble — and **what to do next**."
)

st.markdown("---")

# ---------------- What this tool does ----------------
st.subheader("What this tool does")
st.markdown("""
- Analyzes real transaction data  
- Identifies cash burn and runway  
- Highlights cost concentration risks  
- Gives **clear, COO-level recommendations**  

*(No dashboards. No jargon. Just decisions.)*
""")

st.markdown("---")

# ---------------- Sample CSV download ----------------
st.subheader("Need a sample CSV format?")

sample_csv = """date,amount,type,description
2025-01-01,42000,Inflow,Sales
2025-01-02,-15000,Outflow,Advertising
2025-01-03,-8000,Outflow,Salary
2025-01-04,-4000,Outflow,Rent
2025-01-05,-2500,Outflow,Packaging
"""

st.download_button(
    label="📥 Download sample transactions CSV",
    data=sample_csv,
    file_name="sample_transactions.csv",
    mime="text/csv"
)

st.markdown("---")

# ---------------- File upload ----------------
st.subheader("Upload your transactions CSV")
uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)

        required_cols = {"date", "amount", "type", "description"}
        if not required_cols.issubset(df.columns):
            st.error("CSV must contain: date, amount, type, description")
            st.stop()

        # Clean data
        df["date"] = pd.to_datetime(df["date"])
        df["amount"] = pd.to_numeric(df["amount"])

        inflow = df[df["amount"] > 0]["amount"].sum()
        outflow = abs(df[df["amount"] < 0]["amount"].sum())
        cash_today = inflow - outflow

        avg_daily_burn = outflow / max(df["date"].nunique(), 1)
        runway_days = int(cash_today / avg_daily_burn) if avg_daily_burn > 0 else 0

        # ---------------- Expense categorisation ----------------
        expense_df = df[df["amount"] < 0].copy()
        expense_df["cost"] = abs(expense_df["amount"])

        def normalize_category(text):
            t = text.lower()
            if "ad" in t or "marketing" in t:
                return "Advertising"
            if "salary" in t or "payroll" in t:
                return "Salary"
            if "rent" in t:
                return "Rent"
            if "delivery" in t:
                return "Delivery"
            if "pack" in t:
                return "Packaging"
            if "refund" in t:
                return "Refund"
            return "Other"

        expense_df["category"] = expense_df["description"].apply(normalize_category)

        expense_breakdown = (
            expense_df.groupby("category")["cost"]
            .sum()
            .sort_values(ascending=False)
        )

        total_expense = expense_breakdown.sum()

        advertising_spend = expense_breakdown.get("Advertising", 0)
        ad_ratio = (advertising_spend / inflow * 100) if inflow > 0 else 0

        # ---------------- AI COO Summary ----------------
        st.markdown("---")
        st.subheader("📊 AI COO Summary")

        st.write(f"**Cash position:** ₹{cash_today:,.0f}")
        st.write(f"**Cash runway:** ~{runway_days} days")

        if ad_ratio > 30:
            st.write(
                f"⚠️ **Advertising consumes {ad_ratio:.1f}% of revenue**, "
                "which is high and increases cash risk if sales slow."
            )
        elif ad_ratio > 15:
            st.write(
                f"🟡 Advertising is **{ad_ratio:.1f}% of revenue** — monitor ROI closely."
            )
        else:
            st.write(
                f"🟢 Advertising spend is controlled at **{ad_ratio:.1f}% of revenue**."
            )

        # ---------------- Cost concentration risk ----------------
        st.markdown("---")
        st.subheader("⚠️ Key risks")

        top_category = expense_breakdown.index[0]
        top_share = expense_breakdown.iloc[0] / total_expense * 100

        if top_share > 50:
            st.warning(
                f"High cost concentration: **{top_category} accounts for "
                f"{top_share:.1f}% of total expenses**."
            )
        else:
            st.success("No major cost concentration risks detected.")

        # ---------------- Recommendations ----------------
        st.markdown("---")
        st.subheader("✅ Recommended actions")

        actions = []

        if ad_ratio > 25:
            actions.append("Reduce advertising or improve conversion efficiency")
        if runway_days < 90:
            actions.append("Extend runway by cutting fixed costs or increasing collections")
        if "Salary" in expense_breakdown and expense_breakdown["Salary"] / total_expense > 0.3:
            actions.append("Review team size and productivity metrics")

        if not actions:
            actions.append("Maintain current spending discipline")

        for a in actions:
            st.write(f"• {a}")

        # ---------------- Expense pie chart ----------------
        st.markdown("---")
        st.subheader("📉 Expense category breakdown")

        fig, ax = plt.subplots(figsize=(5, 5))

        ax.pie(
            expense_breakdown.values,
            labels=expense_breakdown.index,
            autopct="%1.1f%%",
            startangle=90,
            pctdistance=0.7,
            labeldistance=1.1,
            wedgeprops={"edgecolor": "white"}
        )

        ax.axis("equal")
        st.pyplot(fig)

    except Exception as e:
        st.error(f"Error processing file: {e}")
