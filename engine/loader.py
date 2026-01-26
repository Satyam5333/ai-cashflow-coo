import pandas as pd

def load_transactions(csv_path: str) -> pd.DataFrame:
    """
    Load transactions CSV and return cleaned DataFrame
    """
    df = pd.read_csv(csv_path)

    # Ensure correct data types
    df["date"] = pd.to_datetime(df["date"])
    df["amount"] = df["amount"].astype(float)

    return df
