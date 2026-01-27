import pandas as pd
import re

def load_transactions(uploaded_file):
    # Load the file
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    # Standardize headers to lowercase
    df.columns = [str(c).lower().strip() for c in df.columns]

    # CLEANING ENGINE: Strips commas/symbols so math works
    def clean_num(val):
        if pd.isna(val) or val == "": return 0.0
        cleaned = re.sub(r'[^\d.-]', '', str(val))
        try: return float(cleaned)
        except: return 0.0

    # Map Headers
    if 'txn date' in df.columns: df = df.rename(columns={'txn date': 'date'})
    if 'activity' in df.columns: df = df.rename(columns={'activity': 'description'})

    # Process ICICI (Amount/Type)
    if 'amount' in df.columns and 'type' in df.columns:
        df['temp'] = df['amount'].apply(clean_num)
        df['amount'] = df.apply(lambda x: -abs(x['temp']) if 'DR' in str(x['type']).upper() else abs(x['temp']), axis=1)

    # Process Axis (Withdrawals/Deposits)
    elif 'withdrawals' in df.columns and 'deposits' in df.columns:
        df['amount'] = df['deposits'].apply(clean_num) - df['withdrawals'].apply(clean_num)

    df['date'] = pd.to_datetime(df['date'], dayfirst=True, errors='coerce')
    return df.dropna(subset=['date', 'amount'])