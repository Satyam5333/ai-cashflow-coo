import pandas as pd

def calculate_daily_cashflow(
    df: pd.DataFrame,
    opening_cash: float
) -> pd.DataFrame:
    """
    Replicates Excel Daily_Cash_Balance logic
    """

    # Group transactions by date
    daily_flow = (
        df.groupby("date")["amount"]
        .sum()
        .reset_index()
        .rename(columns={"amount": "net_flow"})
    )

    # Sort by date
    daily_flow = daily_flow.sort_values("date").reset_index(drop=True)

    # Calculate opening & closing cash
    opening_cash_list = []
    closing_cash_list = []

    current_cash = opening_cash

    for net in daily_flow["net_flow"]:
        opening_cash_list.append(current_cash)
        closing = current_cash + net
        closing_cash_list.append(closing)
        current_cash = closing

    daily_flow["opening_cash"] = opening_cash_list
    daily_flow["closing_cash"] = closing_cash_list

    return daily_flow


def get_latest_cash(daily_cashflow: pd.DataFrame) -> float:
    """
    Returns last closing cash (Cash Today)
    """
    return float(daily_cashflow["closing_cash"].iloc[-1])
