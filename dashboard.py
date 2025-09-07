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

# -----------------------
# Streamlit App
# -----------------------
st.set_page_config(page_title="S&P 500 Dashboard (Interactive)", layout="wide")
st.title("📈 S&P 500 Interactive Dashboard (Yahoo Finance)")

tickers = get_sp500_tickers()
selected = st.selectbox("Select a company:", tickers if tickers else ["None"])

if selected != "None":
    try:
        ticker_symbol = selected.split("(")[-1].replace(")", "").strip()

        # Date range picker
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start date", datetime.now() - timedelta(days=365))
        with col2:
            end_date = st.date_input("End date", datetime.now())

        st.write(f"Fetching historical data for: {ticker_symbol}")

        # Fetch historical data
        hist = yf.download(ticker_symbol, start=start_date, end=end_date)
        hist = hist.dropna()
        hist.columns = hist.columns.get_level_values(0)

        if hist.empty:
            st.warning("No historical data available for this ticker.")
        else:
            st.subheader(selected)
            st.write("### Last 10 Days of Historical Prices")
            st.dataframe(hist.tail(10))

            # Sidebar: select indicators
            st.sidebar.header("Chart Options")
            show_ma = st.sidebar.checkbox("Show Moving Averages (MA20 & MA50)", value=True)
            show_bb = st.sidebar.checkbox("Show Bollinger Bands", value=True)
            show_rsi = st.sidebar.checkbox("Show RSI", value=True)
            show_macd = st.sidebar.checkbox("Show MACD", value=True)
            show_volume = st.sidebar.checkbox("Show Volume", value=True)

            # Calculate indicators
            if show_ma:
                hist["MA20"] = hist["Close"].rolling(window=20).mean()
                hist["MA50"] = hist["Close"].rolling(window=50).mean()
            if show_bb:
                hist = calculate_bollinger_bands(hist)
            if show_rsi:
                hist = calculate_rsi(hist)
            if show_macd:
                hist = calculate_macd(hist)

            # Price chart with optional indicators
            st.write("### Price Chart")
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=hist.index, y=hist["Close"], mode="lines", name="Close"))

            if show_ma:
                fig.add_trace(go.Scatter(x=hist.index, y=hist["MA20"], mode="lines", name="MA20"))
                fig.add_trace(go.Scatter(x=hist.index, y=hist["MA50"], mode="lines", name="MA50"))
            if show_bb:
                fig.add_trace(go.Scatter(x=hist.index, y=hist["BB_Upper"], mode="lines", name="BB Upper", line=dict(dash="dash")))
                fig.add_trace(go.Scatter(x=hist.index, y=hist["BB_Lower"], mode="lines", name="BB Lower", line=dict(dash="dash")))

            st.plotly_chart(fig, use_container_width=True)

            # Volume chart
            if show_volume:
                st.write("### Volume")
                fig_vol = go.Figure()
                fig_vol.add_trace(go.Bar(x=hist.index, y=hist["Volume"], name="Volume"))
                st.plotly_chart(fig_vol, use_container_width=True)

            # RSI chart
            if show_rsi:
                st.write("### RSI")
                fig_rsi = go.Figure()
                fig_rsi.add_trace(go.Scatter(x=hist.index, y=hist["RSI"], mode="lines", name="RSI"))
                fig_rsi.add_hline(y=70, line_dash="dash", line_color="red")
                fig_rsi.add_hline(y=30, line_dash="dash", line_color="green")
                st.plotly_chart(fig_rsi, use_container_width=True)

            # MACD chart
            if show_macd:
                st.write("### MACD")
                fig_macd = go.Figure()
                fig_macd.add_trace(go.Scatter(x=hist.index, y=hist["MACD"], mode="lines", name="MACD"))
                fig_macd.add_trace(go.Scatter(x=hist.index, y=hist["Signal"], mode="lines", name="Signal"))
                st.plotly_chart(fig_macd, use_container_width=True)

            # Summary Metrics
            st.write("### Summary Metrics")
            st.metric("Start Price", f"${hist['Close'].iloc[0]:.2f}")
            st.metric("Current Price", f"${hist['Close'].iloc[-1]:.2f}")
            st.metric("High", f"${hist['High'].max():.2f}")
            st.metric("Low", f"${hist['Low'].min():.2f}")

            # Download CSV
            csv = hist.to_csv().encode("utf-8")
            st.download_button(
                label="⬇️ Download data as CSV",
                data=csv,
                file_name=f"{ticker_symbol}_historical.csv",
                mime="text/csv",
            )

        st.write(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    except Exception as e:
        st.error(f"Error fetching data: {e}")
