import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime

# -----------------------
# Helper Functions
# -----------------------
def calculate_bollinger_bands(df, window=20):
    df["MA20"] = df["Close"].rolling(window=window).mean()
    df["BB_Upper"] = df["MA20"] + 2 * df["Close"].rolling(window=window).std()
    df["BB_Lower"] = df["MA20"] - 2 * df["Close"].rolling(window=window).std()
    return df

def calculate_rsi(df, window=14):
    delta = df["Close"].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=window).mean()
    avg_loss = loss.rolling(window=window).mean()
    rs = avg_gain / avg_loss
    df["RSI"] = 100 - (100 / (1 + rs))
    return df

def calculate_macd(df, short=12, long=26, signal=9):
    short_ema = df["Close"].ewm(span=short, adjust=False).mean()
    long_ema = df["Close"].ewm(span=long, adjust=False).mean()
    df["MACD"] = short_ema - long_ema
    df["Signal"] = df["MACD"].ewm(span=signal, adjust=False).mean()
    return df

def get_confluence_levels(df, show_ma, show_bb):
    levels = []
    if show_ma and "MA20" in df and "MA50" in df:
        last_ma20 = df["MA20"].dropna().iloc[-1]
        last_ma50 = df["MA50"].dropna().iloc[-1]
        levels.extend([last_ma20, last_ma50])
    if show_bb and "BB_Upper" in df and "BB_Lower" in df:
        levels.extend([df["BB_Upper"].dropna().iloc[-1], df["BB_Lower"].dropna().iloc[-1]])
    return levels

# -----------------------
# Streamlit App
# -----------------------
st.set_page_config(page_title="S&P 500 Dashboard", layout="wide")
st.title("📈 S&P 500 Dashboard (with Indicators & One-Point View)")

# User inputs
ticker_symbol = st.text_input("Enter a stock ticker (e.g., AAPL, TSLA, MSFT):", "AAPL")
start_date = st.date_input("Start Date", datetime(2022, 1, 1))
end_date = st.date_input("End Date", datetime.today())

# Indicator checkboxes
show_ma = st.sidebar.checkbox("Show Moving Averages (20 & 50)", True)
show_bb = st.sidebar.checkbox("Show Bollinger Bands", True)
show_rsi = st.sidebar.checkbox("Show RSI", True)
show_macd = st.sidebar.checkbox("Show MACD", True)
show_volume = st.sidebar.checkbox("Show Volume", True)
show_confluence = st.sidebar.checkbox("Show Confluence Levels", True)

try:
    # Fetch data
    hist = yf.download(ticker_symbol, start=start_date, end=end_date)
    hist = hist.sort_index()

    if hist.empty:
        st.warning("No historical data available for this ticker in the selected date range.")
    else:
        # ------------------- Last 10 Days -------------------
        n_days = 10
        last_n_days = hist.tail(n_days)
        st.write(f"### Last {min(n_days, len(hist))} Days of Historical Prices")
        st.dataframe(last_n_days)

        # ------------------- Indicator Requirements -------------------
        st.info("""
        **Indicator Requirements:**  
        - MA20 / Bollinger Bands → 20+ data points  
        - MA50 → 50+ data points  
        - RSI → 14+ data points  
        - MACD → 26+ data points  
        """)

        # ------------------- Minimal One Data Point View -------------------
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
            st.caption("📌 Not enough data for indicators. Showing single/multi-point close price chart.")

        # ------------------- Indicators (only if enough data) -------------------
        else:
            if show_ma:
                if len(hist) >= 20:
                    hist["MA20"] = hist["Close"].rolling(window=20).mean()
                if len(hist) >= 50:
                    hist["MA50"] = hist["Close"].rolling(window=50).mean()

            if show_bb and len(hist) >= 20:
                hist = calculate_bollinger_bands(hist)

            if show_rsi and len(hist) >= 14:
                hist = calculate_rsi(hist)

            if show_macd and len(hist) >= 26:
                hist = calculate_macd(hist)

            if show_confluence:
                confluence_levels = get_confluence_levels(hist, show_ma, show_bb)

            # Price Chart
            st.write("### Price Chart with Indicators")
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=hist.index, y=hist["Close"], mode="lines", name="Close"))

            if show_ma and "MA20" in hist:
                fig.add_trace(go.Scatter(x=hist.index, y=hist["MA20"], mode="lines", name="MA20"))
            if show_ma and "MA50" in hist:
                fig.add_trace(go.Scatter(x=hist.index, y=hist["MA50"], mode="lines", name="MA50"))

            if show_bb and "BB_Upper" in hist:
                fig.add_trace(go.Scatter(x=hist.index, y=hist["BB_Upper"], mode="lines", name="BB Upper", line=dict(dash="dash")))
                fig.add_trace(go.Scatter(x=hist.index, y=hist["BB_Lower"], mode="lines", name="BB Lower", line=dict(dash="dash")))

            if show_confluence and len(confluence_levels) > 0:
                for level in confluence_levels:
                    fig.add_hline(y=level, line_dash="dot", line_color="purple",
                                  annotation_text=f"Confluence: {level:.2f}", annotation_position="top right")

            st.plotly_chart(fig, use_container_width=True)

        # ------------------- Volume -------------------
        if show_volume:
            st.write("### Volume")
            fig_vol = go.Figure()
            fig_vol.add_trace(go.Bar(x=hist.index, y=hist["Volume"], name="Volume"))
            st.plotly_chart(fig_vol, use_container_width=True)

        # ------------------- RSI -------------------
        if show_rsi and "RSI" in hist:
            st.write("### RSI")
            fig_rsi = go.Figure()
            fig_rsi.add_trace(go.Scatter(x=hist.index, y=hist["RSI"], mode="lines", name="RSI"))
            fig_rsi.add_hline(y=70, line_dash="dash", line_color="red")
            fig_rsi.add_hline(y=30, line_dash="dash", line_color="green")
            st.plotly_chart(fig_rsi, use_container_width=True)

        # ------------------- MACD -------------------
        if show_macd and "MACD" in hist:
            st.write("### MACD")
            fig_macd = go.Figure()
            fig_macd.add_trace(go.Scatter(x=hist.index, y=hist["MACD"], mode="lines", name="MACD"))
            fig_macd.add_trace(go.Scatter(x=hist.index, y=hist["Signal"], mode="lines", name="Signal"))
            st.plotly_chart(fig_macd, use_container_width=True)

        # ------------------- Summary Metrics -------------------
        st.write("### Summary Metrics")
        st.metric("Start Price", f"${hist['Close'].iloc[0]:.2f}")
        st.metric("Current Price", f"${hist['Close'].iloc[-1]:.2f}")
        st.metric("High", f"${hist['High'].max():.2f}")
        st.metric("Low", f"${hist['Low'].min():.2f}")

        # ------------------- Download CSV -------------------
        csv = hist.to_csv().encode("utf-8")
        st.download_button(
            label="⬇️ Download data as CSV",
            data=csv,
            file_name=f"{ticker_symbol}_historical.csv",
            mime="text/csv",
        )

except Exception as e:
    st.error(f"Error fetching data: {e}")
