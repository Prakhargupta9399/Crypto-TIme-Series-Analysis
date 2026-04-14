import pandas as pd
import yfinance as yf
import os

def setup_data():
    print("⏳ Setting up data...")
    
    # Create data directory if it doesn't exist
    if not os.path.exists('data'):
        os.makedirs('data')
        
    output_path = 'data/bitcoin_data_cleaned.csv'
    
    # 1. Download Data
    try:
        print("Downloading Bitcoin data from Yahoo Finance...")
        ticker = "BTC-USD"
        # Download data (extended range to ensure enough for analysis)
        data = yf.download(ticker, start="2023-01-01", end="2025-12-31", interval="1d")
        
        if data.empty:
            print("❌ Error: No data downloaded. Check internet connection.")
            return

        # 2. Preprocess / Clean
        print("Cleaning data...")
        # Reset index to make Date a column
        df = data.reset_index()
        
        # Flatten MultiIndex columns if present (yfinance sometimes returns them)
        df.columns = [col if isinstance(col, str) else col[0] for col in df.columns]
        
        # Standardize column names
        df = df.rename(columns={
            'Date': 'Date', 
            'Open': 'Open', 
            'High': 'High', 
            'Low': 'Low', 
            'Close': 'Close', 
            'Volume': 'Volume'
        })
        
        # Ensure specific columns exist
        required_cols = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
        if not all(col in df.columns for col in required_cols):
            print(f"❌ Error: Missing columns. Available: {df.columns}")
            return

        # Convert types
        for col in ['Close', 'High', 'Low', 'Open', 'Volume']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
        df['Date'] = pd.to_datetime(df['Date'])
        
        # Drop NaNs
        df = df.dropna()

        # Save to the path expected by main.py
        df.to_csv(output_path, index=False)
        print(f"✅ Data successfully saved to {output_path}")
        print(f"📊 Records: {len(df)}")
        
    except Exception as e:
        print(f"❌ Error during setup: {e}")

if __name__ == "__main__":
    setup_data()