import pandas as pd
import re

def load_transactions(uploaded_file):
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    # 1. Force headers to lowercase to fix the 'date' vs 'Date' error
    df.columns = [str(c).lower().strip() for c in df.columns]

    # 2. Aggressive Number Cleaning (strips commas and symbols)
    def clean_currency(val):
        if pd.isna(val) or val == "": return 0.0
        cleaned = re.sub(r'[^\d.-]', '', str(val))
        try: return float(cleaned)
        except: return 0.0

    # 3. Handle Axis/ICICI Specific Columns
    if 'withdrawals' in df.columns and 'deposits' in df.columns:
        df['amount'] = df['deposits'].apply(clean_currency) - df['withdrawals'].apply(clean_currency)
    elif 'amount' in df.columns and 'type' in df.columns:
        df['temp_amt'] = df['amount'].apply(clean_currency)
        df['amount'] = df.apply(lambda x: -abs(x['temp_amt']) if 'DR' in str(x['type']).upper() else abs(x['temp_amt']), axis=1)

    # 4. Final Conversion
    df['date'] = pd.to_datetime(df['date'], dayfirst=True, errors='coerce')
    return df.dropna(subset=['date', 'amount'])