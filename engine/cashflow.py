import pandas as pd


def calculate_cash_metrics(df: pd.DataFrame) -> dict:
    """
    Calculates core cash-flow metrics from transaction data.
    Expected columns:
    - date
    - amount
    - type (income / expense / ad_spend / return)  [optional]
    """

    df = df.copy()

    # Ensure date
    df["date"] = pd.to_datetime(df["date"])

    # Sort by date
    df = df.sort_values("date")

    # Cash today
    cash_today = df["amount"].sum()

    # Last 30 days
    last_30 = df[df["date"] >= df["date"].max() - pd.Timedelta(days=30)]

    avg_daily_burn = (
        last_30[last_30["amount"] < 0]["amount"].sum() / 30
        if not last_30.empty
        else 0
    )

    # Ad spend
    if "type" in df.columns:
        ad_spend = df[df["type"] == "ad_spend"]["amount"].abs().sum()
        sales = df[df["type"] == "income"]["amount"].sum()
        returns = df[df["type"] == "return"]["amount"].abs().sum()
    else:
        ad_spend = 0
        sales = df[df["amount"] > 0]["amount"].sum()
        returns = 0

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
