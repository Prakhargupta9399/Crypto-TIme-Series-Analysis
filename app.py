import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf
from datetime import datetime, timedelta



# ── Built-in sentiment scorer (no downloads required) ──────────────────────
def get_sentiment_score(text: str) -> float:
    """Returns polarity in [-1, +1]. Positive = bullish, negative = bearish."""
    pos = {"good","great","bull","bullish","up","rise","rising","surge","surging",
           "gain","gains","growth","rally","strong","positive","profit","profits",
           "win","winning","buy","moon","mooning","pumping","pump","amazing",
           "excellent","recover","recovery","high","higher","best","love","loved",
           "green","optimistic","promising","soar","soaring","boom","booming"}
    neg = {"bad","bear","bearish","down","fall","falling","crash","crashing",
           "drop","dropping","loss","losses","weak","negative","sell","dump",
           "dumping","fear","fearful","panic","terrible","worst","decline",
           "declining","low","lower","red","pessimistic","collapse","collapsing",
           "broke","broken","risk","risky","danger","dangerous","scam","fraud"}
    words = text.lower().split()
    score = sum(1 for w in words if w in pos) - sum(1 for w in words if w in neg)
    total = len(words) if words else 1
    return max(-1.0, min(1.0, score / total * 3))

# Configuration
st.set_page_config(page_title="CryptoTime Analytics", layout="wide", initial_sidebar_state="expanded")

