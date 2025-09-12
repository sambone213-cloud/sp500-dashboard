import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime

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
# Indicator Functions
# -----------------------
def calculate_bollinger_bands(df, window=20):
    df["MA20"] = df["Close"].rolling(window=window).mean()
    df["BB_up"] = df["MA20"] + 2 * df["Close"].rolling(window=window).std()
    df["BB_dn"] = df["MA20"] - 2 * df["Close"].rolling(window=window).std()
    return df

def calculate_rsi(df, periods=14):
    delta = df["Close"].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=periods).mean()
    avg_loss = loss.rolling(window=periods).mean()
    rs = avg_gain / avg_loss
    df["RSI"] = 100 - (100 / (1 + rs))
    return df

def calculate_macd(df):
    exp1 = df["Close"].ewm(span=12, adjust=False).mean()
    exp2 = df["Close"].ewm(span=26, adjust=False).mean()
    df["MACD"] = exp1 - exp2
    df["Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
    return df

# -----------------------
# Streamlit App
# -----------------------
st.set_page_config(page_title="S&P 500 Dashboard", layout="wide")
st.title("📈 S&P 500 Dashboard")

# Sidebar
st.sidebar.header("Settings")
tickers = get_sp500_tickers()
selected = st.sidebar.selectbox("Select a company:", tickers if tickers else ["None"])

start_date = st.sidebar.date_input("Start Date", datetime(2020, 1, 1))
end_date = st.sidebar.date_input("End Date", datetime.now())

show_ma = st.sidebar.checkbox("Show Moving Averages", True)
show_bb = st.sidebar.checkbox("Show Bollinger Bands", False)
show_rsi = st.sidebar.checkbox("Show RSI", False)
show_macd = st.sidebar.checkbox("Show MACD", False)

if selected != "None":
    try:
        ticker_symbol = selected.split("(")[-1].replace(")", "").strip()
        st.write(f"Fetching historical data for: {ticker_symbol}")

        hist = yf.download(ticker_symbol, start=start_date, end=end_date)
        hist = hist.sort_index()

        if hist.empty:
            st.warning("No historical data available for this ticker.")
        else:
            st.subheader(selected)
            st.write("### Last 10 Days of Historical Prices")
            st.dataframe(hist.tail(10))

            # ------------------- Price Chart -------------------
            st.write("### Price Chart with Indicators")

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=hist.index, y=hist["Close"], mode="lines", name="Close"))

            if show_ma:
                if len(hist) >= 20:
                    hist["MA20"] = hist["Close"].rolling(window=20).mean()
                    fig.add_trace(go.Scatter(x=hist.index, y=hist["MA20"], mode="lines", name="MA20"))
                if len(hist) >= 50:
                    hist["MA50"] = hist["Close"].rolling(window=50).mean()
                    fig.add_trace(go.Scatter(x=hist.index, y=hist["MA50"], mode="lines", name="MA50"))

            if show_bb and len(hist) >= 20:
                hist = calculate_bollinger_bands(hist)
                fig.add_trace(go.Scatter(x=hist.index, y=hist["BB_up"], line=dict(dash="dot"), name="BB Upper"))
                fig.add_trace(go.Scatter(x=hist.index, y=hist["BB_dn"], line=dict(dash="dot"), name="BB Lower"))

            fig.update_layout(title="Closing Price with Indicators", xaxis_title="Date", yaxis_title="Price")
            st.plotly_chart(fig, use_container_width=True)
            st.caption("ℹ️ Moving Averages need at least 20–50 days. Bollinger Bands require 20 days. "
                       "If your range is shorter, expand the dates to see these indicators.")

            # ------------------- One Data Point View -------------------
            if len(hist) < 5:
                st.write("### One Data Point View")
                fig_one = go.Figure()
                fig_one.add_trace(go.Scatter(
                    x=hist.index,
                    y=hist["Close"],
                    mode="markers+text",
                    text=[f"${val:.2f}" for val in hist["Close"]],
                    textposition="top center",
                    marker=dict(size=12, color="orange"),
                    name="Close"
                ))
                fig_one.update_layout(
                    title="Minimal Price View (Works with 1 Data Point)",
                    xaxis_title="Date",
                    yaxis_title="Close Price"
                )
                st.plotly_chart(fig_one, use_container_width=True)
                st.caption("📌 This minimal chart is shown when there are not enough data points for indicators.")

            # ------------------- Volume Chart -------------------
            st.write("### Volume Chart")
            fig_vol = go.Figure()
            fig_vol.add_trace(go.Bar(x=hist.index, y=hist["Volume"], name="Volume"))
            fig_vol.update_layout(title="Trading Volume", xaxis_title="Date", yaxis_title="Volume")
            st.plotly_chart(fig_vol, use_container_width=True)
            st.caption("ℹ️ Spikes in volume often occur around earnings reports, major news, or institutional moves.")

            # ------------------- RSI -------------------
            if show_rsi:
                st.write("### RSI Chart")
                if len(hist) >= 14:
                    hist = calculate_rsi(hist)
                    fig_rsi = go.Figure()
                    fig_rsi.add_trace(go.Scatter(x=hist.index, y=hist["RSI"], name="RSI"))
                    fig_rsi.add_hline(y=70, line=dict(color="red", dash="dash"))
                    fig_rsi.add_hline(y=30, line=dict(color="green", dash="dash"))
                    fig_rsi.update_layout(title="Relative Strength Index (RSI)", xaxis_title="Date", yaxis_title="RSI")
                    st.plotly_chart(fig_rsi, use_container_width=True)
                    st.caption("ℹ️ RSI requires 14 data points. Above 70 = overbought, below 30 = oversold.")
                else:
                    st.info("Not enough data for RSI (requires at least 14 days).")

            # ------------------- MACD -------------------
            if show_macd:
                st.write("### MACD Chart")
                if len(hist) >= 26:
                    hist = calculate_macd(hist)
                    fig_macd = go.Figure()
                    fig_macd.add_trace(go.Scatter(x=hist.index, y=hist["MACD"], name="MACD"))
                    fig_macd.add_trace(go.Scatter(x=hist.index, y=hist["Signal"], name="Signal"))
                    fig_macd.update_layout(title="MACD", xaxis_title="Date", yaxis_title="Value")
                    st.plotly_chart(fig_macd, use_container_width=True)
                    st.caption("ℹ️ MACD requires 26 data points. Crossovers can indicate potential trend shifts.")
                else:
                    st.info("Not enough data for MACD (requires at least 26 days).")

            # ------------------- Summary Metrics -------------------
            st.write("### Summary Metrics")
            st.metric("Start Price", f"${hist['Close'].iloc[0]:.2f}")
            st.metric("Current Price", f"${hist['Close'].iloc[-1]:.2f}")
            st.metric("High", f"${hist['High'].max():.2f}")
            st.metric("Low", f"${hist['Low'].min():.2f}")

            # ------------------- Download Data -------------------
            st.download_button(
                label="Download Data as CSV",
                data=hist.to_csv().encode("utf-8"),
                file_name=f"{ticker_symbol}_data.csv",
                mime="text/csv"
            )

            st.write(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    except Exception as e:
        st.error(f"Error fetching data: {e}")
