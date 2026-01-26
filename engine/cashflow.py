import pandas as pd


def calculate_cash_metrics(df: pd.DataFrame) -> dict:
    df = df.copy()

    # Normalize columns
    df.columns = [c.lower().strip() for c in df.columns]

    # Required columns check
    if "date" not in df.columns or "amount" not in df.columns:
        raise ValueError("CSV must contain 'date' and 'amount' columns")

    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")

    cash_today = df["amount"].sum()

    last_30 = df[df["date"] >= df["date"].max() - pd.Timedelta(days=30)]

    avg_daily_burn = (
        last_30[last_30["amount"] < 0]["amount"].sum() / 30
        if not last_30.empty
        else 0
    )

    sales = df[df["amount"] > 0]["amount"].sum()
    expenses = abs(df[df["amount"] < 0]["amount"].sum())

    ad_spend = 0
    returns = 0

    if "type" in df.columns:
        ad_spend = abs(df[df["type"] == "ad_spend"]["amount"].sum())
        returns = abs(df[df["type"] == "return"]["amount"].sum())

    ad_spend_pct = ad_spend / sales if sales > 0 else 0
    return_rate = returns / sales if sales > 0 else 0

    runway_days = (
        "Cash Positive"
        if avg_daily_burn >= 0
        else round(abs(cash_today / avg_daily_burn))
    )

    return {
        "cash_today": cash_today,
        "avg_daily_burn": avg_daily_burn,
        "runway_days": runway_days,
        "ad_spend_pct": ad_spend_pct,
        "return_rate": return_rate,
    }
