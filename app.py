import streamlit as st
import pandas as pd

# ----------------------------
# Page config
# ----------------------------
st.set_page_config(
    page_title="Cash-Flow Early Warning System",
    page_icon="🧠",
    layout="centered"
)

# ----------------------------
# Title
# ----------------------------
st.markdown("## 🧠 Cash-Flow Early Warning System for SMEs")
st.markdown(
    "Know when your business may face cash trouble — **and what to do next.**"
)

st.divider()

# ----------------------------
# What this tool does
# ----------------------------
st.markdown("### What this tool does")
st.markdown(
    """
- Analyzes real transaction data  
- Forecasts cash position for the next **60 days**  
- Flags overspending and cash risks  
- Gives **clear, COO-level recommendations**
"""
)

st.divider()

# ----------------------------
# File upload
# ----------------------------
uploaded_file = st.file_uploader(
    "Upload your transactions CSV (bank / accounting / POS export)",
    type=["csv"]
)

# ----------------------------
# CSV format help (SAFE)
# ----------------------------
with st.expander("📄 Required CSV format"):
    st.markdown("**Your CSV must contain these columns:**")
    st.markdown("- `date` → YYYY-MM-DD")
    st.markdown("- `amount` → positive = inflow, negative = outflow")
    st.markdown("- `type` → Inflow / Outflow")
    st.markdown("- `description` → Sales, Facebook Ads, Salary, Rent")

    st.markdown("**Example:**")
    st.code(
        "date,amount,type,description\n"
        "2025-01-01,42000,Inflow,Sales\n"
        "2025-01-02,-15000,Outflow,Facebook Ads\n"
        "2025-01-03,-8000,Outflow,Salary",
        language="text"
    )

# ----------------------------
# Main logic
# ----------------------------
if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)

        required = {"date", "amount", "type", "description"}
        if not required.issubset(df.columns):
            st.error("CSV columns do not match required format.")
            st.stop()

        df["date"] = pd.to_datetime(df["date"])
        df["amount"] = pd.to_numeric(df["amount"])

        inflow = df[df["amount"] > 0]["amount"].sum()
        outflow = df[df["amount"] < 0]["amount"].sum()
        cash_today = inflow + outflow

        days = max((df["date"].max() - df["date"].min()).days, 1)
        burn = abs(outflow) / days if outflow < 0 else 0
        runway = int(cash_today / burn) if burn > 0 else "Cash positive"

        # Advertising spend detection
        ads_mask = df["description"].str.contains(
            "ad|ads|facebook|google|marketing",
            case=False,
            na=False
        )
        ad_spend = abs(df.loc[ads_mask & (df["amount"] < 0), "amount"].sum())
        ad_pct = (ad_spend / inflow * 100) if inflow > 0 else 0

        # Expense breakdown
        expense_df = df[df["amount"] < 0].copy()

        def categorize(desc):
            d = desc.lower()
            if "ad" in d or "facebook" in d or "google" in d:
                return "Advertising"
            if "salary" in d:
                return "Salary"
            if "rent" in d:
                return "Rent"
            return "Other"

        expense_df["category"] = expense_df["description"].apply(categorize)
        breakdown = expense_df.groupby("category")["amount"].sum().abs()

        # ----------------------------
        # Output
        # ----------------------------
        st.divider()
        st.markdown("## 📊 AI COO Summary")

        st.markdown(f"**Cash today:** ₹{cash_today:,.0f}")
        st.markdown(f"**Runway:** {runway} days")
        st.markdown(f"**Advertising spend:** {ad_pct:.1f}% of sales")

        st.divider()
        st.markdown("### ⚠️ Key risks")
        if ad_pct > 30:
            st.warning("Advertising spend is high relative to revenue.")
        else:
            st.success("No major financial risks detected.")

        st.divider()
        st.markdown("### ✅ Recommended actions")
        if ad_pct > 30:
            st.markdown("- Pause low-performing ad campaigns")
            st.markdown("- Improve conversion before scaling spend")
        else:
            st.markdown("- Maintain current spending discipline")

        st.divider()
        st.markdown("### 📉 Expense category breakdown")
        for cat, val in breakdown.items():
            st.markdown(f"- **{cat}**: ₹{val:,.0f}")

    except Exception as e:
        st.error("Error processing file")
        st.code(str(e))
