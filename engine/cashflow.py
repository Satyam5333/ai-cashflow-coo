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

    df["description"] = df["description"].astype(str)

    # -----------------------------
    # AUTO CLASSIFICATION
    # -----------------------------

    # Detect SALES (inflow + keywords)
    sales_mask = (
        (df["amount"] > 0) &
        (df["description"].str.contains("sale|revenue|income", case=False, na=False)
         | (df["type"] == "inflow"))
    )

    # Detect AD SPEND
    ad_mask = df["description"].str.contains(
        "ads|facebook|google|instagram|meta",
        case=False,
        na=False
    )

    # Detect RETURNS
    return_mask = df["description"].str.contains(
        "refund|return",
        case=False,
        na=False
    )

    # -----------------------------
    # METRICS
    # -----------------------------

    cash_today = df["amount"].sum()

    sales = df.loc[sales_mask, "amount"].sum()
    ad_spend = df.loc[ad_mask, "amount"].abs().sum()
    returns = df.loc[return_mask, "amount"].abs().sum()

    burn_df = df[df["amount"] < 0]
    avg_daily_burn = burn_df.groupby(df["date"].dt.date)["amount"].sum().mean()

    runway = (
        "Cash Positive"
        if avg_daily_burn >= 0 or pd.isna(avg_daily_burn)
        else round(abs(cash_today / avg_daily_burn))
    )

    ad_spend_pct = round((ad_spend / sales) * 100, 1) if sales > 0 else 0.0
    return_rate = round((returns / sales) * 100, 1) if sales > 0 else 0.0

    return {
        "cash_today": round(cash_today, 2),
        "runway_days": runway,
        "ad_spend_pct": ad_spend_pct,
        "return_rate": return_rate,
    }
