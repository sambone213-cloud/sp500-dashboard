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

        if hist.empty:
            st.warning("No historical data available for this ticker.")
        else:
            st.subheader(selected)

            # Show last 10 rows
            st.write("### Last 10 Days of Historical Prices")
            st.dataframe(hist.tail(10))

            # Add Moving Averages
            hist["MA20"] = hist["Close"].rolling(window=20).mean()
            hist["MA50"] = hist["Close"].rolling(window=50).mean()
            ma_df = hist[["Close", "MA20", "MA50"]]

            st.write("### Closing Price with Moving Averages")
            st.line_chart(ma_df)

            # Volume chart
            st.write("### Trading Volume")
            st.bar_chart(hist["Volume"])

            # RSI
            hist = calculate_rsi(hist)
            st.write("### Relative Strength Index (RSI)")
            st.line_chart(hist["RSI"])

            # MACD
            hist = calculate_macd(hist)
            st.write("### MACD (12, 26, 9)")
            st.line_chart(hist[["MACD", "Signal"]])

            # Summary metrics
            st.write("### Summary Metrics")
            st.metric("Start Price", f"${hist['Close'].iloc[0]:.2f}")
            st.metric("Current Price", f"${hist['Close'].iloc[-1]:.2f}")
            st.metric("High", f"${hist['High'].max():.2f}")
            st.metric("Low", f"${hist['Low'].min():.2f}")

            # Download button
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
