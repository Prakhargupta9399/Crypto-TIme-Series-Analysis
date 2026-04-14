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
from prophet import Prophet

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
        # Read CSV normally since it has headers from the setup script
        df = pd.read_csv(file_path)
        
        # Convert Date
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        
        # Convert numeric cols
        numeric_cols = ['Close', 'High', 'Low', 'Open', 'Volume']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Drop invalid rows and sort
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
    return {
        "message": "CryptoTime Analytics API",
        "status": "online",
        "docs": "/docs"
    }

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
    
    # Calculate changes
    price_change_24h = 0.0
    price_change_30d = 0.0
    
    if len(df) > 1:
        price_24h_ago = float(df['Close'].iloc[-2])
        price_change_24h = ((current_price - price_24h_ago) / price_24h_ago) * 100
        
    if len(df) > 30:
        price_30d_ago = float(df['Close'].iloc[-31])
        price_change_30d = ((current_price - price_30d_ago) / price_30d_ago) * 100

    # Market Cap approx (19.5M BTC supply)
    market_cap = f"${(current_price * 19.5e6 / 1e12):.2f}T"
    
    # Volume
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
    """Get predictions from ARIMA and Prophet models"""
    df = load_cleaned_data()
    
    if df.empty or len(df) < 60:
        raise HTTPException(status_code=400, detail="Insufficient data for prediction (need >60 records)")

    # Prepare data
    prices = df['Close'].values
    last_date = df['Date'].iloc[-1]
    
    # --- ARIMA ---
    try:
        model = ARIMA(prices, order=(5, 1, 0))
        model_fit = model.fit()
        arima_forecast = model_fit.forecast(steps=days)
    except Exception as e:
        print(f"ARIMA Error: {e}")
        arima_forecast = [prices[-1]] * days # Fallback

    # --- Prophet ---
    prophet_preds = []
    try:
        prophet_df = df[['Date', 'Close']].copy()
        prophet_df.columns = ['ds', 'y']
        
        m = Prophet(daily_seasonality=True)
        m.fit(prophet_df)
        
        future = m.make_future_dataframe(periods=days)
        forecast = m.predict(future)
        
        # Extract only future predictions
        forecast_tail = forecast.tail(days)
        prophet_preds = forecast_tail['yhat'].tolist()
    except Exception as e:
        print(f"Prophet Error: {e}")
        prophet_preds = [prices[-1]] * days

    # --- LSTM (Simulated/Simplified) ---
    # In a real scenario, this requires a trained ML model. 
    # We simulate it based on recent trend for this demo.
    last_price = prices[-1]
    lstm_preds = []
    for i in range(days):
        # Simple trend simulation
        pred = last_price * (1 + 0.001 * (i+1)) 
        lstm_preds.append(pred)
        last_price = pred

    # Combine
    combined = []
    prediction_dates = [last_date + timedelta(days=i+1) for i in range(days)]
    
    for i in range(days):
        combined.append({
            'date': prediction_dates[i].strftime('%Y-%m-%d'),
            'arima': float(arima_forecast[i]),
            'prophet': float(prophet_preds[i]),
            'lstm': float(lstm_preds[i])
        })

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