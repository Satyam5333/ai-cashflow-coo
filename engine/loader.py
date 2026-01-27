import pandas as pd
import re

def load_transactions(uploaded_file):
    """Universal loader cleaned of non-breaking spaces and formatting errors."""
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        # Standardize headers: lowercase, no spaces
        df.columns = [str(c).lower().strip() for c in df.columns]

        # Cleaning engine for currency strings (handles commas and minus signs)
        def clean_currency(val):
            if pd.isna(val) or val == "": return 0.0
            cleaned = re.sub(r'[^\d.-]', '', str(val))
            try: return float(cleaned)
            except: return 0.0

        # Universal Mapping Logic - Detects Shopify/Bank/Manual headers
        if 'txn date' in df.columns: df = df.rename(columns={'txn date': 'date'})
        if 'description' in df.columns: pass # Already correct
        elif 'activity' in df.columns: df = df.rename(columns={'activity': 'description'})

        # Smart Amount Detection for your Inflow/Outflow sheets
        if 'amount' in df.columns:
            df['amount'] = df['amount'].apply(clean_currency)
        elif 'inflow' in df.columns and 'outflow' in df.columns:
            df['amount'] = df['inflow'].apply(clean_currency) - df['outflow'].apply(clean_currency)
        elif 'debit' in df.columns and 'credit' in df.columns:
            df['amount'] = df['credit'].apply(clean_currency) - df['debit'].apply(clean_currency)

        # Ensure date format is correct
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        return df.dropna(subset=['date', 'amount'])
    except Exception as e:
        return pd.DataFrame()