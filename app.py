import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# -------------------------
# Page config
# -------------------------
st.set_page_config(
    page_title="AI Cash-Flow COO",
    page_icon="🧠",
    layout="centered"
)

st.title("🧠 Cash-Flow Early Warning System for SMEs")
st.write(
    "Know when your business may face cash trouble — **and what to do next.**"
)

st.markdown("---")

# -------------------------
# CSV Upload
# -------------------------
uploaded_file = st.file_uploader(
    "Upload your transactions CSV (bank / accounting / POS export)",
    type=["csv"]
)

# -------------------------
# Helper functions
# -------------------------
def normalize_expense_category(desc: str) -> str:
    d = desc.lower()
    if "ad" in d or "facebook" in d or "google" in d or "instagram" in d:
        return "Advertising"
    if "salary" in d or "wage" in d:
        return "Salary"
    if "rent" in d:
        return "Rent"
    if "delivery" in d:
        return "Delivery"
    if "pack" in d:
        return "Packaging"
    if "refund" in d or "return" in d:
        return "Refund"
    return "Other"

def inr(x):
    return f"₹{int(x):,}"

# -------------------------
# Process CSV
# -------------------------
if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)

        required_cols = {"date", "amount", "type", "description"}
        if not required_cols.issubset(df.columns):
            st.error("CSV must contain: date, amount, type, description")
            st.stop()

        df["date"] = pd.to_datetime(df["date"])
        df["amount"] = df["amount"].astype(float)

        inflow = df[df["amount"] > 0]["amount"].sum()
        outflow = abs(df[df["amount"] < 0]["amount"].sum())
        cash_today = inflow - outflow

        daily_burn = outflow / max(df["date"].nunique(), 1)
        runway_days = int(cash_today / daily_burn) if daily_burn > 0 else 999

        # -------------------------
        # Expense breakdown
        # -------------------------
        expense_df = df[df["amount"] < 0].copy()
        expense_df["category"] = expense_df["description"].apply(normalize_expense_category)
        expense_summary = (
            expense_df.groupby("category")["amount"]
            .sum()
            .abs()
            .sort_values(ascending=False)
        )

        # -------------------------
        # Advertising %
        # -------------------------
        ad_spend = expense_summary.get("Advertising", 0)
        ad_pct = (ad_spend / inflow * 100) if inflow > 0 else 0

        # -------------------------
        # AI COO SUMMARY
        # -------------------------
        st.markdown("## 📊 AI COO Summary")

        st.write(f"**Cash position:** {inr(cash_today)} available")
        st.write(f"**Operational runway:** ~{runway_days} days at current burn rate")
        st.write(f"**Advertising intensity:** {ad_pct:.1f}% of revenue")

        st.markdown("---")

        # -------------------------
        # Key Insights
        # -------------------------
        st.markdown("## ⚠️ Key insights")

        insights = []

        if runway_days < 60:
            insights.append(
                "Runway is below 2 months. Immediate cost control or revenue acceleration is required."
            )
        else:
            insights.append(
                "Cash runway is healthy, giving management flexibility to optimize growth."
            )

        if ad_pct > 25:
            insights.append(
                "Advertising spend is heavy relative to revenue. ROI tracking and campaign pruning is recommended."
            )
        elif ad_pct > 10:
            insights.append(
                "Advertising spend is material. Ensure performance-driven allocation."
            )
        else:
            insights.append(
                "Advertising spend is controlled and not a major risk driver."
            )

        for i in insights:
            st.write("• " + i)

      # --- Expense category pie chart (clean & compact) ---
fig, ax = plt.subplots(figsize=(5, 5))  # 👈 smaller size

labels = list(expense_breakdown.keys())
values = list(expense_breakdown.values())

ax.pie(
    values,
    labels=labels,
    autopct='%1.1f%%',
    startangle=90,
    pctdistance=0.75,     # 👈 percentages move inward
    labeldistance=1.1,    # 👈 labels move outward
    wedgeprops={'linewidth': 1, 'edgecolor': 'white'}
)

ax.set_title("Expense category breakdown", fontsize=14)
ax.axis('equal')  # keeps it circular

st.pyplot(fig)

        # -------------------------
        # Cost concentration risk
        # -------------------------
        top_two_share = expense_summary.iloc[:2].sum() / expense_summary.sum() * 100

        if top_two_share > 60:
            st.warning(
                f"⚠️ **Cost concentration risk:** "
                f"Top two expense categories account for {top_two_share:.1f}% of total costs. "
                f"Any disruption here could materially impact cash flow."
            )
        else:
            st.success(
                "Cost base is reasonably diversified with no major concentration risk."
            )

        # -------------------------
        # COO Actions
        # -------------------------
        st.markdown("---")
        st.markdown("## ✅ Recommended COO actions")

        actions = []

        if ad_pct > 20:
            actions.append("Audit advertising ROI and pause low-performing campaigns.")
        if runway_days < 90:
            actions.append("Delay discretionary spending and preserve liquidity buffer.")
        actions.append("Review fixed costs quarterly to prevent silent margin erosion.")

        for a in actions:
            st.write("• " + a)

    except Exception as e:
        st.error(f"Error processing file: {e}")

else:
    st.info("Upload a CSV file to generate your AI COO analysis.")
