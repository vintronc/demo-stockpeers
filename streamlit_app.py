import streamlit as st
import yfinance as yf
import pandas as pd
import altair as alt

st.set_page_config(
    page_title="Stock peer group analysis",
    page_icon=":chart_with_upwards_trend:",
    layout="wide",
)

"""
# :chart_with_upwards_trend: Stock peer group analysis

Easily compare stocks against others in their peer group.
"""

""  # Add some space.

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
        st.query_params["stocks"] = stocks_to_str(st.session_state.tickers_input)
    else:
        st.query_params.pop("stocks", None)


cols = st.columns([1, 2])
controls = cols[0].container(border=True, height="stretch")

with controls:
    """
    #### Stocks to compare
    """

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

if not tickers:
    st.stop()

# Time horizon selector
horizon_map = {
    "1 Month": "1mo",
    "6 Months": "6mo",
    "1 Year": "1y",
    "5 Years": "5y",
    "10 Years": "10y",
}

with controls:
    horizon = st.segmented_control(
        "Time horizon",
        options=list(horizon_map.keys()),
        default="6 Months",
        width="stretch",
    )


@st.cache_resource(show_spinner=False)
def load_data(tickers, period):
    tickers_obj = yf.Tickers(tickers)
    data = tickers_obj.history(period=period)
    if data is None:
        raise RuntimeError("YFinance returned no data.")
    return data["Close"]


# Load the data
try:
    data = load_data(tickers, horizon_map[horizon])
except yf.exceptions.YFRateLimitError as e:
    st.warning("YFinance is rate-limiting us :(\nTry again later.")
    data = []
    load_data.clear() # Remove the bad cache entry.

if not len(data):
    st.error("No data")
    st.stop()

# Normalize prices (start at 1)
normalized = data.div(data.iloc[0])


# Plot 1: Normalized prices
with cols[1].container(border=True):
    """
    #### Normalized price
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
    )

    st.altair_chart(chart1, use_container_width=True)

""
""

# Plot individual stock vs peer average
"""
#### Individual stocks vs peer average
"""

st.caption(
    """
    For the analysis below, the "peer average" when analyzing stock X always
    excludes X itself.
    """
)

if len(tickers) <= 1:
    st.warning("Pick 2 or more tickers to compare them")
    st.stop()

tabs = st.tabs(["Delta", "Price"])

NUM_COLS = 3
tab_cols = [tab.columns(NUM_COLS) for tab in tabs]

for i, ticker in enumerate(tickers):
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

    cell_num = i % NUM_COLS
    cell = tab_cols[0][cell_num].container(border=True)
    cell.write("")
    cell.altair_chart(chart, use_container_width=True)

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

    cell = tab_cols[1][cell_num].container(border=True)
    cell.write("")
    cell.altair_chart(chart, use_container_width=True)

""
""

"""
#### Raw data
"""

data
