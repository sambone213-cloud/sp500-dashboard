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
    ticker_symbol = selected_ticker.split("(")[-1].replace(")", "").strip()
    stock = yf.Ticker(ticker_symbol)

    st.subheader(f"{selected_ticker}")

    # -----------------------
    # Time range selector
    # -----------------------
    period = st.selectbox(
        "Select time range for chart:",
        ["1mo", "3mo", "6mo", "1y", "5y", "max"],
        index=3
    )

    # -----------------------
    # Fetch historical data safely
    # -----------------------
    try:
        hist = stock.history(period=period)
        st.line_chart(hist['Close'])
        st.bar_chart(hist['Volume'])
    except Exception as e:
        st.error(f"Could not fetch historical data: {e}")

    # -----------------------
    # Display key metrics safely
    # -----------------------
    try:
        info = stock.fast_info

        st.markdown("### Key Metrics")
        cols = st.columns(3)
        cols[0].metric("Previous Close", info.get("previous_close", "N/A"))
        cols[1].metric("Open", info.get("open", "N/A"))
        cols[2].metric("Day High", info.get("day_high", "N/A"))

        cols = st.columns(3)
        cols[0].metric("Day Low", info.get("day_low", "N/A"))
        cols[1].metric("Market Cap", info.get("market_cap", "N/A"))
        cols[2].metric("Volume", info.get("volume", "N/A"))

    except Exception as e:
        st.error(f"Could not fetch fast info: {e}")
