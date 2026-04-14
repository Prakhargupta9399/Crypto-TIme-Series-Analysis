import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def preprocess_bitcoin_data(file_path):
    # 1. Load the data
    # We load it first to handle the non-standard header structure
    df = pd.read_csv(file_path)

    # 2. Cleanup headers and structural rows
    # The original file has 'Ticker' and 'Date' labels in the first few rows
    df.columns = ['Date', 'Close', 'High', 'Low', 'Open', 'Volume']
    # Skip the 'Ticker' and empty 'Date' rows (first two rows)
    df = df.iloc[2:].reset_index(drop=True)

    # 3. Convert Price/Volume columns to numeric
    # 'errors=coerce' turns unparseable strings into NaN
    numeric_cols = ['Close', 'High', 'Low', 'Open', 'Volume']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # 4. Convert Date to datetime objects
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

    # 5. Drop any rows with missing essential data (like empty dates at the end)
    df = df.dropna(subset=['Date'])

    # 6. Sort by date for time-series consistency
    df = df.sort_values(by='Date')
    
    return df

def preprocess_analytics_data(file_path):
    # 1. Load the data
    df = pd.read_csv(file_path)

    # 2. Convert timestamp to datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')

    # 3. Drop rows with invalid timestamps
    df = df.dropna(subset=['timestamp'])
    
    # 4. Sort by timestamp
    df = df.sort_values(by='timestamp')

    return df

# --- Execution ---

# Preprocess the main Bitcoin price data
bitcoin_cleaned = preprocess_bitcoin_data('bitcoin_data.csv')

# Preprocess the analytics data
analytics_cleaned = preprocess_analytics_data('btc_analytics.csv')

# Check for duplicates as a safety measure
print(f"Bitcoin Data Duplicates: {bitcoin_cleaned.duplicated().sum()}")
print(f"Analytics Data Duplicates: {analytics_cleaned.duplicated().sum()}")

# Save the cleaned datasets
bitcoin_cleaned.to_csv('bitcoin_data_cleaned.csv', index=False)
analytics_cleaned.to_csv('btc_analytics_cleaned.csv', index=False)

print("Preprocessing complete. Files saved as 'bitcoin_data_cleaned.csv' and 'btc_analytics_cleaned.csv'.")

# Display the first few rows of the cleaned data
print("\nCleaned Bitcoin Data Head:")
print(bitcoin_cleaned.head())

import matplotlib.pyplot as plt
import seaborn as sns

# Set visual style
sns.set_theme(style="whitegrid")

# --- 1. Load and Clean bitcoin_data.csv ---
# Skip the first 2 rows of metadata
bitcoin_df = pd.read_csv('bitcoin_data.csv', skiprows=0)
bitcoin_df.columns = ['Date', 'Close', 'High', 'Low', 'Open', 'Volume']
bitcoin_df = bitcoin_df.iloc[2:].reset_index(drop=True)

# Convert types and drop NaNs
bitcoin_df['Date'] = pd.to_datetime(bitcoin_df['Date'], errors='coerce')
numeric_cols = ['Close', 'High', 'Low', 'Open', 'Volume']
bitcoin_df[numeric_cols] = bitcoin_df[numeric_cols].apply(pd.to_numeric, errors='coerce')
bitcoin_df = bitcoin_df.dropna().sort_values('Date')

# --- 2. Load and Clean btc_analytics.csv ---
analytics_df = pd.read_csv('btc_analytics.csv')
analytics_df['timestamp'] = pd.to_datetime(analytics_df['timestamp'], errors='coerce')
analytics_df[['price', 'MA30']] = analytics_df[['price', 'MA30']].apply(pd.to_numeric, errors='coerce')
analytics_df = analytics_df.dropna().sort_values('timestamp')

# --- 3. Visualizations ---

# Trend: Close Price
plt.figure(figsize=(12, 6))
sns.lineplot(data=bitcoin_df, x='Date', y='Close', color='blue')
plt.title('Bitcoin Price Trend (2023 - 2026)')
plt.savefig('bitcoin_price_trend.png')

# Analytics: Price vs Moving Average
plt.figure(figsize=(12, 6))
sns.lineplot(data=analytics_df, x='timestamp', y='price', label='Price', alpha=0.5)
sns.lineplot(data=analytics_df, x='timestamp', y='MA30', label='30-Day Moving Average', linewidth=2)
plt.title('Bitcoin Price vs 30-Day Moving Average')
plt.savefig('btc_analytics_trends.png')

# Volume: Trading Volume Over Time
plt.figure(figsize=(12, 6))
plt.fill_between(bitcoin_df['Date'], bitcoin_df['Volume'], color='green', alpha=0.3)
plt.title('Bitcoin Trading Volume Over Time')
plt.savefig('bitcoin_volume_trend.png')

# Save Cleaned Data
bitcoin_df.to_csv('bitcoin_data_cleaned.csv', index=False)
analytics_df.to_csv('btc_analytics_cleaned.csv', index=False)