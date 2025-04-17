import streamlit as st
import yfinance as yf
import pandas as pd
import altair as alt

"""
# Stock peer group analysis

Easily compare stocks against others in their peer group.
"""

STOCKS = [
    "AAPL",
    "ABBV",
    "ACN",
    "ADBE",
    "ADP",
    "AMD",
    "AMGN",
    "AMT",
    "AMZN",
    "APD",
    "AVGO",
    "AXP",
    "BA",
    "BK",
    "BKNG",
    "BMY",
    "BRK.B",
    "BSX",
    "C",
    "CAT",
    "CI",
    "CL",
    "CMCSA",
    "COST",
    "CRM",
    "CSCO",
    "CVX",
    "DE",
    "DHR",
    "DIS",
    "DUK",
    "ELV",
    "EOG",
    "EQR",
    "FDX",
    "GD",
    "GE",
    "GILD",
    "GOOG",
    "GOOGL",
    "HD",
    "HON",
    "HUM",
    "IBM",
    "ICE",
    "INTC",
    "ISRG",
    "JNJ",
    "JPM",
    "KO",
    "LIN",
    "LLY",
    "LMT",
    "LOW",
    "MA",
    "MCD",
    "MDLZ",
    "META",
    "MMC",
    "MO",
    "MRK",
    "MSFT",
    "NEE",
    "NFLX",
    "NKE",
    "NOW",
    "NVDA",
    "ORCL",
    "PEP",
    "PFE",
    "PG",
    "PLD",
    "PM",
    "PSA",
    "REGN",
    "RTX",
    "SBUX",
    "SCHW",
    "SLB",
    "SO",
    "SPGI",
    "T",
    "TJX",
    "TMO",
    "TSLA",
    "TXN",
    "UNH",
    "UNP",
    "UPS",
    "V",
    "VZ",
    "WFC",
    "WM",
    "WMT",
    "XOM",
]

DEFAULT_STOCKS = ["AAPL", "MSFT", "GOOGL", "NVDA", "AMZN", "TSLA", "META"]


def stocks_to_str(stocks):
    return ",".join(stocks)


if "tickers_input" not in st.session_state:
    st.session_state.tickers_input = st.query_params.get(
        "stocks", stocks_to_str(DEFAULT_STOCKS)
    ).split(",")


# Callback to update query param when input changes
def update_query_param():
    if st.session_state.tickers_input:
        st.query_params["stocks"] = stocks_to_str(
            st.session_state.tickers_input)
    else:
        st.query_params.pop("stocks", None)


# Input for stock tickers
tickers = st.multiselect(
    "Stock tickers",
    options=sorted(set(STOCKS) | set(st.session_state.tickers_input)),
    default=st.session_state.tickers_input,
    accept_new_options=True,
)

tickers = [t.upper() for t in tickers]

# Update query param when text input changes
if tickers:
    st.query_params["stocks"] = stocks_to_str(tickers)
else:
    # Clear the param if input is empty
    st.query_params.pop("stocks", None)

# Time horizon selector
horizon_map = {
    "1 Week": "1wk",
    "1 Month": "1mo",
    "3 Months": "3mo",
    "1 Year": "1y",
    "5 Years": "5y",
    "10 Years": "10y",
    "20 Years": "20y",
}
horizon = st.segmented_control(
    "Time horizon",
    options=list(horizon_map.keys()),
    default="3 Months",
)


@st.cache_data(show_spinner=False)
def load_data(tickers, period):
    data = pd.DataFrame()
    for ticker in tickers:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)["Close"]
        data[ticker] = hist
    return data


# Load the data
data = load_data(tickers, horizon_map[horizon])

# Normalize prices (start at 1)
normalized = data.div(data.iloc[0])

""
""

# Plot 1: Normalized prices
"""
### Normalized stock prices
"""

chart1 = (
    alt.Chart(
        normalized.reset_index().melt(
            id_vars=["Date"], var_name="Stock", value_name="Normalized price"
        )
    )
    .mark_line()
    .encode(
        x="Date:T",
        y="Normalized price:Q",
        color=alt.Color("Stock:N", legend=alt.Legend(orient="bottom")),
    )
    .properties(height=400)
)
st.altair_chart(chart1, use_container_width=True)

""
""

# Plot individual stock vs peer average
"""
### Individual stocks vs peer average

For the analysis below, the "peer average" when anlyzing stock X always
excludes X itself.
"""

tabs = st.tabs(["Delta", "Price"])

for ticker in tickers:
    # Calculate peer average (excluding current stock)
    peers = normalized.drop(columns=[ticker])
    peer_avg = peers.mean(axis=1)

    # Create Delta chart
    plot_data = pd.DataFrame(
        {
            "Date": normalized.index,
            "Delta": normalized[ticker] - peer_avg,
        }
    )

    chart = (
        alt.Chart(plot_data)
        .mark_area()
        .encode(
            x="Date:T",
            y="Delta:Q",
        )
        .properties(title=f"{ticker} minus peer average", height=300)
    )

    tabs[0].write("")
    tabs[0].altair_chart(chart, use_container_width=True)

    # Create DataFrame with peer average.
    plot_data = pd.DataFrame(
        {
            "Date": normalized.index,
            "Stock price": normalized[ticker],
            "Peer average": peer_avg,
        }
    ).melt(id_vars=["Date"], var_name="Series", value_name="Price")

    chart = (
        alt.Chart(plot_data)
        .mark_line()
        .encode(
            x="Date:T",
            y="Price:Q",
            color=alt.Color(
                "Series:N",
                scale=alt.Scale(
                    domain=["Stock price", "Peer average"], range=["red", "gray"]
                ),
                legend=alt.Legend(orient="bottom"),
            ),
            tooltip=["Date", "Series", "Price"],
        )
        .properties(title=f"{ticker} vs Peer average", height=300)
    )

    tabs[1].write("")
    tabs[1].altair_chart(chart, use_container_width=True)
