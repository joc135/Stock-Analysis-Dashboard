import sys
import os
import subprocess
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
from sqlalchemy import create_engine
from datetime import datetime

# Paths
ROOT_DIR = os.path.dirname(os.path.dirname(__file__))  # root folder
SRC_DIR = os.path.join(ROOT_DIR, "src")               # src folder
sys.path.insert(0, SRC_DIR)                           # insert at front to prioritize

# Config
from config import DATABASE_URL

# Ensure required build tools are installed
# setuptools and wheel must be in requirements.txt
# Install pybind11 if not installed
try:
    import pybind11
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pybind11"])

# Compile the extension on deploy if missing
so_name = f"option_pricing.cpython-{sys.version_info.major}{sys.version_info.minor}-x86_64-linux-gnu.so"
so_path = os.path.join(SRC_DIR, so_name)
setup_path = os.path.join(SRC_DIR, "pybind11_setup.py")

if not os.path.exists(so_path):
    subprocess.check_call([sys.executable, setup_path, "build_ext", "--inplace"])

# Import compiled module
from option_pricing import monte_carlo_call, monte_carlo_put


# PostgreSQL Connection

engine = create_engine(DATABASE_URL)

# Load Data
try:
    stock_data_df = pd.read_sql("SELECT * FROM stock_data", engine)
    latest_prices_df = pd.read_sql("SELECT * FROM latest_prices", engine)
except Exception as e:
    st.error(f"Error fetching data from PostgreSQL: {e}")
    st.stop()

# Ensure date columns are datetime
stock_data_df['date'] = pd.to_datetime(stock_data_df['date'])
latest_prices_df['date'] = pd.to_datetime(latest_prices_df['date'])

# Streamlit Layout
st.set_page_config(page_title="S&P 500 Dashboard", layout="wide")
st.title("S&P 500 Stock Dashboard")
st.write("Historical and Option Pricing Data for S&P 500 tickers")

# Sidebar: Ticker Selection & Option Settings
st.sidebar.header("Settings")
selected_ticker = st.sidebar.selectbox(
    "Select Ticker",
    sorted(stock_data_df['symbol'].unique())
)

# Filter historical data for selected ticker
hist_df = stock_data_df[stock_data_df['symbol'] == selected_ticker].copy()
hist_df['date'] = pd.to_datetime(hist_df['date'])
hist_df.sort_values('date', inplace=True)  # <- sort by date

# Historical Price Chart
fig_price = px.line(
    hist_df,
    x='date',
    y=['close', 'ma20', 'ma50'],
    title=f"{selected_ticker} Price & Moving Averages"
)
st.plotly_chart(fig_price)

# Historical Volume
fig_vol = px.bar(
    hist_df,
    x='date',
    y='volume',
    title=f"{selected_ticker} Historical Volume"
)
st.plotly_chart(fig_vol)

# Daily Returns & Volatility
fig_vola = px.line(
    hist_df,
    x='date',
    y=['dailyreturn', 'volatility'],
    title=f"{selected_ticker} Daily Return & Volatility"
)
st.plotly_chart(fig_vola)

# Option Pricing Section
st.header("European Option Pricing")

# Fetch latest stock price
latest_row = latest_prices_df[latest_prices_df['symbol'] == selected_ticker].iloc[-1]
S0 = latest_row['close']

# Interactive option parameters
strike_price = st.number_input("Strike Price (K)", value=float(S0), step=1.0)
expiry_years = st.number_input("Time to Expiry (Years)", value=0.25, step=0.01)
risk_free_rate = st.number_input("Risk-free Rate (r)", value=0.03, step=0.001)
volatility = st.number_input("Volatility (σ)", value=0.2, step=0.01)
simulations = st.number_input("Monte Carlo Simulations", value=10000, step=1000)

# Compute option prices
call_price = monte_carlo_call(S0, strike_price, risk_free_rate, volatility, expiry_years, int(simulations))
put_price = monte_carlo_put(S0, strike_price, risk_free_rate, volatility, expiry_years, int(simulations))

# Display results
st.subheader(f"Options Prices for {selected_ticker}")
st.write(f"**Current Price:** ${S0:.2f}")
st.write(f"**Call Option Price:** ${call_price:.2f}")
st.write(f"**Put Option Price:** ${put_price:.2f}")