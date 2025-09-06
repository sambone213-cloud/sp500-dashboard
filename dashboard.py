import streamlit as st

# -----------------------
# Function to load tickers from a local file
# Format in file: Company Name (TICKER)
# -----------------------
def get_sp500_tickers():
    try:
        with open("sp500_tickers.txt", "r") as f:
            tickers = []
            for line in f:
                line = line.strip()
                if line:
                    # Extract ticker from parentheses
                    if "(" in line and ")" in line:
                        ticker = line.split("(")[-1].replace(")", "").strip()
                        name = line.split("(")[0].strip()
                        tickers.append(f"{name} ({ticker})")
                    else:
                        tickers.append(line)
        return tickers
    except Exception as e:
        st.error(f"Error loading tickers: {e}")
        return []

# -----------------------
# Streamlit App
# -----------------------
st.set_page_config(page_title="S&P 500 Dashboard", layout="wide")
st.title("S&P 500 Dashboard")

tickers = get_sp500_tickers()

if tickers:
    st.success(f"Loaded {len(tickers)} tickers!")
    st.write(tickers[:20])  # Show first 20 tickers
else:
    st.warning("No tickers loaded.")

selected_ticker = st.selectbox("Select a ticker", tickers if tickers else ["None"])

if selected_ticker != "None":
    st.write(f"You selected: {selected_ticker}")
