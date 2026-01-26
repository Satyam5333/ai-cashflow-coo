import pandas as pd
import pdfplumber
import io

def load_transactions(uploaded_file):
    """Standardizes Data from CSV, Excel, or PDF Bank Statements."""
    
    # --- PDF HANDLING LOGIC ---
    if uploaded_file.name.endswith('.pdf'):
        all_data = []
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                table = page.extract_table()
                if table:
                    all_data.extend(table)
        
        # Convert extracted list to DataFrame
        df = pd.DataFrame(all_data[1:], columns=all_data[0])
    
    # --- CSV/EXCEL HANDLING ---
    elif uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    # --- SMART NORMALIZATION ---
    # Standardize all column names to lowercase to fix the 'Date' error
    df.columns = [str(c).lower().strip() for c in df.columns]

    # Handle Debit/Credit columns
    if 'debit' in df.columns and 'credit' in df.columns:
        df['amount'] = pd.to_numeric(df['credit'], errors='coerce').fillna(0) - \
                       pd.to_numeric(df['debit'], errors='coerce').fillna(0)
    
    # Map 'activity' or 'particulars' to 'description'
    rename_map = {'activity': 'description', 'particulars': 'description', 'narration': 'description'}
    df = df.rename(columns=rename_map)
    
    # Clean Date
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'], dayfirst=True, errors='coerce')
    
    return df.dropna(subset=['date', 'amount'])