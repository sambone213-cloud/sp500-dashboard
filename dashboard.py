import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# Load tickers
def get_sp500_tickers():
    try:
        with open("sp500_tickers.txt", "r") as f:
            tickers = [line.strip() for line in f if line.strip()]
        return tickers
    except Exception as e:
        st.error(f"Error loading tickers: {e}")
        return []

st.set_page_config(page_title="S&P 500 Dashboard", layout="wide")
st.title("📈 S&P 500 Dashboard (Historical Data)")

tickers = get_sp500_tickers()
selected = st.selectbox("Select a company:", tickers if tickers else ["None"])

if selected != "None":
    # Extract ticker cleanly
    try:
        ticker_symbol = selected.split("(")[-1].replace(")", "").strip()
        st.write(f"Ticker symbol: {ticker_symbol}")
        stock = yf.Ticker(ticker_symbol)

        # Fetch historical data (1 year daily)
        hist = stock.history(period="1y", interval="1d")
        if hist.empty:
            st.warning("No historical data available for this ticker.")
        else:
            st.subheader(selected)
            st.write("### Last 10 Days of Historical Prices")
            st.dataframe(hist.tail(10))
            st.line_chart(hist['Close'])

            # Summary metrics
            st.write("### Summary Metrics (1 Year)")
            st.metric("Start Price (1y ago)", f"${hist['Close'].iloc[0]:.2f}")
            st.metric("Current Price", f"${hist['Close'].iloc[-1]:.2f}")
            st.metric("High (1y)", f"${hist['High'].max():.2f}")
            st.metric("Low (1y)", f"${hist['Low'].min():.2f}")

        st.write(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    except Exception as e:
        st.error(f"Error fetching data: {e}")