# ================= MASSIVE CSS ANIMATION INJECTION =================
animated_css = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Rajdhani:wght@400;600&display=swap');

    #MainMenu, footer, header {visibility: hidden;}
    .block-container {padding-top: 2rem; background: transparent;}

    /* 1. ANIMATED DARK BACKGROUND WITH GRID OVERLAY */
    .stApp {
        background: linear-gradient(-45deg, #050505, #0d1b2a, #1b263b, #050505);
        background-size: 400% 400%;
        animation: movingBackground 15s ease infinite;
        color: white;
        background-image: 
            linear-gradient(rgba(0, 243, 255, 0.03) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0, 243, 255, 0.03) 1px, transparent 1px),
            linear-gradient(-45deg, #050505, #0d1b2a, #1b263b, #050505);
        background-size: 50px 50px, 50px 50px, 400% 400%;
    }

    @keyframes movingBackground {
        0% {background-position: 0% 50%, 0% 50%, 0% 50%;}
        50% {background-position: 100% 50%, 100% 50%, 100% 50%;}
        100% {background-position: 0% 50%, 0% 50%, 0% 50%;}
    }

    /* 2. ANIMATED GLOWING TITLE (Neon Pulse) */
    .glowing-title {
        font-family: 'Orbitron', sans-serif;
        font-size: 3.5rem;
        font-weight: 700;
        color: #fff;
        text-align: center;
        animation: neonPulse 3s ease-in-out infinite alternate;
        margin-bottom: 0px;
    }

    @keyframes neonPulse {
        from { text-shadow: 0 0 10px #00f3ff, 0 0 20px #00f3ff, 0 0 40px #00f3ff, 0 0 80px #00f3ff; }
        to { text-shadow: 0 0 10px #bc13fe, 0 0 20px #bc13fe, 0 0 40px #bc13fe, 0 0 80px #bc13fe; }
    }

    /* 3. LIVE STATUS PULSE */
    .live-dot {
        height: 10px;
        width: 10px;
        background-color: #51cf66;
        border-radius: 50%;
        display: inline-block;
        animation: pulse 2s infinite;
        margin-right: 8px;
        box-shadow: 0 0 10px #51cf66;
    }

    @keyframes pulse {
        0% {box-shadow: 0 0 0 0 rgba(81, 207, 102, 0.7);}
        70% {box-shadow: 0 0 0 10px rgba(81, 207, 102, 0);}
        100% {box-shadow: 0 0 0 0 rgba(81, 207, 102, 0);}
    }

    /* 4. ANIMATED CARDS */
    .cyber-card {
        background: rgba(13, 27, 42, 0.7);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        padding: 20px;
        border: 1px solid rgba(0, 243, 255, 0.2);
        transition: all 0.4s ease;
        position: relative;
        overflow: hidden;
        text-align: center;
        height: 100%;
    }
    .cyber-card:hover {
        transform: translateY(-5px);
        border-color: #00f3ff;
        box-shadow: 0 0 25px rgba(0, 243, 255, 0.4);
    }

    /* 5. ANIMATED SIDEBAR */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0a0a0a 0%, #1b263b 100%);
        border-right: 2px solid #00f3ff;
        box-shadow: 5px 0 15px rgba(0, 243, 255, 0.2);
    }
    [data-testid="stSidebar"] * { color: #e0e0e0 !important; }

    /* 6. CUSTOM STYLING FOR STREAMLIT BUTTONS */
    .stButton > button[kind="primary"] {
        background: transparent;
        border: 2px solid #00f3ff;
        color: #00f3ff;
        font-family: 'Orbitron', sans-serif;
        font-weight: bold;
        transition: all 0.3s ease;
        border-radius: 8px;
    }
    .stButton > button[kind="primary"]:hover {
        background: #00f3ff;
        color: #050505;
        box-shadow: 0 0 20px #00f3ff;
    }
</style>
"""
st.markdown(animated_css, unsafe_allow_html=True)

# ================= HTML ANIMATED HEADER =================
html_header = """
<div class="glowing-title">
    ₿ CryptoTime
</div>
<p style="text-align: center; color: #8b949e; font-family: 'Rajdhani', sans-serif; font-size: 1.2rem; letter-spacing: 5px; margin-top: -10px;">
    <span class="live-dot"></span> SYSTEM ONLINE &nbsp;|&nbsp; ADVANCED ANALYTICS ENGINE
</p>
<hr style="border: 0px; height: 2px; background-image: linear-gradient(to right, rgba(0,0,0,0), #00f3ff, rgba(0,0,0,0)); margin: 30px 0;">
"""
st.markdown(html_header, unsafe_allow_html=True)

# Constants & Sidebar
API_URL = "http://localhost:8000"

st.sidebar.header("⚙️ CONTROL PANEL")
days_to_predict = st.sidebar.slider("Forecast Horizon (Days)", 7, 90, 30, key="horizon_slider")
st.sidebar.markdown("---")
st.sidebar.subheader("💬 Quick Sentiment")
user_text = st.sidebar.text_area("Enter news/tweet:", "Bitcoin is looking extremely bullish!", key="sentiment_text")
if st.sidebar.button("🔍 Analyze Sentiment", use_container_width=True, key="sentiment_sidebar_btn"):
    score = get_sentiment_score(user_text)
    if score > 0:
        label, color, glow = "BULLISH 😊", "#51cf66", "rgba(81,207,102,0.4)"
    elif score < 0:
        label, color, glow = "BEARISH 😟", "#ff6b6b", "rgba(255,107,107,0.4)"
    else:
        label, color, glow = "NEUTRAL 😐", "#8b949e", "rgba(139,148,158,0.4)"
    st.session_state["sentiment_result"] = dict(
        score=score, label=label, border_color=color, glow_color=glow, text=user_text
    )


# ================= TABS =================
tab1, tab2, tab3, tab4 = st.tabs(["📊 LIVE METRICS", "📈 AI PREDICTIONS", "🧠 SENTIMENT", "🔍 HISTORY SEARCH"])

# -------------------- TAB 1: METRICS --------------------
with tab1:
    try:
        kpi_res = requests.get(f"{API_URL}/api/kpi", timeout=5)
        if kpi_res.status_code == 200:
            kpi = kpi_res.json()
            cols = st.columns(4)
            card_html = """
            <div class="cyber-card">
                <p style="color: #00f3ff; margin: 0 0 10px 0; font-family: 'Rajdhani', sans-serif; font-size: 1.1rem; letter-spacing: 1px;">{title}</p>
                <h2 style="color: white; margin: 0; font-family: 'Orbitron', sans-serif; font-size: 1.8rem;">{value}</h2>
            </div>
            """
            cols[0].markdown(card_html.format(title="CURRENT PRICE", value=f"${kpi['current_price']:,.2f}"), unsafe_allow_html=True)
            cols[1].markdown(card_html.format(title="24H CHANGE", value=f"{kpi['price_change_24h']}%"), unsafe_allow_html=True)
            cols[2].markdown(card_html.format(title="MARKET CAP", value=kpi['market_cap']), unsafe_allow_html=True)
            cols[3].markdown(card_html.format(title="24H VOLUME", value=kpi['volume_24h']), unsafe_allow_html=True)
        else:
            st.error(f"Backend Error: {kpi_res.text}")
    except Exception as e:
        st.warning("⚠️ Backend not running. Start it with `python run_project.py`")

# -------------------- TAB 2: PREDICTIONS --------------------
with tab2:
    if st.button("🚀 GENERATE FORECASTS", use_container_width=True, type="primary", key="forecast_btn"):
        with st.spinner("Neural Networks processing..."):
            try:
                res = requests.get(f"{API_URL}/api/predict/all?days={days_to_predict}", timeout=120)
                if res.status_code == 200:
                    data = res.json()
                    df_pred = pd.DataFrame(data['predictions'])
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=df_pred['date'], y=df_pred['arima'], name="ARIMA", mode='lines', line=dict(color='#00f3ff', width=3, shape='spline')))
                    fig.add_trace(go.Scatter(x=df_pred['date'], y=df_pred['prophet'], name="Prophet", mode='lines', line=dict(color='#bc13fe', width=3, shape='spline')))
                    fig.add_trace(go.Scatter(x=df_pred['date'], y=df_pred['lstm'], name="LSTM", mode='lines', line=dict(color='#51cf66', width=3, shape='spline')))
                    fig.update_layout(
                        title="Future Price Trajectories",
                        template="plotly_dark",
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        font=dict(color="white", family="Rajdhani"),
                        xaxis_title="Date",
                        yaxis_title="Price (USD)"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.error(f"Prediction Error: {res.text}")
            except Exception as e:
                st.error(f"Connection Error: {e}")

# -------------------- TAB 3: SENTIMENT --------------------
with tab3:
    st.markdown("<p style='color:#8b949e; font-family:Rajdhani,sans-serif;'></p>", unsafe_allow_html=True)

    # Button lives INSIDE tab3 — result is always visible on the same screen
    if st.button("🔍 Analyze Sentiment", use_container_width=True, type="primary", key="sentiment_btn"):
        score = get_sentiment_score(user_text)
        if score > 0:
            border_color, glow_color, label = "#51cf66", "rgba(81, 207, 102, 0.4)", "BULLISH 😊"
        elif score < 0:
            border_color, glow_color, label = "#ff6b6b", "rgba(255, 107, 107, 0.4)", "BEARISH 😟"
        else:
            border_color, glow_color, label = "#8b949e", "rgba(139, 148, 158, 0.4)", "NEUTRAL 😐"
        # Persist result so it survives tab-switching reruns
        st.session_state["sentiment_result"] = dict(
            score=score, border_color=border_color,
            glow_color=glow_color, label=label, text=user_text
        )

    # Display persisted result (survives reruns / tab switches)
    if "sentiment_result" in st.session_state:
        r = st.session_state["sentiment_result"]
        st.markdown(f"""
        <div style="background:rgba(13,27,42,0.8);padding:30px;border-radius:15px;
                    border:2px solid {r['border_color']};box-shadow:0 0 30px {r['glow_color']};text-align:center;margin-top:20px;">
            <h1 style="color:{r['border_color']};font-family:'Orbitron',sans-serif;margin-bottom:10px;">{r['label']}</h1>
            <h2 style="color:white;font-family:'Orbitron',sans-serif;">Score: {r['score']:.2f}</h2>
            <p style="color:#8b949e;margin-top:15px;">"{r['text']}"</p>
        </div>
        """, unsafe_allow_html=True)

# -------------------- TAB 4: DATE SEARCH (NUCLEAR FIX) --------------------
with tab4:
    st.markdown("""
    <h2 style="font-family: 'Orbitron', sans-serif; color: #00f3ff; text-align: center;">
        ARCHIVE DATA SEARCH
    </h2>
    """, unsafe_allow_html=True)
    
    # 1. SLIDER ADDED
    history_range = st.slider("History Lookback (Days)", 30, 365, 90, key="history_slider")
    
    today = datetime.today()
    min_date = today - timedelta(days=history_range)
    
    # 2. DATE INPUT
    selected_date = st.date_input("Select Date", today, min_value=min_date, max_value=today, key="history_date")

    # Debug Mode to help troubleshoot if it fails again
    debug_mode = st.checkbox("Debug Mode (Show Raw Data)", value=False)

    if st.button("⏳ Fetch Historical Data", use_container_width=True, type="primary", key="fetch_history_btn"):
        with st.spinner("Querying Yahoo Finance Archive..."):
            try:
                end_date = selected_date + timedelta(days=1)
                btc = yf.Ticker("BTC-USD")
                hist = btc.history(start=selected_date, end=end_date)
                
                if debug_mode:
                    st.subheader("Raw Data Received:")
                    st.write(hist)
                    st.write("Columns:", hist.columns.tolist())
                    st.write("Index:", hist.index.tolist())

                if hist.empty:
                    st.error("❌ No data found for this date (Weekend/Holiday).")
                else:
                    # ================= NUCLEAR FIX: POSITIONAL INDEXING =================
                    # We completely ignore column names. We take the first row (iloc[0])
                    # and access columns by index number 0, 1, 2, 3, etc.
                    # This prevents "Series" errors caused by weird column structures.
                    
                    # Standard yfinance order: Open(0), High(1), Low(2), Close(3), Adj Close(4), Volume(5)
                    row = hist.iloc[0] # Get the first row as a Series
                    
                    open_val = float(row.iloc[0])
                    high_val = float(row.iloc[1])
                    low_val  = float(row.iloc[2])
                    close_val = float(row.iloc[3])
                    # Skip Adj Close (index 4)
                    volume_val = float(row.iloc[5])
                    # ================================================================

                    # Format Date: DD/MM/YYYY
                    formatted_date = selected_date.strftime("%d/%m/%Y")

                    # 6. DISPLAY DATA
                    h_cols = st.columns(5)
                    
                    # Date Card
                    h_cols[0].markdown(f"""
                    <div class="cyber-card">
                        <p style="color: #bc13fe; margin: 0; font-family: 'Rajdhani', sans-serif; font-size: 1rem; letter-spacing: 1px;">DATE</p>
                        <h3 style="color: white; margin: 10px 0 0 0; font-family: 'Orbitron', sans-serif; font-size: 1.2rem;">{formatted_date}</h3>
                    </div>
                    """, unsafe_allow_html=True)

                    # Open Card
                    h_cols[1].markdown(f"""
                    <div class="cyber-card">
                        <p style="color: #00f3ff; margin: 0; font-family: 'Rajdhani', sans-serif; font-size: 1rem; letter-spacing: 1px;">OPEN</p>
                        <h3 style="color: white; margin: 10px 0 0 0; font-family: 'Orbitron', sans-serif; font-size: 1.2rem;">${open_val:,.2f}</h3>
                    </div>
                    """, unsafe_allow_html=True)

                    # High Card
                    h_cols[2].markdown(f"""
                    <div class="cyber-card">
                        <p style="color: #51cf66; margin: 0; font-family: 'Rajdhani', sans-serif; font-size: 1rem; letter-spacing: 1px;">HIGH</p>
                        <h3 style="color: white; margin: 10px 0 0 0; font-family: 'Orbitron', sans-serif; font-size: 1.2rem;">${high_val:,.2f}</h3>
                    </div>
                    """, unsafe_allow_html=True)

                    # Low Card
                    h_cols[3].markdown(f"""
                    <div class="cyber-card">
                        <p style="color: #ff6b6b; margin: 0; font-family: 'Rajdhani', sans-serif; font-size: 1rem; letter-spacing: 1px;">LOW</p>
                        <h3 style="color: white; margin: 10px 0 0 0; font-family: 'Orbitron', sans-serif; font-size: 1.2rem;">${low_val:,.2f}</h3>
                    </div>
                    """, unsafe_allow_html=True)

                    # Close Card
                    h_cols[4].markdown(f"""
                    <div class="cyber-card">
                        <p style="color: #bc13fe; margin: 0; font-family: 'Rajdhani', sans-serif; font-size: 1rem; letter-spacing: 1px;">CLOSE</p>
                        <h3 style="color: white; margin: 10px 0 0 0; font-family: 'Orbitron', sans-serif; font-size: 1.2rem;">${close_val:,.2f}</h3>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    # Volume Display
                    st.markdown(f"""
                    <div style="background: rgba(13, 27, 42, 0.8); padding: 15px; border-radius: 15px; 
                                border: 1px solid #00f3ff; text-align: center; width: 50%; margin: 0 auto;">
                        <p style="color: #00f3ff; font-family: 'Rajdhani', sans-serif; letter-spacing: 2px; margin:0;">TRADING VOLUME</p>
                        <h2 style="color: white; font-family: 'Orbitron', sans-serif; margin: 5px 0 0 0;">${volume_val:,.0f}</h2>
                    </div>
                    """, unsafe_allow_html=True)

            except Exception as e:
                st.error(f"Critical Error: {str(e)}")
