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
    ticker_symbol = selected.split("(")[-1].replace(")", "")
    stock = yf.Ticker(ticker_symbol)

    st.subheader(selected)

    # ------------------------
    # Fetch historical data (default 6 months)
    # ------------------------
    try:
        hist = stock.history(period="6mo", interval="1d")  # 6 months daily
        if not hist.empty:
            st.write("### Historical Prices")
            st.dataframe(hist.tail(10))  # Show last 10 rows
            st.line_chart(hist['Close'])
            
            # Summary metrics
            st.write("### Summary Metrics")
            st.metric("Start Price (6mo ago)", f"${hist['Close'].iloc[0]:.2f}")
            st.metric("Current Price", f"${hist['Close'].iloc[-1]:.2f}")
            st.metric("High (6mo)", f"${hist['High'].max():.2f}")
            st.metric("Low (6mo)", f"${hist['Low'].min():.2f}")
        else:
            st.info("No historical data available.")
    except Exception as e:
        st.warning(f"Could not fetch historical data: {e}")

    st.write(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")




