import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import yfinance as yf
import plotly.graph_objects as go

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
# Technical Indicators
# -----------------------
def calculate_rsi(data, window=14):
    delta = data["Close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    data["RSI"] = 100 - (100 / (1 + rs))
    return data

def calculate_macd(data, short=12, long=26, signal=9):
    short_ema = data["Close"].ewm(span=short, adjust=False).mean()
    long_ema = data["Close"].ewm(span=long, adjust=False).mean()
    data["MACD"] = short_ema - long_ema
    data["Signal"] = data["MACD"].ewm(span=signal, adjust=False).mean()
    return data

def calculate_bollinger_bands(data, window=20, num_std=2):
    rolling_mean = data["Close"].rolling(window=window).mean()
    rolling_std = data["Close"].rolling(window=window).std()
    data["BB_Upper"] = rolling_mean + (rolling_std * num_std)
    data["BB_Lower"] = rolling_mean - (rolling_std * num_std)
    return data

def get_confluence_levels(hist, show_ma=True, show_bb=True):
    levels = []
    if show_ma:
        if "MA20" in hist: levels.append(hist["MA20"].iloc[-1])
        if "MA50" in hist: levels.append(hist["MA50"].iloc[-1])
    if show_bb:
        if "BB_Upper" in hist: levels.append(hist["BB_Upper"].iloc[-1])
        if "BB_Lower" in hist: levels.append(hist["BB_Lower"].iloc[-1])
    levels += [hist['Close'].max(), hist['Close'].min()]
    levels = sorted(list(set([round(x, 2) for x in levels if pd.notna(x)])))
    return levels

# -----------------------
# Streamlit App
# -----------------------
st.set_page_config(page_title="S&P 500 Interactive Dashboard", layout="wide")
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to:", ["Dashboard", "Info"])

# -----------------------
# Information Page
# -----------------------
if page == "Info":
    st.title("ℹ️ Dashboard Information")
    st.markdown("""
    Welcome to the S&P 500 Interactive Dashboard! This page explains all the tools and indicators.  

    ---
    ### Data Requirements for Indicators:
    - MA20 → needs **20+ data points**
    - MA50 → needs **50+ data points**
    - Bollinger Bands → needs **20+ data points**
    - RSI → needs **14+ data points**
    - MACD → needs **26+ data points**

    If you select a shorter date range, simplified charts will appear instead.
    """)

# -----------------------
# Dashboard
# -----------------------
else:
    st.title("📈 S&P 500 Interactive Dashboard")
    tickers = get_sp500_tickers()
    selected = st.selectbox("Select a company:", tickers if tickers else ["None"])

    if selected != "None":
        try:
            ticker_symbol = selected.split("(")[-1].replace(")", "").strip()

            # Date range
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Start date", datetime.now() - timedelta(days=365))
            with col2:
                end_date = st.date_input("End date", datetime.now())

            st.write(f"Fetching historical data for: {ticker_symbol}")
            hist = yf.download(ticker_symbol, start=start_date, end=end_date).dropna()
            hist.columns = hist.columns.get_level_values(0)
            filtered_hist = hist.loc[start_date:end_date]

            if filtered_hist.empty:
                st.warning("No historical data available for this ticker in the selected date range.")
            else:
                st.subheader(selected)

                # ------------------- Last N Days Table -------------------
                n_days = 10
                last_n_days = filtered_hist.tail(n_days)
                st.write(f"### Last {min(n_days, len(filtered_hist))} Days of Historical Prices")
                st.dataframe(last_n_days)

                # Sidebar indicators
                st.sidebar.header("Chart Options")
                show_ma = st.sidebar.checkbox("Show Moving Averages (MA20 & MA50)", value=True)
                show_bb = st.sidebar.checkbox("Show Bollinger Bands", value=True)
                show_rsi = st.sidebar.checkbox("Show RSI", value=True)
                show_macd = st.sidebar.checkbox("Show MACD", value=True)
                show_volume = st.sidebar.checkbox("Show Volume", value=True)
                show_confluence = st.sidebar.checkbox("Show Confluence Levels", value=True)

                # ------------------- Price Chart -------------------
                st.write("### Price Chart with Indicators")
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=filtered_hist.index, y=filtered_hist["Close"], mode="lines+markers", name="Close"))

                # Moving Averages
                if show_ma:
                    if len(filtered_hist) >= 20:
                        filtered_hist["MA20"] = filtered_hist["Close"].rolling(window=20).mean()
                        fig.add_trace(go.Scatter(x=filtered_hist.index, y=filtered_hist["MA20"], mode="lines", name="MA20"))
                    else:
                        st.info("MA20 requires at least 20 data points.")
                    if len(filtered_hist) >= 50:
                        filtered_hist["MA50"] = filtered_hist["Close"].rolling(window=50).mean()
                        fig.add_trace(go.Scatter(x=filtered_hist.index, y=filtered_hist["MA50"], mode="lines", name="MA50"))
                    else:
                        st.info("MA50 requires at least 50 data points.")

                # Bollinger Bands
                if show_bb:
                    if len(filtered_hist) >= 20:
                        filtered_hist = calculate_bollinger_bands(filtered_hist)
                        fig.add_trace(go.Scatter(x=filtered_hist.index, y=filtered_hist["BB_Upper"], mode="lines", name="BB Upper", line=dict(dash="dash")))
                        fig.add_trace(go.Scatter(x=filtered_hist.index, y=filtered_hist["BB_Lower"], mode="lines", name="BB Lower", line=dict(dash="dash")))
                    else:
                        st.info("Bollinger Bands require at least 20 data points.")

                # Confluence
                if show_confluence:
                    confluence_levels = get_confluence_levels(filtered_hist, show_ma, show_bb)
                    for level in confluence_levels:
                        fig.add_hline(y=level, line_dash="dot", line_color="purple", annotation_text=f"Confluence: {level}", annotation_position="top right")

                st.plotly_chart(fig, use_container_width=True)

                # ------------------- Volume Chart -------------------
                if show_volume:
                    st.write("### Volume")
                    fig_vol = go.Figure()
                    fig_vol.add_trace(go.Bar(x=filtered_hist.index, y=filtered_hist["Volume"], name="Volume"))
                    st.plotly_chart(fig_vol, use_container_width=True)
                    st.caption("📊 Volume works with any number of data points.")

                # ------------------- RSI Chart -------------------
                if show_rsi:
                    st.write("### RSI")
                    if len(filtered_hist) >= 14:
                        filtered_hist = calculate_rsi(filtered_hist)
                        fig_rsi = go.Figure()
                        fig_rsi.add_trace(go.Scatter(x=filtered_hist.index, y=filtered_hist["RSI"], mode="lines", name="RSI"))
                        fig_rsi.add_hline(y=70, line_dash="dash", line_color="red")
                        fig_rsi.add_hline(y=30, line_dash="dash", line_color="green")
                        st.plotly_chart(fig_rsi, use_container_width=True)
                    else:
                        st.warning("RSI requires at least 14 data points.")

                # ------------------- MACD Chart -------------------
                if show_macd:
                    st.write("### MACD")
                    if len(filtered_hist) >= 26:
                        filtered_hist = calculate_macd(filtered_hist)
                        fig_macd = go.Figure()
                        fig_macd.add_trace(go.Scatter(x=filtered_hist.index, y=filtered_hist["MACD"], mode="lines", name="MACD"))
                        fig_macd.add_trace(go.Scatter(x=filtered_hist.index, y=filtered_hist["Signal"], mode="lines", name="Signal"))
                        st.plotly_chart(fig_macd, use_container_width=True)
                    else:
                        st.warning("MACD requires at least 26 data points.")

                # ------------------- Summary Metrics -------------------
                st.write("### Summary Metrics")
                st.metric("Start Price", f"${filtered_hist['Close'].iloc[0]:.2f}")
                st.metric("Current Price", f"${filtered_hist['Close'].iloc[-1]:.2f}")
                st.metric("High", f"${filtered_hist['High'].max():.2f}")
                st.metric("Low", f"${filtered_hist['Low'].min():.2f}")

                # ------------------- Download CSV -------------------
                csv = filtered_hist.to_csv().encode("utf-8")
                st.download_button(
                    label="⬇️ Download filtered data as CSV",
                    data=csv,
                    file_name=f"{ticker_symbol}_historical_filtered.csv",
                    mime="text/csv",
                )

            st.write(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        except Exception as e:
            st.error(f"Error fetching data: {e}")
