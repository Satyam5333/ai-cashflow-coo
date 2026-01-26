import pandas as pd

def calculate_cash_metrics(df: pd.DataFrame) -> dict:
    # --- Normalise columns ---
    df.columns = df.columns.str.lower().str.strip()

    # Ensure required columns exist
    required_cols = {"date", "amount", "type"}
    if not required_cols.issubset(df.columns):
        raise ValueError("CSV must contain date, amount, type columns")

    # Convert date
    df["date"] = pd.to_datetime(df["date"])

    # Normalise text
    df["type"] = df["type"].astype(str).str.lower()

    # OPTIONAL description column
    if "description" not in df.columns:
        df["description"] = ""

    df["description"] = df["description"].astype(str)

    # --------------------------------------------------
    # 🔥 ENHANCEMENT: AUTO-DETECT AD SPEND FROM DESCRIPTION
    # --------------------------------------------------
    ad_keywords = r"ads|facebook|google|instagram|meta"

    df.loc[
        df["description"].str.contains(ad_keywords, case=False, na=False),
        "type"
    ] = "ad_spend"

    # --------------------------------------------------
    # CALCULATIONS
    # --------------------------------------------------

    cash_today = df["amount"].sum()

    # Daily burn (only negative cash)
    burn_df = df[df["amount"] < 0]
    avg_daily_burn = burn_df.groupby(df["date"].dt.date)["amount"].sum().mean()

    runway_days = (
        float("inf")
        if avg_daily_burn >= 0 or pd.isna(avg_daily_burn)
        else abs(cash_today / avg_daily_burn)
    )

    sales = df[df["type"] == "sales"]["amount"].sum()
    ad_spend = df[df["type"] == "ad_spend"]["amount"].abs().sum()
    returns = df[df["type"] == "return"]["amount"].abs().sum()

    ad_spend_pct = (ad_spend / sales) if sales > 0 else 0
    return_rate = (returns / sales) if sales > 0 else 0

    return {
        "cash_today": round(cash_today, 2),
        "avg_daily_burn": round(avg_daily_burn, 2) if avg_daily_burn else 0,
        "runway_days": round(runway_days) if runway_days != float("inf") else "Cash Positive",
        "ad_spend_pct": round(ad_spend_pct * 100, 1),
        "return_rate": round(return_rate * 100, 1),
    }
