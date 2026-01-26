import pandas as pd

def load_transactions(uploaded_file):
    """Standardizes Bank/Tally data with Debit/Credit columns."""
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    # CRITICAL FIX: Standardize all column names to lowercase 
    # This solves the 'Date' (capital) vs 'date' (lowercase) error
    df.columns = [c.lower().strip() for c in df.columns]

    # Map 'activity' to 'description' as seen in your Image 4
    if 'activity' in df.columns:
        df = df.rename(columns={'activity': 'description'})

    # FIX: Handle separate Debit and Credit columns found in your file
    if 'debit' in df.columns and 'credit' in df.columns:
        # Fill empty cells with 0 and calculate net amount 
        # (Credit is money in (+), Debit is money out (-))
        df['amount'] = df['credit'].fillna(0) - df['debit'].fillna(0)
    
    # Ensure date column is recognized correctly
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'], dayfirst=True, errors='coerce')
    
    return df.dropna(subset=['date', 'amount'])