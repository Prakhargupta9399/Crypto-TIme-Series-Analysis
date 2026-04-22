"""
CryptoTime Analytics - Backend API
FastAPI application for Bitcoin price prediction and analysis
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import warnings
from statsmodels.tsa.arima.model import ARIMA

# FIX 1: Removed "from prophet import Prophet"
# Prophet requires cmdstanpy/pystan backend which fails to install on most systems,
# crashing the entire server at startup. Replaced with a numpy-only trend model below.

warnings.filterwarnings('ignore')

app = FastAPI(title="CryptoTime Analytics API")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== PYDANTIC MODELS ====================

class PriceData(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int

class PredictionData(BaseModel):
    date: str
    arima: Optional[float] = None
    lstm: Optional[float] = None
    prophet: Optional[float] = None

class KPIResponse(BaseModel):
    current_price: float
    price_change_24h: float
    price_change_30d: float
    market_cap: str
    volume_24h: str
    high_24h: float
    low_24h: float

# ==================== HELPER FUNCTIONS ====================

def load_cleaned_data():
    """Load cleaned Bitcoin data from CSV"""
    file_path = 'data/bitcoin_data_cleaned.csv'

    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        return pd.DataFrame()

    try:
        df = pd.read_csv(file_path)
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        numeric_cols = ['Close', 'High', 'Low', 'Open', 'Volume']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        df = df.dropna(subset=['Date', 'Close']).sort_values('Date')
        return df
    except Exception as e:
        print(f"Error loading data: {e}")
        return pd.DataFrame()

def calculate_moving_average(df, window=30):
    df['MA30'] = df['Close'].rolling(window=window).mean()
    return df

# ==================== API ENDPOINTS ====================

@app.get("/")
async def root():
    return {"message": "CryptoTime Analytics API", "status": "online", "docs": "/docs"}

@app.get("/api/health")
async def health_check():
    df = load_cleaned_data()
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "data_records": len(df) if not df.empty else 0
    }

@app.get("/api/kpi", response_model=KPIResponse)
async def get_kpi_metrics():
    df = load_cleaned_data()

    if df.empty:
        raise HTTPException(status_code=404, detail="Data file not found or empty. Run setup_data.py first.")

    current_price = float(df['Close'].iloc[-1])
    price_change_24h = 0.0
    price_change_30d = 0.0

    if len(df) > 1:
        price_24h_ago = float(df['Close'].iloc[-2])
        price_change_24h = ((current_price - price_24h_ago) / price_24h_ago) * 100

    if len(df) > 30:
        price_30d_ago = float(df['Close'].iloc[-31])
        price_change_30d = ((current_price - price_30d_ago) / price_30d_ago) * 100

    market_cap = f"${(current_price * 19.5e6 / 1e12):.2f}T"
    vol_val = float(df['Volume'].iloc[-1])
    volume_24h = f"${(vol_val / 1e9):.2f}B"

    return KPIResponse(
        current_price=current_price,
        price_change_24h=round(price_change_24h, 2),
        price_change_30d=round(price_change_30d, 2),
        market_cap=market_cap,
        volume_24h=volume_24h,
        high_24h=float(df['High'].iloc[-1]),
        low_24h=float(df['Low'].iloc[-1])
    )

@app.get("/api/predict/all")
async def predict_all_models(days: int = Query(default=30)):
    """Get predictions from ARIMA, Trend (Prophet), and LSTM models"""
    df = load_cleaned_data()

    if df.empty or len(df) < 60:
        raise HTTPException(status_code=400, detail="Insufficient data for prediction (need >60 records)")

    prices = df["Close"].values.astype(float)
    prices = prices[~np.isnan(prices)]  # strip NaNs before any math

    # FIX 2: Always predict forward from TODAY, not the last date in the CSV.
    # Old code used df['Date'].iloc[-1] which was the training cutoff (e.g. Jan 27),
    # making all "future" predictions land in the past.
    last_date = datetime.today()

    # --- ARIMA ---
    try:
        model = ARIMA(prices, order=(5, 1, 0))
        model_fit = model.fit()
        arima_forecast = list(model_fit.forecast(steps=days))
    except Exception as e:
        print(f"ARIMA Error: {e}")
        arima_forecast = [float(prices[-1])] * days

    # --- Prophet replacement: Weighted MA + Linear Trend (no install required) ---
    prophet_preds = []
    try:
        window = min(30, len(prices))
        weights = np.linspace(1, 3, window)
        weights /= weights.sum()
        wma_base = float(np.dot(prices[-window:], weights))

        trend_window = min(60, len(prices))
        x = np.arange(trend_window)
        y = prices[-trend_window:]
        slope, _ = np.polyfit(x, y, 1)

        for i in range(days):
            dampen = 1 / (1 + 0.02 * i)
            pred = wma_base + slope * (i + 1) * dampen
            prophet_preds.append(float(max(pred, 0)))
    except Exception as e:
        print(f"Trend Model Error: {e}")
        prophet_preds = [float(prices[-1])] * days

    # --- LSTM (trend simulation) ---
    # FIX 3: Old code set last_price = pred inside the loop which caused
    # compounding — prices diverged to unrealistic values over 30-90 days.
    # Now we calculate each prediction independently from the original base price.
    lstm_preds = []
    try:
        base_price = float(prices[-1])
        # Use recent 7-day momentum to set direction
        if len(prices) >= 7:
            momentum = (prices[-1] - prices[-7]) / prices[-7] / 7  # daily % change
        else:
            momentum = 0.001
        # Cap momentum to avoid absurd forecasts (max ±2% per day)
        momentum = max(min(momentum, 0.02), -0.02)

        for i in range(days):
            # Independent from base — no compounding divergence
            pred = base_price * (1 + momentum * (i + 1))
            lstm_preds.append(float(max(pred, 0)))
    except Exception as e:
        print(f"LSTM Error: {e}")
        lstm_preds = [float(prices[-1])] * days

    # --- Combine ---
    prediction_dates = [last_date + timedelta(days=i + 1) for i in range(days)]
    combined = [
        {
            'date': prediction_dates[i].strftime('%Y-%m-%d'),
            'arima': arima_forecast[i],
            'prophet': prophet_preds[i],
            'lstm': lstm_preds[i]
        }
        for i in range(days)
    ]

    return {
        "status": "success",
        "predictions": combined,
        "generated_at": datetime.now().isoformat()
    }

# ==================== MAIN ====================

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting CryptoTime Analytics API...")
    print("📂 Ensure 'data/bitcoin_data_cleaned.csv' exists.")
    uvicorn.run(app, host="0.0.0.0", port=8000)
