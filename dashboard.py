import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import yfinance as yf
import plotly.graph_objects as go

# -----------------------
# Load tickers
# -----------------------
def get_sp500_tickers():
    try:
        with open("sp500_tickers.txt", "r") as f:
            tickers = [line.strip() for line in f if line.strip()]
        return tickers
    except Exception as e:
        st.error(f"Error loading tickers: {e}")
        return []

# -----------------------
# Technical Indicators
# -----------------------
def calculate_rsi(data, window=14):
    delta = data["Close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    data["RSI"] = 100 - (100 / (1 + rs))
    return data

def calculate_macd(data, short=12, long=26, signal=9):
    short_ema = data["Close"].ewm(span=short, adjust=False).mean()
    long_ema = data["Close"].ewm(span=long, adjust=False).mean()
    data["MACD"] = short_ema - long_ema
    data["Signal"] = data["MACD"].ewm(span=signal, adjust=False).mean()
    return data

def calculate_bollinger_bands(data, window=20, num_std=2):
    rolling_mean = data["Close"].rolling(window=window).mean()
    rolling_std = data["Close"].rolling(window=window).std()
    data["BB_Upper"] = rolling_mean + (rolling_std * num_std)
    data["BB_Lower"] = rolling_mean - (rolling_std * num_std)
    return data

def get_confluence_levels(hist, show_ma=True, show_bb=True):
    levels = []
    if show_ma:
        levels += [hist["MA20"].iloc[-1], hist["MA50"].iloc[-1]]
    if show_bb:
        levels += [hist["BB_Upper"].iloc[-1], hist["BB_Lower"].iloc[-1]]
    levels += [hist['Close'].max(), hist['Close'].min()]
    levels = sorted(list(set([round(x, 2) for x in levels])))
    return levels

# -----------------------
# Streamlit App
# -----------------------
st.set_page_config(page_title="S&P 500 Interactive Dashboard", layout="wide")
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to:", ["Dashboard", "Info"])

# -----------------------
# Information Page
# -----------------------
if page == "Info":
    st.title("ℹ️ Dashboard Information")
    st.markdown("""
    Welcome to the S&P 500 Interactive Dashboard! This page explains all the tools and indicators used in the dashboard, with tips for beginners.  

    ---

    ### **1. Moving Averages (MA20 & MA50)**
    - **What it is:** The average closing price over 20 or 50 days.  
    - **Purpose:** Identify trend direction and potential reversal points.  
    - **Signals & Tips:**  
        - Price above MA → bullish trend, below MA → bearish trend.  
        - MA20 crossing MA50 → short/medium-term trend signal.  

    ### **2. Bollinger Bands**
    - **What it is:** Bands 2 standard deviations above/below MA20.  
    - **Purpose:** Measure volatility; detect overbought/oversold.  
    - **Signals & Tips:**  
        - Price near upper band → overbought; lower band → oversold.  
        - Narrow bands (squeeze) → low volatility, often precedes strong moves.  

    ### **3. RSI (Relative Strength Index)**
    - **What it is:** Momentum oscillator 0–100.  
    - **Purpose:** Detect overbought (>70) or oversold (<30).  
    - **Signals & Tips:**  
        - RSI >70 → potential reversal down; RSI <30 → potential reversal up.  
        - Divergence with price can indicate trend change.  

    ### **4. MACD**
    - **What it is:** Difference between 12-day & 26-day EMA; signal line = 9-day EMA of MACD.  
    - **Purpose:** Identify trend and momentum.  
    - **Signals & Tips:**  
        - MACD crosses above Signal → bullish, below → bearish.  
        - Use with volume and confluence for higher confidence.  

    ### **5. Volume**
    - **What it is:** Number of shares traded.  
    - **Purpose:** Confirm strength of price moves.  
    - **Signals & Tips:**  
        - Rising volume confirms trend; spikes may indicate breakouts or reversals.  

    ### **6. Confluence Levels**
    - **What it is:** Price levels where multiple indicators align (MA, Bollinger Bands, highs/lows).  
    - **Purpose:** Strong support/resistance zones.  
    - **Signals & Tips:**  
        - Price reaction likely near these levels; more indicators agreeing → stronger level.  

    ### **7. CSV Download**
    - **Purpose:** Export historical data for further analysis or backtesting.  

    ---
    
    **General Tips for Beginners:**  
    - Combine multiple indicators for confirmation.  
    - Check trend on larger timeframes before trading short-term.  
    - Zoom and interact with charts; toggle indicators to explore patterns.  
    - Practice on historical data before live trades.
    """)

# -----------------------
# Dashboard
# -----------------------
else:
    st.title("📈 S&P 500 Interactive Dashboard")
    tickers = get_sp500_tickers()
    selected = st.selectbox("Select a company:", tickers if tickers else ["None"])

    if selected != "None":
        try:
            ticker_symbol = selected.split("(")[-1].replace(")", "").strip()

            # Date range
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Start date", datetime.now() - timedelta(days=365))
            with col2:
                end_date = st.date_input("End date", datetime.now())

            st.write(f"Fetching historical data for: {ticker_symbol}")

            # ----------------------- NEW: Intraday support -----------------------
            if start_date == end_date:
                hist = yf.download(
                    ticker_symbol,
                    start=start_date,
                    end=start_date + timedelta(days=1),  # yfinance requires end > start
                    interval="5m"  # Intraday interval: 1m, 5m, 15m, etc.
                ).dropna()
                hist.columns = hist.columns.get_level_values(0)
                if hist.empty:
                    st.warning("No intraday data available for this ticker on this date.")
            else:
                hist = yf.download(ticker_symbol, start=start_date, end=end_date).dropna()
                hist.columns = hist.columns.get_level_values(0)

            filtered_hist = hist.loc[start_date:end_date]

            if filtered_hist.empty:
                st.warning("No historical data available for this ticker in the selected date range.")
            else:
                st.subheader(selected)

                # ------------------- Last N Days Table -------------------
                n_days = 10
                last_n_days = filtered_hist.tail(n_days)
                st.write(f"### Last {min(n_days, len(filtered_hist))} Days of Historical Prices")
                st.dataframe(last_n_days)

                # Sidebar indicators
                st.sidebar.header("Chart Options")
                show_ma = st.sidebar.checkbox("Show Moving Averages (MA20 & MA50)", value=True)
                show_bb = st.sidebar.checkbox("Show Bollinger Bands", value=True)
                show_rsi = st.sidebar.checkbox("Show RSI", value=True)
                show_macd = st.sidebar.checkbox("Show MACD", value=True)
                show_volume = st.sidebar.checkbox("Show Volume", value=True)
                show_confluence = st.sidebar.checkbox("Show Confluence Levels", value=True)

                # ------------------- Calculate Indicators -------------------
                if show_ma:
                    filtered_hist["MA20"] = filtered_hist["Close"].rolling(window=20).mean()
                    filtered_hist["MA50"] = filtered_hist["Close"].rolling(window=50).mean()
                if show_bb:
                    filtered_hist = calculate_bollinger_bands(filtered_hist)
                if show_rsi:
                    filtered_hist = calculate_rsi(filtered_hist)
                if show_macd:
                    filtered_hist = calculate_macd(filtered_hist)
                if show_confluence:
                    confluence_levels = get_confluence_levels(filtered_hist, show_ma, show_bb)

                # ------------------- Price Chart -------------------
                st.write("### Price Chart with Indicators")
                fig = go.Figure()

                # Close price
                fig.add_trace(go.Scatter(
                    x=filtered_hist.index,
                    y=filtered_hist["Close"],
                    mode="lines" if len(filtered_hist) > 1 else "lines+markers",
                    name="Close",
                    marker=dict(size=6)
                ))

                # Moving Averages
                if show_ma:
                    fig.add_trace(go.Scatter(x=filtered_hist.index, y=filtered_hist["MA20"], mode="lines", name="MA20"))
                    fig.add_trace(go.Scatter(x=filtered_hist.index, y=filtered_hist["MA50"], mode="lines", name="MA50"))

                # Bollinger Bands
                if show_bb:
                    fig.add_trace(go.Scatter(x=filtered_hist.index, y=filtered_hist["BB_Upper"], mode="lines", name="BB Upper", line=dict(dash="dash")))
                    fig.add_trace(go.Scatter(x=filtered_hist.index, y=filtered_hist["BB_Lower"], mode="lines", name="BB Lower", line=dict(dash="dash")))

                # Confluence levels
                if show_confluence:
                    for level in confluence_levels:
                        fig.add_hline(y=level, line_dash="dot", line_color="purple", annotation_text=f"Confluence: {level}", annotation_position="top right")

                st.plotly_chart(fig, use_container_width=True)

                # ------------------- Volume Chart -------------------
                if show_volume:
                    st.write("### Volume")
                    fig_vol = go.Figure()
                    fig_vol.add_trace(go.Bar(x=filtered_hist.index, y=filtered_hist["Volume"], name="Volume"))
                    st.plotly_chart(fig_vol, use_container_width=True)

                # ------------------- RSI Chart -------------------
                if show_rsi:
                    st.write("### RSI")
                    fig_rsi = go.Figure()
                    fig_rsi.add_trace(go.Scatter(x=filtered_hist.index, y=filtered_hist["RSI"], mode="lines", name="RSI"))
                    fig_rsi.add_hline(y=70, line_dash="dash", line_color="red")
                    fig_rsi.add_hline(y=30, line_dash="dash", line_color="green")
                    st.plotly_chart(fig_rsi, use_container_width=True)

                # ------------------- MACD Chart -------------------
                if show_macd:
                    st.write("### MACD")
                    fig_macd = go.Figure()
                    fig_macd.add_trace(go.Scatter(x=filtered_hist.index, y=filtered_hist["MACD"], mode="lines", name="MACD"))
                    fig_macd.add_trace(go.Scatter(x=filtered_hist.index, y=filtered_hist["Signal"], mode="lines", name="Signal"))
                    st.plotly_chart(fig_macd, use_container_width=True)

                # ------------------- Summary Metrics -------------------
                st.write("### Summary Metrics")
                st.metric("Start Price", f"${filtered_hist['Close'].iloc[0]:.2f}")
                st.metric("Current Price", f"${filtered_hist['Close'].iloc[-1]:.2f}")
                st.metric("High", f"${filtered_hist['High'].max():.2f}")
                st.metric("Low", f"${filtered_hist['Low'].min():.2f}")

                # ------------------- Download CSV -------------------
                csv = filtered_hist.to_csv().encode("utf-8")
                st.download_button(
                    label="⬇️ Download filtered data as CSV",
                    data=csv,
                    file_name=f"{ticker_symbol}_historical_filtered.csv",
                    mime="text/csv",
                )

            st.write(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        except Exception as e:
            st.error(f"Error fetching data: {e}")
