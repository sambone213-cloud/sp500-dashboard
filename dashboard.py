import streamlit as st
import yfinance as yf
import pandas as pd

# -----------------------
# Load tickers from file
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
# Streamlit App
# -----------------------
st.set_page_config(page_title="S&P 500 Dashboard", layout="wide")
st.title("📈 S&P 500 Dashboard")

tickers = get_sp500_tickers()
selected_ticker = st.selectbox("Select a company:", tickers)

if selected_ticker != "None":
    # Extract ticker symbol from format "Company Name (TICKER)"
    ticker_symbol = selected_ticker.split("(")[-1].replace(")", "").strip()
    stock = yf.Ticker(ticker_symbol)

    st.subheader(f"{selected_ticker}")

    # Safely get price data
    try:
        hist = stock.history(period="1y")  # last 1 year
        st.line_chart(hist['Close'])
    except Exception as e:
        st.error(f"Could not fetch historical data: {e}")

    # Fast info (avoids 403)
    try:
        info = stock.fast_info
        st.write("Market Cap:", info.get("market_cap"))
        st.write("Previous Close:", info.get("previous_close"))
        st.write("Open:", info.get("open"))
        st.write("Day High:", info.get("day_high"))
        st.write("Day Low:", info.get("day_low"))
    except Exception as e:
        st.error(f"Could not fetch fast info: {e}")



