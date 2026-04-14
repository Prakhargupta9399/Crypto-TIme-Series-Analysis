import yfinance as yf
import pandas as pd

# Define the cryptocurrency ticker
ticker = "BTC-USD"

# 1. Download historical data
# Valid periods: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
# Valid intervals: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo
data = yf.download(ticker, start="2023-01-01", end="2026-03-01", interval="1d")

# 2. View the first few rows
print(data.head())

# 3. Export to CSV for use in PowerBI, Tableau, or Excel
data.to_csv("bitcoin_data.csv")

crypto = yf.Ticker("ETH-USD")

# Get real-time info (Market Cap, Circulating Supply, etc.)
info = crypto.info
print(f"Market Cap: {info.get('marketCap')}")
print(f"24h Volume: {info.get('volume24Hr')}")

# Get news related to the asset
# news = crypto.news
# for article in news[:3]:
#     print(f"Title: {article['title']} \nLink: {article['link']}\n")



import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# --- CONFIGURATION ---
API_KEY = "CG-NXSMkMAz3TeGgne81HrZdgm5"  # Replace with your actual key
COIN_ID = "bitcoin"            # CoinGecko ID
CURRENCY = "usd"
DAYS = "365"

# # --- 1. FETCH DATA ---
url = f"https://api.coingecko.com/api/v3/coins/{COIN_ID}/market_chart"
params = {
    'vs_currency': CURRENCY,
    'days': DAYS,
    'interval': 'daily'
}
headers = {
    "accept": "application/json",
    "x-cg-demo-api-key": API_KEY
}

response = requests.get(url, params=params, headers=headers)
data = response.json()

# --- 2. PROCESS DATA ---
# Prices are returned as a list of [timestamp, price]
df = pd.DataFrame(data['prices'], columns=['timestamp', 'price'])

# Convert timestamp (ms) to readable date
df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
df.set_index('timestamp', inplace=True)

# --- 3. ANALYTICS: Add a 30-day Moving Average ---
df['MA30'] = df['price'].rolling(window=30).mean()

# # --- 4. VISUALIZATION ---
plt.figure(figsize=(12, 6))
plt.plot(df.index, df['price'], label='Daily Price', color='#f2a900', linewidth=2)
plt.plot(df.index, df['MA30'], label='30-Day MA', color='#4A90E2', linestyle='--')

plt.title(f'{COIN_ID.capitalize()} Price Trend (Past Year)', fontsize=16)
plt.xlabel('Date')
plt.ylabel('Price (USD)')
plt.legend()
plt.grid(True, alpha=0.3)
plt.show()

# Optional: Save to CSV for Excel/PowerBI
df.to_csv("btc_analytics.csv")




































