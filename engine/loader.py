import pandas as pd
import re

def load_transactions(uploaded_file):
    """Universal loader with aggressive numerical cleaning to fix 'str' errors."""
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    # 1. Standardize headers to lowercase
    df.columns = [str(c).lower().strip() for c in df.columns]

    # 2. AGGRESSIVE CLEANING ENGINE: Fixes 'str' math errors by removing commas
    def clean_currency(val):
        if pd.isna(val) or val == "": return 0.0
        # Remove commas, symbols, and spaces so math can happen
        cleaned = re.sub(r'[^\d.-]', '', str(val))
        try:
            return float(cleaned)
        except:
            return 0.0

    # 3. Universal Column Mapping
    if 'txn date' in df.columns: df = df.rename(columns={'txn date': 'date'})
    if 'activity' in df.columns: df = df.rename(columns={'activity': 'description'})

    # 4. Aggressive Amount Detection (Looks for any money-related columns)
    if 'amount' in df.columns:
        df['amount'] = df['amount'].apply(clean_currency)
    elif 'debit' in df.columns and 'credit' in df.columns:
        df['amount'] = df['credit'].apply(clean_currency) - df['debit'].apply(clean_currency)
    elif 'withdrawals' in df.columns and 'deposits' in df.columns:
        df['amount'] = df['deposits'].apply(clean_currency) - df['withdrawals'].apply(clean_currency)

    # 5. Final Cleaning
    df['date'] = pd.to_datetime(df['date'], dayfirst=True, errors='coerce')
    return df.dropna(subset=['date', 'amount'])