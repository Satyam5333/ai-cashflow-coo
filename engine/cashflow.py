import pandas as pd

def calculate_cash_metrics(df: pd.DataFrame) -> dict:
    df.columns = df.columns.str.lower().str.strip()

    required = {"date", "amount", "type"}
    if not required.issubset(df.columns):
        raise ValueError("CSV must contain date, amount, type columns")

    df["date"] = pd.to_datetime(df["date"])
    df["type"] = df["type"].astype(str).str.lower()

    if "description" not in df.columns:
        df["description"] = ""

    df["description"] = df["description"].astype(str).str.lower()

    # -----------------------------
    # SALES / ADS / RETURNS
    # -----------------------------
    sales = df[(df["amount"] > 0) & (df["type"] == "inflow")]["amount"].sum()

    ad_spend = df[
        df["description"].str.contains("ads|facebook|google|instagram|meta", na=False)
    ]["amount"].abs().sum()

    returns = df[
        df["description"].str.contains("refund|return", na=False)
    ]["amount"].abs().sum()

    cash_today = df["amount"].sum()

    burn = df[df["amount"] < 0].groupby(df["date"].dt.date)["amount"].sum().mean()
    runway = "Cash Positive" if burn >= 0 or pd.isna(burn) else round(abs(cash_today / burn))

    # -----------------------------
    # EXPENSE CATEGORY BREAKDOWN
    # -----------------------------
    expense_df = df[df["amount"] < 0].copy()

    def classify_expense(desc):
        if any(x in desc for x in ["ads", "facebook", "google", "meta"]):
            return "Advertising"
        if any(x in desc for x in ["salary", "wages", "payroll"]):
            return "Salaries"
        if any(x in desc for x in ["rent", "office", "lease"]):
            return "Rent"
        if any(x in desc for x in ["software", "saas", "tool"]):
            return "Software"
        return "Other"

    expense_df["category"] = expense_df["description"].apply(classify_expense)

    expense_summary = (
        expense_df.groupby("category")["amount"]
        .sum()
        .abs()
        .sort_values(ascending=False)
    )

    total_expense = expense_summary.sum()

    expense_breakdown = []
    for cat, amt in expense_summary.items():
        pct = round((amt / total_expense) * 100, 1) if total_expense > 0 else 0
        expense_breakdown.append({
            "category": cat,
            "amount": round(amt, 2),
            "percentage": pct
        })

    return {
        "cash_today": round(cash_today, 2),
        "runway_days": runway,
        "ad_spend_pct": round((ad_spend / sales) * 100, 1) if sales > 0 else 0.0,
        "return_rate": round((returns / sales) * 100, 1) if sales > 0 else 0.0,
        "expense_breakdown": expense_breakdown
    }
