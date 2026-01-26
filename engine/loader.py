import pandas as pd

def load_transactions(uploaded_file):
    """Standardizes Tally/Bank data with Debit/Credit columns."""
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    # Standardize all column names to lowercase to fix the 'date' vs 'Date' error
    df.columns = [c.lower().strip() for c in df.columns]

    # Map 'activity' to 'description' as seen in your screenshot
    if 'activity' in df.columns:
        df = df.rename(columns={'activity': 'description'})

    # CRITICAL FIX: Handle separate Debit and Credit columns
    if 'debit' in df.columns and 'credit' in df.columns:
        # Fill empty cells with 0 and calculate net amount
        # Credits increase cash (+), Debits decrease cash (-)
        df['amount'] = df['credit'].fillna(0) - df['debit'].fillna(0)
    
    # Ensure date column is recognized as a date
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'], dayfirst=True, errors='coerce')
    
    return df.dropna(subset=['date', 'amount'])