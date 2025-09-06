import streamlit as st
import pandas as pd
from datetime import datetime
from pandas_datareader import data as pdr

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
# Streamlit App
# -----------------------
st.set_page_config(page_title="S&P 500 Dashboard (Stooq)", layout="wide")
st.title("📈 S&P 500 Dashboard (Stooq Historical Data)")

tickers = get_sp500_tickers()
selected = st.selectbox("Select a company:", tickers if tickers else ["None"])

if selected != "None":
    # Extract ticker symbol and replace dots for Stooq format
    try:
        ticker_symbol = selected.split("(")[-1].replace(")", "").strip()
        ticker_symbol_stooq = ticker_symbol.replace(".", "").upper() + ".US"  # e.g., BRK.B -> BRKB.US
        st.write(f"Fetching historical data for: {ticker_symbol_stooq}")

        # Fetch historical data from Stooq
        hist = pdr.DataReader(ticker_symbol_stooq, "stooq")
        hist = hist.sort_index()  # oldest to newest

        if hist.empty:
            st.warning("No historical data available for this ticker.")
        else:
            st.subheader(selected)
            st.write("### Last 10 Days of Historical Prices")
            st.dataframe(hist.tail(10))
            st.line_chart(hist['Close'])

            # Summary metrics
            st.write("### Summary Metrics")
            st.metric("Start Price", f"${hist['Close'].iloc[0]:.2f}")
            st.metric("Current Price", f"${hist['Close'].iloc[-1]:.2f}")
            st.metric("High", f"${hist['High'].max():.2f}")
            st.metric("Low", f"${hist['Low'].min():.2f}")

        st.write(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    except Exception as e:
        st.error(f"Error fetching data: {e}")



