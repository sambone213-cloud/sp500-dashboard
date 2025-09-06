import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# -----------------------
# Function to load tickers from a local file
# -----------------------
def get_sp500_tickers():
    try:
        with open("sp500_tickers.txt", "r") as f:
            # Expecting format: Company Name (TICKER)
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

if tickers:
    st.success(f"Loaded {len(tickers)} tickers!")
else:
    st.warning("No tickers loaded.")

selected = st.selectbox("Select a company:", tickers if tickers else ["None"])

if selected != "None":
    # Extract ticker symbol from string
    try:
        ticker_symbol = selected.split("(")[-1].replace(")", "")
        stock = yf.Ticker(ticker_symbol)

        # Fetch recent 1-day intraday data
        hist = stock.history(period="1d", interval="5m")
        if hist.empty:
            st.warning("No recent data available.")
        else:
            current_price = hist['Close'].iloc[-1]
            open_price = hist['Open'].iloc[-1]
            day_high = hist['High'].iloc[-1]
            day_low = hist['Low'].iloc[-1]
            volume = hist['Volume'].iloc[-1]

            st.subheader(f"{selected}")
            col1, col2, col3 = st.columns(3)
            col1.metric("Current Price", f"${current_price:.2f}")
            col2.metric("Open", f"${open_price:.2f}")
            col3.metric("High / Low", f"${day_high:.2f} / ${day_low:.2f}")
            st.metric("Volume", f"{volume:,}")

            # Line chart for recent prices
            st.line_chart(hist['Close'], use_container_width=True)

            # Last updated
            st.write(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

            # Auto-refresh every 60 seconds
            st.experimental_rerun()
    except Exception as e:
        st.error(f"Error fetching data for {selected}: {e}")


