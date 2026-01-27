import pandas as pd
import re

def load_transactions(uploaded_file):
    """Universal loader that detects columns automatically and ignores hidden spaces."""
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        # Standardize headers: lowercase and strip spaces
        df.columns = [str(c).lower().strip() for c in df.columns]

        # Universal Cleaning Engine for numbers
        def clean_currency(val):
            if pd.isna(val) or val == "": return 0.0
            cleaned = re.sub(r'[^\d.-]', '', str(val))
            try: return float(cleaned)
            except: return 0.0

        # FLEXIBLE MAPPING: Looks for common names in Shopify/Bank/Wallet exports
        # Detect Date
        date_cols = [c for c in df.columns if 'date' in c or 'time' in c]
        if date_cols: df = df.rename(columns={date_cols[0]: 'date'})
        
        # Detect Description
        desc_cols = [c for c in df.columns if 'desc' in c or 'activity' in c or 'name' in c]
        if desc_cols: df = df.rename(columns={desc_cols[0]: 'description'})

        # Detect Amount Logic
        if 'amount' in df.columns:
            df['amount'] = df['amount'].apply(clean_currency)
        elif 'debit' in df.columns and 'credit' in df.columns:
            df['amount'] = df['credit'].apply(clean_currency) - df['debit'].apply(clean_currency)
        elif 'inflow' in df.columns and 'outflow' in df.columns:
            df['amount'] = df['inflow'].apply(clean_currency) - df['outflow'].apply(clean_currency)
        elif 'deposits' in df.columns and 'withdrawals' in df.columns:
            df['amount'] = df['deposits'].apply(clean_currency) - df['withdrawals'].apply(clean_currency)

        # Fix Dates
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        return df.dropna(subset=['date', 'amount'])
    except Exception as e:
        return pd.DataFrame()