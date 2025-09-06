import streamlit as st
import yfinance as yf
import pandas as pd

# -----------------------
# Load S&P 500 tickers from a local file
# Format in the file: Company Name (TICKER)
# -----------------------
def get_sp500_tickers(file_path="sp500_tickers.txt"):
    try:
        with open(file_path, "r") as f:
            tickers = [line.strip() for line in f if line.strip()]
        return tickers
    except Exception as e:
        st.error(f"Error loading tickers: {e}")
        return []

# -----------------------
# Streamlit App Setup
# -----------------------
st.set_page_config(page_title="S&P 500 Dashboard", layout="wide")
st.title("📈 S&P 500 Dashboard")

# Load tickers
tickers = get_sp500_tickers()

if tickers:
    st.success(f"Loaded {len(tickers)} tickers!")
else:
    st.warning("No tickers loaded.")

# -----------------------
# Ticker Selection
# -----------------------
selected_ticker = st.selectbox(
    "Select a company:",
    options=tickers,
    index=0,
    help="Search by company name or ticker"
)

# -----------------------
# Display Stock Info
# -----------------------
if selected_ticker and selected_ticker != "None":
    ticker_symbol = selected_ticker.split("(")[-1].replace(")", "")
    stock = yf.Ticker(ticker_symbol)
    info = stock.info

    # Metrics row
    st.subheader(f"{info.get('shortName', selected_ticker)} ({ticker_symbol})")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Current Price", f"${info.get('currentPrice', 'N/A')}")
    col2.metric("Day Change", f"{info.get('dayChange', 'N/A')}")
    col3.metric("Market Cap", f"${info.get('marketCap', 'N/A'):,}")
    col4.metric("PE Ratio", f"{info.get('trailingPE', 'N/A')}")

    # Stock History Chart
    st.subheader("📊 Price Chart (1 Month)")
    hist = stock.history(period="1mo")
    st.line_chart(hist['Close'])

    # Additional Info
    st.subheader("Company Info")
    st.write({
        "Sector": info.get('sector', 'N/A'),
        "Industry": info.get('industry', 'N/A'),
        "Website": info.get('website', 'N/A'),
        "Description": info.get('longBusinessSummary', 'N/A')
    })



