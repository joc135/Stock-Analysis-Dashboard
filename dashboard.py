import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import os
import plotly.express as px

db_url = os.getenv("DATABASE_URL")
if not db_url:
    st.error("DATABASE_URL not set. Please export it before running.")
    st.stop()

engine = create_engine(db_url)

@st.cache_data
def load_symbols():
    query = "SELECT DISTINCT symbol FROM stock_data ORDER BY symbol"
    return pd.read_sql(query, engine)

@st.cache_data
def load_stock_data(symbol):
    query = f"""
        SELECT date, open, close, volume
        FROM stock_data
        WHERE symbol = '{symbol}'
        ORDER BY date
    """
    return pd.read_sql(query, engine)

st.title("S&P 500 Stock Dashboard")

symbols = load_symbols()
symbol = st.sidebar.selectbox("Select a ticker", symbols["symbol"])

df = load_stock_data(symbol)

fig = px.line(df, x="date", y="close", title=f"{symbol} Closing Price")
st.plotly_chart(fig, use_container_width=True)

fig_vol = px.bar(df, x="date", y="volume", title=f"{symbol} Volume")
st.plotly_chart(fig_vol, use_container_width=True)



df["MA20"] = df["close"].rolling(window=20).mean()
df["MA60"] = df["close"].rolling(window=60).mean()
df["Returns"] = df["close"].pct_change()

fig_price = px.line(df, x="date", y="close", title=f"{symbol} Closing Price with Moving Averages")
fig_price.add_scatter(x=df["date"], y=df["MA20"], mode="lines", name="20-day MA")
fig_price.add_scatter(x=df["date"], y=df["MA60"], mode="lines", name="60-day MA")
st.plotly_chart(fig_price, use_container_width=True)

fig_ret = px.line(df, x="date", y="Returns", title=f"{symbol} Daily Returns")
st.plotly_chart(fig_ret, use_container_width=True)



st.sidebar.subheader("Correlation Heatmap")
selected_symbols = st.sidebar.multiselect(
    "Select tickers (2–10) for correlation analysis",
    options=symbols["symbol"].tolist(),
    default=["AAPL", "MSFT", "GOOG"]  
)

def load_multiple_stock_data(symbols):
    query = f"""
        SELECT symbol, date, close
        FROM stock_data
        WHERE symbol IN ({','.join("'" + s + "'" for s in symbols)})
        ORDER BY date
    """
    df = pd.read_sql(query, engine)
    df = df.pivot(index="date", columns="symbol", values="close")
    returns = df.pct_change().dropna()
    return returns

if selected_symbols and len(selected_symbols) >= 2:
    returns = load_multiple_stock_data(selected_symbols)
    corr = returns.corr()

    st.subheader("Correlation Heatmap")
    import plotly.express as px
    fig_corr = px.imshow(
        corr,
        text_auto=True,
        color_continuous_scale="RdBu",
        title="Stock Correlations"
    )
    st.plotly_chart(fig_corr, use_container_width=True)

