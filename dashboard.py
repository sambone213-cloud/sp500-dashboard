import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import yfinance as yf

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
    rsi = 100 - (100 / (1 + rs))
    data["RSI"] = rsi
    return data

def calculate_macd(data, short=12, long=26, signal=9):
    short_ema = data["Close"].ewm(span=short, adjust=False).mean()
    long_ema = data["Close"].ewm(span=long, adjust=False).mean()
    data["MACD"] = short_ema - long_ema
    data["Signal"] = data["MACD"].ewm(span=signal, adjust=False).mean()
    return data

# -----------------------
# Streamlit App
# -----------------------
st.set_page_config(page_title="S&P 500 Dashboard (Yahoo Finance)", layout="wide")
st.title("📈 S&P 500 Dashboard (Yahoo Finance Data)")

tickers = get_sp500_tickers()
selected = st.selectbox("Select a company:", tickers if tickers else ["None"])

if selected != "None":
    try:
        # Extract ticker symbol (the part in parentheses, e.g., "AAPL")
        ticker_symbol = selected.split("(")[-1].replace(")", "").strip()

        # Date range picker (default: last 1 year)
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start date", datetime.now() - timedelta(days=365))
        with col2:
            end_date = st.date_input("End date", datetime.now())

        st.write(f"Fetching historical data for: {ticker_symbol}")

        # Fetch historical data from Yahoo Finance
        hist = yf.download(ticker_symbol, start=start_date, end=end_date)
        hist = hist.dropna()

        # Flatten columns in case yfinance returns MultiIndex
        hist.columns = hist.columns.get_level_values(0)

        if hist.empty:
            st.warning("No historical data available for this

