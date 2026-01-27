import pandas as pd
import re

def load_transactions(uploaded_file):
    """Aggressive loader to handle currency strings and multi-bank formats."""
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    # Standardize headers to lowercase
    df.columns = [str(c).lower().strip() for c in df.columns]

    # CLEANING ENGINE: Fixes 'str' absolute error by removing commas
    def clean_currency(val):
        if pd.isna(val) or val == "": return 0.0
        # Remove everything except digits, dots, and minus signs
        cleaned = re.sub(r'[^\d.-]', '', str(val))
        try:
            return float(cleaned)
        except:
            return 0.0

    # Handle Universal Column Mapping
    if 'txn date' in df.columns: df = df.rename(columns={'txn date': 'date'})
    if 'activity' in df.columns: df = df.rename(columns={'activity': 'description'})

    # AGGRESSIVE DETECTION for Axis (Withdrawals/Deposits)
    if 'withdrawals' in df.columns and 'deposits' in df.columns:
        df['amount'] = df['deposits'].apply(clean_currency) - df['withdrawals'].apply(clean_currency)

    # AGGRESSIVE DETECTION for ICICI (Amount/Type)
    elif 'amount' in df.columns and 'type' in df.columns:
        df['temp_amt'] = df['amount'].apply(clean_currency)
        # Force negative sign if type is DR (Debit)
        df['amount'] = df.apply(lambda x: -abs(x['temp_amt']) if 'DR' in str(x['type']).upper() else abs(x['temp_amt']), axis=1)

    # Final conversion and date cleaning
    df['date'] = pd.to_datetime(df['date'], dayfirst=True, errors='coerce')
    return df.dropna(subset=['date', 'amount'])