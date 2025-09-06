import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

def get_sp500_tickers():
    try:
        with open("sp500_tickers.txt", "r") as f:
            tickers = [line.strip() for line in f if line.strip()]
        return tickers
    except Exception as e:
        st.error(f"Error loading tickers: {e}")
        return []

st.set_page_config(page_title="S&P 500 Dashboard", layout="wide")
st.title("📈 S&P 500 Dashboard")

tickers = get_sp500_tickers()

selected = st.selectbox("Select a company:", tickers if tickers else ["None"])

if selected != "None":
    ticker_symbol = selected.split("(")[-1].replace(")", "")
    stock = yf.Ticker(ticker_symbol)

    st.subheader(selected)

    # ------------------------
    # Fetch fast info (reliable)
    # ------------------------
    try:
        fast = stock.fast_info  # fast_info avoids 403
        st.metric("Current Price", f"${fast['last_price']:.2f}")
        st.metric("Day High", f"${fast['day_high']:.2f}")
        st.metric("Day Low", f"${fast['day_low']:.2f}")
        st.metric("Open", f"${fast['open']:.2f}")
        st.metric("Previous Close", f"${fast['previous_close']:.2f}")
        st.metric("Market Cap", f"${fast['market_cap']:,}")
    except Exception as e:
        st.warning(f"Could not fetch fast info: {e}")

    # ------------------------
    # Historical chart (fallback)
    # ------------------------
    try:
        hist = stock.history(period="5d", interval="1h")  # 5 days, hourly
        if not hist.empty:
            st.line_chart(hist['Close'])
        else:
            st.info("No historical chart available.")
    except Exception as e:
        st.warning(f"Could not fetch historical data: {e}")

    st.write(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")




